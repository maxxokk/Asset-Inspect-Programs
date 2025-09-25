import subprocess
import sys

def install(package):
    """Install a package using pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

program_loc = r"C:\Users\asset\OneDrive - Asset Inspect\AI Shared Folder\Administration\Programs\autoCopy3.py"
name = "autoCopy3"

def main():
    subprocess.check_call([sys.executable, "-m", "pyinstaller", "--"+name, program_loc])

if __name__ == "__main__":
    main()