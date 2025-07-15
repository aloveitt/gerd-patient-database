import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import csv
import patient_master

def build_report_view(parent_frame):
    for widget in parent_frame.winfo_children():
        widget.destroy()

    conn = sqlite3.connect("gerd_center.db")
    conn.row_factory = sqlite3.Row

    checked_img = tk.PhotoImage(width=16, height=16)
    unchecked_img = tk.PhotoImage(width=16, height=16)
    checked_img.put(("black",), to=(4, 4, 12, 12))
    unchecked_img.put(("white",), to=(0, 0, 16, 16))
    unchecked_img.put(("black",), to=(4, 4, 12, 12))

    # Store image references to prevent garbage collection
    parent_frame.checked_img = checked_img
    parent_frame.unchecked_img = unchecked_img

    filters = tk.Frame(parent_frame, padx=10, pady=10)
    filters.pack(fill="x")

    tk.Label(filters, text="Reason for Recall:").grid(row=0, column=0, sticky="w")
    reason_combo = ttk.Combobox(filters, values=["All", "Office Visit", "Endoscopy", "Surveillance Form", "Other"], state="readonly", width=20)
    reason_combo.set("All")
    reason_combo.grid(row=0, column=1, sticky="w")

    tk.Label(filters, text="Due in next (days):").grid(row=1, column=0, sticky="w", pady=(5,0))
    days_entry = tk.Entry(filters, width=8)
    days_entry.insert(0, "30")
    days_entry.grid(row=1, column=1, sticky="w", pady=(5,0))

    include_past = tk.IntVar(value=1)
    include_completed = tk.IntVar(value=0)
    barretts_only = tk.IntVar(value=0)

    tk.Checkbutton(filters, text="Include past due", variable=include_past).grid(row=2, column=0, columnspan=2, sticky="w")
    tk.Checkbutton(filters, text="Include completed", variable=include_completed).grid(row=3, column=0, columnspan=2, sticky="w")
    tk.Checkbutton(filters, text="With Barrett's only (ever)", variable=barretts_only).grid(row=4, column=0, columnspan=2, sticky="w")

    button_frame = tk.Frame(filters)
    button_frame.grid(row=0, column=2, rowspan=5, padx=20)
    tk.Button(button_frame, text="Run Report", command=lambda: run_report()).pack(side="top", fill="x", pady=2)
    tk.Button(button_frame, text="Export to CSV", command=lambda: export_csv()).pack(side="top", fill="x", pady=2)
    tk.Button(button_frame, text="Print", command=lambda: print_report()).pack(side="top", fill="x", pady=2)
    tk.Button(button_frame, text="Save Changes", command=lambda: save_changes()).pack(side="top", fill="x", pady=10)

    table_frame = tk.Frame(parent_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("Completed", "Name", "MRN", "Recall Date", "Reason", "Notes", "Latest Pathology")
    col_widths = [30, 150, 80, 100, 130, 200, 250]

    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
    for i, col in enumerate(columns):
        tree.heading(col, text=col)
        tree.column(col, width=col_widths[i], anchor="w")
    tree.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    result_data = []

    def run_report():
        for row in tree.get_children():
            tree.delete(row)
        result_data.clear()

        try:
            days = int(days_entry.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number of days.")
            return

        deadline = datetime.today().date() + timedelta(days=days)
        reason_filter = reason_combo.get()
        include_completed_flag = include_completed.get()
        include_past_flag = include_past.get()

        query = '''
            SELECT R.RecallID, R.RecallDate, R.RecallReason, R.Notes, R.Completed,
                   P.PatientID, P.FirstName, P.LastName, P.MRN
            FROM tblRecall R
            JOIN tblPatients P ON R.PatientID = P.PatientID
            WHERE 1=1
        '''
        params = []

        if reason_filter != "All":
            query += " AND R.RecallReason = ?"
            params.append(reason_filter)

        if not include_completed_flag:
            query += " AND R.Completed = 0"

        
        query += " AND R.RecallDate <= ?"
        params.append(deadline.strftime("%Y-%m-%d"))
        if not include_past_flag:
            query += " AND R.RecallDate >= DATE('now')"
    

        query += " ORDER BY R.RecallDate ASC"

        cur = conn.cursor()
        cur.execute(query, params)
        recalls = cur.fetchall()

        today = datetime.today().date()

        for row in recalls:
            recall_id, recall_date, reason, notes, completed, pid, first, last, mrn = row
            name = f"{last}, {first}"

            cur.execute("SELECT * FROM tblPathology WHERE PatientID = ? ORDER BY PathologyDate DESC LIMIT 1", (pid,))
            path_row = cur.fetchone()
            if path_row:
                summary = f"{path_row['PathologyDate']}: "
                parts = []
                if path_row["Biopsy"]: parts.append("Biopsy")
                if path_row["EsoPredict"]: parts.append(f"EsoPredict ({path_row['EsoPredictRisk']})")
                if path_row["TissueCypher"]: parts.append(f"TissueCypher ({path_row['TissueCypherRisk']})")
                if path_row["Barretts"]: parts.append("Barrett's")
                if path_row["DysplasiaGrade"]: parts.append(path_row["DysplasiaGrade"])
                if path_row["Hpylori"]: parts.append("H. pylori")
                if path_row["AtrophicGastritis"]: parts.append("Atrophic Gastritis")
                if path_row["EOE"]: parts.append(f"EoE ({path_row['EosinophilCount']} eos)")
                pathology_summary = summary + ", ".join(parts)
            else:
                pathology_summary = "None"

            if barretts_only.get():
                cur.execute("SELECT 1 FROM tblPathology WHERE PatientID = ? AND Barretts = 1 LIMIT 1", (pid,))
                if not cur.fetchone():
                    continue

            result_data.append((recall_id, completed, pid))
            values = ("", name, mrn, recall_date, reason, notes, pathology_summary)
            tag = "past_due" if datetime.strptime(recall_date, "%Y-%m-%d").date() < today and not completed else ""
            tree.insert("", "end", values=(('☑' if completed else '☐'),) + values[1:], tags=(tag,))

        tree.tag_configure("past_due", foreground="red")

    def on_click(event):
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            if col == "#1":  # First column
                idx = tree.index(row_id)
                recall_id, completed, pid = result_data[idx]
                result_data[idx] = (recall_id, not completed, pid)
                values = list(tree.item(row_id)["values"])
                values[0] = "☑" if values[0] == "☐" else "☐"
                tree.item(row_id, values=values)
                result_data[idx] = (recall_id, not completed, pid)

    def save_changes():
        cur = conn.cursor()
        for recall_id, completed, _ in result_data:
            cur.execute("UPDATE tblRecall SET Completed = ? WHERE RecallID = ?", (1 if completed else 0, recall_id))
        conn.commit()
        messagebox.showinfo("Saved", "Changes saved successfully.")

    def on_double_click(event=None):
        selected = tree.selection()
        if not selected:
            return
        idx = tree.index(selected[0])
        patient_id = result_data[idx][2]
        patient_master.open_patient_master(patient_id, window_size="1000x700")

    
    def export_csv():
        if not result_data:
            messagebox.showinfo("No Data", "No results to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in result_data:
                    completed = "Yes" if row[1] else "No"
                    writer.writerow([completed] + list(tree.item(tree.get_children()[result_data.index(row)])["values"][1:]))
            messagebox.showinfo("Exported", "Recall report exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
    

    
    
    def print_report():
        top = tk.Toplevel(parent_frame)
        top.title("Print Preview")

        text = tk.Text(top, wrap="none", font=("Courier New", 10), padx=10, pady=10)
        text.pack(fill="both", expand=True)

        header = "{:<10} {:<20} {:<10} {:<12} {:<18} {:<30} {:<40}\n".format(
            "Completed", "Name", "MRN", "Recall Date", "Reason", "Notes", "Latest Pathology"
        )
        text.insert(tk.END, header)
        text.insert(tk.END, "-" * 140 + "\n")

        for item in tree.get_children():
            values = tree.item(item)["values"]
            formatted = "{:<10} {:<20} {:<10} {:<12} {:<18} {:<30} {:<40}\n".format(
                str(values[0])[:10], str(values[1])[:20], str(values[2])[:10],
                str(values[3])[:12], str(values[4])[:18], str(values[5])[:30], str(values[6])[:40]
            )
            text.insert(tk.END, formatted)

        text.config(state="disabled")
    
        top = tk.Toplevel(parent_frame)
        top.title("Print Preview")
        text = tk.Text(top, wrap="none", font=("Courier New", 10))
        text.pack(fill="both", expand=True)
        header_line = "\t".join(columns) + "\n"
        text.insert(tk.END, header_line)
        for item in tree.get_children():
            values = tree.item(item)["values"]
            line = "\t".join(str(val) for val in values) + "\n"
            text.insert(tk.END, line)
        text.config(state="disabled")
    

    tree.bind("<Button-1>", on_click)
    tree.bind("<Double-Button-1>", on_double_click)