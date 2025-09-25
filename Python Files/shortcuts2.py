###########################
# This program generates a ps1 (powershell) file for each word document (job sheet) in all_dir, and saves them all, unordered, in powershell_scripts_dir. 
# It then creates a batch file for each job sheet and saves these batch files by year->week.
# This script is also necessary for the shortcutMaker application to work. 
###########################



import os
from datetime import datetime, timedelta

# Define directories (Fixed paths) !!!UPDATE THESE TO MATCH YOUR COMPUTER!!! that is, the "\Users\asset" part will be unique to you
all_dir = r"C:\Users\asset\OneDrive - Asset Inspect\AI Shared Folder\Runs\All"
weeks_job_dir = r"C:\Users\asset\OneDrive - Asset Inspect\AI Shared Folder\Runs\Weeks"
powershell_scripts_dir = r"C:\Users\asset\OneDrive - Asset Inspect\AI Shared Folder\Administration\Programs\OneDrive Programs\ps1_shortcuts"

# List of consultants
consultants = ["Steven", "Andrew", "Harry", "Heath", "Sean", "Alan P", "Alan S", "Eugene", "PJ"]

debug = False

# Create necessary directories
os.makedirs(weeks_job_dir, exist_ok=True)

def get_first_monday(year):
    """Calculate the first Monday of a given year."""
    first_day_of_year = datetime(year, 1, 1)
    days_to_add = (7 - first_day_of_year.weekday()) % 7
    return first_day_of_year + timedelta(days=days_to_add)

def generate_weekly_scripts():
    """Generate weekly PowerShell and batch scripts for consultants."""
    current_year = datetime.today().year
    start_date = get_first_monday(current_year)
    end_date = datetime(current_year + 1, 1, 1)

    current_date = start_date
    while current_date < end_date:
        date_str = current_date.strftime('%d_%m_%Y')
        month_name = current_date.strftime('%B')
        for consultant in consultants:
            # Filenames
            ps1_file_name = f"{consultant} - Wk {date_str}.ps1"
            bat_file_name = f"{consultant} - Wk {date_str}.bat"

            # Paths
            ps1_file_path = os.path.join(powershell_scripts_dir, ps1_file_name)
            bat_folder_path = os.path.join(weeks_job_dir, str(current_date.year), f"{current_date.month} {current_date.strftime('%B')}", date_str)
            bat_file_path = os.path.join(bat_folder_path, bat_file_name)

            os.makedirs(bat_folder_path, exist_ok=True)

            if os.path.exists(ps1_file_path) and os.path.exists(bat_file_path):
                continue

            bat_content = f"""@echo off
set "OneDrivePath=%OneDrive%"
powershell.exe {"-NoExit" if debug else "-WindowStyle Hidden"} -ExecutionPolicy Bypass -File "%OneDrivePath%\\AI Shared Folder\\Administration\\Programs\\OneDrive Programs\\ps1_shortcuts\\{ps1_file_name}"
"""

            with open(bat_file_path, 'w') as bat_file:
                bat_file.write(bat_content)

            print(f"Generated .bat file: {bat_file_name}")

        current_date += timedelta(weeks=1)

# Run the function to generate the scripts
generate_weekly_scripts()
print("All scripts generated successfully.")