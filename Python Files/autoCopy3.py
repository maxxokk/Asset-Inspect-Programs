#####################
# Welcome to the autocopy program for risk improvements
# Firstly, make sure you have setup the risk improvements database. Do this by going into RI_database_setup.py (in Programs\Databases) and following the instructions.
# The purpose of this program is to take the users input, look into the database for the given RI code, and output the risk improvement (automatically copied to your clipboard)
# Most of the complexity comes from how the user inputs what they want and how the output is formatted. 
# Run this program and type "help" in the terminal for a detailed summary of all the instruction codes (as this is a fully text-based program)
# Type "example" for a detailed description of how I (Max) utilise this program.
#####################
# I am in the process of developing a windowed GUI for this program, however it is not fully implemented yet
# I am also in the process of developing a way to change the database from within this program, however this is also not fully implemented.
# In the meantime, use DB Browser for SQLite (download from the internet) to edit the database.
#####################
# Please note, there is quite a bit of dead weight in this code (old implementations, etc). I'll hopefully get around to tidying it up...
#####################

import os
import pyperclip
import sys
import sqlite3
import re
import json
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import threading
import queue
from collections import Counter

windowed = True

program_ver = "3.01"

class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.tag_configure("input", foreground="grey")
        self.text_widget.tag_configure("warning", foreground="red")

    def write(self, string):
        self.text_widget.after(0, self._write, string)

    def _write(self, string):
        self.text_widget.config(state='normal')
        if string.startswith(">>> "):
            self.text_widget.insert(tk.END, string, "input")
        elif "Warning:" in string:
            self.text_widget.insert(tk.END, string, "warning")
        else:
            self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')

    def flush(self):
        pass

class StdinRedirector:
    def __init__(self, gui_ref):
        self.input_queue = queue.Queue()
        self.gui = gui_ref

    def readline(self):
        self.gui.expecting_line_input = True
        self.gui.set_input_mode_label(multiline=False)
        line = self.input_queue.get()
        self.gui.expecting_line_input = False
        return line

    def read(self, n=-1):
        self.gui.expecting_line_input = False
        self.gui.set_input_mode_label(multiline=True)
        return self.input_queue.get()

    def push(self, text):
        self.input_queue.put(text + '\n')

class TerminalApp(tk.Tk):
    def __init__(self, target_function):
        super().__init__()
        self.title(f"AutoCopy{program_ver}")

        self.expecting_line_input = False  # Flag for Enter key behaviour

        container = ttk.Frame(self, padding=10)
        container.pack(expand=True, fill='both')

        self.controls_visible = True
        self.manual_override_disabled = False

        # Output label and box
        self.output_label = ttk.Label(container, text="Output:")
        self.output_label.pack(anchor='w')
        self.output = ScrolledText(container, height=8, wrap='word', bg='white', fg='black', font = ("Consolas", 10))
        self.output.pack(fill='both', expand=True, pady=(0, 10))
        self.output.config(state='disabled')

        # Input label and box
        self.input_label = ttk.Label(container, text="Input:")
        self.input_label.pack(anchor='w')
        self.input_text = ScrolledText(container, height=8, wrap='word', bg='white', fg='black', font = ("Consolas", 10))
        self.input_text.pack(fill='x')
        self.input_text.bind("<Return>", self.handle_return)
        self.input_text.bind("<Control-Return>", self.ctrl_enter_submit)

        self.input_text.bind("<Button-3>", self.paste_from_clipboard)

        ttk.Label(container, text="Codes to Copy:").pack(anchor='w', pady=(10, 0))

        # Display area for list (read-only text box)
        self.display_list_label = ttk.Label(container, text="", anchor='w', background='white')
        self.display_list_label.pack(fill='x', pady=(0, 10))

        button_row = ttk.Frame(container)
        button_row.pack(pady=(10, 0))

        ttk.Button(button_row, text="Toggle Controls", command=self.toggle_controls).pack(side='left', padx=(0, 5))
        ttk.Button(button_row, text="Help", command=lambda: self.on_instruction_press("help")).pack(side='left')

        # === Controls Section (Settings + Instructions + Submit) ===
        self.controls_frame = ttk.Frame(container)
        self.controls_frame.pack(fill='x', pady=10)

        # Settings (checkboxes)
        settings_frame = ttk.LabelFrame(self.controls_frame, text="Settings")
        settings_frame.pack(side='left', expand=True, fill='both', padx=(0, 10))

        setting_names = [("Header", 'h'), ("Dash", '-'), ("Additional Info", 'i'), ("Show Full RI", 'p'), ("Warnings", 'w'), ("Debug", 'o')]
        self.settings = []
        for i in range(6):
            name, char = setting_names[i]
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(settings_frame, text=name, variable=var)
            cb.config(command=lambda c=char: self.on_setting_toggle(c))
            cb.pack(anchor='w', padx=5, pady=2)
            self.settings.append((var, cb))

        # Instructions (buttons)
        instructions_frame = ttk.LabelFrame(self.controls_frame, text="Instructions")
        instructions_frame.pack(side='right', expand=True, fill='both')        

        instruction_names = [("Next", 'x'), ("Auto Setup (paste all RIs)", 'z'), ("Manual Setup (enter RIs one-by-one)", 's'), ("Show copied codes", 'c'), ("Finish", 'f')]

        self.instruction_buttons = []
        for name, char in instruction_names:
            b = ttk.Button(instructions_frame, text=name)
            b.config(command=lambda c=char: self.on_instruction_press(c))
            b.pack(fill='x', padx=5, pady=2)
            self.instruction_buttons.append(b)

        # Separator + Submit button frame
        self.submit_section = ttk.Frame(container)
        self.submit_section.pack(fill='x')

        ttk.Separator(self.submit_section, orient='horizontal').pack(fill='x', pady=(10, 5))
        ttk.Button(self.submit_section, text="Submit", command=self.on_submit).pack(fill='x')

        # Redirection + target function thread
        self.stdin = StdinRedirector(self)
        self.stdout = StdoutRedirector(self.output)
        sys.stdin = self.stdin
        sys.stdout = self.stdout

        

        self.thread = threading.Thread(target=target_function, daemon=True)
        self.thread.start()
    
    def paste_from_clipboard(self, event=None):
        try:
            text = self.clipboard_get()
            self.input_text.insert(tk.INSERT, text)
        except tk.TclError:
            pass  # Clipboard empty or not text

    def on_submit(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if text:
            self.input_text.delete("1.0", tk.END)
            sys.stdout.write(f">>> {text}\n")
            self.stdin.push(text)

    def handle_return(self, event):
        if self.expecting_line_input:
            self.on_submit()
            return "break"  # Prevent newline insertion
        # Else: allow newline

    def ctrl_enter_submit(self, event):
        self.on_submit()
        return "break"

    def toggle_controls(self):
        if self.controls_visible:
            self.controls_frame.pack_forget()
            self.submit_section.pack_forget()
        else:
            self.controls_frame.pack(fill='x', pady=10)
            self.submit_section.pack(fill='x')
        self.controls_visible = not self.controls_visible

    def on_instruction_press(self, char):
        sys.stdout.write(f">>> {char}\n")
        self.stdin.push(char)

    def on_setting_toggle(self, char):
        sys.stdout.write(f">>> {char}\n")
        self.stdin.push(char)
    
    def setup_disability(self):
        def disable_widgets():
            manual_setup_index = 2  # Index of "Manual Setup (enter RIs one-by-one)"
            self.manual_override_disabled = True
            for i, button in enumerate(self.instruction_buttons):
                state = 'normal' if i == manual_setup_index else 'disabled'
                button.config(state=state)
            for _, cb in self.settings:
                cb.config(state='disabled')

        self.after(0, disable_widgets)

    def enable_all_instruction_buttons(self):
        def enable_widgets():
            self.manual_override_disabled = False
            for b in self.instruction_buttons:
                b.config(state='enabled')
            for _, cb in self.settings:
                cb.config(state='enabled')

        self.after(0, enable_widgets)

    def set_input_mode_label(self, multiline=False):
        if multiline:
            self.input_label.config(text="Input (Multi-line - ctrl-Enter or press Submit button to submit):")
            for b in self.instruction_buttons:
                b.config(state='disabled')
            for _, cb in self.settings:
                cb.config(state='disabled')
        else:
            self.input_label.config(text="Input:")
            if not self.manual_override_disabled:
                for b in self.instruction_buttons:
                    b.config(state='normal')
                for _, cb in self.settings:
                    cb.config(state='normal')

    def set_output_mode_label(self, table_name='Unknown!'):
        self.output_label.config(text=f"Output (from {table_name}):")

    def sync_checkboxes(self, settings_dict):
        # Keys must match the order of self.settings
        settings_keys = ["codeHeader", "autoDash", "additional_info",
                        "showRI", "warnings", "allWarnings"]
        
        for (var, _), key in zip(self.settings, settings_keys):
            new_value = settings_dict.get(key, False)
            if var.get() != new_value:
                var.set(new_value)

    def update_display_list(self, items):
        display_text = ", ".join(str(item) for item in items)
        self.display_list_label.config(text=display_text)


def resource_path(relative_path):
    """ Get absolute path to resource, whether running as script or PyInstaller .exe """
    if hasattr(sys, '_MEIPASS'):
        # When running as a PyInstaller .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # When running as a .py script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

db_path = resource_path(os.path.join("Databases", "risk_improvements.db"))
print(db_path)

#table_name = "RI20250424" #specify which table to use in the database
table_name_highest_table = True #automatically pick the most recent table in the database

conn = None
cursor = None

nonInstructionLetters = {'M', 'A', 'R', 'X'}

warnings_allowed = False

def get_input(prompt=""):
    print(prompt, end="")  # this will go to your GUI
    return sys.stdin.readline().strip()

def get_multiline_input():
    return sys.stdin.read()


def get_difset():
    cursor.execute(f"SELECT difset FROM differences WHERE id = 1")
    result = cursor.fetchone()

    # If the set exists, deserialize it back into a Python set
    if result:
        set_json = result[0]
        my_set = set(json.loads(set_json))
        return my_set
    
    else:
        return set()

def update_difset(difset):
    # Convert the set to a list, then to JSON for storage
    set_json = json.dumps(list(difset))
    
    # Update if exists, insert otherwise
    cursor.execute("""
        INSERT INTO differences (id, difset)
        VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET difset = excluded.difset
    """, (set_json,))
    
    conn.commit()

def get_highest_table():
    # Query the list of tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Filter the tables that match the pattern 'RI{number}'
    pattern = r"RI(\d+)"
    table_numbers = []

    for table in tables:
        match = re.match(pattern, table[0])
        if match:
            table_numbers.append(int(match.group(1)))  # Extract number part and convert to int

    # If there are any valid tables, return the table with the highest number
    if table_numbers:
        max_number = max(table_numbers)
        return f"RI{max_number:08}"  # Format as RI followed by 8-digit number
    else:
        return None  # No valid tables found
    
def getRI(code, table_name):
    query = f"SELECT title, description FROM {table_name} WHERE code = ?"
    cursor.execute(query, (code,))

    result = cursor.fetchone()
    if result == None:
        return None, None

    return result

def hline():
    print("----------------------")

def formatRI(code, title, description, header):
    head = f"{code}\n-\n" if header else ""
    result = head + title + "\n-\n" + description
    return result.strip()

def windowed_help():
    hline()
    print("""
This program is designed to take in an RI code, and return the RI text straight to your clipboard.
Things to note:
    - There is no case sensitivity (e.g. M094 and m094 will be read the same, as will z and Z).
    - The settings and controls panel is optional - all functionality can be accessed just through the input text box via letter codes.
    - This is taking risk improvement text from risk_improvements.db  (a SQLite database) (saved in Administration/Programs/Databases)
        - Updating and creating databases is outlined in RI_database_setup.py (also saved in Administration/Programs/Databases)

-------Warnings-------
There is a warning system in this program, if you have entered the list of codes to copy. It will warn if:
    - You have already copied the code.
    - The code you are asking to copy is not included in the list of codes to copy.
    - You have pressed Finish (or entered f) without copying all the codes from the list. 
          
----Additional Info----
Often there is additional info you would like to accompany the risk improvement text. Add this to an RI by typing &(code) (e.g. &M091) then press enter. 
The program will prompt you to input the additional info. Type/paste it in then press Submit or ctrl-enter.
This additional info is printed, bracketted and in quotation marks, next to the RI code if you have headers on, or above the RI title if you have headers off. 
          
-----Instructions-----
Next (x): Output the next RI in the codes to copy list. The list will always be ordered Ms then As, sorted numerically
Auto Setup (z): Copy all the flagged items at once and paste into the input box. Once you've pasted, press ctrl-enter or click the submit button. The program goes through and looks for A(xxx) and M(xxx) codes and adds them to the codes to copy list. 
Please note that using the auto setup will clear all current codes. To add a code to the list, use the manual setup.  
Manual Setup (s): Add the codes to the list one by one, pressing enter after each code.
Show copied codes (c): Show the codes that you have copied. 
Finish (f): Press this (or enter f) after you have finished getting all the codes for a certain job. This resets the codes to copy list as well as the warning system.
          
-------Settings-------
Header (h): Toggle whether the output contains the RI code at the top.
Dash (-): Toggles whether a dash is added before the RI text, such that (for header off) you can click straight after the RI written by the consultant and paste.
Additional Info (i): Print whether or not additional info gets printed before the RI text (additional info is typically comments made by the consultant which you can see in the flagged items). 
Show full RI (p): Toggles whether or not the full RI text is printed to the output box, or just the code & title (the entire RI text will ALWAYS be copied to your clipboard). 
Warnings (w): Toggles whether or not warnings will fire. Note that this only works when you have a codes to copy list (i.e. after Auto or Manual setup).
Debug (o): No functional use anymore (used for when I am debugging the program). 
          """)

def help():
    if windowed:
        windowed_help()
        return
    
    hline()
    print("This program is designed to take in an RI code, and return the RI text straight to your clipboard.")
    print("You do not need to manually copy the risk improvement")
    print("There is no case sensitivity. e.g. m093 and M092 work the same, as do HELP and help, H and h, etc")
    print("-----Instructions-----")
    print("h (header): Toggles whether the code number is placed above the risk recommendation")
    print("x: Print next risk improvement in list")
    print("z: Copy all risk codes and insert by pasting. enter>ctrl-z>enter after pasting.")
    print(r"&{code}: Add additional information to the code. This will print out next to the code if header is on, or above the title if header is off.")
    print("i or info: Toggles whether the additional information will print")
    print("s (setup): Enter all the codes for a given job manually. Type 'd' then enter once all are entered")
    print("c (copied): Display the codes you have copied so far")
    print("t (tocopy): Display what codes you have left to copy")
    print("f (finished): Display what codes have not been copied from the list. Also resets the list of codes to copy.")
    print("w (warnings): Turn warnings off")
    print("p (print): Toggle whether to show the full risk recommendation text after entering a code (will copy all of it no matter what)")
    print("AAA or MMM: This automatically adds the letter code, allowing you to just enter the numbers. Enter 'r' to exit. Note that codes DO still work. e.g. Mf will finish")
    print("-: Toggle whether, while header is off, the copied text already includes an enter-dash-enter such that you can copy onto the existing code")
    print("e (edit): edit the database from which the codes are being copied. NOT FULLY IMPLEMENTED - DO NOT USE.")
    hline()
    print("Type \"example\" then enter to get a walkthrough of how I (Max) use this program")
    hline()

def orderCodes(code_set):
    sorted_codes = sorted(code_set, key=lambda x: (x[0] == "A", int(x[1:])))

    return sorted_codes

def autoExtract(text):
    pattern = r'\b[M|A]\d{3}\b'  
    matches = re.findall(pattern, text)  # Find all matches

    counts = Counter(matches)
    duplicates = {code: count for code, count in counts.items() if count > 1}

    if duplicates:
        formatted = ", ".join(f"({code}:{count}x)" for code, count in duplicates.items())
        print(f"Duplicates: {formatted}")

    return len(matches), set(matches)

def autoSetUp(lists, settings):
    global warnings_allowed
    print("Paste text and then press the Submit button (or press ctrl-enter)")

    text = get_multiline_input().upper()

    count, codes = autoExtract(text)
    set_count = len(codes)

    print(f"{set_count} unique codes from {count} total.")
    print(orderCodes(codes))

    settings["warnings"] = True
    warnings_allowed = True

    lists["toCopy"] = codes

def setUp(lists, settings):
    print("Please enter the full list of codes to copy for then press Manual Setup again once finished (or press 's')")
    app.setup_disability()
    i = 0

    preCode = ""

    while True:
        print(preCode, end="")

        inp = get_input().upper()
        if inp == 'DONE' or inp == 'D' or inp == 'S':
            break

        if inp == "MMM":
            preCode = 'M'
            continue

        if inp == "AAA":
            preCode = 'A'
            continue

        if inp[0] == 'R':
            preCode = ""
            continue

        codeInp = preCode + inp

        pattern = r'\b(?:M|A)\d{3}\b'
        
        if not re.fullmatch(pattern, codeInp):
            print("Invalid code.")
            continue

        if codeInp in lists["toCopy"]:
            hline()
            print(f"{codeInp} already entered")
            hline()

        else: 
            lists["toCopy"].add(codeInp)
        
        i += 1

    app.enable_all_instruction_buttons()
    settings["warnings"] = True
    global warnings_allowed
    warnings_allowed = True
    print(f"{len(lists["toCopy"])} unique codes to copy: {orderCodes(lists["toCopy"])} ({i} codes entered)")

def lazy():
    hline()
    print("Here is Max's method for using this program.")
    hline()
    print("""
First, copy all the text in the "flagged items" section in iAuditor. It will look something like:
        
        INSULATED PANELS
        Electrical switchboards - air gap or suitable fire-rated shield (M069)
        No
        FIRE PROTECTION / SMOKE DETECTION
        Smoke detection - monitoring type (A014)
        Security alarm system

Type 'z' then enter into the terminal. Then paste in all that text from the flagged items. Check whether the program has identified the correct number of risk improvements.

Do your catnet and location description. Then go into the risk improvements. If there are risk improvements with images provided by the consultant, turn the header off (h then enter) and turn autodash on (- then enter)
Type in the risk improvement that the consultant has entered. Click after the RI code written by the consultant, and paste. Repeat this process for all the provided risk improvements with images.

Then, once there are no images left. Press t then enter to see if there are any more risk improvements to copy. If there are, turn the header back on (h then enter) and then go through all the remaining risk improvements by pressing x then enter. 
          """)
    hline()

def parseInstruction(code, lists, settings, table_name):
    global warnings_allowed

    if code[0] == 'P':
        settings["showRI"] = not settings["showRI"]
        print(f"The full risk recommendation will {'' if  settings["showRI"] else 'NOT'} be printed to the screen")
        app.sync_checkboxes(settings)
        return 1
    
    if code[0] == 'O':
        settings["allWarnings"] = not settings["allWarnings"]
        print(f"Debug mode {'on' if settings["allWarnings"] else 'off'}.")
        app.sync_checkboxes(settings)
        return 1
        
    if code[0] == 'C':
        print(f"So far, you have copied {orderCodes(lists["copied"])}")
        return 1

    if code[0] == 'T':
        print(f"You still have the following codes left: {orderCodes(lists["toCopy"])}")
        return 1
    
    if code == 'HELP':
        help()
        return 1
    
    if code == 'EXAMPLE':
        lazy()
        return 1

    if code[0] == 'H':
        settings["codeHeader"] = not settings["codeHeader"]
        print(f"codeHeader is now {'on' if settings["codeHeader"] else 'off'}")
        app.sync_checkboxes(settings)
        return 1
    
    if code[0] == 'S':
        setUp(lists, settings)
        return 1

    if code[0] == 'F':
        return 0
    
    if code[0] == 'W':
        if warnings_allowed:
            settings["warnings"] = not settings["warnings"]
        else:
            settings["warnings"] = False
            print("You cannot turn warnings on without codes to copy.")
        print(f"Warnings now {'on' if settings["warnings"] else 'off'}.")
        app.sync_checkboxes(settings)
        return 1
    
    if code[0] == 'E':
        editDB(table_name)
        return 1

    if code[0] == 'Z':
        autoSetUp(lists, settings)
        return 1
    
    if code[0] == 'I':
        settings['additional_info'] = not settings['additional_info']
        print(f"Additional info is now {'on' if settings["additional_info"] else 'off'}")
        app.sync_checkboxes(settings)
        return 1
    
    if code[0] == '-':
        settings['autoDash'] = not settings['autoDash']
        print(f"Auto dash is now {'on' if settings["autoDash"] else 'off'}")
        app.sync_checkboxes(settings)
        return 1
    
    else:
        print("Invalid instruction")
        return 1
    
def setRI(code, title, description, table_name):
    # Check if the code already exists
    query = f"SELECT 1 FROM {table_name} WHERE code = ?"
    cursor.execute(query, (code,))
    exists = cursor.fetchone()

    if exists:
        # Update existing entry
        query = f"UPDATE {table_name} SET title = ?, description = ? WHERE code = ?"
        cursor.execute(query, (title, description, code))
    else:
        # Insert new entry
        query = f"INSERT INTO {table_name} (code, title, description) VALUES (?, ?, ?)"
        cursor.execute(query, (code, title, description))

    conn.commit()

def deleteRI(code, table_name):
    query = f"DELETE FROM {table_name} WHERE code = ?"
    cursor.execute(query, (code,))
    
    if cursor.rowcount == 0:
        print("Error: Code does not exist.")
        return 0
    
    conn.commit()  # Save changes
    print(f"Successfully deleted code: {code}")
    return 1

def editDB(table_name):
    code = get_input("Enter code to edit/create or 'del' to delete a code").upper().strip()

    if code == 'DEL':
        code = get_input("Enter a code to delete:").upper().strip()
        if not deleteRI(code, table_name):
            return 0

    title, description = getRI(code, table_name)

    if not title or not description:
        if get_input("Code not found. Would you like to make a new entry? 'y' then enter for yes, anything else for no.").lower().strip() != 'y':
            return 0
        
    print(f"Editing database for {code}:")
    print(f"Current title: {title}")
    print("Write \"keep\", then enter > ctrl-Z > enter to keep, or write/paste corrected title, then enter > ctrl-Z > enter")

    titleInp = get_multiline_input()

    newTitle = title if titleInp.lower() == "keep" else titleInp

    print(f"Current description: {description}")
    print("Write \"keep\", enter > ctrl-Z > enter to keep, or write/paste corrected title, then enter > ctrl-Z > enter")

    descrInp = get_multiline_input()

    newDescription = description if descrInp.lower() == "keep" else descrInp

    setRI(code, newTitle, newDescription, table_name)

def program():
    global conn, cursor, warnings_allowed
    conn = sqlite3.connect(db_path)  # Open connection
    cursor = conn.cursor()  # Create cursor

    if table_name_highest_table:
        table_name = get_highest_table()

    app.set_output_mode_label(table_name)

    difset_change = False
    difset = get_difset()

    settings = {
        "codeHeader": True,
        "warnings": False,
        "showRI": False,
        "allWarnings": False,
        "additional_info": True,
        "autoDash": False
    }

    while True:
        warnings_allowed = False
        preCode = ""
        warned = False

        additional_info = dict()

        settings["warnings"] = False
        app.sync_checkboxes(settings)

        lists = {
            "toCopy": set(),
            "copied": set(),
            "exception": set()
        }

        if difset_change:
            update_difset(difset)
            difset = get_difset()
            difset_change = False

        while True:
            app.update_display_list(orderCodes(lists["toCopy"]))
            print("Enter code or instruction:")
            app.sync_checkboxes(settings)


            inp = get_input(preCode).upper().strip()
            #inp = sys.stdin.read().upper().strip()

            if len(inp) == 0:
                continue

            if inp[0] == '&':
                code = inp[1:]
                print(f"Type additional info for {code}. Then click submit or ctrl-enter")
                info = get_multiline_input()

                additional_info[code] = info.strip()

                continue


            if not inp:
                continue

            codesList = inp.split('+')

            check = inp[0].isdigit() and preCode

            if inp[0] == 'X':
                if(len(lists['toCopy']) == 0):
                    print("All codes copied. Click the Finish button or enter 'f'.")
                    continue
                codesList = orderCodes(lists["toCopy"])[:1]
                print(codesList[0])

            intersection = set(codesList) & difset
            if intersection:
                print(f"Please check {intersection} as the description or title has changed")
                print(f"Type '({list(intersection)[0]}' to remove")

            if inp[0] == '(':
                difset.discard(inp[1:])
                difset_change = True
                continue
            
            elif inp[0] not in nonInstructionLetters and not check:
                if parseInstruction(inp, lists, settings, table_name):
                    continue
                else:
                    break

            elif inp == "MMM":
                preCode = 'M'
                continue

            elif inp == "AAA":
                preCode = 'A'
                continue

            elif inp[0] == 'R':
                preCode = ""
                continue



            codesList = [preCode + item for item in codesList]

            titles = []
            descriptions = []
            for code in codesList:
                titleUnchecked, descriptionUnchecked = getRI(code, table_name)

                if not titleUnchecked and not descriptionUnchecked:
                    print(f"Invalid code: {code}")
                    codesList.remove(code)
                    continue
                else:
                    titles.append(titleUnchecked)
                    descriptions.append(descriptionUnchecked)

                if settings['warnings']:
                    try:
                        lists["toCopy"].remove(code)
                    except KeyError:
                        if code not in lists["copied"]:
                            print("------------------------")
                            print(f"Warning: {code} not found in the list.")
                            print("------------------------")

                    if code in lists["copied"]:
                        print("------------------------")
                        print(f"Warning: {code} already copied: {orderCodes(lists["copied"])}")
                        print("------------------------")

                elif not warned:
                    print("------------------------")
                    print("You have not entered full list of codes. Warnings are now disabled. To reset, click the Finish button or enter 'f'")
                    print("------------------------")
                    warned = True

                lists["copied"].add(code)

            if len(titles) == 0 or len(descriptions) == 0:
                print("No valid codes received.")
                continue

            texts = []
            for title, description, code in zip(titles, descriptions, codesList):
                additional = ''

                if code in additional_info and settings["additional_info"]:
                    additional = additional_info[code]
                    print(additional)

                if settings["codeHeader"] and len(titles) == 1:
                    text = f"{code}{f" (\"{additional}\")" if additional else ''}\n-\n{title}{f"\n-\n{description}" if description else ''}"
                elif settings["autoDash"] and title == titles[0]:
                    text = f"{f"(\"{additional}\")\n-\n" if additional else '\n-\n'}{title}{f"\n-\n{description}" if description else ''}"
                else:
                    text = f"{f"(\"{additional}\")\n-\n" if additional else ''}{title}{f"\n-\n{description}" if description else ''}"
                    

                if settings["showRI"]:
                    print(text)
                else:
                    print(title)

                texts.append(text)

            final = '\n+\n'.join(texts)

            pyperclip.copy(final)

        if lists["toCopy"]:
            print("------------------------")
            print(f"Warning: codes not copied - {orderCodes(lists["toCopy"])}")
            print("------------------------")
            
        elif settings["warnings"]:
            print("Every code was copied!")
        else:
            print("Warnings were disabled - let's hope everything was copied!")

        set_json = json.dumps(list(difset))

        cursor.execute("""
            INSERT OR REPLACE INTO differences (id, difset)
            VALUES (1, ?)
        """, (set_json,))

        print("...everything reset...")

def tryfinally():
    try:
        program()

    finally:
        conn.close()

if __name__ == "__main__":

    if windowed:
        app = TerminalApp(tryfinally)
        app.mainloop()
    
    else:
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__
        tryfinally()