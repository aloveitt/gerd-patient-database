import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3

def open_add_surgical(tab_frame, patient_id, refresh_callback=None):
    popup = tk.Toplevel()
    popup.title("Add Surgical Entry")
    popup.grab_set()

    tk.Label(popup, text="Surgery Date:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    entry_date = DateEntry(popup, date_pattern="yyyy-mm-dd")
    entry_date.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(popup, text="Surgeon:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    surgeon_var = tk.StringVar()
    try:
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("SELECT SurgeonName FROM tblSurgeons ORDER BY SurgeonName")
        surgeon_names = [row[0] for row in cursor.fetchall()]
        conn.close()
    except:
        surgeon_names = []
    cbo_surgeon = ttk.Combobox(popup, textvariable=surgeon_var, values=surgeon_names, state="readonly")
    cbo_surgeon.grid(row=1, column=1, padx=5, pady=5)

    procedure_frame = tk.LabelFrame(popup, text="Procedures Performed", padx=10, pady=10)
    procedure_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    procedures = [
        "HiatalHernia", "ParaesophagealHernia", "MeshUsed", "GastricBypass", "SleeveGastrectomy", "Toupet", "TIF", "Nissen",
        "Dor", "HellerMyotomy", "Stretta", "Ablation", "LINX", "GPOEM", "EPOEM", "ZPOEM", "Pyloroplasty",
        "Revision", "GastricStimulator", "Dilation", "Other"
    ]
    check_vars = {}
    for i, proc in enumerate(procedures):
        var = tk.IntVar()
        check_vars[proc] = var
        label = proc.replace("GPOEM", "G-POEM").replace("EPOEM", "E-POEM").replace("ZPOEM", "Z-POEM")
        tk.Checkbutton(procedure_frame, text=label, variable=var).grid(row=i // 2, column=i % 2, sticky="w")

    tk.Label(popup, text="Notes:").grid(row=3, column=0, sticky="ne", padx=5, pady=5)
    txt_notes = tk.Text(popup, width=40, height=4)
    txt_notes.grid(row=3, column=1, padx=5, pady=5)

    def save():
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO tblSurgicalHistory (
                    PatientID, SurgeryDate, SurgerySurgeon, Notes,
                    {', '.join(procedures)}
                ) VALUES (
                    ?, ?, ?, ?, {', '.join('?' for _ in procedures)}
                )
            """, (
                patient_id,
                entry_date.get(),
                cbo_surgeon.get(),
                txt_notes.get("1.0", tk.END).strip(),
                *[check_vars[p].get() for p in procedures]
            ))
            conn.commit()
            conn.close()
            popup.destroy()
            if refresh_callback:
                refresh_callback()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(popup, text="Save", command=save).grid(row=4, column=0, columnspan=2, pady=10)
