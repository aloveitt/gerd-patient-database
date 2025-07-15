# surveillance_tab.py

import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta
import diagnostics_tab
import pathology_tab
import recall_tab

def build(tab_frame, patient_id, tabs=None):
    selected_ids = []

    def load_data():
        lst.delete(0, tk.END)
        selected_ids.clear()
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SurveillanceID, NextBarrettsEGD, Undecided, LastModified
            FROM tblSurveillance
            WHERE PatientID = ?
            ORDER BY LastModified DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()

        for idx, row in enumerate(rows):
            surveil_id, next_date, undecided, modified = row
            if undecided:
                summary = f"Plan Undecided (Last Updated: {modified})"
                color = "gray"
            else:
                summary = f"Next EGD Due: {next_date} (Last Updated: {modified})"
                try:
                    egd_date = datetime.strptime(next_date, "%Y-%m-%d").date()
                    today = datetime.today().date()
                    days_until = (egd_date - today).days
                    if days_until < 0:
                        color = "red"
                    elif days_until <= 365:
                        color = "orange"
                    else:
                        color = "green"
                except ValueError:
                    summary += " ⚠️ Invalid date"
                    color = "black"

            lst.insert(tk.END, summary)
            lst.itemconfig(idx, {'fg': color})
            selected_ids.append(surveil_id)

    def set_interval(years):
        today = datetime.today()
        future = today + timedelta(days=365 * years)
        entry_next.set_date(future)
        var_undecided.set(0)

    def toggle_undecided():
        if var_undecided.get():
            entry_next.set_date(datetime.today())

    def save_plan():
        if var_undecided.get():
            next_egd = ""
        else:
            try:
                next_egd = entry_next.get_date().strftime("%Y-%m-%d")
            except Exception:
                messagebox.showerror("Date Error", "Invalid date.")
                return

        last_modified = datetime.today().strftime("%Y-%m-%d")

        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tblSurveillance (PatientID, NextBarrettsEGD, Undecided, LastModified)
                VALUES (?, ?, ?, ?)
            """, (patient_id, next_egd, var_undecided.get(), last_modified))
            conn.commit()

            if not var_undecided.get():
                if messagebox.askyesno("Create Recall", "Would you like to create a recall for this surveillance EGD?"):
                    cursor.execute("""
                        INSERT INTO tblRecall (PatientID, RecallDate, RecallReason, Notes, Completed)
                        VALUES (?, ?, 'Endoscopy', 'Auto-created from Surveillance Tab', 0)
                    """, (patient_id, next_egd))
                    conn.commit()
                    if tabs:
                        try:
                            recall_tab.build(tabs.nametowidget(tabs.tabs()[5]), patient_id, tabs)
                        except:
                            pass

            conn.close()
            load_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_plan():
        selected = lst.curselection()
        if not selected:
            return
        surveil_id = selected_ids[selected[0]]

        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("SELECT NextBarrettsEGD FROM tblSurveillance WHERE SurveillanceID = ?", (surveil_id,))
        result = cursor.fetchone()
        date_to_delete = result[0] if result else None

        if not messagebox.askyesno("Delete", "Are you sure you want to delete this plan?"):
            conn.close()
            return

        try:
            cursor.execute("DELETE FROM tblSurveillance WHERE SurveillanceID = ?", (surveil_id,))
            conn.commit()

            if date_to_delete:
                cursor.execute("""
                    SELECT RecallID FROM tblRecall
                    WHERE PatientID = ? AND RecallDate = ? AND RecallReason = 'Endoscopy'
                """, (patient_id, date_to_delete))
                recall_row = cursor.fetchone()
                if recall_row:
                    if messagebox.askyesno("Delete Recall", "Also delete the linked recall for this surveillance EGD?"):
                        cursor.execute("DELETE FROM tblRecall WHERE RecallID = ?", (recall_row[0],))
                        conn.commit()

                        if tabs:
                            try:
                                recall_tab.build(tabs.nametowidget(tabs.tabs()[5]), patient_id, tabs)
                            except:
                                pass

            conn.close()
            load_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_last_barretts():
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT PathologyID, PathologyDate, DysplasiaGrade
            FROM tblPathology
            WHERE PatientID = ? AND Barretts = 1
            ORDER BY PathologyDate DESC
            LIMIT 1
        """, (patient_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def get_last_egd():
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DiagnosticID, TestDate
            FROM tblDiagnostics
            WHERE PatientID = ? AND Endoscopy = 1
            ORDER BY TestDate DESC
            LIMIT 1
        """, (patient_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    info = tk.Frame(tab_frame, padx=10, pady=10)
    info.pack(anchor="w")

    last_path = get_last_barretts()
    tk.Label(info, text="Last Barrett’s Pathology:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
    if last_path:
        pid, pdate, grade = last_path
        lbl = tk.Label(info, text=f"{pdate} — {grade or 'No Grade'}", fg="blue", cursor="hand2")
        lbl.grid(row=0, column=1, sticky="w", padx=10)
        if tabs:
            lbl.bind("<Button-1>", lambda e: (
                tabs.select(3),
                tab_frame.after(100, lambda: pathology_tab.build(tabs.nametowidget(tabs.tabs()[3]), patient_id, tabs, expand_id=pid))
            ))
    else:
        tk.Label(info, text="No Barrett’s pathology found", fg="gray").grid(row=0, column=1, sticky="w", padx=10)

    last_egd = get_last_egd()
    tk.Label(info, text="Last EGD:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
    if last_egd:
        did, ddate = last_egd
        try:
            d = datetime.strptime(ddate, "%Y-%m-%d").date()
            delta = (datetime.today().date() - d).days
            yrs, days = divmod(delta, 365)
            lbl2 = tk.Label(info, text=f"{ddate} ({yrs} yr, {days} days ago)", fg="blue", cursor="hand2")
            lbl2.grid(row=1, column=1, sticky="w", padx=10)
            if tabs:
                lbl2.bind("<Button-1>", lambda e: (
                    tabs.select(1),
                    tab_frame.after(100, lambda: diagnostics_tab.build(tabs.nametowidget(tabs.tabs()[1]), patient_id, tabs, expand_id=did))
                ))
        except:
            tk.Label(info, text=ddate, fg="blue").grid(row=1, column=1, sticky="w", padx=10)
    else:
        tk.Label(info, text="No EGD found", fg="gray").grid(row=1, column=1, sticky="w", padx=10)

    frm = tk.Frame(tab_frame, padx=10, pady=10)
    frm.pack(anchor="w")
    tk.Label(frm, text="Next EGD Due:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=2)
    entry_next = DateEntry(frm, width=12, date_pattern="yyyy-mm-dd")
    entry_next.grid(row=0, column=1, sticky="w", padx=5, pady=2)

    var_undecided = tk.IntVar()
    tk.Checkbutton(frm, text="Undecided", variable=var_undecided, command=toggle_undecided).grid(row=0, column=2, padx=10)

    btns = tk.Frame(frm)
    btns.grid(row=1, column=0, columnspan=3, pady=5)
    for years in [1, 2, 3, 5]:
        tk.Button(btns, text=f"+{years} yr", width=8, command=lambda y=years: set_interval(y)).pack(side=tk.LEFT, padx=3)

    tk.Button(frm, text="Save Surveillance Plan", command=save_plan).grid(row=2, column=0, columnspan=3, pady=10)

    legend = tk.Frame(tab_frame, padx=10)
    legend.pack(anchor="w")
    for label, color in [("Overdue", "red"), ("Due Soon (<1yr)", "orange"), ("Future (>1yr)", "green"), ("Undecided", "gray")]:
        tk.Label(legend, text=label, fg=color).pack(side=tk.LEFT, padx=10)

    lst = tk.Listbox(tab_frame, width=85)
    lst.pack(pady=5, padx=10, anchor="w")

    tk.Button(tab_frame, text="Delete Selected Plan", command=delete_plan).pack(pady=5, padx=10, anchor="w")

    load_data()
