# add_pathology.py

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3

def open_add_pathology(patient_id, refresh_callback):
    def save():
        try:
            date = entry_date.get()
            barretts = var_barretts.get()
            dysplasia = cbo_dysplasia.get() if barretts else ""
            data = {
                "PatientID": patient_id,
                "PathologyDate": date,
                "Biopsy": var_biopsy.get(),
                "WATS3D": var_wats3d.get(),
                "EsoPredict": var_esopredict.get(),
                "TissueCypher": var_tissuecypher.get(),
                "Hpylori": var_hpylori.get(),
                "Barretts": barretts,
                "DysplasiaGrade": dysplasia,
                "AtrophicGastritis": var_gastritis.get(),
                "EoE": var_eoe.get(),
                "EosinophilCount": entry_eos.get() if var_eoe.get() else None,
                "OtherFinding": entry_other.get(),
                "EsoPredictRisk": entry_esopredict.get(),
                "TissueCypherRisk": entry_tissuecypher.get(),
                "Notes": txt_notes.get("1.0", tk.END).strip()
            }

            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO tblPathology (
                    PatientID, PathologyDate, Biopsy, WATS3D, EsoPredict, TissueCypher,
                    Hpylori, Barretts, DysplasiaGrade, AtrophicGastritis, EoE,
                    EosinophilCount, OtherFinding, EsoPredictRisk, TissueCypherRisk, Notes
                ) VALUES (
                    :PatientID, :PathologyDate, :Biopsy, :WATS3D, :EsoPredict, :TissueCypher,
                    :Hpylori, :Barretts, :DysplasiaGrade, :AtrophicGastritis, :EoE,
                    :EosinophilCount, :OtherFinding, :EsoPredictRisk, :TissueCypherRisk, :Notes
                )
            """ , data)

            conn.commit()
            conn.close()

            if barretts:
                messagebox.showinfo("Surveillance Reminder", "Barrett’s detected. Don't forget to update the surveillance plan.")

            popup.destroy()
            if refresh_callback:
                refresh_callback()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def toggle_fields():
        cbo_dysplasia.config(state="readonly" if var_barretts.get() else "disabled")
        entry_eos.config(state="normal" if var_eoe.get() else "disabled")
        if not var_barretts.get():
            cbo_dysplasia.set("")
        if not var_eoe.get():
            entry_eos.delete(0, tk.END)

    popup = tk.Toplevel()
    popup.title("Add Pathology Entry")
    popup.grab_set()

    # Date picker
    tk.Label(popup, text="Pathology Date:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    entry_date = DateEntry(popup, date_pattern="yyyy-mm-dd")
    entry_date.grid(row=0, column=1, padx=5, pady=5)

    # Test types
    test_frame = tk.LabelFrame(popup, text="Test Types")
    test_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    var_biopsy = tk.IntVar()
    tk.Checkbutton(test_frame, text="Biopsy", variable=var_biopsy).grid(row=0, column=0, sticky="w")
    var_wats3d = tk.IntVar()
    tk.Checkbutton(test_frame, text="WATS3D", variable=var_wats3d).grid(row=0, column=1, sticky="w")
    var_esopredict = tk.IntVar()
    tk.Checkbutton(test_frame, text="EsoPredict", variable=var_esopredict).grid(row=1, column=0, sticky="w")
    var_tissuecypher = tk.IntVar()
    tk.Checkbutton(test_frame, text="TissueCypher", variable=var_tissuecypher).grid(row=1, column=1, sticky="w")

    # Findings
    findings_frame = tk.LabelFrame(popup, text="Findings")
    findings_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    # Row 1: Barrett's + Grade
    var_barretts = tk.IntVar()
    tk.Checkbutton(findings_frame, text="Barrett’s", variable=var_barretts, command=toggle_fields).grid(row=0, column=0, sticky="w", padx=5)

    tk.Label(findings_frame, text="Grade:").grid(row=0, column=1, sticky="e", padx=5)
    cbo_dysplasia = ttk.Combobox(findings_frame,
        values=["NGIM", "No Dysplasia", "Indeterminate", "Low Grade", "High Grade"],
        state="disabled", width=17)
    cbo_dysplasia.grid(row=0, column=2, sticky="w", padx=5)

    # Row 2: EoE + Eosinophil Count
    var_eoe = tk.IntVar()
    tk.Checkbutton(findings_frame, text="EoE", variable=var_eoe, command=toggle_fields).grid(row=1, column=0, sticky="w", padx=5)

    tk.Label(findings_frame, text="Eosinophil Count:").grid(row=1, column=1, sticky="e", padx=5)
    entry_eos = tk.Entry(findings_frame, width=10, state="disabled")
    entry_eos.grid(row=1, column=2, sticky="w", padx=5)

    # Row 3: H. pylori + Atrophic Gastritis
    var_hpylori = tk.IntVar()
    tk.Checkbutton(findings_frame, text="H. pylori", variable=var_hpylori).grid(row=2, column=0, sticky="w", padx=5)

    var_gastritis = tk.IntVar()
    tk.Checkbutton(findings_frame, text="Atrophic Gastritis", variable=var_gastritis).grid(row=2, column=1, sticky="w", padx=5)

    # Row 4: Other Finding
    tk.Label(findings_frame, text="Other Finding:").grid(row=3, column=0, sticky="e", padx=5)
    entry_other = tk.Entry(findings_frame, width=30)
    entry_other.grid(row=3, column=1, columnspan=2, sticky="w", padx=5)

    # Risk scores
    risk_frame = tk.LabelFrame(popup, text="Risk Scores")
    risk_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    tk.Label(risk_frame, text="EsoPredict Risk:").grid(row=0, column=0, sticky="e")
    entry_esopredict = tk.Entry(risk_frame, width=30)
    entry_esopredict.grid(row=0, column=1, padx=5, pady=2)

    tk.Label(risk_frame, text="TissueCypher Risk:").grid(row=1, column=0, sticky="e")
    entry_tissuecypher = tk.Entry(risk_frame, width=30)
    entry_tissuecypher.grid(row=1, column=1, padx=5, pady=2)

    # Notes
    tk.Label(popup, text="Notes:").grid(row=4, column=0, sticky="ne", padx=5, pady=5)
    txt_notes = tk.Text(popup, width=45, height=4)
    txt_notes.grid(row=4, column=1, padx=5, pady=5)

    # Save
    tk.Button(popup, text="Save", command=save).grid(row=5, column=0, columnspan=2, pady=10)
