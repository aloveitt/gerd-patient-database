import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import recall_report  # NEW
import barretts_report  # NEW
import print_summary

class GERDApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minnesota Reflux & Heartburn Center")
        self.state('zoomed')
        self.patient_id = None
        self.results_list = []

        self.left_frame = tk.Frame(self, width=300, padx=10, pady=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.left_frame, text="🔍 Search Patients", font=("Arial", 12, "bold")).pack(anchor="w")
        self.search_entry = tk.Entry(self.left_frame, width=30)
        self.search_entry.pack(pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_patients())

        self.results_listbox = tk.Listbox(self.left_frame, width=40)
        self.results_listbox.pack(pady=5, fill=tk.Y, expand=True)
        self.results_listbox.bind("<Double-Button-1>", lambda e: self.load_selected_patient())

        tk.Button(self.left_frame, text="Add New Patient", command=self.add_patient_popup).pack(pady=(10, 5))
        tk.Button(self.left_frame, text="Delete Selected Patient", command=self.delete_patient).pack(pady=(0, 10))

        # 📊 Reports section
        tk.Label(self.left_frame, text="📊 Reports", font=("Arial", 12, "bold")).pack(anchor="w", pady=(15, 5))
        tk.Button(self.left_frame, text="Generate Recall Report", command=self.load_recall_report).pack()
        tk.Button(self.left_frame, text="Generate Barrett's Report", command=self.load_barretts_report).pack()

        self.right_frame = tk.Frame(self, padx=10, pady=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.search_patients()

    def search_patients(self):
        search_term = self.search_entry.get().strip()
        self.results_listbox.delete(0, tk.END)

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT PatientID, FirstName, LastName, MRN
            FROM tblPatients
            WHERE FirstName LIKE ? OR LastName LIKE ? OR MRN LIKE ?
            ORDER BY LastName
        """, (f"{search_term}%", f"{search_term}%", f"{search_term}%"))
        self.results_list = cursor.fetchall()
        conn.close()

        for row in self.results_list:
            pid, first, last, mrn = row
            display = f"{last}, {first} — MRN: {mrn}"
            self.results_listbox.insert(tk.END, display)

    def load_selected_patient(self):
        selected = self.results_listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        self.patient_id = self.results_list[idx][0]

        for widget in self.right_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("SELECT FirstName, LastName, MRN, DOB FROM tblPatients WHERE PatientID = ?", (self.patient_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            first, last, mrn, dob = row
            header = tk.Frame(self.right_frame, pady=5)
            header.pack(fill=tk.X)
            tk.Label(header, text=f"🧍 {last}, {first}", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=10)
            tk.Label(header, text=f"MRN: {mrn}", font=("Arial", 12)).pack(side=tk.LEFT, padx=20)
            tk.Label(header, text=f"DOB: {dob}", font=("Arial", 12)).pack(side=tk.LEFT, padx=20)
            btn_print = tk.Button(header, text="🖨️ Print Summary", command=lambda: print_summary.generate_pdf(self.patient_id))
            btn_print.pack(side=tk.RIGHT, padx=10)

        from demographics_tab import build as build_demographics
        from diagnostics_tab import build as build_diagnostics
        from surgical_tab import build as build_surgical
        from pathology_tab import build as build_pathology
        from surveillance_tab import build as build_surveillance
        from recall_tab import build as build_recall

        self.tabs = ttk.Notebook(self.right_frame)
        self.tabs.pack(expand=1, fill="both")

        for label, builder in [
            ("Demographics", build_demographics),
            ("Diagnostics", build_diagnostics),
            ("Surgical History", build_surgical),
            ("Pathology", build_pathology),
            ("Surveillance", build_surveillance),
            ("Recalls", build_recall)
        ]:
            frame = ttk.Frame(self.tabs)
            if label == "Demographics":
                builder(frame, self.patient_id, self.tabs, on_demographics_updated=self.search_patients)
            else:
                builder(frame, self.patient_id, self.tabs)
            self.tabs.add(frame, text=label)

    def delete_patient(self):
        selected = self.results_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a patient to delete.")
            return

        idx = selected[0]
        patient_id = self.results_list[idx][0]

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            "⚠️ Are you sure you want to permanently delete this patient and ALL related records?\n\n"
            "This includes diagnostics, surgeries, pathology, recalls, and surveillance.\n\n"
            "This action cannot be undone."
        )
        if not confirm:
            return

        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()

            cursor.execute("DELETE FROM tblDiagnostics WHERE PatientID = ?", (patient_id,))
            cursor.execute("DELETE FROM tblPathology WHERE PatientID = ?", (patient_id,))
            cursor.execute("DELETE FROM tblSurgicalHistory WHERE PatientID = ?", (patient_id,))
            cursor.execute("DELETE FROM tblRecall WHERE PatientID = ?", (patient_id,))
            cursor.execute("DELETE FROM tblSurveillance WHERE PatientID = ?", (patient_id,))
            cursor.execute("DELETE FROM tblPatients WHERE PatientID = ?", (patient_id,))

            conn.commit()
            conn.close()

            if self.patient_id == patient_id:
                for widget in self.right_frame.winfo_children():
                    widget.destroy()
                self.patient_id = None

            self.search_patients()
            messagebox.showinfo("Deleted", "Patient and all associated records have been deleted.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete patient.\n\n{e}")

    def add_patient_popup(self):
        from add_patient import build

        def handle_new_patient(patient_id):
            self.search_patients()
            for i, row in enumerate(self.results_list):
                if row[0] == patient_id:
                    self.results_listbox.selection_clear(0, tk.END)
                    self.results_listbox.selection_set(i)
                    self.results_listbox.see(i)
                    self.load_selected_patient()
                    break

        build(on_save_callback=handle_new_patient)

    def load_recall_report(self):
        self.patient_id = None
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        recall_report.build_report_view(self.right_frame)



    def load_barretts_report(self):
        self.patient_id = None
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        barretts_report.BarrettsReport(self.right_frame)

if __name__ == "__main__":
    app = GERDApp()
    app.mainloop()