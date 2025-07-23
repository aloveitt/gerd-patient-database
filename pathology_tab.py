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
            if barretts: findings.append(f"Barrett's ({grade})" if grade else "Barrett's")
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
            messagebox.showinfo("Deleted", "Pathology entry deleted successfully.")
            build(tab_frame, patient_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def expand_entry(pathology_id, editable=False):
        nonlocal expanded_frame
        for w in scrollable_frame.winfo_children():
            if isinstance(w, tk.LabelFrame) and w.cget("text") == "Pathology Details":
                w.destroy()

        expanded_frame = tk.LabelFrame(scrollable_frame, text="Pathology Details", padx=15, pady=15)
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

        def add_field(parent, label, key, is_text=False):
            tk.Label(parent, text=label).pack(anchor="w", pady=(5, 2))
            if editable:
                if is_text:
                    txt = tk.Text(parent, height=3, wrap="word")
                    txt.insert("1.0", data.get(key, ""))
                    txt.pack(fill="x", pady=2)
                    entries[key] = txt
                else:
                    var = tk.StringVar(value=data.get(key, ""))
                    ent = tk.Entry(parent, textvariable=var)
                    ent.pack(fill="x", pady=2)
                    entries[key] = var
            else:
                # View mode
                value = data.get(key, "")
                if is_text:
                    if value and value.strip():
                        text_frame = tk.Frame(parent, relief="sunken", bd=1)
                        text_frame.pack(fill="x", pady=2)
                        lbl = tk.Label(text_frame, text=value.strip(), anchor="nw", justify="left", 
                                      wraplength=500, padx=8, pady=5)
                        lbl.pack(fill="both")
                    else:
                        lbl = tk.Label(parent, text="No notes recorded", relief="sunken", bd=1, 
                                      anchor="w", padx=8, pady=5, fg="gray", font=("Arial", 9, "italic"))
                        lbl.pack(fill="x", pady=2)
                else:
                    display_value = value if value else "Not specified"
                    lbl = tk.Label(parent, text=display_value, relief="sunken", bd=1, 
                                  anchor="w", padx=8, pady=5)
                    lbl.pack(fill="x", pady=2)
                # Create dummy entries for consistency
                entries[key] = tk.StringVar(value=value or "")

        def add_dropdown(parent, label, key, options):
            tk.Label(parent, text=label).pack(anchor="w", pady=(5, 2))
            if editable:
                var = tk.StringVar(value=data.get(key, ""))
                cbo = ttk.Combobox(parent, textvariable=var, values=options, state="readonly")
                cbo.pack(fill="x", pady=2)
                entries[key] = var
            else:
                # View mode - show the actual selected value
                value = data.get(key, "")
                display_value = value if value else "Not specified"
                lbl = tk.Label(parent, text=display_value, relief="sunken", bd=1, 
                              anchor="w", padx=8, pady=5)
                lbl.pack(fill="x", pady=2)
                entries[key] = tk.StringVar(value=value or "")

        def add_checkbox(parent, label, key):
            var = tk.IntVar(value=data.get(key, 0))
            if editable:
                cb = tk.Checkbutton(parent, text=label, variable=var)
                cb.pack(anchor="w", pady=2)
            else:
                # View mode - show status with visual indicator
                status = "✅ Positive" if var.get() else "❌ Negative"
                lbl = tk.Label(parent, text=f"{label}: {status}", anchor="w", pady=2)
                lbl.pack(anchor="w", pady=2)
            checks[key] = var

        # Header - always show
        header_frame = tk.Frame(expanded_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(header_frame, text=f"🗓️ Pathology Date: {data.get('PathologyDate', 'Not specified')}", 
                font=("Arial", 12, "bold")).pack(anchor="w")

        # Test Types Section
        test_frame = tk.LabelFrame(expanded_frame, text="🧪 Test Types Performed", padx=10, pady=8)
        test_frame.pack(fill="x", pady=5)
        
        test_types = ["Biopsy", "WATS3D", "EsoPredict", "TissueCypher"]
        test_keys = ["Biopsy", "WATS3D", "EsoPredict", "TissueCypher"]
        
        if editable:
            test_row1 = tk.Frame(test_frame)
            test_row1.pack(fill="x")
            test_row2 = tk.Frame(test_frame)
            test_row2.pack(fill="x")
            
            for i, (test_type, key) in enumerate(zip(test_types, test_keys)):
                parent_frame = test_row1 if i < 2 else test_row2
                var = tk.IntVar(value=data.get(key, 0))
                cb = tk.Checkbutton(parent_frame, text=test_type, variable=var)
                cb.pack(side="left", padx=20)
                checks[key] = var
        else:
            # View mode - show which tests were performed
            performed_tests = [test_types[i] for i, key in enumerate(test_keys) if data.get(key, 0)]
            if performed_tests:
                for test in performed_tests:
                    tk.Label(test_frame, text=f"✅ {test}", anchor="w").pack(anchor="w", pady=1)
            else:
                tk.Label(test_frame, text="❌ No tests performed", anchor="w", fg="gray", 
                        font=("Arial", 9, "italic")).pack(anchor="w", pady=5)

        # Pathology Findings Section
        findings_frame = tk.LabelFrame(expanded_frame, text="🔬 Pathology Findings", padx=10, pady=8)
        findings_frame.pack(fill="x", pady=5)

        # Barrett's and Dysplasia
        barrett_frame = tk.Frame(findings_frame)
        barrett_frame.pack(fill="x", pady=2)
        
        add_checkbox(barrett_frame, "Barrett's Esophagus", "Barretts")
        
        dysplasia_frame = tk.Frame(barrett_frame)
        dysplasia_frame.pack(fill="x", pady=2)
        add_dropdown(dysplasia_frame, "Dysplasia Grade:", "DysplasiaGrade", 
                    ["", "NGIM", "No Dysplasia", "Indeterminate", "Low Grade", "High Grade"])

        # EoE and Eosinophil Count
        eoe_frame = tk.Frame(findings_frame)
        eoe_frame.pack(fill="x", pady=2)
        
        add_checkbox(eoe_frame, "Eosinophilic Esophagitis (EoE)", "EoE")
        
        eos_frame = tk.Frame(eoe_frame)
        eos_frame.pack(fill="x", pady=2)
        add_field(eos_frame, "Eosinophil Count (per hpf):", "EosinophilCount")

        # Other findings
        other_findings_frame = tk.Frame(findings_frame)
        other_findings_frame.pack(fill="x", pady=2)
        
        add_checkbox(other_findings_frame, "H. pylori", "Hpylori")
        add_checkbox(other_findings_frame, "Atrophic Gastritis", "AtrophicGastritis")
        
        other_frame = tk.Frame(other_findings_frame)
        other_frame.pack(fill="x", pady=2)
        add_field(other_frame, "Other Finding:", "OtherFinding")

        # Risk Assessment Section
        risk_frame = tk.LabelFrame(expanded_frame, text="📊 Risk Assessment Scores", padx=10, pady=8)
        risk_frame.pack(fill="x", pady=5)
        
        eso_risk_frame = tk.Frame(risk_frame)
        eso_risk_frame.pack(fill="x", pady=2)
        add_field(eso_risk_frame, "EsoPredict Risk Score:", "EsoPredictRisk")
        
        tc_risk_frame = tk.Frame(risk_frame)
        tc_risk_frame.pack(fill="x", pady=2)
        add_field(tc_risk_frame, "TissueCypher Risk Score:", "TissueCypherRisk")

        # Notes Section
        notes_frame = tk.LabelFrame(expanded_frame, text="📝 Additional Notes", padx=10, pady=8)
        notes_frame.pack(fill="x", pady=5)
        add_field(notes_frame, "Clinical Notes:", "Notes", is_text=True)

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
                    entries.get("PathologyDate", tk.StringVar()).get() if "PathologyDate" in entries else data.get("PathologyDate", ""),
                    checks.get("Biopsy", tk.IntVar()).get() if "Biopsy" in checks else 0,
                    checks.get("WATS3D", tk.IntVar()).get() if "WATS3D" in checks else 0,
                    checks.get("EsoPredict", tk.IntVar()).get() if "EsoPredict" in checks else 0,
                    checks.get("TissueCypher", tk.IntVar()).get() if "TissueCypher" in checks else 0,
                    checks.get("Barretts", tk.IntVar()).get() if "Barretts" in checks else 0,
                    entries.get("DysplasiaGrade", tk.StringVar()).get() if "DysplasiaGrade" in entries else "",
                    checks.get("EoE", tk.IntVar()).get() if "EoE" in checks else 0,
                    entries.get("EosinophilCount", tk.StringVar()).get() if "EosinophilCount" in entries else "",
                    checks.get("Hpylori", tk.IntVar()).get() if "Hpylori" in checks else 0,
                    checks.get("AtrophicGastritis", tk.IntVar()).get() if "AtrophicGastritis" in checks else 0,
                    entries.get("OtherFinding", tk.StringVar()).get() if "OtherFinding" in entries else "",
                    entries.get("EsoPredictRisk", tk.StringVar()).get() if "EsoPredictRisk" in entries else "",
                    entries.get("TissueCypherRisk", tk.StringVar()).get() if "TissueCypherRisk" in entries else "",
                    entries["Notes"].get("1.0", tk.END).strip() if "Notes" in entries and hasattr(entries["Notes"], 'get') else "",
                    pathology_id
                ))
                conn.commit()
                conn.close()

                # Check if Barrett's surveillance reminder is needed
                if checks.get("Barretts", tk.IntVar()).get() if "Barretts" in checks else 0:
                    dysplasia_grade = entries.get("DysplasiaGrade", tk.StringVar()).get() if "DysplasiaGrade" in entries else ""
                    surveillance_msg = "Barrett's esophagus detected. "
                    if dysplasia_grade in ["High Grade"]:
                        surveillance_msg += "High-grade dysplasia requires 3-month surveillance intervals."
                    elif dysplasia_grade in ["Low Grade"]:
                        surveillance_msg += "Low-grade dysplasia requires 6-month surveillance intervals."
                    elif dysplasia_grade in ["No Dysplasia", "NGIM"]:
                        surveillance_msg += "No dysplasia - 3-year surveillance intervals recommended."
                    else:
                        surveillance_msg += "Please plan appropriate surveillance based on dysplasia grade."
                    
                    messagebox.showinfo("Barrett's Surveillance Reminder", 
                                       f"Pathology saved successfully!\n\n🔔 CLINICAL REMINDER:\n{surveillance_msg}")
                else:
                    messagebox.showinfo("Saved", "Pathology changes saved successfully.")

                build(tab_frame, patient_id)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        if editable:
            save_frame = tk.Frame(expanded_frame)
            save_frame.pack(pady=15)
            tk.Button(save_frame, text="💾 Save Changes", command=save_changes,
                     font=("Arial", 11, "bold"), bg="lightgreen", padx=20, pady=8).pack()

        # Show clinical significance in view mode
        if not editable:
            # Add clinical significance summary
            clinical_frame = tk.LabelFrame(expanded_frame, text="🎯 Clinical Significance", 
                                         padx=10, pady=8, fg="darkblue")
            clinical_frame.pack(fill="x", pady=10)
            
            significance = []
            
            if data.get("Barretts", 0):
                grade = data.get("DysplasiaGrade", "")
                if grade == "High Grade":
                    significance.append("🚨 HIGH PRIORITY: High-grade dysplasia requires immediate oncology consultation and 3-month surveillance")
                elif grade == "Low Grade":
                    significance.append("⚠️ MODERATE PRIORITY: Low-grade dysplasia requires 6-month surveillance intervals")
                elif grade in ["No Dysplasia", "NGIM"]:
                    significance.append("✅ ROUTINE: Barrett's without dysplasia - 3-year surveillance appropriate")
                else:
                    significance.append("📋 Barrett's esophagus confirmed - surveillance planning needed")
            
            if data.get("EoE", 0):
                eos_count = data.get("EosinophilCount", "")
                if eos_count:
                    try:
                        count = float(eos_count)
                        if count >= 15:
                            significance.append("🔬 EoE confirmed with eosinophil count supporting diagnosis")
                        else:
                            significance.append("⚠️ EoE diagnosis with low eosinophil count - consider repeat biopsy")
                    except:
                        significance.append("🔬 EoE diagnosis noted")
                else:
                    significance.append("🔬 EoE diagnosis noted")
            
            if data.get("Hpylori", 0):
                significance.append("🦠 H. pylori positive - consider eradication therapy")
            
            if data.get("AtrophicGastritis", 0):
                significance.append("📊 Atrophic gastritis - surveillance for gastric cancer may be appropriate")
            
            if significance:
                for sig in significance:
                    tk.Label(clinical_frame, text=sig, anchor="w", wraplength=600, 
                            justify="left", font=("Arial", 9), pady=2).pack(anchor="w")
            else:
                tk.Label(clinical_frame, text="No specific clinical actions required based on these findings", 
                        anchor="w", font=("Arial", 9, "italic"), fg="gray").pack(anchor="w")

    load_pathology()