"""
Patch index.html to add a Month (MMM-YY) filter to the sidebar
"""
import re

FILE = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\index.html"

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# ──────────────────────────────────────────────────
# 1. Add selectedMonths state variable after activeMetrics line
# ──────────────────────────────────────────────────
old_state = "let activeMetrics = new Set(METRICS.map(m=>m.key));"
new_state = """let activeMetrics = new Set(METRICS.map(m=>m.key));
let selectedMonths = new Set(MONTH_ORDER);  // Month filter: all selected by default"""
content = content.replace(old_state, new_state)
print("[1] Added selectedMonths state variable")

# ──────────────────────────────────────────────────
# 2. Add Month filter UI at the TOP of buildFilters function
# ──────────────────────────────────────────────────
old_build = """function buildFilters() {
  const container = document.getElementById('filter-container');
  container.innerHTML = '';
  FILTER_DIMS.forEach(({key, label}) => {"""

new_build = """function buildFilters() {
  const container = document.getElementById('filter-container');
  container.innerHTML = '';

  // ── MONTH FILTER (MMM-YY) ──
  {
    const group = document.createElement('div');
    group.className = 'filter-group';
    group.id = 'month-filter-group';
    const lbl = document.createElement('div');
    lbl.className = 'filter-label';
    lbl.innerHTML = `<span>📅 Month (MMM-YY)</span><span class="arrow">▾</span>`;
    lbl.onclick = () => { optsDiv.classList.toggle('open'); lbl.classList.toggle('open'); };
    const optsDiv = document.createElement('div');
    optsDiv.className = 'filter-opts';
    optsDiv.id = 'month-filter-opts';

    // Select All
    const allLabel = document.createElement('label');
    allLabel.className = 'filter-opt';
    allLabel.style.fontWeight = '700';
    allLabel.style.borderBottom = '1px solid var(--border)';
    allLabel.style.marginBottom = '2px';
    allLabel.style.paddingBottom = '6px';
    allLabel.style.color = 'var(--proj)';
    allLabel.innerHTML = `<input type="checkbox" checked class="month-select-all"> Select All`;
    allLabel.querySelector('input').addEventListener('change', (e) => {
      const checked = e.target.checked;
      optsDiv.querySelectorAll('input[type=checkbox]:not(.month-select-all)').forEach(cb => {
        cb.checked = checked;
      });
      applyMonthFilter();
    });
    optsDiv.appendChild(allLabel);

    MONTH_ORDER.forEach(m => {
      const item = document.createElement('label');
      item.className = 'filter-opt';
      item.innerHTML = `<input type="checkbox" checked value="${m}" class="month-cb"> ${m}`;
      item.querySelector('input').addEventListener('change', (e) => {
        const allCb = optsDiv.querySelector('.month-select-all');
        const others = optsDiv.querySelectorAll('.month-cb');
        const allChecked = Array.from(others).every(c => c.checked);
        const noneChecked = Array.from(others).every(c => !c.checked);
        allCb.checked = allChecked;
        allCb.indeterminate = !allChecked && !noneChecked;
        applyMonthFilter();
      });
      optsDiv.appendChild(item);
    });
    group.appendChild(lbl);
    group.appendChild(optsDiv);
    container.appendChild(group);
  }

  FILTER_DIMS.forEach(({key, label}) => {"""
content = content.replace(old_build, new_build)
print("[2] Added Month filter UI to buildFilters")

# ──────────────────────────────────────────────────
# 3. Add applyMonthFilter function after resetFilters
# ──────────────────────────────────────────────────
old_reset_end = """function resetFilters() {
  document.querySelectorAll('.filter-opts input[type=checkbox]').forEach(cb => {
    cb.checked = true;
    cb.indeterminate = false;
  });
  activeFilters = {};
  renderAll();
}

function isFiltered() { return Object.keys(activeFilters).length > 0; }"""

new_reset_end = """function resetFilters() {
  document.querySelectorAll('.filter-opts input[type=checkbox]').forEach(cb => {
    cb.checked = true;
    cb.indeterminate = false;
  });
  activeFilters = {};
  selectedMonths = new Set(MONTH_ORDER);
  renderAll();
}

function applyMonthFilter() {
  selectedMonths = new Set();
  document.querySelectorAll('.month-cb').forEach(cb => {
    if (cb.checked) selectedMonths.add(cb.value);
  });
  if (selectedMonths.size === 0) selectedMonths = new Set(MONTH_ORDER); // fallback: show all
  renderAll();
}

function isFiltered() { return Object.keys(activeFilters).length > 0 || selectedMonths.size < MONTH_ORDER.length; }"""
content = content.replace(old_reset_end, new_reset_end)
print("[3] Added applyMonthFilter and updated isFiltered/resetFilters")

# ──────────────────────────────────────────────────
# 4. Update getFilteredData() to respect selectedMonths
#    Replace the entire function
# ──────────────────────────────────────────────────
old_getFiltered = """function getFilteredData() {
  if (!isFiltered()) return DATA;
  // Recompute by filtering dim_data
  const dd = DATA.dim_data;
  const months = MONTH_ORDER;

  // For each active filter dim, collect allowed values
  const allowed = {};
  FILTER_DIMS.forEach(({key, label}) => {
    const fk = key.trim();
    const dimKey = label === 'Item Parent' ? 'Item Parent' :
                   label === 'Customer' ? 'Customer' :
                   label === 'Customer Group' ? 'Customer Group' :
                   label === 'Origin' ? 'Origin' :
                   label === 'New Mis Item Group' ? 'New Mis Item Group' :
                   label === 'Item Type (KVI/VA)' ? 'Item Type' :
                   label === 'Packaging Type' ? 'Packaging Type' :
                   label === 'Packaging Method' ? 'Packaging Method' :
                   label === 'Sales Order Created By' ? 'Sales Order Created By' : label;
    if (activeFilters[key]) {
      // excluded values
      allowed[dimKey] = activeFilters[key]; // these are EXCLUDED
    }
  });

  // For each filter being applied, we sum over the dim_data but exclude certain values
  // Strategy: find the first active filter and use its dim to compute monthly sums
  // If multiple filters active, use the most restrictive approach: sum only matching rows
  // Since dim_data is per-dimension, multi-dim filtering is approximate via intersection

  // Simple approach: use the primary filter dim that has the most exclusions
  const activeDims = Object.keys(activeFilters);
  if (activeDims.length === 0) return DATA;

  // Use first active dim
  const primaryFiltKey = activeDims[0];
  const primaryLabel = FILTER_DIMS.find(d => d.key === primaryFiltKey)?.label || '';
  const dimKey = primaryLabel === 'Item Parent' ? 'Item Parent' :
                 primaryLabel === 'Customer' ? 'Customer' :
                 primaryLabel === 'Customer Group' ? 'Customer Group' :
                 primaryLabel === 'Origin' ? 'Origin' :
                 primaryLabel === 'New Mis Item Group' ? 'New Mis Item Group' :
                 primaryLabel === 'Item Type (KVI/VA)' ? 'Item Type' :
                 primaryLabel === 'Packaging Type' ? 'Packaging Type' :
                 primaryLabel === 'Packaging Method' ? 'Packaging Method' :
                 primaryLabel === 'Sales Order Created By' ? 'Sales Order Created By' : primaryLabel;

  const dimDD = dd[dimKey];
  if (!dimDD) return DATA;
  const excluded = activeFilters[primaryFiltKey];

  // Sum monthly data excluding excluded values
  const monthly = { months: MONTH_ORDER, proj:[], so:[], disp:[], pend:[], clsd:[], prdn:[] };
  MONTH_ORDER.forEach(m => {
    let p=0,s=0,d=0,pnd=0,c=0,r=0;
    Object.entries(dimDD).forEach(([name, mdata]) => {
      if (excluded && excluded.has(name)) return;
      const md = mdata[m] || {};
      p += md.proj||0; s += md.so||0; d += md.disp||0; pnd += md.pend||0; c += md.clsd||0; r += md.prdn||0;
    });
    monthly.proj.push(Math.round(p));
    monthly.so.push(Math.round(s));
    monthly.disp.push(Math.round(d));
    monthly.pend.push(Math.round(pnd));
    monthly.clsd.push(Math.round(c));
    monthly.prdn.push(Math.round(r));
  });

  // Quarterly
  const qmap = {0:'Q1 (Apr-Jun)',1:'Q1 (Apr-Jun)',2:'Q1 (Apr-Jun)',3:'Q2 (Jul-Sep)',4:'Q2 (Jul-Sep)',5:'Q2 (Jul-Sep)',
                6:'Q3 (Oct-Dec)',7:'Q3 (Oct-Dec)',8:'Q3 (Oct-Dec)',9:'Q4 (Jan-Mar)',10:'Q4 (Jan-Mar)',11:'Q4 (Jan-Mar)'};
  const qdata = {quarters:QTR_ORDER, proj:[0,0,0,0], so:[0,0,0,0], disp:[0,0,0,0], pend:[0,0,0,0], clsd:[0,0,0,0], prdn:[0,0,0,0]};
  MONTH_ORDER.forEach((m, i) => {
    const qi = QTR_ORDER.indexOf(qmap[i]);
    ['proj','so','disp','pend','clsd','prdn'].forEach(k => { qdata[k][qi] += monthly[k][i]; });
  });

  const kpis = {
    proj: monthly.proj.reduce((a,b)=>a+b,0),
    so: monthly.so.reduce((a,b)=>a+b,0),
    disp: monthly.disp.reduce((a,b)=>a+b,0),
    pend: monthly.pend.reduce((a,b)=>a+b,0),
    clsd: monthly.clsd.reduce((a,b)=>a+b,0),
    prdn: monthly.prdn.reduce((a,b)=>a+b,0),
  };

  // Recompute table for active dim using filtered values from dim_data
  const tables = {};
  const tDimKey = dimKey;
  const tDD = dd[tDimKey];
  if (tDD) {
    const rows = [];
    Object.entries(tDD).forEach(([name, mdata]) => {
      if (excluded && excluded.has(name)) return;
      let p=0,s=0,d=0,pnd=0,c=0,r=0;
      MONTH_ORDER.forEach(m => {
        const md = mdata[m] || {};
        p += md.proj||0; s += md.so||0; d += md.disp||0; pnd += md.pend||0; c += md.clsd||0; r += md.prdn||0;
      });
      rows.push({name, proj:p, so:s, disp:d, pend:pnd, clsd:c, prdn:r,
        so_proj_pct: p>0 ? +(s/p*100).toFixed(1) : 0,
        disp_so_pct: s>0 ? +(d/s*100).toFixed(1) : 0
      });
    });
    rows.sort((a,b) => b.proj - a.proj);
    tables[dimKey] = rows;
  }

  return { ...DATA, kpis, monthly, quarterly: qdata, tables: {...DATA.tables, ...tables} };
}"""

new_getFiltered = """function getFilteredData() {
  const monthFiltered = selectedMonths.size < MONTH_ORDER.length;
  const dimFiltered = Object.keys(activeFilters).length > 0;
  if (!monthFiltered && !dimFiltered) return DATA;

  const dd = DATA.dim_data;
  const filteredMonths = monthFiltered ? MONTH_ORDER.filter(m => selectedMonths.has(m)) : MONTH_ORDER;

  // Determine primary dim filter
  const activeDims = Object.keys(activeFilters);
  let dimKey = 'Item Parent'; // default
  let excluded = null;
  if (activeDims.length > 0) {
    const primaryFiltKey = activeDims[0];
    const primaryLabel = FILTER_DIMS.find(d => d.key === primaryFiltKey)?.label || '';
    dimKey = primaryLabel === 'Item Parent' ? 'Item Parent' :
             primaryLabel === 'Customer' ? 'Customer' :
             primaryLabel === 'Customer Group' ? 'Customer Group' :
             primaryLabel === 'Origin' ? 'Origin' :
             primaryLabel === 'New Mis Item Group' ? 'New Mis Item Group' :
             primaryLabel === 'Item Type (KVI/VA)' ? 'Item Type' :
             primaryLabel === 'Packaging Type' ? 'Packaging Type' :
             primaryLabel === 'Packaging Method' ? 'Packaging Method' :
             primaryLabel === 'Sales Order Created By' ? 'Sales Order Created By' : primaryLabel;
    excluded = activeFilters[primaryFiltKey];
  }

  const dimDD = dd[dimKey];
  if (!dimDD) return DATA;

  // Sum monthly data excluding excluded values AND respecting month filter
  const monthly = { months: MONTH_ORDER, proj:[], so:[], disp:[], pend:[], clsd:[], prdn:[] };
  MONTH_ORDER.forEach(m => {
    if (!selectedMonths.has(m)) {
      monthly.proj.push(0); monthly.so.push(0); monthly.disp.push(0);
      monthly.pend.push(0); monthly.clsd.push(0); monthly.prdn.push(0);
      return;
    }
    let p=0,s=0,d=0,pnd=0,c=0,r=0;
    Object.entries(dimDD).forEach(([name, mdata]) => {
      if (excluded && excluded.has(name)) return;
      const md = mdata[m] || {};
      p += md.proj||0; s += md.so||0; d += md.disp||0; pnd += md.pend||0; c += md.clsd||0; r += md.prdn||0;
    });
    monthly.proj.push(Math.round(p));
    monthly.so.push(Math.round(s));
    monthly.disp.push(Math.round(d));
    monthly.pend.push(Math.round(pnd));
    monthly.clsd.push(Math.round(c));
    monthly.prdn.push(Math.round(r));
  });

  // Quarterly
  const qmap = {0:'Q1 (Apr-Jun)',1:'Q1 (Apr-Jun)',2:'Q1 (Apr-Jun)',3:'Q2 (Jul-Sep)',4:'Q2 (Jul-Sep)',5:'Q2 (Jul-Sep)',
                6:'Q3 (Oct-Dec)',7:'Q3 (Oct-Dec)',8:'Q3 (Oct-Dec)',9:'Q4 (Jan-Mar)',10:'Q4 (Jan-Mar)',11:'Q4 (Jan-Mar)'};
  const qdata = {quarters:QTR_ORDER, proj:[0,0,0,0], so:[0,0,0,0], disp:[0,0,0,0], pend:[0,0,0,0], clsd:[0,0,0,0], prdn:[0,0,0,0]};
  MONTH_ORDER.forEach((m, i) => {
    const qi = QTR_ORDER.indexOf(qmap[i]);
    ['proj','so','disp','pend','clsd','prdn'].forEach(k => { qdata[k][qi] += monthly[k][i]; });
  });

  const kpis = {
    proj: monthly.proj.reduce((a,b)=>a+b,0),
    so: monthly.so.reduce((a,b)=>a+b,0),
    disp: monthly.disp.reduce((a,b)=>a+b,0),
    pend: monthly.pend.reduce((a,b)=>a+b,0),
    clsd: monthly.clsd.reduce((a,b)=>a+b,0),
    prdn: monthly.prdn.reduce((a,b)=>a+b,0),
  };

  // Recompute tables for ALL dims using month filter
  const tables = {};
  for (const [dk, dimData] of Object.entries(dd)) {
    const rows = [];
    Object.entries(dimData).forEach(([name, mdata]) => {
      if (dk === dimKey && excluded && excluded.has(name)) return;
      let p=0,s=0,d=0,pnd=0,c=0,r=0;
      filteredMonths.forEach(m => {
        const md = mdata[m] || {};
        p += md.proj||0; s += md.so||0; d += md.disp||0; pnd += md.pend||0; c += md.clsd||0; r += md.prdn||0;
      });
      if (p === 0 && s === 0 && d === 0 && pnd === 0 && c === 0 && r === 0) return; // skip empty
      rows.push({name, proj:p, so:s, disp:d, pend:pnd, clsd:c, prdn:r,
        so_proj_pct: p>0 ? +(s/p*100).toFixed(1) : 0,
        disp_so_pct: s>0 ? +(d/s*100).toFixed(1) : 0
      });
    });
    rows.sort((a,b) => b.proj - a.proj);
    tables[dk] = rows;
  }

  return { ...DATA, kpis, monthly, quarterly: qdata, tables };
}"""

content = content.replace(old_getFiltered, new_getFiltered)
print("[4] Updated getFilteredData to support month filtering")

# ──────────────────────────────────────────────────
# 5. Update getSparkline to also respect selectedMonths
# ──────────────────────────────────────────────────
old_sparkline = """function getSparkline(name, metricKey) {
  // Get monthly data for this name from dim_data
  const dimKey = activeDim;
  const dd = DATA.dim_data[dimKey];
  if (!dd || !dd[name]) return MONTHS.map(()=>0);
  return MONTHS.map(m => (dd[name][m] || {})[metricKey] || 0);
}"""

new_sparkline = """function getSparkline(name, metricKey) {
  // Get monthly data for this name from dim_data, respecting month filter
  const dimKey = activeDim;
  const dd = DATA.dim_data[dimKey];
  if (!dd || !dd[name]) return MONTH_ORDER.map(()=>0);
  return MONTH_ORDER.map(m => {
    if (!selectedMonths.has(m)) return 0;
    return (dd[name][m] || {})[metricKey] || 0;
  });
}"""
content = content.replace(old_sparkline, new_sparkline)
print("[5] Updated getSparkline to respect month filter")

# ──────────────────────────────────────────────────
# 6. Update monthly chart subtitle to show filtered months
# ──────────────────────────────────────────────────
old_monthly_sub = '<div class="chart-sub" id="monthly-sub">All metrics · Apr-25 → Mar-26</div>'
new_monthly_sub = '<div class="chart-sub" id="monthly-sub">All metrics · Apr-25 → Mar-26</div>'
# Keep as is, but update renderCharts to dynamically set it


# ──────────────────────────────────────────────────
# 7. Update live sync to also reset month filter
# ──────────────────────────────────────────────────
old_live_reset = "          DATA = newData;\n          activeFilters = {};"
new_live_reset = "          DATA = newData;\n          activeFilters = {};\n          selectedMonths = new Set(MONTH_ORDER);"
content = content.replace(old_live_reset, new_live_reset)
print("[7] Updated live sync to reset month filter")

# ──────────────────────────────────────────────────
# 8. Update Excel upload to also reset month filter
# ──────────────────────────────────────────────────
old_excel_reset = "        DATA = newData;\n        activeFilters = {};"
new_excel_reset = "        DATA = newData;\n        activeFilters = {};\n        selectedMonths = new Set(MONTH_ORDER);"
content = content.replace(old_excel_reset, new_excel_reset)
print("[8] Updated Excel upload to reset month filter")

# Write the patched file
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ All patches applied successfully!")
print("   - Month filter added to sidebar (using MMM-YY from Projection, SO and dispatch, Prdn tabs)")
print("   - KPIs, Charts, and Tables all respect the month filter")
print("   - Reset button clears month filter too")
