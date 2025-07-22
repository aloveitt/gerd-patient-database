import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import recall_report
import barretts_report
import print_summary
import threading
import time
import os
from datetime import datetime, date, timedelta

class ModernMedicalTheme:
    """Modern medical UI theme colors and styles"""
    
    # Medical color palette
    PRIMARY_BLUE = "#1e3a8a"      # Deep medical blue
    SECONDARY_BLUE = "#3b82f6"    # Bright blue
    ACCENT_TEAL = "#0d9488"       # Medical teal
    SUCCESS_GREEN = "#059669"     # Success green
    WARNING_ORANGE = "#d97706"    # Warning orange
    DANGER_RED = "#dc2626"        # Danger red
    
    # Neutral colors
    WHITE = "#ffffff"
    LIGHT_GRAY = "#f8fafc"
    GRAY_100 = "#f1f5f9"
    GRAY_200 = "#e2e8f0"
    GRAY_300 = "#cbd5e1"
    GRAY_400 = "#94a3b8"
    GRAY_600 = "#475569"
    GRAY_800 = "#1e293b"
    DARK = "#0f172a"
    
    # Fonts
    FONT_LARGE = ("Segoe UI", 16, "bold")
    FONT_HEADING = ("Segoe UI", 14, "bold")
    FONT_SUBHEADING = ("Segoe UI", 12, "bold")
    FONT_BODY = ("Segoe UI", 11)
    FONT_SMALL = ("Segoe UI", 10)
    FONT_CAPTION = ("Segoe UI", 9)

class ModernCard(tk.Frame):
    """Modern card component with shadow effect"""
    
    def __init__(self, parent, title=None, bg_color=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.bg_color = bg_color or ModernMedicalTheme.WHITE
        
        # Configure card appearance
        self.configure(bg=self.bg_color, relief="flat", bd=0)
        
        # Add subtle border
        self.configure(highlightbackground=ModernMedicalTheme.GRAY_200, 
                      highlightthickness=1)
        
        if title:
            self.title_frame = tk.Frame(self, bg=self.bg_color, height=40)
            self.title_frame.pack(fill="x", padx=15, pady=(15, 0))
            self.title_frame.pack_propagate(False)
            
            tk.Label(self.title_frame, text=title, 
                    font=ModernMedicalTheme.FONT_SUBHEADING,
                    bg=self.bg_color, fg=ModernMedicalTheme.GRAY_800).pack(anchor="w")
            
            # Add separator line
            separator = tk.Frame(self, height=1, bg=ModernMedicalTheme.GRAY_200)
            separator.pack(fill="x", padx=15)
            
        # Content frame
        self.content_frame = tk.Frame(self, bg=self.bg_color)
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=15)

class ModernButton(tk.Button):
    """Modern button with medical styling"""
    
    def __init__(self, parent, style="primary", **kwargs):
        
        # Style configurations
        styles = {
            "primary": {
                "bg": ModernMedicalTheme.PRIMARY_BLUE,
                "fg": ModernMedicalTheme.WHITE,
                "activebackground": ModernMedicalTheme.SECONDARY_BLUE,
                "activeforeground": ModernMedicalTheme.WHITE
            },
            "success": {
                "bg": ModernMedicalTheme.SUCCESS_GREEN,
                "fg": ModernMedicalTheme.WHITE,
                "activebackground": "#047857",
                "activeforeground": ModernMedicalTheme.WHITE
            },
            "warning": {
                "bg": ModernMedicalTheme.WARNING_ORANGE,
                "fg": ModernMedicalTheme.WHITE,
                "activebackground": "#b45309",
                "activeforeground": ModernMedicalTheme.WHITE
            },
            "danger": {
                "bg": ModernMedicalTheme.DANGER_RED,
                "fg": ModernMedicalTheme.WHITE,
                "activebackground": "#b91c1c",
                "activeforeground": ModernMedicalTheme.WHITE
            },
            "secondary": {
                "bg": ModernMedicalTheme.GRAY_100,
                "fg": ModernMedicalTheme.GRAY_800,
                "activebackground": ModernMedicalTheme.GRAY_200,
                "activeforeground": ModernMedicalTheme.GRAY_800
            }
        }
        
        style_config = styles.get(style, styles["primary"])
        
        # Default button configuration
        defaults = {
            "font": ModernMedicalTheme.FONT_BODY,
            "relief": "flat",
            "bd": 0,
            "padx": 20,
            "pady": 8,
            "cursor": "hand2"
        }
        
        # Merge with style and user kwargs
        final_config = {**defaults, **style_config, **kwargs}
        
        super().__init__(parent, **final_config)

class BulkPrintDialog:
    """Modern bulk print dialog"""
    
    def __init__(self, parent, patient_list):
        self.parent = parent
        self.patient_list = patient_list
        self.cancelled = False
        self.setup_modern_dialog()
    
    def setup_modern_dialog(self):
        """Create modern bulk print dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Clinical Summary Generator")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        # Header
        header = tk.Frame(self.dialog, bg=ModernMedicalTheme.PRIMARY_BLUE, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🖨️ Clinical Summary Generator", 
                font=ModernMedicalTheme.FONT_LARGE, 
                fg=ModernMedicalTheme.WHITE, 
                bg=ModernMedicalTheme.PRIMARY_BLUE).pack(expand=True)
        
        # Main content
        main_frame = tk.Frame(self.dialog, bg=ModernMedicalTheme.LIGHT_GRAY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Instructions card
        inst_card = ModernCard(main_frame, title="Instructions")
        inst_card.pack(fill="x", pady=(0, 15))
        
        tk.Label(inst_card.content_frame, 
                text="Generate professional clinical summaries for multiple patients. "
                     "Select patients below and choose your output format.",
                font=ModernMedicalTheme.FONT_BODY,
                bg=ModernMedicalTheme.WHITE,
                wraplength=500, justify="left").pack(anchor="w")
        
        # Patient selection card
        patient_card = ModernCard(main_frame, title=f"Patient Selection ({len(self.patient_list)} patients)")
        patient_card.pack(fill="both", expand=True, pady=(0, 15))
        
        # Selection controls
        controls_frame = tk.Frame(patient_card.content_frame, bg=ModernMedicalTheme.WHITE)
        controls_frame.pack(fill="x", pady=(0, 10))
        
        ModernButton(controls_frame, text="✅ Select All", style="success",
                    command=self.select_all).pack(side="left", padx=(0, 10))
        ModernButton(controls_frame, text="❌ Clear All", style="secondary",
                    command=self.select_none).pack(side="left")
        
        # Patient list with modern styling
        list_frame = tk.Frame(patient_card.content_frame, bg=ModernMedicalTheme.WHITE)
        list_frame.pack(fill="both", expand=True)
        
        # Scrollable patient list
        canvas = tk.Canvas(list_frame, bg=ModernMedicalTheme.WHITE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=ModernMedicalTheme.WHITE)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add patients with modern checkboxes
        self.patient_vars = {}
        for i, (pid, first, last, mrn) in enumerate(self.patient_list):
            var = tk.IntVar(value=1)
            self.patient_vars[pid] = var
            
            # Patient row frame
            row_frame = tk.Frame(self.scrollable_frame, bg=ModernMedicalTheme.WHITE)
            row_frame.pack(fill="x", padx=5, pady=2)
            
            # Modern checkbox
            cb = tk.Checkbutton(row_frame, 
                              text=f"{last}, {first} (MRN: {mrn})",
                              variable=var,
                              font=ModernMedicalTheme.FONT_BODY,
                              bg=ModernMedicalTheme.WHITE,
                              fg=ModernMedicalTheme.GRAY_800,
                              selectcolor=ModernMedicalTheme.WHITE,
                              activebackground=ModernMedicalTheme.WHITE)
            cb.pack(anchor="w", padx=5, pady=5)
            
            # Add hover effect
            if i % 2 == 0:
                row_frame.configure(bg=ModernMedicalTheme.GRAY_100)
                cb.configure(bg=ModernMedicalTheme.GRAY_100, activebackground=ModernMedicalTheme.GRAY_100)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Output options card
        output_card = ModernCard(main_frame, title="Output Options")
        output_card.pack(fill="x", pady=(0, 15))
        
        self.output_var = tk.StringVar(value="individual")
        
        tk.Radiobutton(output_card.content_frame, 
                      text="📄 Individual PDFs (one file per patient)", 
                      variable=self.output_var, value="individual",
                      font=ModernMedicalTheme.FONT_BODY,
                      bg=ModernMedicalTheme.WHITE,
                      fg=ModernMedicalTheme.GRAY_800,
                      selectcolor=ModernMedicalTheme.WHITE,
                      activebackground=ModernMedicalTheme.WHITE).pack(anchor="w", pady=5)
        
        tk.Radiobutton(output_card.content_frame, 
                      text="📋 Combined PDF (all patients in one file)", 
                      variable=self.output_var, value="combined",
                      font=ModernMedicalTheme.FONT_BODY,
                      bg=ModernMedicalTheme.WHITE,
                      fg=ModernMedicalTheme.GRAY_800,
                      selectcolor=ModernMedicalTheme.WHITE,
                      activebackground=ModernMedicalTheme.WHITE).pack(anchor="w", pady=5)
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg=ModernMedicalTheme.LIGHT_GRAY)
        button_frame.pack(fill="x")
        
        ModernButton(button_frame, text="🚀 Generate Summaries", style="primary",
                    font=ModernMedicalTheme.FONT_SUBHEADING,
                    command=self.start_bulk_print, padx=30, pady=12).pack(side="left")
        
        ModernButton(button_frame, text="Cancel", style="secondary",
                    command=self.cancel, padx=30, pady=12).pack(side="right")
    
    def select_all(self):
        for var in self.patient_vars.values():
            var.set(1)
    
    def select_none(self):
        for var in self.patient_vars.values():
            var.set(0)
    
    def start_bulk_print(self):
        selected_patients = []
        for pid, var in self.patient_vars.items():
            if var.get():
                for patient_data in self.patient_list:
                    if patient_data[0] == pid:
                        selected_patients.append(patient_data)
                        break
        
        if not selected_patients:
            messagebox.showwarning("No Selection", "Please select at least one patient to print.")
            return
        
        self.dialog.destroy()
        threading.Thread(target=self.bulk_print_worker, args=(selected_patients,), daemon=True).start()
    
    def bulk_print_worker(self, selected_patients):
        # Modern progress dialog
        progress_window = tk.Toplevel(self.parent)
        progress_window.title("Generating Clinical Summaries")
        progress_window.geometry("450x200")
        progress_window.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
        progress_window.transient(self.parent)
        progress_window.grab_set()
        
        # Center progress window
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (200 // 2)
        progress_window.geometry(f"450x200+{x}+{y}")
        
        # Progress header
        header = tk.Frame(progress_window, bg=ModernMedicalTheme.ACCENT_TEAL, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🖨️ Generating Clinical Summaries", 
                font=ModernMedicalTheme.FONT_HEADING, 
                fg=ModernMedicalTheme.WHITE, 
                bg=ModernMedicalTheme.ACCENT_TEAL).pack(expand=True)
        
        # Progress content
        content = tk.Frame(progress_window, bg=ModernMedicalTheme.LIGHT_GRAY)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        progress_label = tk.Label(content, text="Initializing...", 
                                font=ModernMedicalTheme.FONT_BODY,
                                bg=ModernMedicalTheme.LIGHT_GRAY,
                                fg=ModernMedicalTheme.GRAY_800)
        progress_label.pack(pady=10)
        
        # Modern progress bar
        progress_bar = ttk.Progressbar(content, length=400, mode='determinate')
        progress_bar.pack(pady=10)
        progress_bar['maximum'] = len(selected_patients)
        
        ModernButton(content, text="Cancel", style="secondary",
                    command=lambda: setattr(self, 'cancelled', True)).pack(pady=10)
        
        # Generate summaries (same logic as before)
        generated_files = []
        
        for i, (pid, first, last, mrn) in enumerate(selected_patients):
            if self.cancelled:
                break
            
            progress_label.config(text=f"Generating summary for {last}, {first}...")
            progress_bar['value'] = i
            progress_window.update()
            
            try:
                filepath = print_summary.generate_pdf(pid)
                if filepath:
                    generated_files.append((filepath, f"{last}, {first}"))
                time.sleep(0.1)
            except Exception as e:
                print(f"Error generating summary for {last}, {first}: {e}")
                continue
        
        progress_bar['value'] = len(selected_patients)
        
        if not self.cancelled:
            progress_label.config(text="Complete! Opening summaries...")
            progress_window.update()
            
            for filepath, patient_name in generated_files[:5]:
                try:
                    import webbrowser
                    webbrowser.open_new(filepath)
                    time.sleep(0.5)
                except:
                    pass
            
            progress_window.destroy()
            
            # Modern success dialog
            success_dialog = tk.Toplevel(self.parent)
            success_dialog.title("Success")
            success_dialog.geometry("400x250")
            success_dialog.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
            success_dialog.transient(self.parent)
            success_dialog.grab_set()
            
            # Success header
            success_header = tk.Frame(success_dialog, bg=ModernMedicalTheme.SUCCESS_GREEN, height=60)
            success_header.pack(fill="x")
            success_header.pack_propagate(False)
            
            tk.Label(success_header, text="🎉 Success!", 
                    font=ModernMedicalTheme.FONT_HEADING, 
                    fg=ModernMedicalTheme.WHITE, 
                    bg=ModernMedicalTheme.SUCCESS_GREEN).pack(expand=True)
            
            # Success content
            success_content = tk.Frame(success_dialog, bg=ModernMedicalTheme.LIGHT_GRAY)
            success_content.pack(fill="both", expand=True, padx=20, pady=20)
            
            tk.Label(success_content, 
                    text=f"Generated {len(generated_files)} clinical summaries!\n\n"
                         f"Files saved to temporary directory.\n"
                         f"First {min(5, len(generated_files))} files opened automatically.",
                    font=ModernMedicalTheme.FONT_BODY,
                    bg=ModernMedicalTheme.LIGHT_GRAY,
                    fg=ModernMedicalTheme.GRAY_800,
                    justify="center").pack(expand=True)
            
            ModernButton(success_content, text="OK", style="primary",
                        command=success_dialog.destroy).pack()
        else:
            progress_window.destroy()
    
    def cancel(self):
        self.dialog.destroy()

class ModernGERDApp(tk.Tk):
    """Modern medical interface for GERD patient management"""
    
    def __init__(self):
        super().__init__()
        self.title("Minnesota Reflux & Heartburn Center - Clinical Management System")
        self.state('zoomed')
        self.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
        
        self.patient_id = None
        self.results_list = []
        
        self.setup_modern_interface()
        self.search_patients()

    def setup_modern_interface(self):
        """Create modern medical interface"""
        
        # Main header
        self.create_main_header()
        
        # Main content area
        main_container = tk.Frame(self, bg=ModernMedicalTheme.LIGHT_GRAY)
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Left sidebar
        self.create_sidebar(main_container)
        
        # Right content area
        self.create_content_area(main_container)

    def create_main_header(self):
        """Create modern header with branding"""
        header = tk.Frame(self, bg=ModernMedicalTheme.PRIMARY_BLUE, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Hospital logo/title area
        title_frame = tk.Frame(header, bg=ModernMedicalTheme.PRIMARY_BLUE)
        title_frame.pack(side="left", fill="y", padx=20)
        
        tk.Label(title_frame, text="🏥 Minnesota Reflux & Heartburn Center", 
                font=ModernMedicalTheme.FONT_LARGE,
                fg=ModernMedicalTheme.WHITE, 
                bg=ModernMedicalTheme.PRIMARY_BLUE).pack(anchor="w", pady=(15, 5))
        
        tk.Label(title_frame, text="Clinical Management System", 
                font=ModernMedicalTheme.FONT_BODY,
                fg=ModernMedicalTheme.GRAY_300, 
                bg=ModernMedicalTheme.PRIMARY_BLUE).pack(anchor="w")
        
        # Header actions
        actions_frame = tk.Frame(header, bg=ModernMedicalTheme.PRIMARY_BLUE)
        actions_frame.pack(side="right", fill="y", padx=20)
        
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%B %d, %Y")
        
        tk.Label(actions_frame, text=current_date, 
                font=ModernMedicalTheme.FONT_BODY,
                fg=ModernMedicalTheme.GRAY_300, 
                bg=ModernMedicalTheme.PRIMARY_BLUE).pack(anchor="e", pady=(15, 0))
        
        tk.Label(actions_frame, text=current_time, 
                font=ModernMedicalTheme.FONT_SUBHEADING,
                fg=ModernMedicalTheme.WHITE, 
                bg=ModernMedicalTheme.PRIMARY_BLUE).pack(anchor="e", pady=(0, 5))

    def create_sidebar(self, parent):
        """Create modern sidebar with cards"""
        sidebar = tk.Frame(parent, bg=ModernMedicalTheme.LIGHT_GRAY, width=350)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)
        
        # Patient search card
        search_card = ModernCard(sidebar, title="🔍 Patient Search")
        search_card.pack(fill="x", pady=(0, 15))
        
        self.search_entry = tk.Entry(search_card.content_frame, 
                                   font=ModernMedicalTheme.FONT_BODY,
                                   relief="flat", bd=5,
                                   bg=ModernMedicalTheme.GRAY_100)
        self.search_entry.pack(fill="x", pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_patients())
        
        # Results listbox with modern styling
        listbox_frame = tk.Frame(search_card.content_frame, bg=ModernMedicalTheme.WHITE)
        listbox_frame.pack(fill="both", expand=True)
        
        self.results_listbox = tk.Listbox(listbox_frame, 
                                        font=ModernMedicalTheme.FONT_BODY,
                                        relief="flat", bd=0,
                                        bg=ModernMedicalTheme.WHITE,
                                        fg=ModernMedicalTheme.GRAY_800,
                                        selectbackground=ModernMedicalTheme.SECONDARY_BLUE,
                                        selectforeground=ModernMedicalTheme.WHITE,
                                        activestyle="none")
        self.results_listbox.pack(fill="both", expand=True)
        self.results_listbox.bind("<Double-Button-1>", lambda e: self.load_selected_patient())
        
        # Patient management card
        mgmt_card = ModernCard(sidebar, title="👥 Patient Management")
        mgmt_card.pack(fill="x", pady=(0, 15))
        
        ModernButton(mgmt_card.content_frame, text="➕ Add New Patient", 
                    style="success", command=self.add_patient_popup).pack(fill="x", pady=(0, 10))
        
        ModernButton(mgmt_card.content_frame, text="🗑️ Delete Selected", 
                    style="danger", command=self.delete_patient).pack(fill="x")
        
        # Bulk operations card
        bulk_card = ModernCard(sidebar, title="🖨️ Bulk Operations")
        bulk_card.pack(fill="x", pady=(0, 15))
        
        ModernButton(bulk_card.content_frame, text="📋 Print All Summaries", 
                    style="primary", command=self.bulk_print_all_patients).pack(fill="x", pady=(0, 10))
        
        ModernButton(bulk_card.content_frame, text="📄 Print Search Results", 
                    style="secondary", command=self.bulk_print_search_results).pack(fill="x")
        
        # Clinical reports card
        reports_card = ModernCard(sidebar, title="📊 Clinical Reports")
        reports_card.pack(fill="x")
        
        ModernButton(reports_card.content_frame, text="📞 Recall Management", 
                    style="warning", command=self.load_recall_report).pack(fill="x", pady=(0, 10))
        
        ModernButton(reports_card.content_frame, text="🔬 Barrett's Surveillance", 
                    style="primary", command=self.load_barretts_report).pack(fill="x")

    def create_content_area(self, parent):
        """Create modern content area"""
        self.content_frame = tk.Frame(parent, bg=ModernMedicalTheme.LIGHT_GRAY)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Welcome card (shown when no patient selected)
        self.welcome_card = ModernCard(self.content_frame)
        self.welcome_card.pack(fill="both", expand=True)
        
        welcome_content = tk.Frame(self.welcome_card.content_frame, bg=ModernMedicalTheme.WHITE)
        welcome_content.pack(expand=True)
        
        tk.Label(welcome_content, text="🏥", font=("Arial", 48), 
                bg=ModernMedicalTheme.WHITE, fg=ModernMedicalTheme.GRAY_400).pack(pady=(50, 20))
        
        tk.Label(welcome_content, text="Welcome to the Clinical Management System", 
                font=ModernMedicalTheme.FONT_HEADING,
                bg=ModernMedicalTheme.WHITE, fg=ModernMedicalTheme.GRAY_800).pack(pady=(0, 10))
        
        tk.Label(welcome_content, text="Search for a patient or use the tools on the left to get started.", 
                font=ModernMedicalTheme.FONT_BODY,
                bg=ModernMedicalTheme.WHITE, fg=ModernMedicalTheme.GRAY_600).pack()

    def search_patients(self):
        """Enhanced patient search with modern styling"""
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
            display = f"{last}, {first} — {mrn}"
            self.results_listbox.insert(tk.END, display)

    def load_selected_patient(self):
        """Load selected patient with modern interface"""
        selected = self.results_listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        self.patient_id = self.results_list[idx][0]

        # Clear content area
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Get patient data
        conn = sqlite3.connect("gerd_center.db")
        cursor = conn.cursor()
        cursor.execute("SELECT FirstName, LastName, MRN, DOB FROM tblPatients WHERE PatientID = ?", (self.patient_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            first, last, mrn, dob = row
            
            # Modern patient header
            self.create_patient_header(first, last, mrn, dob)
            
            # Load patient tabs with modern styling
            self.load_patient_tabs()

    def create_patient_header(self, first, last, mrn, dob):
        """Create modern patient header"""
        header_card = ModernCard(self.content_frame, bg_color=ModernMedicalTheme.SECONDARY_BLUE)
        header_card.pack(fill="x", pady=(0, 20))
        
        # Configure card for patient header
        header_card.configure(bg=ModernMedicalTheme.SECONDARY_BLUE)
        header_card.content_frame.configure(bg=ModernMedicalTheme.SECONDARY_BLUE)
        
        header_content = tk.Frame(header_card.content_frame, bg=ModernMedicalTheme.SECONDARY_BLUE)
        header_content.pack(fill="x")
        
        # Patient info
        info_frame = tk.Frame(header_content, bg=ModernMedicalTheme.SECONDARY_BLUE)
        info_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(info_frame, text=f"👤 {last}, {first}", 
                font=ModernMedicalTheme.FONT_LARGE,
                fg=ModernMedicalTheme.WHITE, 
                bg=ModernMedicalTheme.SECONDARY_BLUE).pack(anchor="w")
        
        details_frame = tk.Frame(info_frame, bg=ModernMedicalTheme.SECONDARY_BLUE)
        details_frame.pack(anchor="w", pady=(5, 0))
        
        tk.Label(details_frame, text=f"MRN: {mrn}", 
                font=ModernMedicalTheme.FONT_BODY,
                fg=ModernMedicalTheme.GRAY_100, 
                bg=ModernMedicalTheme.SECONDARY_BLUE).pack(side="left", padx=(0, 30))
        
        tk.Label(details_frame, text=f"DOB: {dob}", 
                font=ModernMedicalTheme.FONT_BODY,
                fg=ModernMedicalTheme.GRAY_100, 
                bg=ModernMedicalTheme.SECONDARY_BLUE).pack(side="left")
        
        # Action buttons
        actions_frame = tk.Frame(header_content, bg=ModernMedicalTheme.SECONDARY_BLUE)
        actions_frame.pack(side="right")
        
        ModernButton(actions_frame, text="🖨️ Print Summary", 
                    style="success", 
                    command=lambda: print_summary.generate_pdf(self.patient_id)).pack(pady=(0, 10))
        
        ModernButton(actions_frame, text="⚡ Quick Actions", 
                    style="warning", 
                    command=lambda: self.show_quick_actions(self.patient_id)).pack()

    def load_patient_tabs(self):
        """Load patient tabs with modern styling"""
        from demographics_tab import build as build_demographics
        from diagnostics_tab import build as build_diagnostics
        from surgical_tab import build as build_surgical
        from pathology_tab import build as build_pathology
        from surveillance_tab import build as build_surveillance
        from recall_tab import build as build_recall

        # Create modern notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TNotebook', background=ModernMedicalTheme.LIGHT_GRAY)
        style.configure('Modern.TNotebook.Tab', 
                       padding=[20, 10], 
                       font=ModernMedicalTheme.FONT_BODY)

        self.tabs = ttk.Notebook(self.content_frame, style='Modern.TNotebook')
        self.tabs.pack(fill="both", expand=True)

        tab_configs = [
            ("👤 Demographics", build_demographics),
            ("🔍 Diagnostics", build_diagnostics),
            ("🏥 Surgical History", build_surgical),
            ("🧪 Pathology", build_pathology),
            ("📊 Surveillance", build_surveillance),
            ("📞 Recalls", build_recall)
        ]

        for label, builder in tab_configs:
            frame = ttk.Frame(self.tabs)
            frame.configure(style='Modern.TFrame')
            
            if label == "👤 Demographics":
                builder(frame, self.patient_id, self.tabs, on_demographics_updated=self.search_patients)
            else:
                builder(frame, self.patient_id, self.tabs)
            
            self.tabs.add(frame, text=label)

    def show_quick_actions(self, patient_id):
        """Modern quick actions dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Quick Patient Actions")
        dialog.geometry("300x350")
        dialog.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"300x350+{x}+{y}")
        
        # Header
        header = tk.Frame(dialog, bg=ModernMedicalTheme.ACCENT_TEAL, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="⚡ Quick Actions", 
                font=ModernMedicalTheme.FONT_HEADING,
                fg=ModernMedicalTheme.WHITE, 
                bg=ModernMedicalTheme.ACCENT_TEAL).pack(expand=True)
        
        # Actions
        content = tk.Frame(dialog, bg=ModernMedicalTheme.LIGHT_GRAY)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        actions = [
            ("📅 Add Recall", "primary", lambda: self.quick_action(dialog, 5)),
            ("🧪 Add Pathology", "success", lambda: self.quick_action(dialog, 3)),
            ("🏥 Add Surgery", "warning", lambda: self.quick_action(dialog, 2)),
            ("📊 Plan Surveillance", "primary", lambda: self.quick_action(dialog, 4))
        ]
        
        for text, style, command in actions:
            ModernButton(content, text=text, style=style, 
                        command=command).pack(fill="x", pady=(0, 15))
        
        ModernButton(content, text="Cancel", style="secondary", 
                    command=dialog.destroy).pack(fill="x")

    def quick_action(self, dialog, tab_index):
        """Handle quick actions"""
        dialog.destroy()
        self.tabs.select(tab_index)

    def bulk_print_all_patients(self):
        """Modern bulk print all patients"""
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT PatientID, FirstName, LastName, MRN
                FROM tblPatients
                ORDER BY LastName, FirstName
            """)
            all_patients = cursor.fetchall()
            conn.close()
            
            if not all_patients:
                messagebox.showinfo("No Patients", "No patients found in database.")
                return
            
            if len(all_patients) > 50:
                if not messagebox.askyesno("Large Print Job", 
                    f"This will generate {len(all_patients)} clinical summaries. "
                    f"This may take several minutes. Continue?"):
                    return
            
            BulkPrintDialog(self, all_patients)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load patients: {str(e)}")

    def bulk_print_search_results(self):
        """Modern bulk print search results"""
        if not self.results_list:
            messagebox.showinfo("No Results", "No search results to print. Try searching for patients first.")
            return
        
        BulkPrintDialog(self, self.results_list)

    def delete_patient(self):
        """Modern delete patient confirmation"""
        selected = self.results_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a patient to delete.")
            return

        idx = selected[0]
        patient_id = self.results_list[idx][0]
        patient_name = f"{self.results_list[idx][2]}, {self.results_list[idx][1]}"

        # Modern confirmation dialog
        confirm_dialog = tk.Toplevel(self)
        confirm_dialog.title("Confirm Patient Deletion")
        confirm_dialog.geometry("450x300")
        confirm_dialog.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
        confirm_dialog.transient(self)
        confirm_dialog.grab_set()
        
        # Center dialog
        confirm_dialog.update_idletasks()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (300 // 2)
        confirm_dialog.geometry(f"450x300+{x}+{y}")
        
        # Danger header
        header = tk.Frame(confirm_dialog, bg=ModernMedicalTheme.DANGER_RED, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="⚠️ Permanent Deletion Warning", 
                font=ModernMedicalTheme.FONT_HEADING,
                fg=ModernMedicalTheme.WHITE, 
                bg=ModernMedicalTheme.DANGER_RED).pack(expand=True)
        
        # Warning content
        content = tk.Frame(confirm_dialog, bg=ModernMedicalTheme.LIGHT_GRAY)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(content, text=f"Delete Patient: {patient_name}", 
                font=ModernMedicalTheme.FONT_SUBHEADING,
                bg=ModernMedicalTheme.LIGHT_GRAY, 
                fg=ModernMedicalTheme.GRAY_800).pack(pady=(0, 15))
        
        warning_text = ("This will permanently delete:\n"
                       "• Patient demographics\n"
                       "• All diagnostic studies\n"
                       "• All pathology results\n"
                       "• All surgical history\n"
                       "• All surveillance plans\n"
                       "• All recalls and follow-ups\n\n"
                       "This action cannot be undone!")
        
        tk.Label(content, text=warning_text, 
                font=ModernMedicalTheme.FONT_BODY,
                bg=ModernMedicalTheme.LIGHT_GRAY, 
                fg=ModernMedicalTheme.GRAY_800,
                justify="left").pack()
        
        # Action buttons
        button_frame = tk.Frame(content, bg=ModernMedicalTheme.LIGHT_GRAY)
        button_frame.pack(fill="x", pady=(20, 0))
        
        def confirm_delete():
            try:
                conn = sqlite3.connect("gerd_center.db")
                cursor = conn.cursor()

                delete_queries = [
                    "DELETE FROM tblDiagnostics WHERE PatientID = ?",
                    "DELETE FROM tblPathology WHERE PatientID = ?",
                    "DELETE FROM tblSurgicalHistory WHERE PatientID = ?",
                    "DELETE FROM tblRecall WHERE PatientID = ?",
                    "DELETE FROM tblSurveillance WHERE PatientID = ?",
                    "DELETE FROM tblPatients WHERE PatientID = ?",
                ]
                
                for query in delete_queries:
                    cursor.execute(query, (patient_id,))

                conn.commit()
                conn.close()

                if self.patient_id == patient_id:
                    for widget in self.content_frame.winfo_children():
                        widget.destroy()
                    self.patient_id = None
                    # Recreate welcome card
                    self.create_content_area(self.content_frame.master)

                self.search_patients()
                confirm_dialog.destroy()
                messagebox.showinfo("Deleted", f"{patient_name} has been permanently deleted.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete patient: {str(e)}")
        
        ModernButton(button_frame, text="🗑️ Delete Permanently", 
                    style="danger", command=confirm_delete).pack(side="left")
        
        ModernButton(button_frame, text="Cancel", style="secondary", 
                    command=confirm_dialog.destroy).pack(side="right")

    def add_patient_popup(self):
        """Add patient with modern workflow"""
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
        """Load modern recall report"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.patient_id = None
        recall_report.build_report_view(self.content_frame)

    def load_barretts_report(self):
        """Load modern Barrett's report"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.patient_id = None
        barretts_report.BarrettsReport(self.content_frame)


if __name__ == "__main__":
    app = ModernGERDApp()
    app.mainloop()