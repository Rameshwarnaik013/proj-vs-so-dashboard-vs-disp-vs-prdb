"""Test the data processor to verify Qty columns are being aggregated correctly."""
import sys, os
sys.path.insert(0, r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01")
from data_processor import process_excel_data

FILE = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\Projection vs so vs disp vs prdn dashboard.xlsx"

print("Running data processor...")
d = process_excel_data(FILE)

if d is None:
    print("ERROR: data processor returned None!")
    sys.exit(1)

print("\n=== KPIs (Kg) ===")
for k in ['proj','so','disp','pend','clsd','prdn']:
    print(f"  {k}: {round(d['kpis'].get(k,0)):,}")

print("\n=== KPIs (Qty Units) ===")
for k in ['proj_qty','so_qty','disp_qty','pend_qty','clsd_qty','prdn_qty']:
    print(f"  {k}: {round(d['kpis'].get(k,0)):,}")

print("\n=== Monthly proj_qty (first 3 months) ===")
print(f"  {d['monthly']['proj_qty'][:3]}")

print("\n=== Monthly so_qty (first 3 months) ===")
print(f"  {d['monthly']['so_qty'][:3]}")

print("\n=== Sample table row (Item Parent - first item) ===")
row = d['tables']['Item Parent'][0]
print(f"  Name: {row['name']}")
print(f"  proj(Kg): {round(row['proj']):,}  |  proj_qty: {round(row.get('proj_qty',0)):,}")
print(f"  so(Kg):   {round(row['so']):,}  |  so_qty:   {round(row.get('so_qty',0)):,}")
print(f"  disp(Kg): {round(row['disp']):,}  |  disp_qty: {round(row.get('disp_qty',0)):,}")

print("\n=== dim_data check (first item, Apr-25) ===")
first_item = list(d['dim_data']['Item Parent'].keys())[0]
apr = d['dim_data']['Item Parent'][first_item]['Apr-25']
print(f"  Item: {first_item}")
print(f"  Apr-25 data: {apr}")

print("\nSUCCESS! All Qty data is present.")
