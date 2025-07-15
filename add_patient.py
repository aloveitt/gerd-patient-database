# add_patient.py

import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import sqlite3
from datetime import date

def build(on_save_callback=None):
    window = tk.Toplevel()
    window.title("Add New Patient")
    window.geometry("500x600")

    labels = [
        "First Name", "Last Name", "MRN", "Gender", "DOB",
        "Zip Code", "BMI", "Referral Source", "Referral Details", "Initial Consult Date"
    ]

    entries = {}

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

    def save_patient():
        try:
            data = {}
            for label in labels:
                widget = entries[label]
                if isinstance(widget, DateEntry):
                    data[label] = widget.get_date().strftime("%Y-%m-%d")
                else:
                    data[label] = widget.get().strip()

            if not data["First Name"] or not data["Last Name"] or not data["MRN"]:
                messagebox.showerror("Error", "First name, last name, and MRN are required.")
                return

            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tblPatients WHERE MRN = ?", (data["MRN"],))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Duplicate", "A patient with that MRN already exists.")
                conn.close()
                return

            cursor.execute("""
                INSERT INTO tblPatients (
                    FirstName, LastName, MRN, Gender, DOB, ZipCode, BMI,
                    ReferralSource, ReferralDetails, InitialConsultDate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["First Name"], data["Last Name"], data["MRN"], data["Gender"], data["DOB"],
                data["Zip Code"], data["BMI"], data["Referral Source"], data["Referral Details"],
                data["Initial Consult Date"]
            ))

            patient_id = cursor.lastrowid  # ✅ Get the new PatientID

            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Patient added successfully.")
            window.destroy()

            if on_save_callback:
                on_save_callback(patient_id)

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(window, text="Save Patient", command=save_patient).grid(
        row=len(labels), column=0, columnspan=2, pady=20
    )
