import pandas as pd
import json
import os

FILE_PATH = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\Projection vs so vs disp vs prdn dashboard.xlsx"

def check_file():
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return

    print(f"File size: {os.path.getsize(FILE_PATH) / 1024 / 1024:.2f} MB")
    
    try:
        # Load only first few rows to check columns
        with pd.ExcelFile(FILE_PATH, engine='openpyxl') as xls:
            print("Sheet names:", xls.sheet_names)
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet, nrows=1)
                print(f"\nSheet: {sheet}")
                print("Columns:", df.columns.tolist())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_file()
