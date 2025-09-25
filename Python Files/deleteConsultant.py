import os

# Deletes all by-week-shortcut files associated with a given consultant (can otherwise be a pain to go through every week of the year and manually delete them)
# Replace this with the local location for the Weeks folder
base_directory = r"c:\Users\asset\OneDrive - Asset Inspect\Asset Inspect Shared Folder\Runs\Weeks\2025"
consultant = "Lachlan"

def delete_files(base_directory):
    for root, _, files in os.walk(base_directory):
        for file in files:
            if file.startswith(consultant):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

if __name__ == "__main__":
    if os.path.isdir(base_directory):
        delete_files(base_directory)
    else:
        print("Invalid directory.")
