import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from add_edit_diagnostic import open_add_edit_window

def build(tab_frame, patient_id, tabs=None):
    for widget in tab_frame.winfo_children():
        widget.destroy()

    container = tk.Frame(tab_frame)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Enable mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    expanded_frame = None

    tk.Button(scrollable_frame, text="Add Diagnostic", command=lambda: open_add_edit_window(
        tab_frame, patient_id, refresh_callback=lambda: build(tab_frame, patient_id)
    )).grid(row=0, column=0, columnspan=4, pady=10, sticky="w")

    def load_diagnostics():
        nonlocal expanded_frame

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DiagnosticID, TestDate, Surgeon,
                   Endoscopy, Bravo, pHImpedance, EndoFLIP,
                   Manometry, GastricEmptying, Imaging, UpperGI
            FROM tblDiagnostics
            WHERE PatientID = ?
            ORDER BY TestDate DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()

        headers = ["Date", "Surgeon", "Tests Done", "Actions"]
        for col, header in enumerate(headers):
            tk.Label(scrollable_frame, text=header, font=("Arial", 10, "bold"), width=20, anchor="w").grid(row=1, column=col, padx=5, pady=5, sticky="w")

        for i, row in enumerate(rows, start=2):
            diag_id, date, surgeon, endo, bravo, ph, flip, mano, empty, img, ugi = row
            tests = []
            if endo: tests.append("Endo")
            if bravo: tests.append("Bravo")
            if ph: tests.append("pH")
            if flip: tests.append("FLIP")
            if mano: tests.append("Mano")
            if empty: tests.append("GE")
            if img: tests.append("Img")
            if ugi: tests.append("UGI")

            tk.Label(scrollable_frame, text=date, width=20, anchor="w").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            tk.Label(scrollable_frame, text=surgeon, width=20, anchor="w").grid(row=i, column=1, padx=5, pady=2, sticky="w")
            tk.Label(scrollable_frame, text=", ".join(tests), width=20, anchor="w").grid(row=i, column=2, padx=5, pady=2, sticky="w")

            action_frame = tk.Frame(scrollable_frame)
            action_frame.grid(row=i, column=3, padx=5, pady=2, sticky="w")
            tk.Button(action_frame, text="View", command=lambda d=diag_id: expand_entry(d, editable=False)).pack(side="left", padx=2)
            tk.Button(action_frame, text="Edit", command=lambda d=diag_id: expand_entry(d, editable=True)).pack(side="left", padx=2)
            tk.Button(action_frame, text="Delete", command=lambda d=diag_id: delete_diagnostic(d)).pack(side="left", padx=2)

    def delete_diagnostic(diagnostic_id):
        if not messagebox.askyesno("Confirm Delete", "Delete this diagnostic entry?"):
            return
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblDiagnostics WHERE DiagnosticID = ?", (diagnostic_id,))
            conn.commit()
            conn.close()
            build(tab_frame, patient_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def expand_entry(diagnostic_id, editable=False):
        nonlocal expanded_frame
        for w in scrollable_frame.winfo_children():
            if isinstance(w, tk.LabelFrame) and w.cget("text") == "Diagnostic Details":
                w.destroy()

        expanded_frame = tk.LabelFrame(scrollable_frame, text="Diagnostic Details", padx=10, pady=10)
        expanded_frame.grid(column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblDiagnostics WHERE DiagnosticID = ?", (diagnostic_id,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        conn.close()

        entries = {}
        checks = {}

        def create_dropdown(parent, label, options, value, key):
            tk.Label(parent, text=label).pack(anchor="w")
            if editable:
                var = tk.StringVar(value=value or "")
                cbo = ttk.Combobox(parent, textvariable=var, values=options, state="readonly")
                cbo.pack(fill="x", pady=2)
                entries[key] = var
            else:
                # In view mode, show as a label with the actual value
                display_value = value if value else "Not specified"
                lbl = tk.Label(parent, text=display_value, relief="sunken", bd=1, anchor="w", padx=5, pady=2)
                lbl.pack(fill="x", pady=2)
                # Create a dummy variable for consistency
                entries[key] = tk.StringVar(value=value or "")

        def add_label_text(parent, label, val, key):
            tk.Label(parent, text=label).pack(anchor="w")
            if editable:
                var = tk.StringVar(value=val or "")
                ent = tk.Entry(parent, textvariable=var, state="normal")
                ent.pack(fill="x", pady=2)
                entries[key] = var
            else:
                # In view mode, show as a label with the actual value
                display_value = val if val else "Not specified"
                lbl = tk.Label(parent, text=display_value, relief="sunken", bd=1, anchor="w", padx=5, pady=2)
                lbl.pack(fill="x", pady=2)
                # Create a dummy variable for consistency
                entries[key] = tk.StringVar(value=val or "")

        def add_textarea(parent, label, val, key):
            tk.Label(parent, text=label).pack(anchor="w")
            if editable:
                txt = tk.Text(parent, height=3, wrap="word")
                txt.insert("1.0", val or "")
                txt.pack(fill="x", pady=2)
                entries[key] = txt
            else:
                # In view mode, show as a label if there's content
                if val and val.strip():
                    # Create a frame with border to mimic text area appearance
                    text_frame = tk.Frame(parent, relief="sunken", bd=1)
                    text_frame.pack(fill="x", pady=2)
                    lbl = tk.Label(text_frame, text=val.strip(), anchor="nw", justify="left", 
                                  wraplength=400, padx=5, pady=3)
                    lbl.pack(fill="both")
                else:
                    lbl = tk.Label(parent, text="No findings recorded", relief="sunken", bd=1, 
                                  anchor="w", padx=5, pady=2, fg="gray", font=("Arial", 9, "italic"))
                    lbl.pack(fill="x", pady=2)
                # Create a dummy text widget for consistency
                entries[key] = tk.Text(parent, height=1)
                entries[key].insert("1.0", val or "")

        def add_checkbox(parent, label, key):
            var = tk.IntVar(value=int(data.get(key, 0)))
            if editable:
                cb = tk.Checkbutton(parent, text=label, variable=var)
                cb.pack(anchor="w", pady=2)
            else:
                # In view mode, show status with checkmark or X
                status = "✅ Completed" if var.get() else "❌ Not performed"
                lbl = tk.Label(parent, text=f"{label}: {status}", anchor="w", pady=2)
                lbl.pack(anchor="w", pady=2)
            checks[key] = var

        def has_data(*fields):
            """Check if any of the specified fields have meaningful data"""
            for field in fields:
                value = data.get(field, "")
                if field in ['Endoscopy', 'Bravo', 'pHImpedance', 'EndoFLIP', 'Manometry', 'GastricEmptying', 'Imaging', 'UpperGI']:
                    # For checkbox fields, check if they're checked (1)
                    if value == 1:
                        return True
                else:
                    # For text fields, check if they have content
                    if value and str(value).strip():
                        return True
            return False

        def make_section(name, fields, builder_fn):
            """Create a section if it has data OR if we're in edit mode"""
            if has_data(*fields) or editable:
                frame = tk.LabelFrame(expanded_frame, text=name, padx=10, pady=5)
                frame.pack(fill="x", pady=5)
                builder_fn(frame)

        # Header - always show
        header_frame = tk.Frame(expanded_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(header_frame, text=f"📅 Test Date: {data.get('TestDate', 'Not specified')}", 
                font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(header_frame, text=f"👨‍⚕️ Surgeon: {data.get('Surgeon', 'Not specified')}", 
                font=("Arial", 11)).pack(anchor="w")

        # Sections - show if they have data or if editing
        make_section("🔍 Endoscopy", ["Endoscopy", "EsophagitisGrade", "HiatalHerniaSize", "EndoscopyFindings"], lambda f: [
            add_checkbox(f, "Endoscopy Completed", "Endoscopy"),
            create_dropdown(f, "Esophagitis Grade:", ["", "None", "LA A", "LA B", "LA C", "LA D"], data.get("EsophagitisGrade", ""), "EsophagitisGrade"),
            create_dropdown(f, "Hiatal Hernia Size:", ["", "None", "1 cm", "2 cm", "3 cm", "4 cm", "5 cm", "6 cm", ">6 cm"], data.get("HiatalHerniaSize", ""), "HiatalHerniaSize"),
            add_textarea(f, "Endoscopy Findings:", data.get("EndoscopyFindings", ""), "EndoscopyFindings")
        ])

        make_section("🧪 Bravo / pH Impedance", ["Bravo", "pHImpedance", "DeMeesterScore", "pHFindings"], lambda f: [
            add_checkbox(f, "Bravo Completed", "Bravo"),
            add_checkbox(f, "pH Impedance Completed", "pHImpedance"),
            add_label_text(f, "DeMeester Score:", data.get("DeMeesterScore", ""), "DeMeesterScore"),
            add_textarea(f, "pH Study Findings:", data.get("pHFindings", ""), "pHFindings")
        ])

        make_section("🔬 EndoFLIP", ["EndoFLIP", "EndoFLIPFindings"], lambda f: [
            add_checkbox(f, "EndoFLIP Completed", "EndoFLIP"),
            add_textarea(f, "EndoFLIP Findings:", data.get("EndoFLIPFindings", ""), "EndoFLIPFindings")
        ])

        make_section("📊 Manometry", ["Manometry", "ManometryFindings"], lambda f: [
            add_checkbox(f, "Manometry Completed", "Manometry"),
            add_textarea(f, "Manometry Findings:", data.get("ManometryFindings", ""), "ManometryFindings")
        ])

        make_section("🍽️ Gastric Emptying", ["GastricEmptying", "PercentRetained4h", "GastricEmptyingFindings"], lambda f: [
            add_checkbox(f, "Gastric Emptying Completed", "GastricEmptying"),
            add_label_text(f, "% Retained at 4h:", data.get("PercentRetained4h", ""), "PercentRetained4h"),
            add_textarea(f, "Gastric Emptying Findings:", data.get("GastricEmptyingFindings", ""), "GastricEmptyingFindings")
        ])

        make_section("🖼️ Imaging", ["Imaging", "ImagingFindings"], lambda f: [
            add_checkbox(f, "Imaging Completed", "Imaging"),
            add_textarea(f, "Imaging Findings:", data.get("ImagingFindings", ""), "ImagingFindings")
        ])

        make_section("🥤 Upper GI", ["UpperGI", "UpperGIFindings"], lambda f: [
            add_checkbox(f, "Upper GI Completed", "UpperGI"),
            add_textarea(f, "Upper GI Findings:", data.get("UpperGIFindings", ""), "UpperGIFindings")
        ])

        make_section("📝 Additional Notes", ["DiagnosticNotes"], lambda f: [
            add_textarea(f, "Additional Notes:", data.get("DiagnosticNotes", ""), "DiagnosticNotes")
        ])

        def save_changes():
            try:
                conn = sqlite3.connect("gerd_center.db")
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tblDiagnostics SET
                        Endoscopy = ?, Bravo = ?, pHImpedance = ?, EndoFLIP = ?, Manometry = ?,
                        GastricEmptying = ?, Imaging = ?, UpperGI = ?,
                        EsophagitisGrade = ?, HiatalHerniaSize = ?, EndoscopyFindings = ?,
                        DeMeesterScore = ?, pHFindings = ?, EndoFLIPFindings = ?,
                        ManometryFindings = ?, PercentRetained4h = ?, GastricEmptyingFindings = ?,
                        ImagingFindings = ?, UpperGIFindings = ?, DiagnosticNotes = ?
                    WHERE DiagnosticID = ?
                """, (
                    checks.get("Endoscopy", tk.IntVar()).get() if "Endoscopy" in checks else 0,
                    checks.get("Bravo", tk.IntVar()).get() if "Bravo" in checks else 0,
                    checks.get("pHImpedance", tk.IntVar()).get() if "pHImpedance" in checks else 0,
                    checks.get("EndoFLIP", tk.IntVar()).get() if "EndoFLIP" in checks else 0,
                    checks.get("Manometry", tk.IntVar()).get() if "Manometry" in checks else 0,
                    checks.get("GastricEmptying", tk.IntVar()).get() if "GastricEmptying" in checks else 0,
                    checks.get("Imaging", tk.IntVar()).get() if "Imaging" in checks else 0,
                    checks.get("UpperGI", tk.IntVar()).get() if "UpperGI" in checks else 0,
                    entries.get("EsophagitisGrade", tk.StringVar()).get() if "EsophagitisGrade" in entries else "",
                    entries.get("HiatalHerniaSize", tk.StringVar()).get() if "HiatalHerniaSize" in entries else "",
                    entries["EndoscopyFindings"].get("1.0", tk.END).strip() if "EndoscopyFindings" in entries and hasattr(entries["EndoscopyFindings"], 'get') else "",
                    entries.get("DeMeesterScore", tk.StringVar()).get() if "DeMeesterScore" in entries else "",
                    entries["pHFindings"].get("1.0", tk.END).strip() if "pHFindings" in entries and hasattr(entries["pHFindings"], 'get') else "",
                    entries["EndoFLIPFindings"].get("1.0", tk.END).strip() if "EndoFLIPFindings" in entries and hasattr(entries["EndoFLIPFindings"], 'get') else "",
                    entries["ManometryFindings"].get("1.0", tk.END).strip() if "ManometryFindings" in entries and hasattr(entries["ManometryFindings"], 'get') else "",
                    entries.get("PercentRetained4h", tk.StringVar()).get() if "PercentRetained4h" in entries else "",
                    entries["GastricEmptyingFindings"].get("1.0", tk.END).strip() if "GastricEmptyingFindings" in entries and hasattr(entries["GastricEmptyingFindings"], 'get') else "",
                    entries["ImagingFindings"].get("1.0", tk.END).strip() if "ImagingFindings" in entries and hasattr(entries["ImagingFindings"], 'get') else "",
                    entries["UpperGIFindings"].get("1.0", tk.END).strip() if "UpperGIFindings" in entries and hasattr(entries["UpperGIFindings"], 'get') else "",
                    entries["DiagnosticNotes"].get("1.0", tk.END).strip() if "DiagnosticNotes" in entries and hasattr(entries["DiagnosticNotes"], 'get') else "",
                    diagnostic_id
                ))
                conn.commit()
                conn.close()
                messagebox.showinfo("Saved", "Changes saved successfully.")
                build(tab_frame, patient_id)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        if editable:
            save_frame = tk.Frame(expanded_frame)
            save_frame.pack(pady=15)
            tk.Button(save_frame, text="💾 Save Changes", command=save_changes,
                     font=("Arial", 11, "bold"), bg="lightgreen", padx=20, pady=8).pack()

        # Show a message if no data found in view mode
        if not editable:
            # Count how many sections have data
            section_checks = [
                ("Endoscopy", ["Endoscopy", "EsophagitisGrade", "HiatalHerniaSize", "EndoscopyFindings"]),
                ("Bravo/pH", ["Bravo", "pHImpedance", "DeMeesterScore", "pHFindings"]),
                ("EndoFLIP", ["EndoFLIP", "EndoFLIPFindings"]),
                ("Manometry", ["Manometry", "ManometryFindings"]),
                ("Gastric Emptying", ["GastricEmptying", "PercentRetained4h", "GastricEmptyingFindings"]),
                ("Imaging", ["Imaging", "ImagingFindings"]),
                ("Upper GI", ["UpperGI", "UpperGIFindings"]),
                ("Notes", ["DiagnosticNotes"])
            ]
            
            sections_with_data = [name for name, fields in section_checks if has_data(*fields)]
            
            if not sections_with_data:
                no_data_frame = tk.Frame(expanded_frame, bg="lightyellow", relief="solid", bd=1)
                no_data_frame.pack(fill="x", pady=10, padx=10)
                tk.Label(no_data_frame, text="ℹ️ No detailed findings recorded for this diagnostic study", 
                        bg="lightyellow", font=("Arial", 10, "italic"), pady=10).pack()

    load_diagnostics()