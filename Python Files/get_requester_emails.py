###############
# Get requester emails from exported GeoOp job report
# Essentially just searches the second line of the description for an email
###############

import csv
import re

csv_file = r"c:\Users\asset\Downloads\jobs (41).csv" # Replace this with the .csv location
output_csv_file = r"c:\Users\asset\Downloads\unique_emails.csv" # Replace this with where you want it to save

def extract_info_from_line(text_line):
    """Extracts Name 1 (after ':'), Name 2 (after '/'), and email from a line."""
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_line)
    email = email_match.group(0) if email_match else None

    name1 = ""
    name2 = ""

    if ':' in text_line:
        after_colon = text_line.split(':', 1)[1].strip()
        name1 = after_colon.split()[0] if after_colon else ""

    if '/' in text_line:
        after_slash = text_line.split('/', 1)[1].strip()
        name2 = after_slash.split()[0] if after_slash else ""

    return name1, name2, email

def extract_emails_with_names(csv_file, output_file=output_csv_file):
    seen_emails = set()
    output_rows = []

    with open(csv_file, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            description = row.get("Job Description", "")
            lines = description.split('\n')
            if len(lines) >= 2:
                line = lines[1]
                name1, name2, email = extract_info_from_line(line)
                if email and email not in seen_emails: # Only append new emails
                    seen_emails.add(email)
                    output_rows.append([name1, name2, email])

    # Write results to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["Name 1", "Name 2", "Email"])
        writer.writerows(output_rows)

    print(f"Extracted {len(output_rows)} unique emails to {output_file}")

extract_emails_with_names(csv_file)

