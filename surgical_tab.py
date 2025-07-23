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

    # Enhanced refresh callback for add surgical
    def add_surgical_with_refresh():
        def refresh_callback():
            build(tab_frame, patient_id, tabs)
            # Trigger cross-tab refresh for surgical changes
            try:
                from main import tab_refresh_manager
                tab_refresh_manager.refresh_related_tabs('surgical', 'surgical')
            except:
                pass
        
        open_add_surgical(tab_frame, patient_id, refresh_callback=refresh_callback)

    tk.Button(scrollable_frame, text="Add Surgical", command=add_surgical_with_refresh).grid(row=0, column=0, columnspan=5, pady=10, sticky="w")

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

        expanded_frame = tk.LabelFrame(scrollable_frame, text="Surgical Details", padx=15, pady=15)
        expanded_frame.grid(column=0, columnspan=4, sticky="ew", padx=10, pady=10)

        # Header - always show
        header_frame = tk.Frame(expanded_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(header_frame, text=f"🗓️ Surgery Date: {data.get('SurgeryDate', 'Not specified')}", 
                font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(header_frame, text=f"👨‍⚕️ Surgeon: {data.get('SurgerySurgeon', 'Not specified')}", 
                font=("Arial", 11)).pack(anchor="w")

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

        # Group procedures by type for better organization
        procedure_groups = [
            ("🔧 Hernia Repairs", ["HiatalHernia", "ParaesophagealHernia", "MeshUsed"]),
            ("🌯 Fundoplications", ["Nissen", "Toupet", "Dor"]),
            ("⚡ POEM Procedures", ["GPOEM", "EPOEM", "ZPOEM"]),
            ("🍽️ Bariatric Procedures", ["GastricBypass", "SleeveGastrectomy"]),
            ("🔬 Other Anti-Reflux", ["TIF", "LINX", "Stretta"]),
            ("🔪 Motility/Access", ["HellerMyotomy", "Pyloroplasty", "Dilation"]),
            ("⚙️ Advanced/Other", ["Ablation", "GastricStimulator", "Revision", "Other"])
        ]

        if editable:
            check_vars = {}
            
            for group_name, group_procedures in procedure_groups:
                # Only show groups that have procedures or if we're editing
                group_has_procedures = any(data.get(proc, 0) for proc in group_procedures)
                
                if group_has_procedures or editable:
                    group_frame = tk.LabelFrame(expanded_frame, text=group_name, padx=10, pady=8)
                    group_frame.pack(fill="x", pady=5)
                    
                    for proc in group_procedures:
                        if proc in procedure_names:
                            idx = procedure_names.index(proc)
                            val = int(data.get(proc, 0))
                            var = tk.IntVar(value=val)
                            cb = tk.Checkbutton(group_frame, text=check_labels[idx], variable=var)
                            cb.pack(anchor="w", pady=2)
                            check_vars[proc] = var
        else:
            # VIEW MODE - Show organized by groups with clear visual indicators
            procedures_performed = []
            
            for group_name, group_procedures in procedure_groups:
                group_performed = []
                
                for proc in group_procedures:
                    if proc in procedure_names and data.get(proc, 0):
                        idx = procedure_names.index(proc)
                        group_performed.append(check_labels[idx])
                
                if group_performed:
                    procedures_performed.append((group_name, group_performed))
            
            if procedures_performed:
                procedures_frame = tk.LabelFrame(expanded_frame, text="🏥 Procedures Performed", 
                                               padx=15, pady=10)
                procedures_frame.pack(fill="x", pady=10)
                
                for group_name, group_procs in procedures_performed:
                    # Group header
                    group_header = tk.Label(procedures_frame, text=group_name, 
                                          font=("Arial", 10, "bold"), fg="darkblue")
                    group_header.pack(anchor="w", pady=(5, 2))
                    
                    # Procedures in this group
                    for proc in group_procs:
                        proc_label = tk.Label(procedures_frame, text=f"   ✅ {proc}", 
                                            font=("Arial", 9), fg="darkgreen")
                        proc_label.pack(anchor="w", padx=20)
            else:
                no_procedures_frame = tk.Frame(expanded_frame, bg="lightyellow", relief="solid", bd=1)
                no_procedures_frame.pack(fill="x", pady=10)
                tk.Label(no_procedures_frame, text="ℹ️ No specific procedures recorded for this surgery", 
                        bg="lightyellow", font=("Arial", 10, "italic"), pady=10).pack()

        # Notes section
        notes_frame = tk.LabelFrame(expanded_frame, text="📝 Operative Notes", padx=10, pady=8)
        notes_frame.pack(fill="x", pady=10)
        
        if editable:
            notes = tk.Text(notes_frame, height=4, wrap="word")
            notes.insert("1.0", data.get("Notes", ""))
            notes.pack(fill="x", pady=5)
        else:
            # View mode for notes
            notes_content = data.get("Notes", "")
            if notes_content and notes_content.strip():
                # Create a frame with border to mimic text area appearance
                notes_display_frame = tk.Frame(notes_frame, relief="sunken", bd=1)
                notes_display_frame.pack(fill="x", pady=5)
                notes_label = tk.Label(notes_display_frame, text=notes_content.strip(), 
                                     anchor="nw", justify="left", wraplength=500, 
                                     padx=8, pady=8, font=("Arial", 9))
                notes_label.pack(fill="both")
            else:
                no_notes_label = tk.Label(notes_frame, text="No operative notes recorded", 
                                        relief="sunken", bd=1, anchor="w", padx=8, pady=8, 
                                        fg="gray", font=("Arial", 9, "italic"))
                no_notes_label.pack(fill="x", pady=5)

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
                    *[check_vars.get(f, tk.IntVar()).get() for f in procedure_names],
                    notes.get("1.0", "end").strip(),
                    surgery_id
                ))
                conn.commit()
                conn.close()
                messagebox.showinfo("Saved", "Surgical details saved successfully.")
                
                # Refresh current tab and trigger cross-tab refresh
                build(tab_frame, patient_id, tabs)
                try:
                    from main import tab_refresh_manager
                    tab_refresh_manager.refresh_related_tabs('surgical', 'surgical')
                except:
                    pass
                    
            except Exception as e:
                messagebox.showerror("Error", str(e))

        if editable:
            save_frame = tk.Frame(expanded_frame)
            save_frame.pack(pady=15)
            tk.Button(save_frame, text="💾 Save Changes", command=save,
                     font=("Arial", 11, "bold"), bg="lightgreen", padx=20, pady=8).pack()

    def delete_surgery(surgery_id):
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this surgical record?"):
            return
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblSurgicalHistory WHERE SurgeryID = ?", (surgery_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Deleted", "Surgical record deleted successfully.")
            
            # Refresh current tab and trigger cross-tab refresh
            build(tab_frame, patient_id, tabs)
            try:
                from main import tab_refresh_manager
                tab_refresh_manager.refresh_related_tabs('surgical', 'surgical')
            except:
                pass
                
        except Exception as e:
            messagebox.showerror("Error", str(e))

    load_surgeries()