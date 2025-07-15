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
            var = tk.StringVar(value=value)
            cbo = ttk.Combobox(parent, textvariable=var, values=options, state="readonly" if editable else "disabled")
            cbo.pack(fill="x")
            entries[key] = var

        def add_label_text(parent, label, val, key):
            tk.Label(parent, text=label).pack(anchor="w")
            var = tk.StringVar(value=val)
            ent = tk.Entry(parent, textvariable=var, state="normal" if editable else "readonly")
            ent.pack(fill="x")
            entries[key] = var

        def add_textarea(parent, label, val, key):
            tk.Label(parent, text=label).pack(anchor="w")
            txt = tk.Text(parent, height=2)
            txt.insert("1.0", val)
            if not editable:
                txt.config(state="disabled")
            txt.pack(fill="x")
            entries[key] = txt

        def add_checkbox(parent, label, key):
            var = tk.IntVar(value=int(data.get(key, 0)))
            cb = tk.Checkbutton(parent, text=label, variable=var)
            if not editable:
                cb.config(state="disabled")
            cb.pack(anchor="w")
            checks[key] = var

        def should_expand(*fields):
            return any(data.get(f, "") for f in fields)

        def make_section(name, fields, builder_fn):
            if not should_expand(*fields) and not editable:
                return
            frame = tk.LabelFrame(expanded_frame, text=name)
            frame.pack(fill="x", pady=5)
            builder_fn(frame)

        # Header
        tk.Label(expanded_frame, text=f"Test Date: {data.get('TestDate', '')}").pack(anchor="w")
        tk.Label(expanded_frame, text=f"Surgeon: {data.get('Surgeon', '')}").pack(anchor="w")

        # Sections
        make_section("Endoscopy", ["EsophagitisGrade", "HiatalHerniaSize", "EndoscopyFindings", "Endoscopy"], lambda f: [
            add_checkbox(f, "Completed", "Endoscopy"),
            create_dropdown(f, "Esophagitis Grade", ["None", "LA A", "LA B", "LA C", "LA D"], data.get("EsophagitisGrade", ""), "EsophagitisGrade"),
            create_dropdown(f, "Hiatal Hernia Size", ["None", "1 cm", "2 cm", "3 cm", "4 cm", "5 cm", "6 cm", ">6 cm"], data.get("HiatalHerniaSize", ""), "HiatalHerniaSize"),
            add_textarea(f, "Findings", data.get("EndoscopyFindings", ""), "EndoscopyFindings")
        ])

        make_section("Bravo / pH Impedance", ["DeMeesterScore", "pHFindings", "Bravo", "pHImpedance"], lambda f: [
            add_checkbox(f, "Bravo Completed", "Bravo"),
            add_checkbox(f, "pH Impedance Completed", "pHImpedance"),
            add_label_text(f, "DeMeester Score", data.get("DeMeesterScore", ""), "DeMeesterScore"),
            add_textarea(f, "Findings", data.get("pHFindings", ""), "pHFindings")
        ])

        make_section("EndoFLIP", ["EndoFLIPFindings", "EndoFLIP"], lambda f: [
            add_checkbox(f, "Completed", "EndoFLIP"),
            add_textarea(f, "Findings", data.get("EndoFLIPFindings", ""), "EndoFLIPFindings")
        ])

        make_section("Manometry", ["ManometryFindings", "Manometry"], lambda f: [
            add_checkbox(f, "Completed", "Manometry"),
            add_textarea(f, "Findings", data.get("ManometryFindings", ""), "ManometryFindings")
        ])

        make_section("Gastric Emptying", ["PercentRetained4h", "GastricEmptyingFindings", "GastricEmptying"], lambda f: [
            add_checkbox(f, "Completed", "GastricEmptying"),
            add_label_text(f, "% Retained at 4h", data.get("PercentRetained4h", ""), "PercentRetained4h"),
            add_textarea(f, "Findings", data.get("GastricEmptyingFindings", ""), "GastricEmptyingFindings")
        ])

        make_section("Imaging", ["ImagingFindings", "Imaging"], lambda f: [
            add_checkbox(f, "Completed", "Imaging"),
            add_textarea(f, "Findings", data.get("ImagingFindings", ""), "ImagingFindings")
        ])

        make_section("Upper GI", ["UpperGIFindings", "UpperGI"], lambda f: [
            add_checkbox(f, "Completed", "UpperGI"),
            add_textarea(f, "Findings", data.get("UpperGIFindings", ""), "UpperGIFindings")
        ])

        make_section("Other Notes", ["DiagnosticNotes"], lambda f: [
            add_textarea(f, "Notes", data.get("DiagnosticNotes", ""), "DiagnosticNotes")
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
                    checks["Endoscopy"].get(), checks["Bravo"].get(), checks["pHImpedance"].get(), checks["EndoFLIP"].get(),
                    checks["Manometry"].get(), checks["GastricEmptying"].get(), checks["Imaging"].get(), checks["UpperGI"].get(),
                    entries["EsophagitisGrade"].get(), entries["HiatalHerniaSize"].get(), entries["EndoscopyFindings"].get("1.0", tk.END).strip(),
                    entries["DeMeesterScore"].get(), entries["pHFindings"].get("1.0", tk.END).strip(), entries["EndoFLIPFindings"].get("1.0", tk.END).strip(),
                    entries["ManometryFindings"].get("1.0", tk.END).strip(), entries["PercentRetained4h"].get(), entries["GastricEmptyingFindings"].get("1.0", tk.END).strip(),
                    entries["ImagingFindings"].get("1.0", tk.END).strip(), entries["UpperGIFindings"].get("1.0", tk.END).strip(), entries["DiagnosticNotes"].get("1.0", tk.END).strip(),
                    diagnostic_id
                ))
                conn.commit()
                conn.close()
                messagebox.showinfo("Saved", "Changes saved successfully.")
                build(tab_frame, patient_id)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        if editable:
            tk.Button(expanded_frame, text="Save Changes", command=save_changes).pack(pady=10)

    load_diagnostics()
