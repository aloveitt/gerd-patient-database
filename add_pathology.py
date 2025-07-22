# add_pathology.py - BULLETPROOF VERSION

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, date
import re

def is_good_date(date_obj):
    """Check if a pathology date makes sense"""
    if not date_obj:
        return False
    
    today = date.today()
    min_date = date(1990, 1, 1)  # No pathology before 1990
    max_date = today  # Can't do pathology in the future
    
    return min_date <= date_obj <= max_date

def is_good_eosinophil_count(count_text):
    """Check if eosinophil count makes sense"""
    if not count_text or count_text.strip() == "":
        return True  # Optional field
    
    try:
        count = float(count_text.strip())
        return 0 <= count <= 1000  # Reasonable range for eosinophils per hpf
    except:
        return False

def is_valid_risk_score(risk_text):
    """Check if risk score text looks reasonable"""
    if not risk_text or risk_text.strip() == "":
        return True  # Optional field
    
    # Allow percentages, words, numbers - just check it's not too crazy
    risk_clean = risk_text.strip()
    return len(risk_clean) <= 100  # Reasonable length

def dysplasia_makes_sense(has_barretts, dysplasia_grade):
    """Check if dysplasia grade makes sense with Barrett's status"""
    if not has_barretts and dysplasia_grade:
        return False  # Can't have dysplasia without Barrett's
    return True

def eoe_makes_sense(has_eoe, eosinophil_count):
    """Check if EoE diagnosis makes sense with eosinophil count"""
    if has_eoe and eosinophil_count:
        try:
            count = float(eosinophil_count.strip())
            if count < 15:  # Usually need >15 eos/hpf for EoE
                return "warning"  # Not an error, but worth noting
        except:
            pass
    return True

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

def open_add_pathology(patient_id, refresh_callback):
    """Open add pathology window - NOW SUPER BULLETPROOF!"""
    
    popup = tk.Toplevel()
    popup.title("Add Pathology Entry")
    popup.geometry("550x700")
    popup.grab_set()

    def check_all_pathology_data():
        """Check if all the pathology data makes sense"""
        errors = []
        warnings = []
        
        # Check pathology date
        try:
            path_date = entry_date.get_date()
            if not is_good_date(path_date):
                errors.append("Pathology date must be between 1990 and today")
        except:
            errors.append("Please select a valid pathology date")
        
        # Check eosinophil count if EoE is checked
        if var_eoe.get():
            eos_text = entry_eos.get().strip()
            if not eos_text:
                errors.append("Eosinophil count is required when EoE is selected")
            elif not is_good_eosinophil_count(eos_text):
                errors.append("Eosinophil count must be a number between 0 and 1000")
            else:
                # Check if count makes sense for EoE
                eoe_check = eoe_makes_sense(True, eos_text)
                if eoe_check == "warning":
                    try:
                        count = float(eos_text)
                        warnings.append(f"EoE diagnosis with {count} eosinophils/hpf is unusual (typically >15 for EoE)")
                    except:
                        pass
        
        # Check Barrett's and dysplasia consistency
        has_barretts = var_barretts.get()
        dysplasia_grade = cbo_dysplasia.get().strip()
        
        if not dysplasia_makes_sense(has_barretts, dysplasia_grade):
            errors.append("Cannot specify dysplasia grade without Barrett's esophagus")
        
        # Check if at least one test type is selected
        test_types = [var_biopsy.get(), var_wats3d.get(), var_esopredict.get(), var_tissuecypher.get()]
        if not any(test_types):
            errors.append("Please select at least one test type (Biopsy, WATS3D, EsoPredict, or TissueCypher)")
        
        # Check risk scores
        eso_risk = entry_esopredict.get().strip()
        tc_risk = entry_tissuecypher.get().strip()
        
        if var_esopredict.get() and not eso_risk:
            warnings.append("EsoPredict was performed but no risk score entered")
        
        if var_tissuecypher.get() and not tc_risk:
            warnings.append("TissueCypher was performed but no risk score entered")
        
        if not is_valid_risk_score(eso_risk):
            errors.append("EsoPredict risk score is too long or contains invalid characters")
        
        if not is_valid_risk_score(tc_risk):
            errors.append("TissueCypher risk score is too long or contains invalid characters")
        
        return errors, warnings

    # Date picker
    tk.Label(popup, text="Pathology Date:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="e", padx=5, pady=8)
    entry_date = DateEntry(popup, date_pattern="yyyy-mm-dd", width=15)
    entry_date.grid(row=0, column=1, padx=5, pady=8, sticky="w")

    # Test types section
    test_frame = tk.LabelFrame(popup, text="Test Types Performed", font=("Arial", 10, "bold"), padx=10, pady=10)
    test_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    var_biopsy = tk.IntVar()
    tk.Checkbutton(test_frame, text="Biopsy", variable=var_biopsy, font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=2)
    
    var_wats3d = tk.IntVar()
    tk.Checkbutton(test_frame, text="WATS3D", variable=var_wats3d, font=("Arial", 10)).grid(row=0, column=1, sticky="w", pady=2)
    
    var_esopredict = tk.IntVar()
    chk_esopredict = tk.Checkbutton(test_frame, text="EsoPredict", variable=var_esopredict, font=("Arial", 10))
    chk_esopredict.grid(row=1, column=0, sticky="w", pady=2)
    
    var_tissuecypher = tk.IntVar()
    chk_tissuecypher = tk.Checkbutton(test_frame, text="TissueCypher", variable=var_tissuecypher, font=("Arial", 10))
    chk_tissuecypher.grid(row=1, column=1, sticky="w", pady=2)

    # Findings section
    findings_frame = tk.LabelFrame(popup, text="Pathology Findings", font=("Arial", 10, "bold"), padx=10, pady=10)
    findings_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    # Barrett's and dysplasia (Row 1)
    var_barretts = tk.IntVar()
    chk_barretts = tk.Checkbutton(findings_frame, text="Barrett's Esophagus", variable=var_barretts, 
                                 command=lambda: toggle_dysplasia(), font=("Arial", 10))
    chk_barretts.grid(row=0, column=0, sticky="w", padx=5, pady=3)

    tk.Label(findings_frame, text="Dysplasia Grade:", font=("Arial", 10)).grid(row=0, column=1, sticky="e", padx=5, pady=3)
    cbo_dysplasia = ttk.Combobox(findings_frame,
        values=["", "NGIM", "No Dysplasia", "Indeterminate", "Low Grade", "High Grade"],
        state="disabled", width=17)
    cbo_dysplasia.grid(row=0, column=2, sticky="w", padx=5, pady=3)

    # EoE and eosinophil count (Row 2)
    var_eoe = tk.IntVar()
    chk_eoe = tk.Checkbutton(findings_frame, text="Eosinophilic Esophagitis (EoE)", variable=var_eoe, 
                            command=lambda: toggle_eosinophils(), font=("Arial", 10))
    chk_eoe.grid(row=1, column=0, sticky="w", padx=5, pady=3)

    tk.Label(findings_frame, text="Eosinophil Count:", font=("Arial", 10)).grid(row=1, column=1, sticky="e", padx=5, pady=3)
    entry_eos = tk.Entry(findings_frame, width=12, state="disabled")
    entry_eos.grid(row=1, column=2, sticky="w", padx=5, pady=3)
    tk.Label(findings_frame, text="(per hpf)", font=("Arial", 8), fg="gray").grid(row=1, column=3, sticky="w", padx=2)

    # H. pylori and Atrophic Gastritis (Row 3)
    var_hpylori = tk.IntVar()
    tk.Checkbutton(findings_frame, text="H. pylori", variable=var_hpylori, font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=5, pady=3)

    var_gastritis = tk.IntVar()
    tk.Checkbutton(findings_frame, text="Atrophic Gastritis", variable=var_gastritis, font=("Arial", 10)).grid(row=2, column=1, sticky="w", padx=5, pady=3)

    # Other finding (Row 4)
    tk.Label(findings_frame, text="Other Finding:", font=("Arial", 10)).grid(row=3, column=0, sticky="e", padx=5, pady=3)
    entry_other = tk.Entry(findings_frame, width=40)
    entry_other.grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=3)

    # Risk scores section
    risk_frame = tk.LabelFrame(popup, text="Risk Assessment Scores", font=("Arial", 10, "bold"), padx=10, pady=10)
    risk_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    tk.Label(risk_frame, text="EsoPredict Risk:", font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
    entry_esopredict = tk.Entry(risk_frame, width=40)
    entry_esopredict.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    tk.Label(risk_frame, text="TissueCypher Risk:", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5, pady=5)
    entry_tissuecypher = tk.Entry(risk_frame, width=40)
    entry_tissuecypher.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # Notes section
    tk.Label(popup, text="Additional Notes:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="nw", padx=10, pady=(10, 5))
    txt_notes = tk.Text(popup, width=50, height=4, wrap="word")
    txt_notes.grid(row=4, column=1, padx=10, pady=(10, 5), sticky="ew")

    def toggle_dysplasia():
        """Enable/disable dysplasia dropdown based on Barrett's checkbox"""
        if var_barretts.get():
            cbo_dysplasia.config(state="readonly")
        else:
            cbo_dysplasia.config(state="disabled")
            cbo_dysplasia.set("")  # Clear selection

    def toggle_eosinophils():
        """Enable/disable eosinophil count based on EoE checkbox"""
        if var_eoe.get():
            entry_eos.config(state="normal")
            entry_eos.focus()  # Focus on the field for easy entry
        else:
            entry_eos.config(state="disabled")
            entry_eos.delete(0, tk.END)  # Clear the field

    def check_surveillance_needed():
        """Check if this pathology result needs surveillance planning"""
        if var_barretts.get():
            dysplasia = cbo_dysplasia.get()
            if dysplasia in ["Low Grade", "High Grade", "Indeterminate"]:
                return f"Barrett's with {dysplasia} dysplasia detected - surveillance planning recommended"
            elif dysplasia in ["No Dysplasia", "NGIM"]:
                return "Barrett's without dysplasia detected - surveillance planning recommended"
            else:
                return "Barrett's detected - surveillance planning recommended"
        return None

    def save():
        """Save pathology data with full validation"""
        
        # Check all data first
        errors, warnings = check_all_pathology_data()
        
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
            """Actually save the pathology data"""
            try:
                path_date = entry_date.get_date().strftime("%Y-%m-%d")
            except:
                raise ValueError("Invalid pathology date")

            barretts = var_barretts.get()
            dysplasia = cbo_dysplasia.get() if barretts else ""
            eos_count = entry_eos.get().strip() if var_eoe.get() else None
            
            data = {
                "PatientID": patient_id,
                "PathologyDate": path_date,
                "Biopsy": var_biopsy.get(),
                "WATS3D": var_wats3d.get(),
                "EsoPredict": var_esopredict.get(),
                "TissueCypher": var_tissuecypher.get(),
                "Hpylori": var_hpylori.get(),
                "Barretts": barretts,
                "DysplasiaGrade": dysplasia,
                "AtrophicGastritis": var_gastritis.get(),
                "EoE": var_eoe.get(),
                "EosinophilCount": eos_count,
                "OtherFinding": entry_other.get().strip(),
                "EsoPredictRisk": entry_esopredict.get().strip(),
                "TissueCypherRisk": entry_tissuecypher.get().strip(),
                "Notes": txt_notes.get("1.0", tk.END).strip()
            }

            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO tblPathology (
                    PatientID, PathologyDate, Biopsy, WATS3D, EsoPredict, TissueCypher,
                    Hpylori, Barretts, DysplasiaGrade, AtrophicGastritis, EoE,
                    EosinophilCount, OtherFinding, EsoPredictRisk, TissueCypherRisk, Notes
                ) VALUES (
                    :PatientID, :PathologyDate, :Biopsy, :WATS3D, :EsoPredict, :TissueCypher,
                    :Hpylori, :Barretts, :DysplasiaGrade, :AtrophicGastritis, :EoE,
                    :EosinophilCount, :OtherFinding, :EsoPredictRisk, :TissueCypherRisk, :Notes
                )
            """, data)

            conn.commit()
            conn.close()
            return True

        # Use our safety wrapper
        success = safe_database_operation("Save pathology", do_the_save)
        
        if success:
            # Check if surveillance reminder is needed
            surveillance_message = check_surveillance_needed()
            
            if surveillance_message:
                show_nice_success(f"Pathology saved successfully!\n\n🔔 REMINDER: {surveillance_message}")
            else:
                show_nice_success("Pathology saved successfully!")
            
            popup.destroy()
            if refresh_callback:
                refresh_callback()

    # Save button
    save_frame = tk.Frame(popup)
    save_frame.grid(row=5, column=0, columnspan=2, pady=15)
    
    tk.Button(save_frame, text="Save Pathology Entry", command=save, 
             font=("Arial", 11, "bold"), bg="lightgreen", padx=20, pady=8).pack()

    # Make the popup resizable
    popup.columnconfigure(1, weight=1)
    
    # Set focus to date field
    entry_date.focus()