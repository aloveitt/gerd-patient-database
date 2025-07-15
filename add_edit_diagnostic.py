import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime

def open_add_edit_window(parent, patient_id, diagnostic_id=None, refresh_callback=None, view_only=False):
    window = tk.Toplevel(parent)
    window.title("View Diagnostic Test" if view_only else "Add/Edit Diagnostic Test")
    window.geometry("600x800")
    window.transient(parent)

    conn = sqlite3.connect("gerd_center.db")
    cursor = conn.cursor()

    is_edit_mode = diagnostic_id is not None
    data = {}

    if is_edit_mode:
        cursor.execute("SELECT * FROM tblDiagnostics WHERE DiagnosticID = ?", (diagnostic_id,))
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            data = dict(zip(columns, row))

    def disable_widget(widget):
        try:
            widget.configure(state="disabled")
        except:
            pass

    # Form fields
    tk.Label(window, text="Test Date:").pack()
    entry_date = DateEntry(window, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    if "TestDate" in data:
        entry_date.set_date(data["TestDate"])
    entry_date.pack(pady=5)

    tk.Label(window, text="Surgeon:").pack()
    surgeon_var = tk.StringVar()
    try:
        cursor.execute("SELECT SurgeonName FROM tblSurgeons ORDER BY SurgeonName")
        surgeon_names = [row[0] for row in cursor.fetchall()]
    except:
        surgeon_names = []
    surgeon_combo = ttk.Combobox(window, textvariable=surgeon_var, values=surgeon_names, state="readonly")
    surgeon_combo.set(data.get("Surgeon", ""))
    surgeon_combo.pack(pady=5)

    section_frames = {}

    def create_section(name):
        section_frame = tk.Frame(window, bd=2, relief="groove", padx=5, pady=5)
        section_frame.pack(fill="x", pady=5)
        toggle_btn = tk.Button(section_frame, text=f"► {name}", anchor="w")
        toggle_btn.pack(fill="x")
        content_frame = tk.Frame(section_frame)
        section_frames[name] = (content_frame, toggle_btn)

        def toggle():
            if content_frame.winfo_ismapped():
                content_frame.pack_forget()
                toggle_btn.config(text=f"► {name}")
            else:
                content_frame.pack(fill="x")
                toggle_btn.config(text=f"▼ {name}")

        toggle_btn.config(command=toggle)
        return content_frame

    # Endoscopy
    endoscopy_frame = create_section("Endoscopy")
    endoscopy_var = tk.IntVar(value=data.get("Endoscopy", 0))
    endoscopy_chk = tk.Checkbutton(endoscopy_frame, text="Completed", variable=endoscopy_var)
    endoscopy_chk.pack(anchor="w")

    tk.Label(endoscopy_frame, text="Esophagitis Grade:").pack(anchor="w")
    esophagitis_var = tk.StringVar(value=data.get("EsophagitisGrade", ""))
    esophagitis_combo = ttk.Combobox(endoscopy_frame, textvariable=esophagitis_var, values=["None", "LA A", "LA B", "LA C", "LA D"])
    esophagitis_combo.pack(anchor="w")

    tk.Label(endoscopy_frame, text="Hiatal Hernia Size:").pack(anchor="w")
    hernia_var = tk.StringVar(value=data.get("HiatalHerniaSize", ""))
    hernia_combo = ttk.Combobox(endoscopy_frame, textvariable=hernia_var, values=["None", "1 cm", "2 cm", "3 cm", "4 cm", "5 cm", "6 cm", ">6 cm"])
    hernia_combo.pack(anchor="w")

    endo_notes = tk.Text(endoscopy_frame, height=3)
    endo_notes.insert("1.0", data.get("EndoscopyFindings", ""))
    endo_notes.pack(fill="x")

    # Bravo / pH Impedance
    ph_frame = create_section("Bravo / pH Impedance")
    bravo_var = tk.IntVar(value=data.get("Bravo", 0))
    bravo_chk = tk.Checkbutton(ph_frame, text="Bravo Completed", variable=bravo_var)
    bravo_chk.pack(anchor="w")
    ph_var = tk.IntVar(value=data.get("pHImpedance", 0))
    ph_chk = tk.Checkbutton(ph_frame, text="pH Impedance Completed", variable=ph_var)
    ph_chk.pack(anchor="w")

    tk.Label(ph_frame, text="DeMeester Score:").pack(anchor="w")
    demeester_var = tk.StringVar(value=data.get("DeMeesterScore", ""))
    demeester_entry = tk.Entry(ph_frame, textvariable=demeester_var)
    demeester_entry.pack(anchor="w")

    ph_notes = tk.Text(ph_frame, height=3)
    ph_notes.insert("1.0", data.get("pHFindings", ""))
    ph_notes.pack(fill="x")

    # EndoFLIP
    flip_frame = create_section("EndoFLIP")
    flip_var = tk.IntVar(value=data.get("EndoFLIP", 0))
    flip_chk = tk.Checkbutton(flip_frame, text="Completed", variable=flip_var)
    flip_chk.pack(anchor="w")
    flip_notes = tk.Text(flip_frame, height=3)
    flip_notes.insert("1.0", data.get("EndoFLIPFindings", ""))
    flip_notes.pack(fill="x")

    # Manometry
    mano_frame = create_section("Manometry")
    mano_var = tk.IntVar(value=data.get("Manometry", 0))
    mano_chk = tk.Checkbutton(mano_frame, text="Completed", variable=mano_var)
    mano_chk.pack(anchor="w")
    mano_notes = tk.Text(mano_frame, height=3)
    mano_notes.insert("1.0", data.get("ManometryFindings", ""))
    mano_notes.pack(fill="x")

    # Gastric Emptying
    empty_frame = create_section("Gastric Emptying")
    empty_var = tk.IntVar(value=data.get("GastricEmptying", 0))
    empty_chk = tk.Checkbutton(empty_frame, text="Completed", variable=empty_var)
    empty_chk.pack(anchor="w")

    tk.Label(empty_frame, text="% Retained at 4h:").pack(anchor="w")
    retained_var = tk.StringVar(value=data.get("PercentRetained4h", ""))
    retained_entry = tk.Entry(empty_frame, textvariable=retained_var)
    retained_entry.pack(anchor="w")

    empty_notes = tk.Text(empty_frame, height=3)
    empty_notes.insert("1.0", data.get("GastricEmptyingFindings", ""))
    empty_notes.pack(fill="x")

    # Imaging
    imaging_frame = create_section("Imaging")
    imaging_var = tk.IntVar(value=data.get("Imaging", 0))
    imaging_chk = tk.Checkbutton(imaging_frame, text="Completed", variable=imaging_var)
    imaging_chk.pack(anchor="w")
    imaging_notes = tk.Text(imaging_frame, height=3)
    imaging_notes.insert("1.0", data.get("ImagingFindings", ""))
    imaging_notes.pack(fill="x")

    # Upper GI
    ugi_frame = create_section("Upper GI")
    ugi_var = tk.IntVar(value=data.get("UpperGI", 0))
    ugi_chk = tk.Checkbutton(ugi_frame, text="Completed", variable=ugi_var)
    ugi_chk.pack(anchor="w")
    ugi_notes = tk.Text(ugi_frame, height=3)
    ugi_notes.insert("1.0", data.get("UpperGIFindings", ""))
    ugi_notes.pack(fill="x")

    other_notes_label = tk.Label(window, text="Other Notes:")
    other_notes_label.pack(anchor="w")
    other_notes = tk.Text(window, height=4)
    other_notes.insert("1.0", data.get("DiagnosticNotes", ""))
    other_notes.pack(fill="x")

    if view_only:
        def expand_if_checked(name, var):
            frame, toggle_btn = section_frames[name]
            if var.get():
                frame.pack(fill="x")
                toggle_btn.config(text=f"▼ {name}")

        expand_if_checked("Endoscopy", endoscopy_var)
        expand_if_checked("Bravo / pH Impedance", bravo_var)
        expand_if_checked("Bravo / pH Impedance", ph_var)
        expand_if_checked("EndoFLIP", flip_var)
        expand_if_checked("Manometry", mano_var)
        expand_if_checked("Gastric Emptying", empty_var)
        expand_if_checked("Imaging", imaging_var)
        expand_if_checked("Upper GI", ugi_var)

        widgets_to_disable = [
            entry_date, surgeon_combo, endoscopy_chk, esophagitis_combo, hernia_combo, endo_notes,
            bravo_chk, ph_chk, demeester_entry, ph_notes,
            flip_chk, flip_notes,
            mano_chk, mano_notes,
            empty_chk, retained_entry, empty_notes,
            imaging_chk, imaging_notes,
            ugi_chk, ugi_notes,
            other_notes
        ]
        for widget in widgets_to_disable:
            disable_widget(widget)

    def save():
        try:
            date = entry_date.get_date().strftime("%Y-%m-%d")
        except Exception:
            messagebox.showerror("Error", "Test date is required.")
            return

        values = (
            patient_id,
            date,
            surgeon_var.get(),
            endoscopy_var.get(), esophagitis_var.get(), hernia_var.get(), endo_notes.get("1.0", tk.END).strip(),
            bravo_var.get(), ph_var.get(), demeester_var.get(), ph_notes.get("1.0", tk.END).strip(),
            flip_var.get(), flip_notes.get("1.0", tk.END).strip(),
            mano_var.get(), mano_notes.get("1.0", tk.END).strip(),
            empty_var.get(), retained_var.get(), empty_notes.get("1.0", tk.END).strip(),
            imaging_var.get(), imaging_notes.get("1.0", tk.END).strip(),
            ugi_var.get(), ugi_notes.get("1.0", tk.END).strip(),
            other_notes.get("1.0", tk.END).strip(),
        )

        try:
            cursor.execute("""
                INSERT INTO tblDiagnostics (
                    PatientID, TestDate, Surgeon,
                    Endoscopy, EsophagitisGrade, HiatalHerniaSize, EndoscopyFindings,
                    Bravo, pHImpedance, DeMeesterScore, pHFindings,
                    EndoFLIP, EndoFLIPFindings,
                    Manometry, ManometryFindings,
                    GastricEmptying, PercentRetained4h, GastricEmptyingFindings,
                    Imaging, ImagingFindings,
                    UpperGI, UpperGIFindings,
                    DiagnosticNotes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)

            conn.commit()
            messagebox.showinfo("Saved", "Diagnostic test saved successfully.")
            window.destroy()
            if refresh_callback:
                refresh_callback()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    if not view_only:
        tk.Button(window, text="Save", command=save).pack(pady=10)

    window.protocol("WM_DELETE_WINDOW", lambda: (conn.close(), window.destroy()))
