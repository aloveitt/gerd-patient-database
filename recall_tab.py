# recall_tab.py - BULLETPROOF WITH CLINICAL INTELLIGENCE

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, date, timedelta
import re

def get_recall_priority(reason, patient_id=None):
    """
    Determine recall priority based on reason and patient history
    Returns (priority_level, priority_explanation)
    1 = Critical, 2 = High, 3 = Medium, 4 = Low
    """
    if not reason:
        return 4, "Standard follow-up"
    
    reason_lower = reason.lower()
    
    # Check for Barrett's history if patient_id provided
    has_high_grade = False
    has_barrett = False
    
    if patient_id:
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DysplasiaGrade FROM tblPathology 
                WHERE PatientID = ? AND Barretts = 1 
                ORDER BY PathologyDate DESC LIMIT 1
            """, (patient_id,))
            result = cursor.fetchone()
            if result:
                has_barrett = True
                grade = result[0] or ""
                has_high_grade = "high grade" in grade.lower()
            conn.close()
        except:
            pass
    
    # Priority logic
    if "endoscopy" in reason_lower or "egd" in reason_lower:
        if has_high_grade:
            return 1, "Critical - High-grade dysplasia surveillance"
        elif has_barrett:
            return 2, "High - Barrett's surveillance"
        else:
            return 3, "Medium - Endoscopy follow-up"
    
    if "surveillance" in reason_lower:
        if has_high_grade:
            return 1, "Critical - High-grade dysplasia surveillance"
        elif has_barrett:
            return 2, "High - Barrett's surveillance"
        else:
            return 3, "Medium - Surveillance follow-up"
    
    if "office visit" in reason_lower or "clinic" in reason_lower:
        return 3, "Medium - Office visit"
    
    return 4, "Standard follow-up"

def suggest_recall_date(reason):
    """Suggest appropriate recall date based on reason"""
    if not reason:
        return datetime.today() + timedelta(days=30)
    
    reason_lower = reason.lower()
    today = datetime.today()
    
    if "endoscopy" in reason_lower or "surveillance" in reason_lower:
        # Surveillance endoscopy - typically 3-12 months out
        return today + timedelta(days=180)  # 6 months default
    elif "office visit" in reason_lower:
        # Office visit - typically 1-3 months
        return today + timedelta(days=60)   # 2 months default
    else:
        # Other - 1 month default
        return today + timedelta(days=30)

def is_good_recall_date(date_obj):
    """Check if recall date makes sense"""
    if not date_obj:
        return False
    
    today = date.today()
    min_date = today  # Can't schedule recalls in the past
    max_date = today + timedelta(days=365 * 5)  # Not more than 5 years out
    
    return min_date <= date_obj <= max_date

def get_overdue_severity(recall_date, reason):
    """Determine how overdue a recall is and its clinical significance"""
    if not recall_date:
        return 0, "No date"
    
    try:
        recall_dt = datetime.strptime(recall_date, "%Y-%m-%d").date()
        today = date.today()
        days_overdue = (today - recall_dt).days
        
        if days_overdue <= 0:
            return 0, "Not overdue"
        
        reason_lower = reason.lower() if reason else ""
        
        # Different thresholds based on recall type
        if "endoscopy" in reason_lower or "surveillance" in reason_lower:
            if days_overdue <= 30:
                return 1, f"{days_overdue} days overdue - schedule soon"
            elif days_overdue <= 90:
                return 2, f"{days_overdue} days overdue - needs attention"
            else:
                return 3, f"{days_overdue} days overdue - URGENT"
        else:
            if days_overdue <= 14:
                return 1, f"{days_overdue} days overdue - schedule soon"
            elif days_overdue <= 60:
                return 2, f"{days_overdue} days overdue - needs attention"
            else:
                return 3, f"{days_overdue} days overdue - URGENT"
    except:
        return 0, "Invalid date"

def validate_recall_data(reason, recall_date, notes):
    """Validate recall data comprehensively"""
    errors = []
    warnings = []
    
    # Check reason
    if not reason or reason.strip() == "":
        errors.append("Please select a recall reason")
    
    # Check date
    try:
        if not is_good_recall_date(recall_date):
            errors.append("Recall date must be today or later (not more than 5 years)")
    except:
        errors.append("Please select a valid recall date")
    
    # Check notes for important recalls
    if reason and "endoscopy" in reason.lower() and not notes.strip():
        warnings.append("Endoscopy recall without notes - consider adding clinical indication")
    
    # Check if date is reasonable for reason
    if reason and recall_date:
        try:
            days_out = (recall_date - date.today()).days
            reason_lower = reason.lower()
            
            if "endoscopy" in reason_lower and days_out < 30:
                warnings.append("Endoscopy recall scheduled very soon - verify this is appropriate")
            elif "office visit" in reason_lower and days_out > 180:
                warnings.append("Office visit recall scheduled far in future - verify this is appropriate")
        except:
            pass
    
    return errors, warnings

def show_nice_error(title, message):
    """Show a nice error message"""
    messagebox.showerror(title, message)

def show_nice_success(message):
    """Show a nice success message"""
    messagebox.showinfo("Success!", message)

def show_nice_warning(title, message):
    """Show a warning message"""
    return messagebox.askyesno(title, f"{message}\n\nDo you want to continue anyway?")

def show_nice_info(title, message):
    """Show an info message"""
    messagebox.showinfo(title, message)

def safe_database_operation(operation_name, operation_function):
    """Safely do database operations with nice error handling"""
    try:
        return operation_function()
    except sqlite3.IntegrityError as e:
        show_nice_error("Data Problem", f"There's a problem with the data: {str(e)}")
        return False
    except sqlite3.OperationalError as e:
        show_nice_error("Database Problem", f"The database had a problem: {str(e)}")
        return False
    except Exception as e:
        show_nice_error("Unexpected Problem", f"Something unexpected happened: {str(e)}")
        return False

def build(tab_frame, patient_id, tabs=None):
    """Build recall tab with clinical intelligence"""
    
    # Clear previous widgets to avoid duplication
    for widget in tab_frame.winfo_children():
        widget.destroy()

    def load_recalls():
        """Load recalls with priority and status analysis"""
        for widget in list_frame.winfo_children():
            widget.destroy()

        def get_recall_data():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT RecallID, RecallDate, RecallReason, Notes, Completed
                FROM tblRecall
                WHERE PatientID = ?
                ORDER BY 
                    Completed ASC,
                    CASE 
                        WHEN RecallDate IS NULL OR RecallDate = '' THEN 1
                        ELSE 0
                    END,
                    RecallDate ASC
            """, (patient_id,))
            results = cursor.fetchall()
            conn.close()
            return results

        rows = safe_database_operation("Load recalls", get_recall_data) or []

        # Create header
        header_frame = tk.Frame(list_frame, bg="lightgray", relief="raised", bd=1)
        header_frame.pack(fill="x", pady=(0, 2))
        
        tk.Label(header_frame, text="Priority", width=8, font=("Arial", 9, "bold"), bg="lightgray").pack(side="left", padx=2)
        tk.Label(header_frame, text="Date", width=12, font=("Arial", 9, "bold"), bg="lightgray").pack(side="left", padx=2)
        tk.Label(header_frame, text="Reason", width=15, font=("Arial", 9, "bold"), bg="lightgray").pack(side="left", padx=2)
        tk.Label(header_frame, text="Status", width=20, font=("Arial", 9, "bold"), bg="lightgray").pack(side="left", padx=2)
        tk.Label(header_frame, text="Notes", width=25, font=("Arial", 9, "bold"), bg="lightgray").pack(side="left", padx=2)
        tk.Label(header_frame, text="Actions", width=15, font=("Arial", 9, "bold"), bg="lightgray").pack(side="left", padx=2)

        for row in rows:
            add_recall_row(*row)

    def add_recall_row(recall_id, date, reason, notes, completed):
        """Add a recall row with priority and status indicators"""
        row = tk.Frame(list_frame, bd=1, relief="solid", padx=2, pady=2)
        row.pack(fill="x", pady=1)

        # Get priority and overdue status
        priority_level, priority_text = get_recall_priority(reason, patient_id)
        overdue_level, overdue_text = get_overdue_severity(date, reason)

        # Determine colors
        if completed:
            color = "gray"
            bg_color = "#f0f0f0"
        elif overdue_level >= 3:
            color = "white"
            bg_color = "red"  # Urgent overdue
        elif overdue_level >= 2:
            color = "black"
            bg_color = "orange"  # Needs attention
        elif overdue_level >= 1:
            color = "black"
            bg_color = "yellow"  # Schedule soon
        elif priority_level <= 2:
            color = "black"
            bg_color = "lightblue"  # High priority
        else:
            color = "black"
            bg_color = "white"  # Normal

        row.config(bg=bg_color)

        # Priority indicator
        priority_text_short = {1: "CRIT", 2: "HIGH", 3: "MED", 4: "LOW"}[priority_level]
        lbl_priority = tk.Label(row, text=priority_text_short, width=8, anchor="w", 
                               fg=color, bg=bg_color, font=("Arial", 8, "bold"))
        lbl_priority.pack(side="left", padx=2)

        # Date
        lbl_date = tk.Label(row, text=f"{date}", width=12, anchor="w", 
                           fg=color, bg=bg_color, font=("Arial", 9))
        lbl_date.pack(side="left", padx=2)

        # Reason
        lbl_reason = tk.Label(row, text=reason, width=15, anchor="w", 
                             fg=color, bg=bg_color, font=("Arial", 9))
        lbl_reason.pack(side="left", padx=2)

        # Status
        if completed:
            status_text = "✓ Completed"
        else:
            status_text = overdue_text
        
        lbl_status = tk.Label(row, text=status_text, width=20, anchor="w", 
                             fg=color, bg=bg_color, font=("Arial", 8))
        lbl_status.pack(side="left", padx=2)

        # Notes (truncated)
        notes_short = (notes[:35] + "...") if len(notes) > 35 else notes
        lbl_notes = tk.Label(row, text=notes_short, width=25, anchor="w", 
                            fg=color, bg=bg_color, font=("Arial", 8))
        lbl_notes.pack(side="left", padx=2)

        # Actions
        action_frame = tk.Frame(row, bg=bg_color)
        action_frame.pack(side="left", padx=2)

        # Complete/Uncomplete toggle
        var = tk.IntVar(value=completed)
        cb = tk.Checkbutton(action_frame, variable=var, bg=bg_color,
                           command=lambda: toggle_complete(recall_id, var, row))
        cb.pack(side="left")

        # Delete button
        tk.Button(action_frame, text="Del", command=lambda: delete_recall(recall_id), 
                 font=("Arial", 7), bg=bg_color).pack(side="left", padx=2)

        # Click to see full details
        def show_details():
            detail_msg = f"Recall Details:\n\n"
            detail_msg += f"Date: {date}\n"
            detail_msg += f"Reason: {reason}\n"
            detail_msg += f"Priority: {priority_text}\n"
            detail_msg += f"Status: {status_text}\n"
            detail_msg += f"Notes: {notes}\n"
            show_nice_info("Recall Details", detail_msg)

        for widget in [lbl_date, lbl_reason, lbl_notes]:
            widget.bind("<Double-Button-1>", lambda e: show_details())

    def toggle_complete(recall_id, var, row_widget):
        """Toggle recall completion status"""
        def do_toggle():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE tblRecall SET Completed = ? WHERE RecallID = ?", 
                          (var.get(), recall_id))
            conn.commit()
            conn.close()
            return True

        success = safe_database_operation("Update recall status", do_toggle)
        if success:
            load_recalls()  # Refresh display

    def delete_recall(recall_id):
        """Delete recall with confirmation"""
        if not messagebox.askyesno("Delete Recall", "Delete this recall entry?"):
            return
        
        def do_delete():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblRecall WHERE RecallID = ?", (recall_id,))
            conn.commit()
            conn.close()
            return True

        success = safe_database_operation("Delete recall", do_delete)
        if success:
            load_recalls()

    def on_reason_change(event=None):
        """Update suggested date when reason changes"""
        reason = cbo_reason.get()
        if reason:
            suggested_date = suggest_recall_date(reason)
            date_entry.set_date(suggested_date)

    def save_recall():
        """Save recall with comprehensive validation"""
        reason = cbo_reason.get().strip()
        notes = txt_notes.get("1.0", tk.END).strip()
        
        try:
            recall_date = date_entry.get_date()
        except Exception:
            show_nice_error("Invalid Date", "Please select a valid recall date.")
            return

        # Validate data
        errors, warnings = validate_recall_data(reason, recall_date, notes)

        if errors:
            error_message = "Please fix these problems:\n\n"
            for error in errors:
                error_message += f"• {error}\n"
            show_nice_error("Please Fix These Problems", error_message)
            return

        if warnings:
            warning_message = "Please review these items:\n\n"
            for warning in warnings:
                warning_message += f"• {warning}\n"
            if not show_nice_warning("Please Review", warning_message):
                return

        def do_save():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tblRecall (PatientID, RecallDate, RecallReason, Notes, Completed)
                VALUES (?, ?, ?, ?, 0)
            """, (patient_id, recall_date.strftime("%Y-%m-%d"), reason, notes))
            conn.commit()
            conn.close()
            return True

        success = safe_database_operation("Save recall", do_save)
        if success:
            # Get priority for success message
            priority_level, priority_text = get_recall_priority(reason, patient_id)
            
            success_msg = "Recall saved successfully!\n\n"
            success_msg += f"Priority: {priority_text}\n"
            success_msg += f"Date: {recall_date.strftime('%Y-%m-%d')}"
            
            show_nice_success(success_msg)
            
            # Clear form
            cbo_reason.set("")
            txt_notes.delete("1.0", tk.END)
            date_entry.set_date(datetime.today())
            
            # Refresh list
            load_recalls()

    # Build interface
    # Title and summary
    tk.Label(tab_frame, text="📞 Patient Recalls & Follow-up", 
             font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

    # Quick stats
    def get_recall_stats():
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN Completed = 0 THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN Completed = 0 AND RecallDate < date('now') THEN 1 ELSE 0 END) as overdue
                FROM tblRecall WHERE PatientID = ?
            """, (patient_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except:
            return (0, 0, 0)

    total, pending, overdue = get_recall_stats()
    stats_text = f"Total: {total} | Pending: {pending} | Overdue: {overdue}"
    tk.Label(tab_frame, text=stats_text, font=("Arial", 9), fg="gray").pack(anchor="w", padx=10)

    # Entry form
    entry_frame = tk.LabelFrame(tab_frame, text="Add New Recall", 
                               font=("Arial", 10, "bold"), padx=10, pady=10)
    entry_frame.pack(fill="x", padx=10, pady=10)

    # Recall date
    tk.Label(entry_frame, text="Recall Date:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=2)
    date_entry = DateEntry(entry_frame, width=12, date_pattern="yyyy-mm-dd")
    date_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")

    # Reason with smart suggestions
    tk.Label(entry_frame, text="Reason:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=2)
    cbo_reason = ttk.Combobox(entry_frame, 
                             values=["Office Visit", "Endoscopy", "Barrett's Surveillance", 
                                   "Surveillance Form", "Post-op Follow-up", "Lab Review", "Other"], 
                             width=25)
    cbo_reason.grid(row=1, column=1, padx=5, pady=2, sticky="w")
    cbo_reason.bind("<<ComboboxSelected>>", on_reason_change)

    # Notes
    tk.Label(entry_frame, text="Notes:", font=("Arial", 10)).grid(row=2, column=0, sticky="nw", pady=2)
    txt_notes = tk.Text(entry_frame, width=50, height=3, wrap="word")
    txt_notes.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

    # Save button
    tk.Button(entry_frame, text="Save Recall", command=save_recall, 
             font=("Arial", 10, "bold"), bg="lightgreen", padx=15, pady=5).grid(row=3, column=0, columnspan=2, pady=10)

    # Make entry frame expandable
    entry_frame.columnconfigure(1, weight=1)

    # Priority legend
    legend_frame = tk.Frame(tab_frame, padx=10, pady=5)
    legend_frame.pack(fill="x")
    
    tk.Label(legend_frame, text="Priority Colors:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
    
    legend_items = [
        ("URGENT", "red", "white"),
        ("Needs Attention", "orange", "black"),
        ("Schedule Soon", "yellow", "black"),
        ("High Priority", "lightblue", "black"),
        ("Completed", "lightgray", "gray")
    ]
    
    for text, bg, fg in legend_items:
        lbl = tk.Label(legend_frame, text=text, bg=bg, fg=fg, padx=8, pady=2, 
                      relief="solid", bd=1, font=("Arial", 8))
        lbl.pack(side=tk.LEFT, padx=5)

    # Recalls list
    tk.Label(tab_frame, text="📋 Current Recalls", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(15, 5))
    
    list_frame = tk.Frame(tab_frame)
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)

    load_recalls()