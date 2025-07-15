# recall_tab.py

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime

def build(tab_frame, patient_id, tabs=None):
    # Clear previous widgets to avoid duplication
    for widget in tab_frame.winfo_children():
        widget.destroy()

    def load_recalls():
        for widget in list_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT RecallID, RecallDate, RecallReason, Notes, Completed
            FROM tblRecall
            WHERE PatientID = ?
            ORDER BY RecallDate ASC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            add_recall_row(*row)

    def save_recall():
        try:
            date = date_entry.get_date().strftime("%Y-%m-%d")
        except Exception:
            messagebox.showerror("Invalid Date", "Please select a valid date.")
            return

        reason = cbo_reason.get()
        notes = txt_notes.get("1.0", tk.END).strip()

        if not reason:
            messagebox.showerror("Missing Info", "Please select a reason.")
            return

        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tblRecall (PatientID, RecallDate, RecallReason, Notes, Completed)
                VALUES (?, ?, ?, ?, 0)
            """, (patient_id, date, reason, notes))
            conn.commit()
            conn.close()
            date_entry.set_date(datetime.today())
            cbo_reason.set("")
            txt_notes.delete("1.0", tk.END)
            load_recalls()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def toggle_complete(recall_id, var, row_widgets):
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE tblRecall SET Completed = ? WHERE RecallID = ?", (var.get(), recall_id))
            conn.commit()
            conn.close()
            color = "gray" if var.get() else get_row_color(row_widgets['date'].cget("text"))
            for w in row_widgets.values():
                w.config(fg=color)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_recall(recall_id):
        if not messagebox.askyesno("Delete", "Delete this recall entry?"):
            return
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblRecall WHERE RecallID = ?", (recall_id,))
            conn.commit()
            conn.close()
            load_recalls()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_row_color(date_str):
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            delta = (d - datetime.today().date()).days
            if delta < 0:
                return "red"
            elif delta <= 365:
                return "orange"
            else:
                return "green"
        except:
            return "black"

    def add_recall_row(recall_id, date, reason, notes, completed):
        row = tk.Frame(list_frame, bd=1, relief="solid", padx=5, pady=5)
        row.pack(fill="x", pady=2)

        color = "gray" if completed else get_row_color(date)

        lbl_date = tk.Label(row, text=f"{date}", width=15, anchor="w", fg=color)
        lbl_reason = tk.Label(row, text=reason, width=20, anchor="w", fg=color)
        lbl_notes = tk.Label(row, text=notes, width=40, anchor="w", fg=color)
        lbl_done = tk.Label(row, text="Completed", anchor="w")

        lbl_date.grid(row=0, column=0, sticky="w")
        lbl_reason.grid(row=0, column=1, sticky="w")
        lbl_notes.grid(row=0, column=2, sticky="w")
        lbl_done.grid(row=0, column=3, padx=5)

        var = tk.IntVar(value=completed)
        cb = tk.Checkbutton(row, variable=var)
        cb.grid(row=0, column=4, padx=5)
        cb.config(command=lambda: toggle_complete(recall_id, var, {
            'date': lbl_date, 'reason': lbl_reason, 'notes': lbl_notes, 'done': lbl_done
        }))

        tk.Button(row, text="Delete", command=lambda: delete_recall(recall_id)).grid(row=0, column=5, padx=5)

    entry_frame = tk.Frame(tab_frame, padx=10, pady=10)
    entry_frame.pack(anchor="w")

    tk.Label(entry_frame, text="Recall Date:").grid(row=0, column=0, sticky="w")
    date_entry = DateEntry(entry_frame, width=12, date_pattern="yyyy-mm-dd")
    date_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

    tk.Label(entry_frame, text="Reason:").grid(row=1, column=0, sticky="w")
    cbo_reason = ttk.Combobox(entry_frame, values=["Office Visit", "Endoscopy", "Surveillance Form", "Other"], width=27)
    cbo_reason.grid(row=1, column=1, padx=5, pady=2, sticky="w")

    tk.Label(entry_frame, text="Notes:").grid(row=2, column=0, sticky="nw")
    txt_notes = tk.Text(entry_frame, width=50, height=3)
    txt_notes.grid(row=2, column=1, padx=5, pady=2, sticky="w")

    tk.Button(entry_frame, text="Save Recall", command=save_recall).grid(row=3, column=0, columnspan=2, pady=10, sticky="w")

    # Color Key Legend
    legend = tk.Frame(tab_frame, padx=10, pady=5)
    legend.pack(anchor="w")
    for label, color in [("Overdue", "red"), ("Due Soon (<1yr)", "orange"), ("Future (>1yr)", "green")]:
        tk.Label(legend, text=label, fg=color).pack(side=tk.LEFT, padx=10)

    list_frame = tk.Frame(tab_frame, padx=10)
    list_frame.pack(fill="both", expand=True, anchor="w")

    load_recalls()
