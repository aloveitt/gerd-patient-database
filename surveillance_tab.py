# surveillance_tab.py - Enhanced with refresh system and clinical intelligence

import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta
import diagnostics_tab
import pathology_tab
import recall_tab

def get_surveillance_recommendation(dysplasia_grade, patient_age=None, barrett_length=None):
    """
    Get surveillance recommendation based on ACG/AGA guidelines
    Returns (months, explanation)
    """
    if not dysplasia_grade:
        return 36, "No specific dysplasia grade - default 3-year interval"
    
    dysplasia_grade = dysplasia_grade.strip().lower()
    
    if dysplasia_grade in ["high grade", "high-grade"]:
        return 3, "High-grade dysplasia - requires 3-month intervals"
    elif dysplasia_grade in ["low grade", "low-grade"]:
        return 6, "Low-grade dysplasia - requires 6-month intervals"
    elif dysplasia_grade in ["indeterminate"]:
        return 6, "Indeterminate dysplasia - requires 6-month intervals until clarified"
    elif dysplasia_grade in ["no dysplasia", "ngim"]:
        # Length-based recommendations for no dysplasia
        if barrett_length and "cm" in barrett_length.lower():
            try:
                length_num = float(barrett_length.lower().replace("cm", "").replace(">", "").strip())
                if length_num >= 3:
                    return 36, "Barrett's ≥3cm without dysplasia - 3-year intervals"
                else:
                    return 60, "Barrett's <3cm without dysplasia - 5-year intervals"
            except:
                pass
        return 36, "Barrett's without dysplasia - 3-year intervals (verify length)"
    else:
        return 36, f"Unrecognized dysplasia grade '{dysplasia_grade}' - default 3-year interval"

def is_good_surveillance_date(date_obj):
    """Check if surveillance date makes sense"""
    if not date_obj:
        return False
    
    today = datetime.today().date()
    min_date = today  # Can't schedule surveillance in the past
    max_date = today + timedelta(days=365 * 10)  # Not more than 10 years out
    
    return min_date <= date_obj <= max_date

def check_barrett_history(patient_id):
    """Check if patient has Barrett's history"""
    try:
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM tblPathology 
            WHERE PatientID = ? AND Barretts = 1
        """, (patient_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except:
        return False

def get_latest_barrett_pathology(patient_id):
    """Get the most recent Barrett's pathology"""
    try:
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT PathologyDate, DysplasiaGrade, Notes
            FROM tblPathology
            WHERE PatientID = ? AND Barretts = 1
            ORDER BY PathologyDate DESC
            LIMIT 1
        """, (patient_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except:
        return None

def get_latest_egd_with_barrett_length(patient_id):
    """Get the most recent EGD with Barrett's length info"""
    try:
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TestDate, EndoscopyFindings
            FROM tblDiagnostics
            WHERE PatientID = ? AND Endoscopy = 1
            ORDER BY TestDate DESC
            LIMIT 3
        """, (patient_id,))
        results = cursor.fetchall()
        conn.close()
        
        # Look for Barrett's length in findings
        for test_date, findings in results:
            if findings and ("barrett" in findings.lower() or "cm" in findings.lower()):
                return test_date, findings
        
        return None, None
    except:
        return None, None

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
    """Build surveillance tab with enhanced refresh system"""
    
    # Clear previous widgets to avoid duplication
    for widget in tab_frame.winfo_children():
        widget.destroy()
    
    selected_ids = []

    def load_data():
        """Load surveillance data with error handling"""
        lst.delete(0, tk.END)
        selected_ids.clear()
        
        def get_surveillance_data():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SurveillanceID, NextBarrettsEGD, Undecided, LastModified
                FROM tblSurveillance
                WHERE PatientID = ?
                ORDER BY LastModified DESC
            """, (patient_id,))
            results = cursor.fetchall()
            conn.close()
            return results
        
        rows = safe_database_operation("Load surveillance data", get_surveillance_data) or []

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

    def check_surveillance_eligibility():
        """Check if patient is eligible for Barrett's surveillance"""
        has_barretts = check_barrett_history(patient_id)
        
        if not has_barretts:
            return False, "No Barrett's esophagus found in pathology history"
        
        return True, "Patient has Barrett's history - surveillance appropriate"

    def get_smart_recommendations():
        """Get intelligent surveillance recommendations"""
        # Get latest Barrett's pathology
        latest_path = get_latest_barrett_pathology(patient_id)
        if not latest_path:
            return None, "No Barrett's pathology found"
        
        path_date, dysplasia_grade, notes = latest_path
        
        # Get Barrett's length from latest EGD
        egd_date, egd_findings = get_latest_egd_with_barrett_length(patient_id)
        barrett_length = None
        if egd_findings:
            # Try to extract length from findings
            import re
            length_match = re.search(r'(\d+(?:\.\d+)?)\s*cm', egd_findings.lower())
            if length_match:
                barrett_length = f"{length_match.group(1)}cm"
        
        # Get recommendation
        months, explanation = get_surveillance_recommendation(dysplasia_grade, barrett_length=barrett_length)
        
        return {
            'months': months,
            'explanation': explanation,
            'last_path_date': path_date,
            'dysplasia_grade': dysplasia_grade,
            'barrett_length': barrett_length,
            'egd_findings': egd_findings
        }, None

    def set_interval(years):
        """Set surveillance interval in years"""
        today = datetime.today()
        future = today + timedelta(days=365 * years)
        entry_next.set_date(future)
        var_undecided.set(0)

    def set_smart_interval():
        """Set interval based on clinical guidelines"""
        recommendations, error = get_smart_recommendations()
        
        if error:
            show_nice_error("Cannot Calculate Smart Interval", error)
            return
        
        if recommendations:
            months = recommendations['months']
            explanation = recommendations['explanation']
            
            today = datetime.today()
            future = today + timedelta(days=30 * months)
            entry_next.set_date(future)
            var_undecided.set(0)
            
            # Show explanation
            details = f"Recommended Interval: {months} months\n\n"
            details += f"Reasoning: {explanation}\n\n"
            if recommendations['last_path_date']:
                details += f"Based on pathology from: {recommendations['last_path_date']}\n"
            if recommendations['dysplasia_grade']:
                details += f"Dysplasia grade: {recommendations['dysplasia_grade']}\n"
            if recommendations['barrett_length']:
                details += f"Barrett's length: {recommendations['barrett_length']}\n"
            
            show_nice_info("Smart Interval Set", details)

    def toggle_undecided():
        """Toggle undecided status"""
        if var_undecided.get():
            entry_next.set_date(datetime.today())

    def validate_surveillance_plan():
        """Validate the surveillance plan before saving"""
        errors = []
        warnings = []
        
        # Check Barrett's eligibility
        eligible, message = check_surveillance_eligibility()
        if not eligible:
            errors.append(f"Barrett's surveillance not appropriate: {message}")
        
        # Check date if not undecided
        if not var_undecided.get():
            try:
                next_date = entry_next.get_date()
                if not is_good_surveillance_date(next_date):
                    errors.append("Surveillance date must be today or later (not more than 10 years)")
                
                # Check if date is reasonable based on latest pathology
                latest_path = get_latest_barrett_pathology(patient_id)
                if latest_path:
                    path_date_str = latest_path[0]
                    try:
                        path_date = datetime.strptime(path_date_str, "%Y-%m-%d").date()
                        days_since_path = (next_date - path_date).days
                        
                        if days_since_path < 60:  # Less than 2 months
                            warnings.append("Surveillance scheduled very soon after last pathology - verify this is appropriate")
                        elif days_since_path > 365 * 7:  # More than 7 years
                            warnings.append("Surveillance scheduled more than 7 years out - verify this follows guidelines")
                    except:
                        pass
            except:
                errors.append("Please select a valid surveillance date")
        
        return errors, warnings

    def save_plan():
        """Save surveillance plan with enhanced refresh"""
        
        # Validate first
        errors, warnings = validate_surveillance_plan()
        
        if errors:
            error_message = "Please fix these problems:\n\n"
            for error in errors:
                error_message += f"• {error}\n"
            show_nice_error("Cannot Save Surveillance Plan", error_message)
            return
        
        if warnings:
            warning_message = "Please review these items:\n\n"
            for warning in warnings:
                warning_message += f"• {warning}\n"
            if not show_nice_warning("Please Review", warning_message):
                return

        def do_the_save():
            """Actually save the surveillance plan"""
            if var_undecided.get():
                next_egd = ""
            else:
                try:
                    next_egd = entry_next.get_date().strftime("%Y-%m-%d")
                except Exception:
                    raise ValueError("Invalid surveillance date")

            last_modified = datetime.today().strftime("%Y-%m-%d")

            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tblSurveillance (PatientID, NextBarrettsEGD, Undecided, LastModified)
                VALUES (?, ?, ?, ?)
            """, (patient_id, next_egd, var_undecided.get(), last_modified))
            conn.commit()

            # Offer to create recall
            if not var_undecided.get():
                should_create_recall = messagebox.askyesno(
                    "Create Recall", 
                    "Would you like to create a recall reminder for this surveillance EGD?"
                )
                if should_create_recall:
                    cursor.execute("""
                        INSERT INTO tblRecall (PatientID, RecallDate, RecallReason, Notes, Completed)
                        VALUES (?, ?, 'Endoscopy', 'Auto-created from Barrett''s Surveillance', 0)
                    """, (patient_id, next_egd))
                    conn.commit()

            conn.close()
            return True

        success = safe_database_operation("Save surveillance plan", do_the_save)
        if success:
            show_nice_success("Surveillance plan saved successfully!")
            load_data()
            
            # Trigger cross-tab refresh
            try:
                from main import tab_refresh_manager
                tab_refresh_manager.refresh_related_tabs('surveillance', 'surveillance')
            except:
                pass

    def delete_plan():
        """Delete surveillance plan with enhanced refresh"""
        selected = lst.curselection()
        if not selected:
            show_nice_error("No Selection", "Please select a surveillance plan to delete")
            return
        
        surveil_id = selected_ids[selected[0]]

        def get_plan_details():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("SELECT NextBarrettsEGD FROM tblSurveillance WHERE SurveillanceID = ?", (surveil_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None

        date_to_delete = safe_database_operation("Get plan details", get_plan_details)

        if not messagebox.askyesno("Delete Surveillance Plan", "Are you sure you want to delete this surveillance plan?"):
            return

        def do_the_delete():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblSurveillance WHERE SurveillanceID = ?", (surveil_id,))
            conn.commit()

            # Offer to delete linked recall
            if date_to_delete:
                cursor.execute("""
                    SELECT RecallID FROM tblRecall
                    WHERE PatientID = ? AND RecallDate = ? AND RecallReason = 'Endoscopy'
                """, (patient_id, date_to_delete))
                recall_row = cursor.fetchone()
                if recall_row:
                    delete_recall = messagebox.askyesno(
                        "Delete Linked Recall", 
                        "Also delete the linked recall reminder for this surveillance?"
                    )
                    if delete_recall:
                        cursor.execute("DELETE FROM tblRecall WHERE RecallID = ?", (recall_row[0],))
                        conn.commit()

            conn.close()
            return True

        success = safe_database_operation("Delete surveillance plan", do_the_delete)
        if success:
            load_data()
            
            # Trigger cross-tab refresh
            try:
                from main import tab_refresh_manager
                tab_refresh_manager.refresh_related_tabs('surveillance', 'surveillance')
            except:
                pass

    def get_last_barretts():
        """Get last Barrett's pathology safely"""
        return safe_database_operation("Get Barrett's pathology", lambda: get_latest_barrett_pathology(patient_id))

    def get_last_egd():
        """Get last EGD safely"""
        def get_egd():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DiagnosticID, TestDate
                FROM tblDiagnostics
                WHERE PatientID = ? AND Endoscopy = 1
                ORDER BY TestDate DESC
                LIMIT 1
            """, (patient_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        
        return safe_database_operation("Get last EGD", get_egd)

    # Build the interface
    info = tk.Frame(tab_frame, padx=10, pady=10)
    info.pack(anchor="w")

    # Clinical context section
    tk.Label(info, text="📋 Clinical Context", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

    last_path = get_last_barretts()
    tk.Label(info, text="Last Barrett's Pathology:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
    if last_path:
        pid, pdate, grade = last_path[0], last_path[1], last_path[2]
        grade_text = grade or "No Grade Specified"
        lbl = tk.Label(info, text=f"{pdate} — {grade_text}", fg="blue", cursor="hand2")
        lbl.grid(row=1, column=1, sticky="w", padx=10)
        if tabs:
            lbl.bind("<Button-1>", lambda e: (
                tabs.select(3),
                tab_frame.after(100, lambda: pathology_tab.build(tabs.nametowidget(tabs.tabs()[3]), patient_id, tabs))
            ))
    else:
        tk.Label(info, text="No Barrett's pathology found", fg="red").grid(row=1, column=1, sticky="w", padx=10)

    last_egd = get_last_egd()
    tk.Label(info, text="Last EGD:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w")
    if last_egd:
        did, ddate = last_egd
        try:
            d = datetime.strptime(ddate, "%Y-%m-%d").date()
            delta = (datetime.today().date() - d).days
            yrs, days = divmod(delta, 365)
            lbl2 = tk.Label(info, text=f"{ddate} ({yrs} yr, {days} days ago)", fg="blue", cursor="hand2")
            lbl2.grid(row=2, column=1, sticky="w", padx=10)
            if tabs:
                lbl2.bind("<Button-1>", lambda e: (
                    tabs.select(1),
                    tab_frame.after(100, lambda: diagnostics_tab.build(tabs.nametowidget(tabs.tabs()[1]), patient_id, tabs))
                ))
        except:
            tk.Label(info, text=ddate, fg="blue").grid(row=2, column=1, sticky="w", padx=10)
    else:
        tk.Label(info, text="No EGD found", fg="gray").grid(row=2, column=1, sticky="w", padx=10)

    # Smart recommendations
    recommendations, error = get_smart_recommendations()
    if recommendations and not error:
        rec_text = f"Recommended: {recommendations['months']} months ({recommendations['explanation']})"
        tk.Label(info, text="Guideline Recommendation:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w")
        tk.Label(info, text=rec_text, fg="darkgreen", wraplength=400).grid(row=3, column=1, sticky="w", padx=10)

    # Surveillance planning section
    tk.Label(tab_frame, text="🗓️ Surveillance Planning", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(20, 10))

    frm = tk.Frame(tab_frame, padx=10, pady=10)
    frm.pack(anchor="w")
    
    tk.Label(frm, text="Next EGD Due:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=2)
    entry_next = DateEntry(frm, width=12, date_pattern="yyyy-mm-dd")
    entry_next.grid(row=0, column=1, sticky="w", padx=5, pady=2)

    var_undecided = tk.IntVar()
    tk.Checkbutton(frm, text="Plan Undecided", variable=var_undecided, command=toggle_undecided).grid(row=0, column=2, padx=10)

    # Smart interval button
    tk.Button(frm, text="🧠 Smart Interval", command=set_smart_interval, 
             bg="lightgreen", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=10)

    # Manual interval buttons
    btns = tk.Frame(frm)
    btns.grid(row=1, column=0, columnspan=4, pady=5)
    for years in [1, 2, 3, 5]:
        tk.Button(btns, text=f"+{years} yr", width=8, command=lambda y=years: set_interval(y)).pack(side=tk.LEFT, padx=3)

    tk.Button(frm, text="💾 Save Surveillance Plan", command=save_plan, 
             font=("Arial", 11, "bold"), bg="lightblue", padx=20, pady=5).grid(row=2, column=0, columnspan=4, pady=15)

    # Status legend
    legend = tk.Frame(tab_frame, padx=10)
    legend.pack(anchor="w")
    tk.Label(legend, text="Status Colors:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 15))
    for label, color in [("Overdue", "red"), ("Due Soon (<1yr)", "orange"), ("Future (>1yr)", "green"), ("Undecided", "gray")]:
        tk.Label(legend, text=label, fg=color).pack(side=tk.LEFT, padx=10)

    # Surveillance plans list
    tk.Label(tab_frame, text="📋 Current Surveillance Plans", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
    
    lst = tk.Listbox(tab_frame, width=85, height=8)
    lst.pack(pady=5, padx=10, anchor="w")

    tk.Button(tab_frame, text="🗑️ Delete Selected Plan", command=delete_plan, 
             font=("Arial", 10, "bold"), bg="lightcoral", padx=15, pady=5).pack(pady=5, padx=10, anchor="w")

    load_data()