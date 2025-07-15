# pathology_tab.py

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from add_pathology import open_add_pathology

def build(tab_frame, patient_id, tabs=None):
    for widget in tab_frame.winfo_children():
        widget.destroy()

    container = tk.Frame(tab_frame)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    expanded_frame = None

    tk.Button(scrollable_frame, text="Add Pathology", command=lambda: open_add_pathology(
        patient_id, refresh_callback=lambda: build(tab_frame, patient_id)
    )).grid(row=0, column=0, columnspan=4, pady=10, sticky="w")

    def load_pathology():
        nonlocal expanded_frame

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT PathologyID, PathologyDate,
                   Biopsy, WATS3D, EsoPredict, TissueCypher,
                   Barretts, DysplasiaGrade, EoE, EosinophilCount,
                   Hpylori, AtrophicGastritis, OtherFinding,
                   EsoPredictRisk, TissueCypherRisk, Notes
            FROM tblPathology
            WHERE PatientID = ?
            ORDER BY PathologyDate DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()

        headers = ["Date", "Test Types", "Findings", "Risk Scores", "Actions"]
        for col, header in enumerate(headers):
            tk.Label(scrollable_frame, text=header, font=("Arial", 10, "bold"), width=20, anchor="w").grid(row=1, column=col, padx=5, pady=5, sticky="w")

        for i, row in enumerate(rows, start=2):
            (pid, date, biopsy, wats, eso, tc,
             barretts, grade, eoe, eos,
             hp, gastritis, other,
             eso_risk, tc_risk, notes) = row

            # Column 1: Date
            tk.Label(scrollable_frame, text=date, width=20, anchor="w").grid(row=i, column=0, padx=5, pady=2, sticky="w")

            # Column 2: Test Types
            test_types = []
            if biopsy: test_types.append("Biopsy")
            if wats: test_types.append("WATS3D")
            if eso: test_types.append("EsoPredict")
            if tc: test_types.append("TissueCypher")
            tk.Label(scrollable_frame, text=", ".join(test_types), width=20, anchor="w").grid(row=i, column=1, padx=5, pady=2, sticky="w")

            # Column 3: Findings
            findings = []
            if barretts: findings.append(f"Barrett’s ({grade})" if grade else "Barrett’s")
            if eoe: findings.append(f"EoE ({eos})" if eos else "EoE")
            if hp: findings.append("H. pylori")
            if gastritis: findings.append("Atrophic Gastritis")
            if other: findings.append(f"Other: {other}")
            if notes: findings.append(f"Notes: {notes.strip()}")
            tk.Label(scrollable_frame, text=", ".join(findings), width=40, anchor="w", wraplength=350, justify="left").grid(
                row=i, column=2, padx=5, pady=2, sticky="w"
            )

            # Column 4: Risk Scores
            risks = []
            if eso_risk: risks.append(f"Eso: {eso_risk}")
            if tc_risk: risks.append(f"TC: {tc_risk}")
            tk.Label(scrollable_frame, text=", ".join(risks), width=20, anchor="w").grid(row=i, column=3, padx=5, pady=2, sticky="w")

            # Column 5: Buttons
            action_frame = tk.Frame(scrollable_frame)
            action_frame.grid(row=i, column=4, padx=5, pady=2, sticky="w")
            tk.Button(action_frame, text="View", command=lambda rid=pid: expand_entry(rid, editable=False)).pack(side="left", padx=2)
            tk.Button(action_frame, text="Edit", command=lambda rid=pid: expand_entry(rid, editable=True)).pack(side="left", padx=2)
            tk.Button(action_frame, text="Delete", command=lambda rid=pid: delete_entry(rid)).pack(side="left", padx=2)

    def delete_entry(pathology_id):
        if not messagebox.askyesno("Confirm Delete", "Delete this pathology entry?"):
            return
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblPathology WHERE PathologyID = ?", (pathology_id,))
            conn.commit()
            conn.close()
            build(tab_frame, patient_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def expand_entry(pathology_id, editable=False):
        nonlocal expanded_frame
        for w in scrollable_frame.winfo_children():
            if isinstance(w, tk.LabelFrame) and w.cget("text") == "Pathology Details":
                w.destroy()

        expanded_frame = tk.LabelFrame(scrollable_frame, text="Pathology Details", padx=10, pady=10)
        expanded_frame.grid(column=0, columnspan=5, padx=10, pady=10, sticky="ew")

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblPathology WHERE PathologyID = ?", (pathology_id,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        conn.close()

        entries = {}
        checks = {}

        def add_field(label, key, is_text=False):
            tk.Label(expanded_frame, text=label).pack(anchor="w")
            if is_text:
                txt = tk.Text(expanded_frame, height=3)
                txt.insert("1.0", data.get(key, ""))
                if not editable:
                    txt.config(state="disabled")
                txt.pack(fill="x")
                entries[key] = txt
            else:
                var = tk.StringVar(value=data.get(key, ""))
                ent = tk.Entry(expanded_frame, textvariable=var, state="normal" if editable else "readonly")
                ent.pack(fill="x")
                entries[key] = var

        def add_dropdown(label, key, options):
            tk.Label(expanded_frame, text=label).pack(anchor="w")
            var = tk.StringVar(value=data.get(key, ""))
            state = "readonly" if editable else "disabled"
            cbo = ttk.Combobox(expanded_frame, textvariable=var, values=options, state=state)
            cbo.pack(fill="x")
            entries[key] = var

        def add_checkbox(label, key):
            var = tk.IntVar(value=data.get(key))
            cb = tk.Checkbutton(expanded_frame, text=label, variable=var)
            if not editable:
                cb.config(state="disabled")
            cb.pack(anchor="w")
            checks[key] = var

        # Fields
        add_field("Date", "PathologyDate")
        add_checkbox("Biopsy", "Biopsy")
        add_checkbox("WATS3D", "WATS3D")
        add_checkbox("EsoPredict", "EsoPredict")
        add_checkbox("TissueCypher", "TissueCypher")
        add_checkbox("Barrett’s", "Barretts")
        add_dropdown("Grade", "DysplasiaGrade", ["NGIM", "No Dysplasia", "Indeterminate", "Low Grade", "High Grade"])
        add_checkbox("EoE", "EoE")
        add_field("Eosinophil Count", "EosinophilCount")
        add_checkbox("H. pylori", "Hpylori")
        add_checkbox("Atrophic Gastritis", "AtrophicGastritis")
        add_field("Other Finding", "OtherFinding")
        add_field("EsoPredict Risk", "EsoPredictRisk")
        add_field("TissueCypher Risk", "TissueCypherRisk")
        add_field("Notes", "Notes", is_text=True)

        def save_changes():
            try:
                conn = sqlite3.connect("gerd_center.db")
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tblPathology SET
                        PathologyDate = ?, Biopsy = ?, WATS3D = ?, EsoPredict = ?, TissueCypher = ?,
                        Barretts = ?, DysplasiaGrade = ?, EoE = ?, EosinophilCount = ?,
                        Hpylori = ?, AtrophicGastritis = ?, OtherFinding = ?,
                        EsoPredictRisk = ?, TissueCypherRisk = ?, Notes = ?
                    WHERE PathologyID = ?
                """, (
                    entries["PathologyDate"].get(),
                    checks["Biopsy"].get(),
                    checks["WATS3D"].get(),
                    checks["EsoPredict"].get(),
                    checks["TissueCypher"].get(),
                    checks["Barretts"].get(),
                    entries["DysplasiaGrade"].get(),
                    checks["EoE"].get(),
                    entries["EosinophilCount"].get(),
                    checks["Hpylori"].get(),
                    checks["AtrophicGastritis"].get(),
                    entries["OtherFinding"].get(),
                    entries["EsoPredictRisk"].get(),
                    entries["TissueCypherRisk"].get(),
                    entries["Notes"].get("1.0", tk.END).strip(),
                    pathology_id
                ))
                conn.commit()
                conn.close()

                if checks["Barretts"].get():
                    messagebox.showinfo("Surveillance Reminder", "Barrett’s detected. Don't forget to update the surveillance plan.")

                build(tab_frame, patient_id)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        if editable:
            tk.Button(expanded_frame, text="Save Changes", command=save_changes).pack(pady=10)

    load_pathology()
