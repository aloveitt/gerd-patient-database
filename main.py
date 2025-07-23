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

class TabRefreshManager:
    """Manages cross-tab refreshes when data changes"""
    
    def __init__(self):
        self.tabs_widget = None
        self.patient_id = None
        self.tab_builders = {}
        self.app_instance = None
        
    def register_tabs(self, tabs_widget, patient_id, tab_builders, app_instance):
        """Register the tab system"""
        self.tabs_widget = tabs_widget
        self.patient_id = patient_id
        self.tab_builders = tab_builders
        self.app_instance = app_instance
    
    def refresh_related_tabs(self, changed_tab, data_type):
        """Refresh tabs that depend on the changed data"""
        
        # Define which tabs need refreshing based on data changes
        refresh_map = {
            'pathology': ['surveillance', 'recalls'],  # Barrett's changes affect surveillance
            'diagnostics': ['surveillance'],            # EGD results affect surveillance  
            'surgical': ['surveillance', 'recalls'],    # Surgery affects follow-up plans
            'surveillance': ['recalls'],                # Surveillance plans create recalls
            'demographics': ['all']                     # Name changes affect everywhere
        }
        
        tabs_to_refresh = refresh_map.get(data_type, [])
        
        if 'all' in tabs_to_refresh:
            # Refresh all tabs
            for tab_name, builder in self.tab_builders.items():
                if tab_name != changed_tab:
                    self._refresh_tab(tab_name, builder)
        else:
            # Refresh specific tabs
            for tab_name in tabs_to_refresh:
                if tab_name in self.tab_builders and tab_name != changed_tab:
                    builder = self.tab_builders[tab_name]
                    self._refresh_tab(tab_name, builder)
    
    def _refresh_tab(self, tab_name, builder):
        """Actually refresh a specific tab"""
        try:
            # Get the tab frame
            tab_index = list(self.tab_builders.keys()).index(tab_name)
            tab_frame = self.tabs_widget.nametowidget(self.tabs_widget.tabs()[tab_index])
            
            # Rebuild the tab
            builder(tab_frame, self.patient_id, self.tabs_widget)
            
        except Exception as e:
            print(f"Error refreshing {tab_name} tab: {e}")
    
    def refresh_all_tabs(self):
        """Force refresh all tabs - for manual refresh button"""
        for tab_name, builder in self.tab_builders.items():
            self._refresh_tab(tab_name, builder)

# Global instance
tab_refresh_manager = TabRefreshManager()

class ResponsiveWindowManager:
    """Manages responsive window sizing and layout"""
    
    @staticmethod
    def get_screen_dimensions():
        """Get screen dimensions safely"""
        try:
            # Use existing root window if available
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
            # Fallback to common resolution
            screen_width, screen_height = 1920, 1080
            
        return screen_width, screen_height
    
    @staticmethod
    def calculate_optimal_size(min_width=800, min_height=600, max_width_percent=0.9, max_height_percent=0.85):
        """Calculate optimal window size based on screen"""
        screen_width, screen_height = ResponsiveWindowManager.get_screen_dimensions()
        
        # Calculate maximum dimensions (percentage of screen)
        max_width = int(screen_width * max_width_percent)
        max_height = int(screen_height * max_height_percent)
        
        # Use larger of minimum or calculated size
        optimal_width = max(min_width, min(max_width, 1400))  # Default preference
        optimal_height = max(min_height, min(max_height, 900))
        
        return optimal_width, optimal_height
    
    @staticmethod
    def center_window(window, width=None, height=None):
        """Center window on screen with optional size"""
        if width is None or height is None:
            width, height = ResponsiveWindowManager.calculate_optimal_size()
        
        screen_width, screen_height = ResponsiveWindowManager.get_screen_dimensions()
        
        # Calculate center position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Ensure window isn't off-screen
        x = max(0, x)
        y = max(0, y)
        
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        return width, height

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

class ModernGERDApp(tk.Tk):
    """Modern medical interface for GERD patient management with responsive design"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Minnesota Reflux & Heartburn Center - Clinical Management System")
        
        # Setup responsive window
        self.setup_responsive_window()
        
        # Configure responsive layout
        self.setup_responsive_layout()
        
        self.patient_id = None
        self.results_list = []
        
        self.setup_modern_interface()
        self.search_patients()
        
        # Handle window resize events
        self.bind("<Configure>", self.on_window_resize)

    def setup_responsive_window(self):
        """Setup responsive window sizing"""
        # Calculate optimal size
        width, height = ResponsiveWindowManager.calculate_optimal_size(
            min_width=1200, min_height=800
        )
        
        # Center window
        ResponsiveWindowManager.center_window(self, width, height)
        
        # Make resizable with constraints
        self.minsize(1000, 700)
        self.resizable(True, True)
        
        # Configure for different screen sizes
        screen_width, screen_height = ResponsiveWindowManager.get_screen_dimensions()
        
        if screen_width < 1366:  # Smaller screens
            self.small_screen_mode = True
            self.sidebar_width = 300
        else:  # Larger screens
            self.small_screen_mode = False
            self.sidebar_width = 350

    def setup_responsive_layout(self):
        """Setup responsive grid layout"""
        self.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
        
        # Make main window responsive
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # Main content area

    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self:
            # Adjust layout based on window size
            current_width = self.winfo_width()
            
            # Adjust sidebar width for small windows
            if current_width < 1000 and hasattr(self, 'sidebar'):
                self.sidebar.configure(width=250)
            elif hasattr(self, 'sidebar'):
                self.sidebar.configure(width=self.sidebar_width)

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
        sidebar = tk.Frame(parent, bg=ModernMedicalTheme.LIGHT_GRAY, width=self.sidebar_width)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)
        
        # Store reference for resize handling
        self.sidebar = sidebar
        
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
        """Load selected patient with modern interface and refresh system"""
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
            
            # Load patient tabs with refresh system
            self.load_patient_tabs()

    def create_patient_header(self, first, last, mrn, dob):
        """Create modern patient header with refresh button"""
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
        
        # Store reference for refresh button
        self.patient_header_actions = actions_frame
        
        ModernButton(actions_frame, text="🖨️ Print Summary", 
                    style="success", 
                    command=lambda: print_summary.generate_pdf(self.patient_id)).pack(pady=(0, 10))
        
        ModernButton(actions_frame, text="⚡ Quick Actions", 
                    style="warning", 
                    command=lambda: self.show_quick_actions(self.patient_id)).pack(pady=(0, 10))
        
        # Add refresh button
        ModernButton(actions_frame, text="🔄 Refresh All", 
                    style="secondary", 
                    command=tab_refresh_manager.refresh_all_tabs).pack()

    def load_patient_tabs(self):
        """Load patient tabs with enhanced refresh system"""
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

        # Enhanced tab builders with refresh callbacks
        tab_builders = {
            'demographics': lambda frame, pid, tabs: build_demographics(frame, pid, tabs, 
                                                                       on_demographics_updated=lambda: self._handle_data_change('demographics', 'demographics')),
            'diagnostics': lambda frame, pid, tabs: build_diagnostics(frame, pid, tabs),
            'surgical': lambda frame, pid, tabs: build_surgical(frame, pid, tabs),
            'pathology': lambda frame, pid, tabs: build_pathology(frame, pid, tabs),
            'surveillance': lambda frame, pid, tabs: build_surveillance(frame, pid, tabs),
            'recalls': lambda frame, pid, tabs: build_recall(frame, pid, tabs)
        }

        tab_configs = [
            ("👤 Demographics", "demographics"),
            ("🔍 Diagnostics", "diagnostics"),
            ("🏥 Surgical History", "surgical"),
            ("🧪 Pathology", "pathology"),
            ("📊 Surveillance", "surveillance"),
            ("📞 Recalls", "recalls")
        ]

        # Create tabs
        for label, tab_key in tab_configs:
            frame = ttk.Frame(self.tabs)
            frame.configure(style='Modern.TFrame')
            
            # Build the tab
            tab_builders[tab_key](frame, self.patient_id, self.tabs)
            
            self.tabs.add(frame, text=label)

        # Register with refresh manager
        tab_refresh_manager.register_tabs(self.tabs, self.patient_id, tab_builders, self)

    def _handle_data_change(self, tab_name, data_type):
        """Handle when data changes in a tab"""
        tab_refresh_manager.refresh_related_tabs(tab_name, data_type)

    def show_quick_actions(self, patient_id):
        """Modern quick actions dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Quick Patient Actions")
        
        # Use responsive sizing
        width, height = ResponsiveWindowManager.calculate_optimal_size(
            min_width=300, min_height=350, max_width_percent=0.3, max_height_percent=0.5
        )
        ResponsiveWindowManager.center_window(dialog, width, height)
        
        dialog.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
        dialog.transient(self)
        dialog.grab_set()
        
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
        
        # Use responsive sizing
        width, height = ResponsiveWindowManager.calculate_optimal_size(
            min_width=450, min_height=300, max_width_percent=0.4, max_height_percent=0.4
        )
        ResponsiveWindowManager.center_window(confirm_dialog, width, height)
        
        confirm_dialog.configure(bg=ModernMedicalTheme.LIGHT_GRAY)
        confirm_dialog.transient(self)
        confirm_dialog.grab_set()
        
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
            
            # Use responsive bulk print dialog
            from bulk_print_dialog import ResponsiveBulkPrintDialog
            ResponsiveBulkPrintDialog(self, all_patients)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load patients: {str(e)}")

    def bulk_print_search_results(self):
        """Modern bulk print search results"""
        if not self.results_list:
            messagebox.showinfo("No Results", "No search results to print. Try searching for patients first.")
            return
        
        from bulk_print_dialog import ResponsiveBulkPrintDialog
        ResponsiveBulkPrintDialog(self, self.results_list)

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