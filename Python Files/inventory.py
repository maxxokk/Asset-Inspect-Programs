import pandas as pd
from collections import Counter

# Shift-drag the job numbers txt file between the ""
job_nums_txt = r"c:\Users\asset\Downloads\perth_jobs_list.txt"

# Shift-drag the jobs spreadsheet (.csv) between the ""
# MAKE SURE THIS IS A .CSV FILE (Save As then select .csv)
spreadsheet = r"c:\Users\asset\Downloads\jobs (25).csv"

# Enter in what filters you want. You can enter in multiple states or statuses, statuses by putting commas between the quotation marks
# e.g. states = ["QLD", "NSW", "VIC"] or status = ["Unallocated", "Report Finalisation"]
# Make sure to spell your status correctly and use the state abbreviation
status = ["Unallocated"]
states = ["WA"]

# Make a csv with all the jobs which are in the filtered csv file, but not in your txt list
# This will save in your downloads file (if this is not working, make sure the)
make_csv = True

# Where to save your final csv file with missing jobs, and by what name. 
where_to_save = r"c:\Users\asset\Downloads\missing_jobs_WA.csv"

############################################

state_mapping = {
    "QLD": "Queensland",
    "NSW": "New South Wales",
    "SA": "South Australia",
    "NT": "Northern Territory",
    "VIC": "Victoria",
    "TAS": "Tasmania",
    "WA": "Western Australia",
    "ACT": "Australian Capital Territory"
}

state_keywords = []
for state in states:
    if state in state_mapping:
        state_keywords.append(state)
        state_keywords.append(state_mapping[state])

job_data = pd.read_csv(spreadsheet).dropna(axis=1, how="all")

with open(job_nums_txt, "r") as f:
    valid_job_numbers = set(line.strip() for line in f if line.strip())

filtered_data = job_data[job_data["Job Address State"].astype(str).str.contains(
    r'\b(?:' + '|'.join(state_keywords) + r')\b', case=False, na=False
)]

job_data = filtered_data[filtered_data["Status"].astype(str).str.contains(
    '|'.join(status), case=False, na=False
)]

job_number_counts = Counter(valid_job_numbers)
duplicates = [job_num for job_num, count in job_number_counts.items() if count > 1]

if duplicates:
    print("Duplicate job numbers found in the text file:")
    for job_num in duplicates:
        print(job_num)
else:
    print("No duplicate job numbers found in the text file.")

job_numbers_in_csv = set(job_data["Job Reference"].astype(str))

missing_in_csv = [job_num for job_num in valid_job_numbers if job_num not in job_numbers_in_csv]

if missing_in_csv:
    print("Job numbers in text file not found in the CSV file:")
    for job_num in missing_in_csv:
        if job_num.isdigit():
            print(job_num)
else:
    print("All job numbers in the text file are found in the CSV file.")

jobs_not_in_txt = job_data[~job_data["Job Reference"].astype(str).isin(valid_job_numbers)]

if make_csv:
    jobs_not_in_txt.to_csv(where_to_save, index=False)