import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from add_surgical import open_add_surgical
from scrollable_frame import ScrollableFrame

def build(tab_frame, patient_id, tabs=None):
    for widget in tab_frame.winfo_children():
        widget.destroy()

    scroll = ScrollableFrame(tab_frame)
    scroll.pack(fill="both", expand=True)
    scrollable_frame = scroll.scrollable_frame
    expanded_frame = None

    tk.Button(scrollable_frame, text="Add Surgical", command=lambda: open_add_surgical(
        tab_frame, patient_id, refresh_callback=lambda: build(tab_frame, patient_id)
    )).grid(row=0, column=0, columnspan=5, pady=10, sticky="w")

    def load_surgeries():
        nonlocal expanded_frame
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SurgeryID, SurgeryDate, SurgerySurgeon,
                   HiatalHernia, ParaesophagealHernia, MeshUsed, GastricBypass, SleeveGastrectomy,
                   Toupet, TIF, Nissen, Dor, HellerMyotomy, Stretta, Ablation, LINX,
                   GPOEM, EPOEM, ZPOEM, Pyloroplasty, Revision, GastricStimulator, Dilation, Other,
                   Notes
            FROM tblSurgicalHistory
            WHERE PatientID = ?
            ORDER BY SurgeryDate DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()

        # Spacer to prevent column shifting
        scrollable_frame.grid_columnconfigure(0, minsize=150)
        scrollable_frame.grid_columnconfigure(1, minsize=150)
        scrollable_frame.grid_columnconfigure(2, minsize=250)
        scrollable_frame.grid_columnconfigure(3, minsize=180)

        headers = ["Date", "Surgeon", "Procedures", "Actions"]
        for col, header in enumerate(headers):
            tk.Label(scrollable_frame, text=header, font=("Arial", 10, "bold")).grid(row=1, column=col, padx=5, pady=5, sticky="w")

        for i, row in enumerate(rows, start=2):
            sid, date, surgeon, *checks, notes = row
            labels = [
                "Hiatal", "Para", "Mesh", "Bypass", "Sleeve", "Toupet", "TIF", "Nissen", "Dor",
                "Heller", "Stretta", "Ablation", "LINX", "G-POEM", "E-POEM", "Z-POEM",
                "Pyloro", "Revision", "Stim", "Dilation", "Other"
            ]
            done = [label for val, label in zip(checks[:-1], labels) if val]

            tk.Label(scrollable_frame, text=date).grid(row=i, column=0, sticky="w", padx=5)
            tk.Label(scrollable_frame, text=surgeon).grid(row=i, column=1, sticky="w", padx=5)
            tk.Label(scrollable_frame, text=", ".join(done)).grid(row=i, column=2, sticky="w", padx=5)

            btns = tk.Frame(scrollable_frame)
            btns.grid(row=i, column=3, sticky="w", padx=5)
            tk.Button(btns, text="View", command=lambda s=sid: expand_entry(s, False)).pack(side="left", padx=2)
            tk.Button(btns, text="Edit", command=lambda s=sid: expand_entry(s, True)).pack(side="left", padx=2)
            tk.Button(btns, text="Delete", command=lambda s=sid: delete_surgery(s)).pack(side="left", padx=2)

    def expand_entry(surgery_id, editable):
        nonlocal expanded_frame
        for w in scrollable_frame.winfo_children():
            if isinstance(w, tk.LabelFrame) and w.cget("text") == "Surgical Details":
                w.destroy()

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tblSurgicalHistory WHERE SurgeryID = ?", (surgery_id,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        conn.close()

        expanded_frame = tk.LabelFrame(scrollable_frame, text="Surgical Details", padx=10, pady=10)
        expanded_frame.grid(column=0, columnspan=4, sticky="ew", padx=10, pady=10)

        tk.Label(expanded_frame, text=f"Date: {data['SurgeryDate']}").pack(anchor="w")
        tk.Label(expanded_frame, text=f"Surgeon: {data['SurgerySurgeon']}").pack(anchor="w")

        procedure_names = [
            "HiatalHernia", "ParaesophagealHernia", "MeshUsed", "GastricBypass", "SleeveGastrectomy", "Toupet", "TIF", "Nissen",
            "Dor", "HellerMyotomy", "Stretta", "Ablation", "LINX", "GPOEM", "EPOEM", "ZPOEM", "Pyloroplasty",
            "Revision", "GastricStimulator", "Dilation", "Other"
        ]

        check_labels = [name.replace("GPOEM", "G-POEM").replace("EPOEM", "E-POEM").replace("ZPOEM", "Z-POEM")
                        .replace("HiatalHernia", "Hiatal Hernia")
                        .replace("ParaesophagealHernia", "Paraesophageal Hernia")
                        .replace("MeshUsed", "Mesh Used")
                        .replace("GastricBypass", "Gastric Bypass")
                        .replace("SleeveGastrectomy", "Sleeve Gastrectomy")
                        .replace("HellerMyotomy", "Heller Myotomy")
                        .replace("GastricStimulator", "Gastric Stimulator")
                        for name in procedure_names]

        if editable:
            check_vars = {}
            check_frame = tk.LabelFrame(expanded_frame, text="Procedures")
            check_frame.pack(fill="x", pady=5)
            for i, name in enumerate(procedure_names):
                val = int(data.get(name, 0))
                var = tk.IntVar(value=val)
                cb = tk.Checkbutton(check_frame, text=check_labels[i], variable=var)
                cb.grid(row=i // 2, column=i % 2, sticky="w", padx=5)
                check_vars[name] = var
        else:
            performed = [check_labels[i] for i, name in enumerate(procedure_names) if data.get(name, 0)]
            if performed:
                tk.Label(expanded_frame, text="Procedures Performed:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
                for proc in performed:
                    tk.Label(expanded_frame, text=f"• {proc}").pack(anchor="w", padx=10)
            else:
                tk.Label(expanded_frame, text="No procedures recorded.").pack(anchor="w")

        tk.Label(expanded_frame, text="Notes:").pack(anchor="w")
        notes = tk.Text(expanded_frame, height=4)
        notes.insert("1.0", data.get("Notes", ""))
        if not editable:
            notes.config(state="disabled")
        notes.pack(fill="x")

        def save():
            try:
                conn = sqlite3.connect("gerd_center.db")
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE tblSurgicalHistory SET
                        {', '.join(f"{field} = ?" for field in procedure_names)},
                        Notes = ?
                    WHERE SurgeryID = ?
                ''', (
                    *[check_vars[f].get() for f in procedure_names],
                    notes.get("1.0", "end").strip(),
                    surgery_id
                ))
                conn.commit()
                conn.close()
                messagebox.showinfo("Saved", "Changes saved.")
                build(tab_frame, patient_id)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        if editable:
            tk.Button(expanded_frame, text="Save Changes", command=save).pack(pady=10)

    def delete_surgery(surgery_id):
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
            return
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblSurgicalHistory WHERE SurgeryID = ?", (surgery_id,))
            conn.commit()
            conn.close()
            build(tab_frame, patient_id)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    load_surgeries()
