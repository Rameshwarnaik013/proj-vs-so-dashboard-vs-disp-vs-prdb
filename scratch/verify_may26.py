html = open(r'c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\index.html', encoding='utf-8').read()

needles = {
    'MONTH_ORDER has May-26': ("May-26']", html[html.find('MONTH_ORDER'):html.find('MONTH_ORDER')+220]),
    'QTR_ORDER has Q1 FY27':  ("Q1 FY27", html[html.find('QTR_ORDER'):html.find('QTR_ORDER')+220]),
    'qmap has index 13':      ("13:", html[html.find('const qmap'):html.find('const qmap')+450]),
    'processExcelData MONTHS has May-26': ("May-26", html[html.find('const MONTHS'):html.find('const MONTHS')+220]),
    'QMAP_M has Apr-26':      ("Apr-26", html[html.find('QMAP_M'):html.find('QMAP_M')+500]),
    'QMAP_M has May-26':      ("May-26", html[html.find('QMAP_M'):html.find('QMAP_M')+500]),
}

all_ok = True
for label, (needle, snippet) in needles.items():
    status = 'OK' if needle in snippet else 'MISSING'
    if status == 'MISSING':
        all_ok = False
    print(f'[{status}] {label}')

print()
if all_ok:
    print('All patches applied successfully!')
else:
    print('Some patches may be missing - check above.')
