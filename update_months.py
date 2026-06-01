import os

files_to_update = ['data_processor.py', 'live_sync.py', 'farmley_sales_dashboard.html', 'index.html']
old_months = "['Apr-25','May-25','Jun-25','Jul-25','Aug-25','Sep-25','Oct-25','Nov-25','Dec-25','Jan-26','Feb-26','Mar-26']"
new_months = "['Apr-25','May-25','Jun-25','Jul-25','Aug-25','Sep-25','Oct-25','Nov-25','Dec-25','Jan-26','Feb-26','Mar-26','Apr-26','May-26']"
old_months_2 = "['Apr-25', 'May-25', 'Jun-25', 'Jul-25', 'Aug-25', 'Sep-25', 'Oct-25', 'Nov-25', 'Dec-25', 'Jan-26', 'Feb-26', 'Mar-26']"

for f in files_to_update:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = content.replace(old_months, new_months)
        content = content.replace(old_months_2, new_months)
        content = content.replace(old_months.replace("'", '"'), new_months.replace("'", '"'))
        content = content.replace(old_months_2.replace("'", '"'), new_months.replace("'", '"'))
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Updated {f}")
    else:
        print(f"Not found: {f}")

