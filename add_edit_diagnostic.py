# add_edit_diagnostic.py - Enhanced with refresh system and responsive design

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, date
import re

# Import responsive window utilities
def get_screen_dimensions():
    """Get screen dimensions safely"""
    try:
        root = tk._default_root
        if root is None:
            root = tk.Tk()
            root.withdraw()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
        else:
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
    except:
        screen_width, screen_height = 1920, 1080
    return screen_width, screen_height

def calculate_optimal_size(min_width=600, min_height=800, max_width_percent=0.75, max_height_percent=0.95):
    """Calculate optimal window size"""
    screen_width, screen_height = get_screen_dimensions()
    max_width = int(screen_width * max_width_percent)
    max_height = int(screen_height * max_height_percent)
    optimal_width = max(min_width, min(max_width, 800))
    optimal_height = max(min_height, min(max_height, 900))
    return optimal_width, optimal_height

def center_window(window, width=None, height=None):
    """Center window on screen"""
    if width is None or height is None:
        width, height = calculate_optimal_size()
    screen_width, screen_height = get_screen_dimensions()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    x = max(0, x)
    y = max(0, y)
    window.geometry(f"{width}x{height}+{x}+{y}")
    return width, height

def is_good_date(date_obj):
    """Check if a date makes sense for medical tests"""
    if not date_obj:
        return False
    
    today = date.today()
    min_date = date(1990, 1, 1)  # No tests before 1990
    max_date = today  # Can't do tests in the future
    
    return min_date <= date_obj <= max_date

def is_good_demeester_score(score_text):
    """Check if DeMeester score makes sense"""
    if not score_text or score_text.strip() == "":
        return True  # Optional field
    
    try:
        score = float(score_text.strip())
        return 0 <= score <= 500  # Reasonable range for DeMeester
    except:
        return False

def is_good_percentage(percent_text):
    """Check if percentage makes sense (0-100)"""
    if not percent_text or percent_text.strip() == "":
        return True  # Optional field
    
    try:
        percent = float(percent_text.strip())
        return 0 <= percent <= 100
    except:
        return False

def is_valid_surgeon(surgeon_name):
    """Check if surgeon name looks reasonable"""
    if not surgeon_name or surgeon_name.strip() == "":
        return True  # Surgeon is optional
    
    # Should have letters, spaces, periods, commas
    return bool(re.match(r"^[A-Za-z\s\.,'-]+$", surgeon_name.strip()))

def show_nice_error(title, message):
    """Show a nice error message"""
    messagebox.showerror(title, message)

def show_nice_success(message):
    """Show a nice success message"""
    messagebox.showinfo("Success!", message)

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

def open_add_edit_window(parent, patient_id, diagnostic_id=None, refresh_callback=None, view_only=False):
    """Open the add/edit diagnostic window with enhanced refresh system"""
    
    window = tk.Toplevel(parent)
    window.title("View Diagnostic Test" if view_only else ("Edit Diagnostic Test" if diagnostic_id else "Add Diagnostic Test"))
    window.transient(parent)

    # Use responsive sizing
    if view_only:
        width, height = calculate_optimal_size(
            min_width=700, min_height=600, max_width_percent=0.8, max_height_percent=0.9
        )
    else:
        width, height = calculate_optimal_size(
            min_width=600, min_height=800, max_width_percent=0.75, max_height_percent=0.95
        )
    
    center_window(window, width, height)
    
    # Make resizable with constraints
    window.minsize(500, 400)
    window.resizable(True, True)

    # Get existing data if editing
    is_edit_mode = diagnostic_id is not None
    data = {}

    if is_edit_mode:
        def load_existing_data():
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tblDiagnostics WHERE DiagnosticID = ?", (diagnostic_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return {}
        
        data = safe_database_operation("Load diagnostic data", load_existing_data) or {}

    # Create main scrollable frame
    main_frame = tk.Frame(window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create canvas and scrollbar for scrolling
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

    def disable_widget(widget):
        """Safely disable widgets"""
        try:
            widget.configure(state="disabled")
        except:
            pass

    def check_all_diagnostic_data():
        """Check if all the diagnostic data makes sense"""
        errors = []
        
        # Check test date
        try:
            test_date = entry_date.get_date()
            if not is_good_date(test_date):
                errors.append("Test date must be between 1990 and today")
        except:
            errors.append("Please select a valid test date")
        
        # Check surgeon name
        surgeon_name = surgeon_var.get().strip()
        if surgeon_name and not is_valid_surgeon(surgeon_name):
            errors.append("Surgeon name contains invalid characters")
        
        # Check DeMeester score
        demeester_text = demeester_var.get().strip()
        if not is_good_demeester_score(demeester_text):
            errors.append("DeMeester score must be a number between 0 and 500")
        
        # Check percentage retained
        retained_text = retained_var.get().strip()
        if not is_good_percentage(retained_text):
            errors.append("Percentage retained must be between 0 and 100")
        
        return errors

    # Header
    header_frame = tk.Frame(scrollable_frame)
    header_frame.pack(fill="x", pady=(0, 20))
    
    title_text = "View Diagnostic Test" if view_only else ("Edit Diagnostic Test" if is_edit_mode else "Add Diagnostic Test")
    tk.Label(header_frame, text=f"🔍 {title_text}", 
             font=("Arial", 14, "bold"), fg="darkblue").pack(anchor="w")

    # Form fields
    date_frame = tk.Frame(scrollable_frame)
    date_frame.pack(fill="x", pady=5)
    tk.Label(date_frame, text="Test Date:", font=("Arial", 10, "bold")).pack(anchor="w")
    entry_date = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    if "TestDate" in data:
        try:
            entry_date.set_date(data["TestDate"])
        except:
            pass  # Use default date if invalid
    entry_date.pack(pady=5, anchor="w")

    surgeon_frame = tk.Frame(scrollable_frame)
    surgeon_frame.pack(fill="x", pady=5)
    tk.Label(surgeon_frame, text="Surgeon:", font=("Arial", 10, "bold")).pack(anchor="w")
    surgeon_var = tk.StringVar()
    
    # Get surgeon list safely
    def get_surgeon_list():
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
    surgeon_combo = ttk.Combobox(surgeon_frame, textvariable=surgeon_var, values=surgeon_names, state="readonly")
    surgeon_combo.set(data.get("Surgeon", ""))
    surgeon_combo.pack(pady=5, anchor="w")

    section_frames = {}

    def create_section(name):
        """Create collapsible sections"""
        section_frame = tk.Frame(scrollable_frame, bd=2, relief="groove", padx=5, pady=5)
        section_frame.pack(fill="x", pady=5)
        toggle_btn = tk.Button(section_frame, text=f"► {name}", anchor="w", font=("Arial", 10, "bold"))
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

    # Endoscopy Section
    endoscopy_frame = create_section("Endoscopy")
    endoscopy_var = tk.IntVar(value=data.get("Endoscopy", 0))
    endoscopy_chk = tk.Checkbutton(endoscopy_frame, text="Endoscopy Completed", variable=endoscopy_var, font=("Arial", 10))
    endoscopy_chk.pack(anchor="w", pady=2)

    tk.Label(endoscopy_frame, text="Esophagitis Grade:").pack(anchor="w")
    esophagitis_var = tk.StringVar(value=data.get("EsophagitisGrade", ""))
    esophagitis_combo = ttk.Combobox(endoscopy_frame, textvariable=esophagitis_var, 
                                   values=["None", "LA A", "LA B", "LA C", "LA D"], state="readonly")
    esophagitis_combo.pack(anchor="w", pady=2)

    tk.Label(endoscopy_frame, text="Hiatal Hernia Size:").pack(anchor="w")
    hernia_var = tk.StringVar(value=data.get("HiatalHerniaSize", ""))
    hernia_combo = ttk.Combobox(endoscopy_frame, textvariable=hernia_var, 
                              values=["None", "1 cm", "2 cm", "3 cm", "4 cm", "5 cm", "6 cm", ">6 cm"], state="readonly")
    hernia_combo.pack(anchor="w", pady=2)

    tk.Label(endoscopy_frame, text="Endoscopy Findings:").pack(anchor="w")
    endo_notes = tk.Text(endoscopy_frame, height=3, wrap="word")
    endo_notes.insert("1.0", data.get("EndoscopyFindings", ""))
    endo_notes.pack(fill="x", pady=2)

    # Bravo / pH Impedance Section
    ph_frame = create_section("Bravo / pH Impedance")
    bravo_var = tk.IntVar(value=data.get("Bravo", 0))
    bravo_chk = tk.Checkbutton(ph_frame, text="Bravo Completed", variable=bravo_var, font=("Arial", 10))
    bravo_chk.pack(anchor="w", pady=2)
    
    ph_var = tk.IntVar(value=data.get("pHImpedance", 0))
    ph_chk = tk.Checkbutton(ph_frame, text="pH Impedance Completed", variable=ph_var, font=("Arial", 10))
    ph_chk.pack(anchor="w", pady=2)

    tk.Label(ph_frame, text="DeMeester Score (0-500):").pack(anchor="w")
    demeester_var = tk.StringVar(value=data.get("DeMeesterScore", ""))
    demeester_entry = tk.Entry(ph_frame, textvariable=demeester_var, width=20)
    demeester_entry.pack(anchor="w", pady=2)

    tk.Label(ph_frame, text="pH Study Findings:").pack(anchor="w")
    ph_notes = tk.Text(ph_frame, height=3, wrap="word")
    ph_notes.insert("1.0", data.get("pHFindings", ""))
    ph_notes.pack(fill="x", pady=2)

    # EndoFLIP Section
    flip_frame = create_section("EndoFLIP")
    flip_var = tk.IntVar(value=data.get("EndoFLIP", 0))
    flip_chk = tk.Checkbutton(flip_frame, text="EndoFLIP Completed", variable=flip_var, font=("Arial", 10))
    flip_chk.pack(anchor="w", pady=2)
    
    tk.Label(flip_frame, text="EndoFLIP Findings:").pack(anchor="w")
    flip_notes = tk.Text(flip_frame, height=3, wrap="word")
    flip_notes.insert("1.0", data.get("EndoFLIPFindings", ""))
    flip_notes.pack(fill="x", pady=2)

    # Manometry Section
    mano_frame = create_section("Manometry")
    mano_var = tk.IntVar(value=data.get("Manometry", 0))
    mano_chk = tk.Checkbutton(mano_frame, text="Manometry Completed", variable=mano_var, font=("Arial", 10))
    mano_chk.pack(anchor="w", pady=2)
    
    tk.Label(mano_frame, text="Manometry Findings:").pack(anchor="w")
    mano_notes = tk.Text(mano_frame, height=3, wrap="word")
    mano_notes.insert("1.0", data.get("ManometryFindings", ""))
    mano_notes.pack(fill="x", pady=2)

    # Gastric Emptying Section
    empty_frame = create_section("Gastric Emptying")
    empty_var = tk.IntVar(value=data.get("GastricEmptying", 0))
    empty_chk = tk.Checkbutton(empty_frame, text="Gastric Emptying Completed", variable=empty_var, font=("Arial", 10))
    empty_chk.pack(anchor="w", pady=2)

    tk.Label(empty_frame, text="% Retained at 4h (0-100):").pack(anchor="w")
    retained_var = tk.StringVar(value=data.get("PercentRetained4h", ""))
    retained_entry = tk.Entry(empty_frame, textvariable=retained_var, width=20)
    retained_entry.pack(anchor="w", pady=2)

    tk.Label(empty_frame, text="Gastric Emptying Findings:").pack(anchor="w")
    empty_notes = tk.Text(empty_frame, height=3, wrap="word")
    empty_notes.insert("1.0", data.get("GastricEmptyingFindings", ""))
    empty_notes.pack(fill="x", pady=2)

    # Imaging Section
    imaging_frame = create_section("Imaging")
    imaging_var = tk.IntVar(value=data.get("Imaging", 0))
    imaging_chk = tk.Checkbutton(imaging_frame, text="Imaging Completed", variable=imaging_var, font=("Arial", 10))
    imaging_chk.pack(anchor="w", pady=2)
    
    tk.Label(imaging_frame, text="Imaging Findings:").pack(anchor="w")
    imaging_notes = tk.Text(imaging_frame, height=3, wrap="word")
    imaging_notes.insert("1.0", data.get("ImagingFindings", ""))
    imaging_notes.pack(fill="x", pady=2)

    # Upper GI Section
    ugi_frame = create_section("Upper GI")
    ugi_var = tk.IntVar(value=data.get("UpperGI", 0))
    ugi_chk = tk.Checkbutton(ugi_frame, text="Upper GI Completed", variable=ugi_var, font=("Arial", 10))
    ugi_chk.pack(anchor="w", pady=2)
    
    tk.Label(ugi_frame, text="Upper GI Findings:").pack(anchor="w")
    ugi_notes = tk.Text(ugi_frame, height=3, wrap="word")
    ugi_notes.insert("1.0", data.get("UpperGIFindings", ""))
    ugi_notes.pack(fill="x", pady=2)

    # Other Notes Section
    other_notes_label = tk.Label(scrollable_frame, text="Additional Notes:", font=("Arial", 10, "bold"))
    other_notes_label.pack(anchor="w", pady=(10, 2))
    other_notes = tk.Text(scrollable_frame, height=4, wrap="word")
    other_notes.insert("1.0", data.get("DiagnosticNotes", ""))
    other_notes.pack(fill="x", pady=5)

    # If view-only, disable everything and expand relevant sections
    if view_only:
        def expand_if_has_data(name, *check_vars):
            """Expand sections that have data"""
            frame, toggle_btn = section_frames[name]
            if any(var.get() for var in check_vars):
                frame.pack(fill="x")
                toggle_btn.config(text=f"▼ {name}")

        expand_if_has_data("Endoscopy", endoscopy_var)
        expand_if_has_data("Bravo / pH Impedance", bravo_var, ph_var)
        expand_if_has_data("EndoFLIP", flip_var)
        expand_if_has_data("Manometry", mano_var)
        expand_if_has_data("Gastric Emptying", empty_var)
        expand_if_has_data("Imaging", imaging_var)
        expand_if_has_data("Upper GI", ugi_var)

        # Disable all widgets
        widgets_to_disable = [
            entry_date, surgeon_combo, endoscopy_chk, esophagitis_combo, hernia_combo, endo_notes,
            bravo_chk, ph_chk, demeester_entry, ph_notes, flip_chk, flip_notes, mano_chk, mano_notes,
            empty_chk, retained_entry, empty_notes, imaging_chk, imaging_notes, ugi_chk, ugi_notes, other_notes
        ]
        for widget in widgets_to_disable:
            disable_widget(widget)

    def save_diagnostic():
        """Save the diagnostic data with enhanced refresh"""
        
        # First, check all the data
        errors = check_all_diagnostic_data()
        if errors:
            error_message = "Please fix these problems:\n\n"
            for error in errors:
                error_message += f"• {error}\n"
            show_nice_error("Please Fix These Problems", error_message)
            return

        def do_the_save():
            """Actually save to database"""
            try:
                test_date = entry_date.get_date().strftime("%Y-%m-%d")
            except:
                raise ValueError("Invalid test date")

            values = (
                patient_id,
                test_date,
                surgeon_var.get().strip(),
                endoscopy_var.get(), esophagitis_var.get(), hernia_var.get(), endo_notes.get("1.0", tk.END).strip(),
                bravo_var.get(), ph_var.get(), demeester_var.get().strip(), ph_notes.get("1.0", tk.END).strip(),
                flip_var.get(), flip_notes.get("1.0", tk.END).strip(),
                mano_var.get(), mano_notes.get("1.0", tk.END).strip(),
                empty_var.get(), retained_var.get().strip(), empty_notes.get("1.0", tk.END).strip(),
                imaging_var.get(), imaging_notes.get("1.0", tk.END).strip(),
                ugi_var.get(), ugi_notes.get("1.0", tk.END).strip(),
                other_notes.get("1.0", tk.END).strip(),
            )

            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            
            if is_edit_mode:
                # Update existing record
                cursor.execute("""
                    UPDATE tblDiagnostics SET
                        PatientID = ?, TestDate = ?, Surgeon = ?,
                        Endoscopy = ?, EsophagitisGrade = ?, HiatalHerniaSize = ?, EndoscopyFindings = ?,
                        Bravo = ?, pHImpedance = ?, DeMeesterScore = ?, pHFindings = ?,
                        EndoFLIP = ?, EndoFLIPFindings = ?,
                        Manometry = ?, ManometryFindings = ?,
                        GastricEmptying = ?, PercentRetained4h = ?, GastricEmptyingFindings = ?,
                        Imaging = ?, ImagingFindings = ?,
                        UpperGI = ?, UpperGIFindings = ?,
                        DiagnosticNotes = ?
                    WHERE DiagnosticID = ?
                """, values + (diagnostic_id,))
            else:
                # Insert new record
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
            conn.close()
            return True

        # Use our safety wrapper
        success = safe_database_operation("Save diagnostic test", do_the_save)
        
        if success:
            show_nice_success("Diagnostic test saved successfully!")
            window.destroy()
            if refresh_callback:
                refresh_callback()
                
            # Trigger cross-tab refresh
            try:
                from main import tab_refresh_manager
                tab_refresh_manager.refresh_related_tabs('diagnostics', 'diagnostics')
            except:
                pass

    # Save button (only if not view-only)
    if not view_only:
        save_frame = tk.Frame(scrollable_frame)
        save_frame.pack(pady=15)
        
        save_text = "💾 Update Diagnostic Test" if is_edit_mode else "💾 Save Diagnostic Test"
        tk.Button(save_frame, text=save_text, command=save_diagnostic, 
                 font=("Arial", 11, "bold"), bg="lightblue", padx=25, pady=8).pack()

    # Close button
    close_frame = tk.Frame(scrollable_frame)
    close_frame.pack(pady=10)
    tk.Button(close_frame, text="Close", command=window.destroy, padx=20, pady=5).pack()

    # Clean up on close
    window.protocol("WM_DELETE_WINDOW", window.destroy)