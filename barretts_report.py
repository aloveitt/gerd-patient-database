import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os
import tempfile
import webbrowser

DB_PATH = "gerd_center.db"

class BarrettsReport(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.refresh_data()
        tk.Label(self, text="🔍 Report shows the most recent pathology with Barretts=Yes if available, else the latest pathology overall.", bg="white", fg="gray", font=("Arial", 9)).pack(padx=10, anchor="w")

    def create_widgets(self):
        top_frame = tk.Frame(self, bg="white")
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="Due in next (days):", bg="white").pack(side=tk.LEFT)
        self.days_entry = tk.Entry(top_frame, width=5)
        self.days_entry.insert(0, "90")
        self.days_entry.pack(side=tk.LEFT, padx=5)

        self.include_past_due = tk.IntVar(value=1)
        tk.Checkbutton(top_frame, text="Include past due", variable=self.include_past_due, bg="white").pack(side=tk.LEFT)

        self.include_undecided = tk.IntVar(value=1)
        tk.Checkbutton(top_frame, text="Include undecided", variable=self.include_undecided, bg="white").pack(side=tk.LEFT)

        
        tk.Button(top_frame, text="Run Report", command=self.refresh_data).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, text="Print Preview", command=self.preview_pdf).pack(side=tk.RIGHT, padx=5)
        tk.Button(top_frame, text="Export to CSV", command=self.export_csv).pack(side=tk.RIGHT, padx=5)

        # Table
        self.tree = ttk.Treeview(self, columns=("Name", "MRN", "DOB", "NextEGD", "Status", "PathDate"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def refresh_data(self):
        try:
            days = int(self.days_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of days.")
            return

        today = datetime.today().date()
        upcoming = today + timedelta(days=days)

        conn = sqlite3.connect(DB_PATH)
        query = """
-- Display the most recent pathology with Barretts=1 if available, else fallback to most recent overall
WITH LatestBarrettsPath AS (
    SELECT * FROM tblPathology
    WHERE Barretts = 1 AND PathologyDate IS NOT NULL AND PatientID IS NOT NULL AND PathologyDate = (
        SELECT MAX(PathologyDate) FROM tblPathology AS sub
        WHERE sub.PatientID = tblPathology.PatientID AND sub.Barretts = 1
    )
),
LatestAnyPath AS (
    SELECT * FROM tblPathology
    WHERE PathologyDate IS NOT NULL AND PatientID IS NOT NULL AND PathologyDate = (
        SELECT MAX(PathologyDate) FROM tblPathology AS sub
        WHERE sub.PatientID = tblPathology.PatientID
    )
),
FinalPath AS (
    SELECT * FROM LatestBarrettsPath
    UNION
    SELECT * FROM LatestAnyPath
    WHERE PatientID NOT IN (SELECT PatientID FROM LatestBarrettsPath)
)
SELECT p.LastName || ', ' || p.FirstName AS Name,
       p.MRN, p.DOB,
       s.NextBarrettsEGD, s.Undecided,
       f.PathologyDate AS PathDate,
       f.Barretts, f.DysplasiaGrade, f.Notes
FROM tblPatients p
LEFT JOIN tblSurveillance s ON p.PatientID = s.PatientID
LEFT JOIN FinalPath f ON p.PatientID = f.PatientID
"""
        df = pd.read_sql_query(query, conn)
        conn.close()

        df["Status"] = df.apply(lambda row: self.determine_status(row["NextBarrettsEGD"], row["Undecided"]), axis=1)
        df = df[df["Status"] != "Excluded"]
        df["SortKey"] = df["Status"].apply(lambda s: 0 if s == "Undecided" else 1)
        df.sort_values(by=["SortKey", "NextBarrettsEGD", "Name"], inplace=True, na_position="last")

        self.df_filtered = df
        self.update_table(df)

    def determine_status(self, next_egd, undecided):
        today = datetime.today().date()
        try:
            if next_egd:
                egd_date = datetime.strptime(next_egd, "%Y-%m-%d").date()
                if egd_date < today:
                    return "Past due" if self.include_past_due.get() else "Excluded"
                elif egd_date <= today + timedelta(days=int(self.days_entry.get())) and egd_date >= today:
                    return "Due soon"
            if undecided:
                return "Undecided" if self.include_undecided.get() else "Excluded"
        except:
            pass
        return "Excluded"

    def update_table(self, df):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for _, row in df.iterrows():
            values = (
                row["Name"], row["MRN"], row["DOB"],
                row["NextBarrettsEGD"] or "Undecided",
                row["Status"],
                row["PathDate"] if str(row["Barretts"]).strip() == "1" else "Unknown"
            )
            item_id = self.tree.insert("", "end", values=values)
            if row["Status"] == "Past due":
                self.tree.item(item_id, tags=("past_due",))
        self.tree.tag_configure("past_due", background="#ffcccc")

    def export_csv(self):
        if self.df_filtered.empty:
            messagebox.showinfo("No Data", "No data to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.df_filtered[["Name", "MRN", "DOB", "NextBarrettsEGD", "Status", "PathDate"]].to_csv(file_path, index=False)

    def preview_pdf(self):
        if self.df_filtered.empty:
            messagebox.showinfo("No Data", "No data to print.")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            file_path = tmp_file.name

        doc = SimpleDocTemplate(file_path, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        elements = []

        data = [["Name", "MRN", "DOB", "Next EGD", "Status", "Path Date"]]
        for _, row in self.df_filtered.iterrows():
            data.append([
                row["Name"], row["MRN"], row["DOB"], row["NextBarrettsEGD"] or "Undecided",
                row["Status"], row["PathDate"] or "",
                "Yes" if str(row["Barretts"]).strip() == "1" else "No",
                row["DysplasiaGrade"] or "", row["Notes"] or ""
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        elements.append(table)
        doc.build(elements)

        try:
            webbrowser.open_new(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open PDF:\n{e}")