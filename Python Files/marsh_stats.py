import csv
from collections import defaultdict
import re

valuations = ["Replacement Cost Report", "Replacement Cost Reports", "Building Valuation"]
contents_vals = ["Building & Contents Replacement Cost Report", "Building & Contents Valuation"]
desktop_valuations = ["Desktop Replacement Cost Report", "Valuation - Desktop"]
compl_desktop_vals = ["Complimentary Desktop Building Replacement Cost Report", "Complimentary Desktop Building Valuation", 'Complimentary Desktop Replacement Cost Report', "Complimentary Desktop Valuation", "Desktop Valuation - Complimentary", "Valuation - Complementary Desktop", "Valuation - Complimentary Desktop"]
risk_insps = ["Insurance Inspection", "Insurance inspection", "Hostpack Inspection", "Inspection - Jewellers"]
desk_cope = ["Desktop COPE", "Desktop COPE Report"]
all_repl = [*valuations, *contents_vals, *desktop_valuations, *compl_desktop_vals]
on_site_repl = [*valuations, *contents_vals]
desk_repl = [*desktop_valuations, *compl_desktop_vals]


def extract_domain(description):
    if not description:
        return ""
    match = re.search(r'\b[\w\.-]+@([\w-]+)\.', description)
    return match.group(1) if match else ""

def group_matches_by_column(matches, group_by):
    grouped = defaultdict(int)
    for row in matches:
        key = row.get(group_by, "").strip()
        grouped[key] += 1

    # Sort by count (descending), then by key (optional tie-breaker)
    sorted_grouped = sorted(grouped.items(), key=lambda x: (-x[1], x[0]))

    # Print results
    print(f"\nGrouped by '{group_by}':")
    for key, count in sorted_grouped:
        print(f"{key or '[Empty]'}: {count} match(es)")

def row_matches_conditions(row, conditions):
    for column, strings in conditions:
        if not strings:
            continue  # Skip this condition entirely
        cell_value = row.get(column, "")
        if not any(match in cell_value for match in strings):
            return False
    return True

def row_excluded_by_conditions(row, exclude_conditions):
    for column, strings in exclude_conditions:
        if not strings:
            continue
        cell_value = row.get(column, "")
        if any(match in cell_value for match in strings):
            return True
    return False


def enhanced_csv_reader(file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create a shallow copy so we don't modify the original dict
            enhanced_row = dict(row)
            enhanced_row["Requestor Domain"] = extract_domain(row.get("Job Description", ""))
            yield enhanced_row

def count_and_list_matches(file_path, include_conditions, exclude_conditions, dedup_columns=["Client", "Job Title"]):
    count = 0
    matching_rows = []
    seen_values = set()
    duplicate_entries = []

    for row in enhanced_csv_reader(file_path):
        if not row_matches_conditions(row, include_conditions):
            continue
        if row_excluded_by_conditions(row, exclude_conditions):
            continue

        key = (row.get(dedup_columns[0], ""), row.get(dedup_columns[1], "").lower())
        if key in seen_values:
            if "Spinnaker" not in key[0]:
                duplicate_entries.append(row)
                continue  # Skip duplicates
        seen_values.add(key)

        count += 1
        matching_rows.append(row)

    # Print duplicates after processing
    # if duplicate_entries:
        # print(f"\nSkipped {len(duplicate_entries)} duplicate entries (based on '{dedup_column}'):\n")
        # for row in duplicate_entries:
            # print(row["Job Title"])

    return count, matching_rows

underwriters = [
    "Pen Underwriting",
    "360 Commercial",
    "GOAT Insurance",
    "Arch Underwriting",
    "Axis Underwriting",
    "JUA Underwriting",
    "Strata Community Insurance",
    "Australasia Underwriting",
    "Quantum Underwriting",
    "SLE Worldwide",
    "Epsilon Underwriting",
    "Lion Underwriting",
    "The Barn Underwriting Agency",
    "Swiss Re",
    "Kokomo Holiday",
    "Genesis Underwriting",
    "Achmea",
    "One Underwriting",
    "Brooklyn Underwriting",
    "Chase Underwriting Solutions",
    "ALE Underwriting"
]

accidental_stratas = ["BCH", "BBC", "MBC", "BCCC"]

# === USAGE EXAMPLE ===
if __name__ == "__main__":
    csv_file = r"c:\Users\asset\Downloads\jobs (41).csv"

    # for underwriter in underwriters:
    #     include_conditions = [
    #         ["Client", []],
    #         ["Job Title", ["Insurance Inspection", "Insurance inspection"]],
    #         ["Billing Client", [underwriter]]
    #     ]
    #     exclude_conditions = []

    #     count, _ = count_and_list_matches(csv_file, include_conditions, exclude_conditions)
    #     print(f"{underwriter}: {count} matches")

    include_conditions = [
        ["Client", []],
        ["Job Title", [*on_site_repl]],
        ["Billing Client", []]
    ]

    exclude_conditions = [
        ["Billing Client", []],
        ["Job Title", [*desk_repl]],
        ["Client", []]
    ]

    count, matches = count_and_list_matches(csv_file, include_conditions, exclude_conditions)
    group_by = "Job Title"
    group_matches_by_column(matches, group_by)

    print(f"\nTotal matches: {count}\n")

    # for row in matches:
    #     print(f"{row["Client"]} - (({row["Billing Client"]})) - {row["Job Title"]}")
    
    # billing_set = set()
    # for row in matches:
    #     billing_set.add(row["Job Title"])
    # for x in billing_set:
    #     print(x)