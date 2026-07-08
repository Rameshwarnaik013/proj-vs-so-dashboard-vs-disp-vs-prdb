"""
Safely merges a freshly-reprocessed dataset into the live index.html and
publishes it (commit + push), without letting months with implausibly few
source rows silently overwrite good historical data.

Used by live_sync.py's file watcher on every detected Excel save.
"""
import json
import subprocess

ALL_KEYS = ['proj', 'so', 'disp', 'pend', 'clsd', 'prdn', 'proj_qty', 'so_qty', 'disp_qty', 'pend_qty', 'clsd_qty', 'prdn_qty', 'so_amt']

# Which sheet's row_counts govern the sparsity check for each metric key
KEY_SHEET = {
    'proj': 'proj', 'proj_qty': 'proj',
    'so': 'so', 'so_qty': 'so', 'disp': 'so', 'disp_qty': 'so',
    'pend': 'so', 'pend_qty': 'so', 'clsd': 'so', 'clsd_qty': 'so', 'so_amt': 'so',
    'prdn': 'prdn', 'prdn_qty': 'prdn',
}


def _extract_embedded_data(html):
    marker = 'const EMBEDDED_DATA = '
    start_idx = html.index(marker)
    brace_count = 0
    i = html.index('{', start_idx)
    while i < len(html):
        if html[i] == '{': brace_count += 1
        elif html[i] == '}': brace_count -= 1
        if brace_count == 0:
            end_idx = html.index(';', i) + 1
            break
        i += 1
    data = json.loads(html[html.index('{', start_idx):end_idx - 1])
    return data, start_idx, end_idx


def _is_sparse(counts_for_sheet, month, months_list):
    """A month is sparse if its row count is far below its peers in the same sheet -
    a strong sign the source file is temporarily missing rows for that month rather
    than genuinely having low activity."""
    counts = counts_for_sheet or {}
    this_count = counts.get(month, 0)
    others = [counts.get(m, 0) for m in months_list if m != month and counts.get(m, 0) > 0]
    if not others:
        return False
    others_sorted = sorted(others)
    median = others_sorted[len(others_sorted) // 2]
    threshold = max(50, 0.1 * median)
    return this_count < threshold


def safe_merge_and_publish(new_result, repo_dir, html_path, log=print, do_push=True, publish=True):
    """Merges new_result into the currently-committed index.html, freezing any
    sheet-month combination that looks incomplete, then commits (+ pushes) the result.

    If publish=False, only computes and returns the merged dataset for display -
    does not touch disk or git (used for read-only cache warm-up).

    Returns a dict summary: {'changed': bool, 'frozen': [...], 'error': str|None}
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    old_data, start_idx, end_idx = _extract_embedded_data(html)

    OLD_MONTHS = old_data['monthly']['months']
    NEW_MONTHS = new_result['monthly']['months']
    MONTHS = OLD_MONTHS[:]
    for m in NEW_MONTHS:
        if m not in MONTHS:
            MONTHS.append(m)
    DIMENSIONS = list(old_data['tables'].keys())
    row_counts = new_result.get('row_counts', {})

    old_idx = {m: i for i, m in enumerate(OLD_MONTHS)}
    new_idx = {m: i for i, m in enumerate(NEW_MONTHS)}

    sparse_by_key = {}
    frozen_summary = []
    for k in ALL_KEYS:
        sheet = KEY_SHEET[k]
        sparse_months = set(m for m in NEW_MONTHS if _is_sparse(row_counts.get(sheet), m, NEW_MONTHS) and m in OLD_MONTHS)
        sparse_by_key[k] = sparse_months
        for m in sparse_months:
            frozen_summary.append(f"{k}[{m}]")

    monthly = {'months': MONTHS}
    for k in ALL_KEYS:
        vals = []
        for m in MONTHS:
            if m in sparse_by_key[k] and m in old_idx:
                vals.append(old_data['monthly'][k][old_idx[m]])
            elif m in new_idx:
                vals.append(round(new_result['monthly'][k][new_idx[m]], 2))
            elif m in old_idx:
                vals.append(old_data['monthly'][k][old_idx[m]])
            else:
                vals.append(0)
        monthly[k] = vals

    zero_metrics = {k: 0 for k in ALL_KEYS}
    merged_dim_data = {}
    for d in DIMENSIONS:
        merged_dim_data[d] = {}
        old_names = old_data['dim_data'].get(d, {})
        new_names = new_result['dim_data'].get(d, {})
        all_names = set(old_names.keys()) | set(new_names.keys())
        for name in all_names:
            old_entry = old_names.get(name)
            new_entry = new_names.get(name)
            entry = {}
            for m in MONTHS:
                base = {}
                for k in ALL_KEYS:
                    if k in sparse_by_key and m in sparse_by_key[k] and old_entry and m in old_entry:
                        base[k] = old_entry[m][k]
                    elif new_entry and m in new_entry:
                        base[k] = round(new_entry[m][k], 2)
                    elif old_entry and m in old_entry:
                        base[k] = old_entry[m][k]
                    else:
                        base[k] = 0
                entry[m] = base
            merged_dim_data[d][name] = entry

    kpis = {k: round(sum(monthly[k]), 2) for k in ALL_KEYS}

    QTR_ORDER = old_data['quarterly']['quarters']
    QMAP_M = {
        'Apr-25': 0, 'May-25': 0, 'Jun-25': 0,
        'Jul-25': 1, 'Aug-25': 1, 'Sep-25': 1,
        'Oct-25': 2, 'Nov-25': 2, 'Dec-25': 2,
        'Jan-26': 3, 'Feb-26': 3, 'Mar-26': 3,
        'Apr-26': 4, 'May-26': 4, 'Jun-26': 4
    }
    quarterly = {'quarters': QTR_ORDER}
    for k in ALL_KEYS:
        quarterly[k] = [0] * len(QTR_ORDER)
    for m in MONTHS:
        if m not in QMAP_M:
            log(f"[!] auto_publish: month {m} has no quarter mapping (data_processor.py QMAP_M needs a manual bump) - skipping it from quarterly totals")
            continue
        qi = QMAP_M[m]
        m_idx = MONTHS.index(m)
        for k in ALL_KEYS:
            quarterly[k][qi] += monthly[k][m_idx]
    for k in ALL_KEYS:
        quarterly[k] = [round(v, 2) for v in quarterly[k]]

    tables = {}
    for d in DIMENSIONS:
        rows = []
        for name, months_data in merged_dim_data[d].items():
            row = {'name': name}
            for k in ALL_KEYS:
                row[k] = sum(mdata[k] for mdata in months_data.values())
            row['so_proj_pct'] = round((row['so'] / row['proj'] * 100), 1) if row['proj'] > 0 else 0
            row['disp_so_pct'] = round((row['disp'] / row['so'] * 100), 1) if row['so'] > 0 else 0
            row['so_proj_pct_qty'] = round((row['so_qty'] / row['proj_qty'] * 100), 1) if row['proj_qty'] > 0 else 0
            row['disp_so_pct_qty'] = round((row['disp_qty'] / row['so_qty'] * 100), 1) if row['so_qty'] > 0 else 0
            rows.append(row)
        tables[d] = sorted(rows, key=lambda x: x['proj'], reverse=True)

    filters = {d: sorted(list(merged_dim_data[d].keys())) for d in DIMENSIONS}

    final_merged = {
        'kpis': kpis,
        'monthly': monthly,
        'quarterly': quarterly,
        'tables': tables,
        'filters': filters,
        'dim_data': merged_dim_data,
        'row_counts': row_counts,
    }

    if frozen_summary:
        log(f"[!] auto_publish: froze {len(frozen_summary)} sheet-month values with implausibly few source rows: {', '.join(sorted(set(frozen_summary))[:15])}{' ...' if len(frozen_summary) > 15 else ''}")

    # Did anything actually change vs what's already committed?
    unchanged = (monthly == old_data['monthly'])
    if unchanged or not publish:
        if unchanged:
            log("[*] auto_publish: no material change vs currently-published data, skipping commit.")
        return {'changed': not unchanged, 'frozen': sorted(set(frozen_summary)), 'error': None, 'data': final_merged}

    json_str = json.dumps(final_merged, separators=(',', ': '))
    new_line = f'const EMBEDDED_DATA = {json_str};'
    html2 = html[:start_idx] + new_line + html[end_idx:]
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html2)
    log(f"[*] auto_publish: patched index.html ({len(json_str)//1024} KB)")

    error = None
    try:
        subprocess.run(['git', 'add', 'index.html'], cwd=repo_dir, check=True, capture_output=True, text=True)
        commit_msg = "Auto-update: live sync reprocessed Excel"
        if frozen_summary:
            commit_msg += f" ({len(set(frozen_summary))} sheet-month values frozen - low row count)"
        result = subprocess.run(['git', 'commit', '-m', commit_msg], cwd=repo_dir, capture_output=True, text=True)
        if result.returncode != 0 and 'nothing to commit' not in result.stdout:
            error = f"git commit failed: {result.stdout}\n{result.stderr}"
            log(f"[ERROR] {error}")
        elif do_push:
            push_result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_dir, capture_output=True, text=True)
            if push_result.returncode != 0:
                error = f"git push failed: {push_result.stdout}\n{push_result.stderr}"
                log(f"[ERROR] {error}")
            else:
                log("[*] auto_publish: pushed to origin/main")
    except Exception as e:
        error = str(e)
        log(f"[ERROR] auto_publish git step failed: {error}")

    return {'changed': True, 'frozen': sorted(set(frozen_summary)), 'error': error, 'data': final_merged}
