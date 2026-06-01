"""
Patch index.html to add May-26 to all month/quarter arrays in the JS code.
"""

html_path = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

original_size = len(html)
changes = []

# ── 1. MONTH_ORDER (global constant, line ~526) ──────────────────────────────
old = "const MONTH_ORDER = ['Apr-25','May-25','Jun-25','Jul-25','Aug-25','Sep-25','Oct-25','Nov-25','Dec-25','Jan-26','Feb-26','Mar-26','Apr-26'];"
new = "const MONTH_ORDER = ['Apr-25','May-25','Jun-25','Jul-25','Aug-25','Sep-25','Oct-25','Nov-25','Dec-25','Jan-26','Feb-26','Mar-26','Apr-26','May-26'];"
if old in html:
    html = html.replace(old, new, 1)
    changes.append("✅ MONTH_ORDER updated")
elif new in html:
    changes.append("⚠️  MONTH_ORDER already up-to-date")
else:
    changes.append("❌ MONTH_ORDER NOT FOUND")

# ── 2. QTR_ORDER (global constant, line ~527) ────────────────────────────────
old = "const QTR_ORDER = ['Q1 (Apr-Jun)','Q2 (Jul-Sep)','Q3 (Oct-Dec)','Q4 (Jan-Mar)'];"
new = "const QTR_ORDER = ['Q1 (Apr-Jun)','Q2 (Jul-Sep)','Q3 (Oct-Dec)','Q4 (Jan-Mar)','Q1 FY27 (Apr-Jun)'];"
if old in html:
    html = html.replace(old, new, 1)
    changes.append("✅ QTR_ORDER updated")
elif new in html:
    changes.append("⚠️  QTR_ORDER already up-to-date")
else:
    changes.append("❌ QTR_ORDER NOT FOUND")

# ── 3. qmap inside getFilteredData() (line ~796) ─────────────────────────────
old = "  const qmap = {0:'Q1 (Apr-Jun)',1:'Q1 (Apr-Jun)',2:'Q1 (Apr-Jun)',3:'Q2 (Jul-Sep)',4:'Q2 (Jul-Sep)',5:'Q2 (Jul-Sep)',\r\n                6:'Q3 (Oct-Dec)',7:'Q3 (Oct-Dec)',8:'Q3 (Oct-Dec)',9:'Q4 (Jan-Mar)',10:'Q4 (Jan-Mar)',11:'Q4 (Jan-Mar)'};"
new = "  const qmap = {0:'Q1 (Apr-Jun)',1:'Q1 (Apr-Jun)',2:'Q1 (Apr-Jun)',3:'Q2 (Jul-Sep)',4:'Q2 (Jul-Sep)',5:'Q2 (Jul-Sep)',\r\n                6:'Q3 (Oct-Dec)',7:'Q3 (Oct-Dec)',8:'Q3 (Oct-Dec)',9:'Q4 (Jan-Mar)',10:'Q4 (Jan-Mar)',11:'Q4 (Jan-Mar)',\r\n                12:'Q1 FY27 (Apr-Jun)',13:'Q1 FY27 (Apr-Jun)'};"
if old in html:
    html = html.replace(old, new, 1)
    changes.append("✅ qmap (getFilteredData) updated")
elif new in html:
    changes.append("⚠️  qmap already up-to-date")
else:
    # Try LF-only variant
    old_lf = old.replace('\r\n', '\n')
    new_lf = new.replace('\r\n', '\n')
    if old_lf in html:
        html = html.replace(old_lf, new_lf, 1)
        changes.append("✅ qmap (getFilteredData) updated [LF]")
    else:
        changes.append("❌ qmap NOT FOUND — check line endings")

# ── 4. MONTHS inside processExcelData() (line ~1094) ─────────────────────────
old = "  const MONTHS = ['Apr-25','May-25','Jun-25','Jul-25','Aug-25','Sep-25','Oct-25','Nov-25','Dec-25','Jan-26','Feb-26','Mar-26','Apr-26'];"
new = "  const MONTHS = ['Apr-25','May-25','Jun-25','Jul-25','Aug-25','Sep-25','Oct-25','Nov-25','Dec-25','Jan-26','Feb-26','Mar-26','Apr-26','May-26'];"
if old in html:
    html = html.replace(old, new, 1)
    changes.append("✅ MONTHS (processExcelData) updated")
elif new in html:
    changes.append("⚠️  MONTHS (processExcelData) already up-to-date")
else:
    changes.append("❌ MONTHS (processExcelData) NOT FOUND")

# ── 5. QMAP_M inside processExcelData() (line ~1096) ─────────────────────────
old = "  const QMAP_M = {'Apr-25':'Q1 (Apr-Jun)','May-25':'Q1 (Apr-Jun)','Jun-25':'Q1 (Apr-Jun)','Jul-25':'Q2 (Jul-Sep)','Aug-25':'Q2 (Jul-Sep)','Sep-25':'Q2 (Jul-Sep)','Oct-25':'Q3 (Oct-Dec)','Nov-25':'Q3 (Oct-Dec)','Dec-25':'Q3 (Oct-Dec)','Jan-26':'Q4 (Jan-Mar)','Feb-26':'Q4 (Jan-Mar)','Mar-26':'Q4 (Jan-Mar)'};"
new = "  const QMAP_M = {'Apr-25':'Q1 (Apr-Jun)','May-25':'Q1 (Apr-Jun)','Jun-25':'Q1 (Apr-Jun)','Jul-25':'Q2 (Jul-Sep)','Aug-25':'Q2 (Jul-Sep)','Sep-25':'Q2 (Jul-Sep)','Oct-25':'Q3 (Oct-Dec)','Nov-25':'Q3 (Oct-Dec)','Dec-25':'Q3 (Oct-Dec)','Jan-26':'Q4 (Jan-Mar)','Feb-26':'Q4 (Jan-Mar)','Mar-26':'Q4 (Jan-Mar)','Apr-26':'Q1 FY27 (Apr-Jun)','May-26':'Q1 FY27 (Apr-Jun)'};"
if old in html:
    html = html.replace(old, new, 1)
    changes.append("✅ QMAP_M (processExcelData) updated")
elif new in html:
    changes.append("⚠️  QMAP_M (processExcelData) already up-to-date")
else:
    changes.append("❌ QMAP_M (processExcelData) NOT FOUND")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

new_size = len(html)
print(f"[*] Patched index.html  ({original_size//1024} KB → {new_size//1024} KB)")
for c in changes:
    print(f"    {c}")
