# add_patient.py - SUPER ROBUST VERSION (Easy to understand!)

import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import sqlite3
from datetime import date
import re

def is_good_name(name):
    """Check if a name is good (only letters, spaces, hyphens)"""
    if not name or len(name.strip()) == 0:
        return False
    if len(name) > 50:
        return False
    # Only allow letters, spaces, hyphens, apostrophes
    return bool(re.match(r"^[A-Za-z\s\-']+$", name.strip()))

def is_good_mrn(mrn):
    """Check if MRN is good (5-15 letters and numbers)"""
    if not mrn or len(mrn.strip()) < 5 or len(mrn.strip()) > 15:
        return False
    # Only letters and numbers allowed
    return bool(re.match(r'^[A-Za-z0-9]+$', mrn.strip()))

def is_good_bmi(bmi_text):
    """Check if BMI makes sense"""
    if not bmi_text or bmi_text.strip() == "":
        return True  # BMI is optional
    try:
        bmi_number = float(bmi_text)
        return 10.0 <= bmi_number <= 100.0  # Reasonable BMI
    except:
        return False

def is_good_zip(zip_code):
    """Check if ZIP code looks right"""
    if not zip_code or zip_code.strip() == "":
        return True  # ZIP is optional
    # Must be 5 numbers or 5 numbers + dash + 4 numbers
    return bool(re.match(r'^\d{5}(-\d{4})?$', zip_code.strip()))

def show_nice_error(title, message):
    """Show a nice error message to the user"""
    messagebox.showerror(title, message)

def show_nice_success(message):
    """Show a nice success message to the user"""
    messagebox.showinfo("Success!", message)

def safe_database_operation(operation_name, operation_function):
    """
    Safely do database stuff and handle errors nicely
    Think of this as a safety net for database operations
    """
    try:
        return operation_function()
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            show_nice_error("Duplicate Patient", "A patient with that MRN already exists!")
        else:
            show_nice_error("Data Problem", f"There's a problem with the data: {str(e)}")
        return False
    except sqlite3.OperationalError as e:
        show_nice_error("Database Problem", f"The database had a problem: {str(e)}")
        return False
    except Exception as e:
        show_nice_error("Unexpected Problem", f"Something unexpected happened: {str(e)}")
        return False

def build(on_save_callback=None):
    """Build the add patient window - now with SUPER protection!"""
    
    window = tk.Toplevel()
    window.title("Add New Patient")
    window.geometry("500x600")

    # All the form fields
    labels = [
        "First Name", "Last Name", "MRN", "Gender", "DOB",
        "Zip Code", "BMI", "Referral Source", "Referral Details", "Initial Consult Date"
    ]

    entries = {}

    # Create all the input fields (same as before)
    for i, label in enumerate(labels):
        tk.Label(window, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=5)

        if label == "Gender":
            combo = ttk.Combobox(window, values=["Male", "Female", "Other"])
            combo.grid(row=i, column=1, padx=10)
            entries[label] = combo

        elif label == "Referral Source":
            combo = ttk.Combobox(window, values=["Self", "Physician", "Patient", "Other"])
            combo.grid(row=i, column=1, padx=10)
            entries[label] = combo

        elif label in ["DOB", "Initial Consult Date"]:
            date_entry = DateEntry(window, width=18, date_pattern="yyyy-mm-dd")
            date_entry.grid(row=i, column=1, padx=10)
            entries[label] = date_entry

        else:
            entry = tk.Entry(window, width=30)
            entry.grid(row=i, column=1, padx=10)
            entries[label] = entry

    def check_all_data():
        """Check if all the data the user entered is good"""
        errors = []
        
        # Get the data from the form
        first_name = entries["First Name"].get().strip()
        last_name = entries["Last Name"].get().strip()
        mrn = entries["MRN"].get().strip()
        bmi = entries["BMI"].get().strip()
        zip_code = entries["Zip Code"].get().strip()
        
        # Check each piece of data
        if not is_good_name(first_name):
            errors.append("First name must have letters only (1-50 characters)")
        
        if not is_good_name(last_name):
            errors.append("Last name must have letters only (1-50 characters)")
        
        if not is_good_mrn(mrn):
            errors.append("MRN must be 5-15 letters and numbers only")
        
        if not is_good_bmi(bmi):
            errors.append("BMI must be a number between 10 and 100 (or leave blank)")
        
        if not is_good_zip(zip_code):
            errors.append("ZIP code must be like 12345 or 12345-6789 (or leave blank)")
        
        return errors

    def save_patient():
        """Save the patient - now with SUPER protection!"""
        
        # First, check if all data is good
        errors = check_all_data()
        if errors:
            error_message = "Please fix these problems:\n\n"
            for error in errors:
                error_message += f"• {error}\n"
            show_nice_error("Please Fix These Problems", error_message)
            return
        
        # Get all the data from the form
        data = {}
        for label in labels:
            widget = entries[label]
            if isinstance(widget, DateEntry):
                try:
                    data[label] = widget.get_date().strftime("%Y-%m-%d")
                except:
                    data[label] = ""
            else:
                data[label] = widget.get().strip()

        # Now safely save to database
        def do_the_database_save():
            """The actual database saving (wrapped in safety)"""
            conn = sqlite3.connect("gerd_center.db")
            try:
                cursor = conn.cursor()
                
                # Double-check for duplicate MRN
                cursor.execute("SELECT COUNT(*) FROM tblPatients WHERE MRN = ?", (data["MRN"],))
                if cursor.fetchone()[0] > 0:
                    raise sqlite3.IntegrityError("UNIQUE constraint failed: MRN already exists")
                
                # Save the patient
                cursor.execute("""
                    INSERT INTO tblPatients (
                        FirstName, LastName, MRN, Gender, DOB, ZipCode, BMI,
                        ReferralSource, ReferralDetails, InitialConsultDate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["First Name"], data["Last Name"], data["MRN"], data["Gender"], 
                    data["DOB"], data["Zip Code"], data["BMI"], data["Referral Source"], 
                    data["Referral Details"], data["Initial Consult Date"]
                ))

                patient_id = cursor.lastrowid
                conn.commit()
                
                # Success!
                show_nice_success("Patient added successfully!")
                window.destroy()
                
                if on_save_callback:
                    on_save_callback(patient_id)
                
                return True
                
            finally:
                conn.close()  # Always close the database
        
        # Use our safety wrapper
        safe_database_operation("Save Patient", do_the_database_save)

    # The save button
    tk.Button(window, text="Save Patient", command=save_patient).grid(
        row=len(labels), column=0, columnspan=2, pady=20
    )