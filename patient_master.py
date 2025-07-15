# patient_master.py

import tkinter as tk
from tkinter import ttk
import sqlite3
import demographics_tab
import diagnostics_tab
import surgical_tab
import pathology_tab
import surveillance_tab
import recall_tab

def open_patient_master(patient_id, refresh_search_callback=None, window_size=None):
    conn = sqlite3.connect("gerd_center.db")
    cursor = conn.cursor()
    cursor.execute("SELECT FirstName, LastName, MRN, Gender, DOB FROM tblPatients WHERE PatientID = ?", (patient_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return

    first, last, mrn, gender, dob = result

    window = tk.Toplevel()
    window.title(f"Patient Record: {last}, {first}")
    if window_size:
        window.geometry(window_size)
    else:
        window.state('zoomed')


    import print_summary

    # Header area
    header = tk.Frame(window, pady=10)
    header.pack(fill=tk.X)

    lbl_name = tk.Label(header, text=f"Name: {first} {last}", font=("Arial", 12))
    lbl_mrn = tk.Label(header, text=f"MRN: {mrn}", font=("Arial", 12))
    lbl_dob = tk.Label(header, text=f"DOB: {dob}", font=("Arial", 12))
    lbl_gender = tk.Label(header, text=f"Gender: {gender}", font=("Arial", 12))

    lbl_name.grid(row=0, column=0, sticky="w", padx=10)
    lbl_mrn.grid(row=0, column=1, sticky="w", padx=10)
    lbl_dob.grid(row=1, column=0, sticky="w", padx=10)
    lbl_gender.grid(row=1, column=1, sticky="w", padx=10)
    btn_print = tk.Button(header, text="🖨️ Print Summary", command=lambda: print_summary.generate_pdf(patient_id))
    btn_print.grid(row=0, column=2, rowspan=2, sticky="e", padx=20)

    # Tabs
    tab_control = ttk.Notebook(window)
    tab_control.pack(expand=1, fill="both")

    # Demographics Tab
    tab_demographics = ttk.Frame(tab_control)
    tab_control.add(tab_demographics, text="Demographics")
    print("📨 Passing refresh_search_callback to demographics_tab...")
    demographics_tab.build(
        tab_demographics,
        patient_id,
        tab_control,
        on_demographics_updated=refresh_search_callback
    )

    # Diagnostic Tab
    tab_diag = ttk.Frame(tab_control)
    tab_control.add(tab_diag, text='Diagnostics')
    diagnostics_tab.build(tab_diag, patient_id, tab_control)

    # Surgery Tab
    tab_surg = ttk.Frame(tab_control)
    tab_control.add(tab_surg, text='Surgical History')
    surgical_tab.build(tab_surg, patient_id, tab_control)

    # Pathology Tab
    tab_path = ttk.Frame(tab_control)
    tab_control.add(tab_path, text='Pathology')
    pathology_tab.build(tab_path, patient_id, tab_control)

    # Surveillance Tab
    tab_surv = ttk.Frame(tab_control)
    tab_control.add(tab_surv, text='Surveillance')
    surveillance_tab.build(tab_surv, patient_id, tab_control)

    # Recall Tab
    tab_recall = ttk.Frame(tab_control)
    tab_control.add(tab_recall, text='Recalls')
    recall_tab.build(tab_recall, patient_id, tab_control)