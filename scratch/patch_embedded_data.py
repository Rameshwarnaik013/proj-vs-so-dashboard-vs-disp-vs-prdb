"""
Patch script: Regenerate embedded JSON with Qty data and update index.html frontend.
This script:
1. Runs data_processor.py to get fresh data (including _qty fields)
2. Replaces EMBEDDED_DATA in index.html
3. Updates the frontend rendering to support kg/qty toggle
"""
import sys, os, json, re

sys.path.insert(0, r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01")
from data_processor import process_excel_data

INDEX_PATH = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\index.html"
EXCEL_PATH = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\Projection vs so vs disp vs prdn dashboard.xlsx"

# Step 1: Generate fresh data
print("[1/3] Running data processor...")
data = process_excel_data(EXCEL_PATH)
if data is None:
    print("ERROR: data processor failed!")
    sys.exit(1)

# Verify qty data exists
print(f"  proj_qty KPI: {round(data['kpis']['proj_qty']):,}")
print(f"  so_qty KPI:   {round(data['kpis']['so_qty']):,}")

# Step 2: Read index.html
print("[2/3] Patching index.html with new embedded data...")
with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace EMBEDDED_DATA JSON
json_str = json.dumps(data, ensure_ascii=False)
# Find and replace the EMBEDDED_DATA assignment
pattern = r'const EMBEDDED_DATA = \{.*?\};'
# Since the JSON is huge and on one line, use a different approach
lines = content.split('\n')
new_lines = []
for line in lines:
    if line.strip().startswith('const EMBEDDED_DATA = '):
        new_lines.append(f'const EMBEDDED_DATA = {json_str};\r')
        print(f"  Replaced EMBEDDED_DATA line (new size: {len(json_str):,} chars)")
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# Step 3: Write back
print("[3/3] Writing updated index.html...")
with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDONE! Embedded data updated with Qty fields.")
print("  Next: Update frontend rendering logic manually.")
