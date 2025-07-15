import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import sqlite3

def build(tab_frame, patient_id, tabs=None, on_demographics_updated=None):
    fields = {}
    entries = {}
    editing = tk.BooleanVar(value=False)

    labels = [
        ("First Name:", "FirstName"),
        ("Last Name:", "LastName"),
        ("MRN:", "MRN"),
        ("Zip Code:", "ZipCode"),
        ("BMI:", "BMI"),
        ("Referral Source:", "ReferralSource"),
        ("Referral Details:", "ReferralDetails"),
        ("Initial Consult Date:", "InitialConsultDate"),
        ("DOB:", "DOB")
    ]

    def load_data():
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT FirstName, LastName, MRN, ZipCode, BMI, ReferralSource, ReferralDetails, InitialConsultDate, DOB
            FROM tblPatients
            WHERE PatientID = ?
        """, (patient_id,))
        result = cursor.fetchone()
        conn.close()

        for widget in tab_frame.winfo_children():
            widget.destroy()

        for i, (label_text, key) in enumerate(labels):
            tk.Label(tab_frame, text=label_text, anchor="w", width=20).grid(row=i, column=0, sticky="w", pady=2)

            if key == "ReferralSource":
                entry = ttk.Combobox(tab_frame, values=["Self", "Physician", "Patient", "Other"], state="readonly", width=37)
                entry.set(result[i] if result[i] else "")
                entry.grid(row=i, column=1, sticky="w", pady=2)
                entries[key] = entry

            elif key in ["InitialConsultDate", "DOB"]:
                # Use DateEntry with pre-loaded date
                entry = DateEntry(tab_frame, width=18, date_pattern="yyyy-mm-dd")
                if result[i]:
                    entry.set_date(result[i])
                else:
                    entry.set_date("")
                entry.grid(row=i, column=1, sticky="w", pady=2)
                entry.config(state="readonly")
                entries[key] = entry

            else:
                entry = tk.Entry(tab_frame, width=40)
                entry.insert(0, result[i] if result[i] is not None else "")
                entry.grid(row=i, column=1, sticky="w", pady=2)
                entry.config(state="readonly")
                entries[key] = entry

        # Buttons
        btn_frame = tk.Frame(tab_frame)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

        btn_edit = tk.Button(btn_frame, text="Edit", width=12, command=toggle_edit)
        btn_edit.grid(row=0, column=0, padx=5)

        btn_save = tk.Button(btn_frame, text="Save", width=12, command=save_changes, state="disabled")
        btn_save.grid(row=0, column=1, padx=5)

        fields['btn_edit'] = btn_edit
        fields['btn_save'] = btn_save

    def toggle_edit():
        editing.set(True)
        for key, widget in entries.items():
            if isinstance(widget, ttk.Combobox) or isinstance(widget, DateEntry):
                widget.config(state="readonly")
            else:
                widget.config(state="normal")
        for key in ["InitialConsultDate", "DOB"]:
            entries[key].config(state="normal")
        fields['btn_edit'].config(state="disabled")
        fields['btn_save'].config(state="normal")

    def save_changes():
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tblPatients
                SET FirstName = ?, LastName = ?, MRN = ?, ZipCode = ?, BMI = ?, ReferralSource = ?, ReferralDetails = ?, InitialConsultDate = ?, DOB = ?
                WHERE PatientID = ?
            """, (
                entries["FirstName"].get().strip(),
                entries["LastName"].get().strip(),
                entries["MRN"].get().strip(),
                entries["ZipCode"].get().strip(),
                entries["BMI"].get().strip(),
                entries["ReferralSource"].get().strip(),
                entries["ReferralDetails"].get().strip(),
                entries["InitialConsultDate"].get_date().strftime("%Y-%m-%d"),
                entries["DOB"].get_date().strftime("%Y-%m-%d"),
                patient_id
            ))
            conn.commit()
            conn.close()

            # Reset all to read-only
            for key, entry in entries.items():
                entry.config(state="readonly")
            fields['btn_edit'].config(state="normal")
            fields['btn_save'].config(state="disabled")
            editing.set(False)

            if on_demographics_updated:
                on_demographics_updated()

            messagebox.showinfo("Success", "Demographics updated.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    load_data()
