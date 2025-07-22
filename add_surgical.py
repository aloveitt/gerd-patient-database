import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, date

def is_good_surgery_date(date_obj):
    """Check if a surgery date makes sense"""
    if not date_obj:
        return False
    
    today = date.today()
    min_date = date(1980, 1, 1)  # No surgeries before 1980
    max_date = today  # Can't do surgeries in the future
    
    return min_date <= date_obj <= max_date

def check_surgical_logic(procedures):
    """Check if the combination of procedures makes medical sense"""
    errors = []
    warnings = []
    
    # Get which procedures are selected
    hiatal = procedures.get("HiatalHernia", False)
    paraeso = procedures.get("ParaesophagealHernia", False)
    mesh = procedures.get("MeshUsed", False)
    bypass = procedures.get("GastricBypass", False)
    sleeve = procedures.get("SleeveGastrectomy", False)
    toupet = procedures.get("Toupet", False)
    tif = procedures.get("TIF", False)
    nissen = procedures.get("Nissen", False)
    dor = procedures.get("Dor", False)
    heller = procedures.get("HellerMyotomy", False)
    stretta = procedures.get("Stretta", False)
    ablation = procedures.get("Ablation", False)
    linx = procedures.get("LINX", False)
    gpoem = procedures.get("GPOEM", False)
    epoem = procedures.get("EPOEM", False)
    zpoem = procedures.get("ZPOEM", False)
    pyloro = procedures.get("Pyloroplasty", False)
    revision = procedures.get("Revision", False)
    stimulator = procedures.get("GastricStimulator", False)
    dilation = procedures.get("Dilation", False)
    
    # Check mutually exclusive fundoplications
    fundoplications = [toupet, nissen, dor]
    if sum(fundoplications) > 1:
        errors.append("Cannot perform multiple fundoplications in same surgery (Toupet, Nissen, Dor are mutually exclusive)")
    
    # Check POEM procedures
    poem_procedures = [gpoem, epoem, zpoem]
    if sum(poem_procedures) > 1:
        errors.append("Cannot perform multiple POEM procedures in same surgery")
    
    # Check bariatric procedures
    bariatric_procedures = [bypass, sleeve]
    if sum(bariatric_procedures) > 1:
        errors.append("Cannot perform multiple bariatric procedures in same surgery")
    
    # Logical combinations and warnings
    if linx and any(fundoplications):
        warnings.append("LINX device with fundoplication is unusual - verify this combination")
    
    if heller and not any(fundoplications) and not any(poem_procedures):
        warnings.append("Heller myotomy typically includes anti-reflux procedure - consider adding fundoplication")
    
    if mesh and not (hiatal or paraeso):
        warnings.append("Mesh used but no hernia repair marked - verify hernia repair was performed")
    
    if paraeso and not hiatal:
        warnings.append("Paraesophageal hernia repair typically includes hiatal hernia repair")
    
    if any(poem_procedures) and any(fundoplications):
        errors.append("POEM procedures and fundoplications are contradictory approaches")
    
    if stretta and linx:
        warnings.append("Stretta and LINX in same surgery is unusual combination")
    
    if revision and not any([toupet, nissen, dor, linx, tif, bypass, sleeve]):
        warnings.append("Revision marked but no primary procedure to revise is selected")
    
    # Check if any procedure is actually selected
    all_procedures = list(procedures.values())
    if not any(all_procedures):
        errors.append("Please select at least one surgical procedure")
    
    return errors, warnings

def is_valid_surgeon(surgeon_name):
    """Check if surgeon name looks reasonable"""
    if not surgeon_name or surgeon_name.strip() == "":
        return False  # Surgeon is required for surgery
    
    # Should have letters, spaces, periods, commas
    import re
    return bool(re.match(r"^[A-Za-z\s\.,'-]+$", surgeon_name.strip()))

def show_nice_error(title, message):
    """Show a nice error message"""
    messagebox.showerror(title, message)

def show_nice_success(message):
    """Show a nice success message"""
    messagebox.showinfo("Success!", message)

def show_nice_warning(title, message):
    """Show a warning message"""
    return messagebox.askyesno(title, f"{message}\n\nDo you want to continue anyway?")

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

def open_add_surgical(tab_frame, patient_id, refresh_callback=None):
    """Open add surgical window - NOW WITH SURGICAL INTELLIGENCE AND PROPER SIZING!"""
    
    popup = tk.Toplevel()
    popup.title("Add Surgical Entry")
    popup.geometry("700x600")  # Smaller height that fits on screen
    popup.grab_set()
    
    # Create main frame with scrollbar
    main_frame = tk.Frame(popup)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create canvas and scrollbar
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Enable mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def bind_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def unbind_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")
    
    canvas.bind("<Enter>", bind_mousewheel)
    canvas.bind("<Leave>", unbind_mousewheel)

    def check_all_surgical_data():
        """Check if all the surgical data makes sense"""
        errors = []
        warnings = []
        
        # Check surgery date
        try:
            surgery_date = entry_date.get_date()
            if not is_good_surgery_date(surgery_date):
                errors.append("Surgery date must be between 1980 and today")
        except:
            errors.append("Please select a valid surgery date")
        
        # Check surgeon
        surgeon_name = cbo_surgeon.get().strip()
        if not is_valid_surgeon(surgeon_name):
            errors.append("Please select a valid surgeon")
        
        # Get all procedure selections
        procedures = {}
        for proc_name, var in check_vars.items():
            procedures[proc_name] = var.get()
        
        # Check surgical logic
        logic_errors, logic_warnings = check_surgical_logic(procedures)
        errors.extend(logic_errors)
        warnings.extend(logic_warnings)
        
        return errors, warnings

    # Surgery date
    tk.Label(scrollable_frame, text="Surgery Date:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="e", padx=5, pady=8)
    entry_date = DateEntry(scrollable_frame, date_pattern="yyyy-mm-dd", width=15)
    entry_date.grid(row=0, column=1, padx=5, pady=8, sticky="w")

    # Surgeon selection
    tk.Label(scrollable_frame, text="Surgeon:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="e", padx=5, pady=8)
    
    def get_surgeon_list():
        """Get list of surgeons safely"""
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT SurgeonName FROM tblSurgeons ORDER BY SurgeonName")
            return [row[0] for row in cursor.fetchall()]
        except:
            return []  # Return empty list if table doesn't exist
        finally:
            conn.close()
    
    surgeon_names = safe_database_operation("Load surgeon list", get_surgeon_list) or []
    cbo_surgeon = ttk.Combobox(scrollable_frame, values=surgeon_names, state="readonly", width=25)
    cbo_surgeon.grid(row=1, column=1, padx=5, pady=8, sticky="w")

    # Procedures section
    procedure_frame = tk.LabelFrame(scrollable_frame, text="Surgical Procedures Performed", 
                                   font=("Arial", 11, "bold"), padx=15, pady=15)
    procedure_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=15, sticky="ew")

    # Define procedures with medical groupings and descriptions
    procedure_groups = [
        ("Hernia Repairs", [
            ("HiatalHernia", "Hiatal Hernia Repair"),
            ("ParaesophagealHernia", "Paraesophageal Hernia Repair"),
            ("MeshUsed", "Mesh Used"),
        ]),
        ("Fundoplications (Choose One)", [
            ("Nissen", "Nissen Fundoplication (360°)"),
            ("Toupet", "Toupet Fundoplication (270°)"),
            ("Dor", "Dor Fundoplication (180°)"),
        ]),
        ("POEM Procedures (Choose One)", [
            ("GPOEM", "G-POEM (Gastric)"),
            ("EPOEM", "E-POEM (Esophageal)"),
            ("ZPOEM", "Z-POEM (Zenker's)"),
        ]),
        ("Bariatric Procedures (Choose One)", [
            ("GastricBypass", "Gastric Bypass"),
            ("SleeveGastrectomy", "Sleeve Gastrectomy"),
        ]),
        ("Other Anti-Reflux", [
            ("TIF", "TIF (Transoral Incisionless)"),
            ("LINX", "LINX Device"),
            ("Stretta", "Stretta Radiofrequency"),
        ]),
        ("Motility/Access Procedures", [
            ("HellerMyotomy", "Heller Myotomy"),
            ("Pyloroplasty", "Pyloroplasty"),
            ("Dilation", "Esophageal Dilation"),
        ]),
        ("Advanced/Other", [
            ("Ablation", "Ablation Therapy"),
            ("GastricStimulator", "Gastric Stimulator"),
            ("Revision", "Revision Surgery"),
            ("Other", "Other Procedure"),
        ]),
    ]

    check_vars = {}
    current_row = 0

    for group_name, procedures in procedure_groups:
        # Group header
        group_label = tk.Label(procedure_frame, text=group_name, font=("Arial", 10, "bold"), fg="blue")
        group_label.grid(row=current_row, column=0, columnspan=2, sticky="w", pady=(10, 2))
        current_row += 1
        
        # Procedures in this group
        for proc_key, proc_display in procedures:
            var = tk.IntVar()
            check_vars[proc_key] = var
            
            # Color code mutually exclusive groups
            if "Choose One" in group_name:
                cb = tk.Checkbutton(procedure_frame, text=proc_display, variable=var, fg="red")
            else:
                cb = tk.Checkbutton(procedure_frame, text=proc_display, variable=var)
            
            cb.grid(row=current_row, column=0, sticky="w", padx=20, pady=1)
            current_row += 1
        
        # Add some spacing between groups
        current_row += 1

    # Notes section
    tk.Label(scrollable_frame, text="Operative Notes:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="nw", padx=5, pady=(15, 5))
    txt_notes = tk.Text(scrollable_frame, width=50, height=4, wrap="word")  # Smaller height
    txt_notes.grid(row=3, column=1, padx=5, pady=(15, 5), sticky="ew")

    def get_clinical_recommendations():
        """Generate clinical recommendations based on selected procedures"""
        recommendations = []
        
        # Get selected procedures
        selected = []
        for proc_name, var in check_vars.items():
            if var.get():
                selected.append(proc_name)
        
        # Generate recommendations
        if "HiatalHernia" in selected or "ParaesophagealHernia" in selected:
            if not any(fund in selected for fund in ["Nissen", "Toupet", "Dor"]):
                recommendations.append("Consider anti-reflux procedure with hernia repair")
        
        if "HellerMyotomy" in selected:
            if not any(fund in selected for fund in ["Nissen", "Toupet", "Dor"]):
                recommendations.append("Consider fundoplication with Heller myotomy")
        
        if "LINX" in selected:
            recommendations.append("LINX device - ensure proper patient selection criteria met")
        
        if any(poem in selected for poem in ["GPOEM", "EPOEM", "ZPOEM"]):
            recommendations.append("POEM procedure - consider post-op reflux monitoring")
        
        if "Revision" in selected:
            recommendations.append("Revision surgery - document indication and previous procedure")
        
        return recommendations

    def save():
        """Save surgical data with full validation and clinical intelligence"""
        
        # Check all data first
        errors, warnings = check_all_surgical_data()
        
        # Show errors if any
        if errors:
            error_message = "Please fix these problems:\n\n"
            for error in errors:
                error_message += f"• {error}\n"
            show_nice_error("Please Fix These Problems", error_message)
            return
        
        # Show warnings if any
        if warnings:
            warning_message = "Please review these items:\n\n"
            for warning in warnings:
                warning_message += f"• {warning}\n"
            if not show_nice_warning("Please Review", warning_message):
                return  # User chose not to continue

        def do_the_save():
            """Actually save the surgical data"""
            try:
                surgery_date = entry_date.get_date().strftime("%Y-%m-%d")
            except:
                raise ValueError("Invalid surgery date")

            # Get all procedure values in the correct order
            procedure_names = [
                "HiatalHernia", "ParaesophagealHernia", "MeshUsed", "GastricBypass", "SleeveGastrectomy", 
                "Toupet", "TIF", "Nissen", "Dor", "HellerMyotomy", "Stretta", "Ablation", "LINX", 
                "GPOEM", "EPOEM", "ZPOEM", "Pyloroplasty", "Revision", "GastricStimulator", "Dilation", "Other"
            ]
            
            procedure_values = []
            for proc_name in procedure_names:
                procedure_values.append(check_vars[proc_name].get())

            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            
            # Build the SQL dynamically
            sql = f"""
                INSERT INTO tblSurgicalHistory (
                    PatientID, SurgeryDate, SurgerySurgeon, Notes,
                    {', '.join(procedure_names)}
                ) VALUES (
                    ?, ?, ?, ?, {', '.join('?' for _ in procedure_names)}
                )
            """
            
            values = [
                patient_id,
                surgery_date,
                cbo_surgeon.get().strip(),
                txt_notes.get("1.0", tk.END).strip(),
            ] + procedure_values

            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            return True

        # Use our safety wrapper
        success = safe_database_operation("Save surgical procedure", do_the_save)
        
        if success:
            # Generate clinical recommendations
            recommendations = get_clinical_recommendations()
            
            success_message = "Surgical procedure saved successfully!"
            
            if recommendations:
                success_message += "\n\n📋 Clinical Reminders:\n"
                for rec in recommendations:
                    success_message += f"• {rec}\n"
            
            show_nice_success(success_message)
            popup.destroy()
            if refresh_callback:
                refresh_callback()

    # Save button
    save_frame = tk.Frame(scrollable_frame)
    save_frame.grid(row=4, column=0, columnspan=2, pady=20)
    
    tk.Button(save_frame, text="Save Surgical Procedure", command=save, 
             font=("Arial", 11, "bold"), bg="lightblue", padx=25, pady=10).pack()

    # Make the scrollable content expandable
    scrollable_frame.columnconfigure(1, weight=1)
    
    # Set focus to date field
    entry_date.focus()