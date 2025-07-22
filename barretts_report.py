import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta, date
import pandas as pd
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
import tempfile
import webbrowser
import csv

DB_PATH = "gerd_center.db"

class BarrettsSurveillanceCenter(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.pack(fill=tk.BOTH, expand=True)
        self.current_data = []
        self.setup_ui()
        self.load_surveillance_data()

    def setup_ui(self):
        """Create the Barrett's surveillance command center interface"""
        
        # Main title with medical styling
        title_frame = tk.Frame(self, bg="darkgreen", pady=10)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="🔬 Barrett's Esophagus Surveillance Command Center", 
                font=("Arial", 16, "bold"), fg="white", bg="darkgreen").pack()
        
        # Quick action dashboard
        dashboard_frame = tk.Frame(self, bg="lightgreen", pady=8)
        dashboard_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(dashboard_frame, text="🎯 Surveillance Dashboard:", 
                font=("Arial", 12, "bold"), bg="lightgreen").pack(side="left")
        
        # Quick view buttons
        btn_critical = tk.Button(dashboard_frame, text="🚨 High-Grade Due", 
                               command=self.show_high_grade_due, bg="red", fg="white", 
                               font=("Arial", 10, "bold"), padx=15)
        btn_critical.pack(side="left", padx=5)
        
        btn_upcoming = tk.Button(dashboard_frame, text="📅 Due Next 90 Days", 
                               command=self.show_upcoming_surveillance, bg="orange", fg="white",
                               font=("Arial", 10, "bold"), padx=15)
        btn_upcoming.pack(side="left", padx=5)
        
        btn_overdue = tk.Button(dashboard_frame, text="⚠️ Overdue Surveillance", 
                              command=self.show_overdue_surveillance, bg="purple", fg="white",
                              font=("Arial", 10, "bold"), padx=15)
        btn_overdue.pack(side="left", padx=5)
        
        btn_compliance = tk.Button(dashboard_frame, text="📊 Compliance Report", 
                                 command=self.show_compliance_report, bg="blue", fg="white",
                                 font=("Arial", 10, "bold"), padx=15)
        btn_compliance.pack(side="left", padx=5)

        # Advanced filters section
        filter_frame = tk.LabelFrame(self, text="🔍 Advanced Surveillance Filters", 
                                   font=("Arial", 11, "bold"), padx=10, pady=8)
        filter_frame.pack(fill="x", padx=10, pady=5)

        # Filter row 1 - Dysplasia grade and time filters
        filter_row1 = tk.Frame(filter_frame)
        filter_row1.pack(fill="x", pady=3)

        tk.Label(filter_row1, text="Dysplasia Grade:").pack(side="left")
        self.dysplasia_var = tk.StringVar(value="All")
        dysplasia_combo = ttk.Combobox(filter_row1, textvariable=self.dysplasia_var,
                                     values=["All", "High Grade", "Low Grade", "Indeterminate", 
                                           "No Dysplasia", "NGIM", "Unknown"],
                                     state="readonly", width=15)
        dysplasia_combo.pack(side="left", padx=5)

        tk.Label(filter_row1, text="Due in next:").pack(side="left", padx=(20, 5))
        self.days_var = tk.StringVar(value="90")
        days_entry = tk.Entry(filter_row1, textvariable=self.days_var, width=5)
        days_entry.pack(side="left", padx=2)
        tk.Label(filter_row1, text="days").pack(side="left")

        # Filter row 2 - Additional options
        filter_row2 = tk.Frame(filter_frame)
        filter_row2.pack(fill="x", pady=3)

        self.include_past_due = tk.IntVar(value=1)
        tk.Checkbutton(filter_row2, text="Include overdue surveillance", 
                      variable=self.include_past_due).pack(side="left")

        self.include_undecided = tk.IntVar(value=1)
        tk.Checkbutton(filter_row2, text="Include undecided plans", 
                      variable=self.include_undecided).pack(side="left", padx=20)

        # Action buttons
        action_row = tk.Frame(filter_frame)
        action_row.pack(pady=8)
        
        tk.Button(action_row, text="🔍 Run Analysis", command=self.run_surveillance_analysis,
                 font=("Arial", 10, "bold"), bg="green", fg="white", padx=20).pack(side="left", padx=5)
        tk.Button(action_row, text="📊 Export to Excel", command=self.export_surveillance_plan,
                 font=("Arial", 10, "bold"), bg="blue", fg="white", padx=20).pack(side="left", padx=5)
        tk.Button(action_row, text="📋 Print Report", command=self.print_physician_report,
                 font=("Arial", 10, "bold"), bg="purple", fg="white", padx=20).pack(side="left", padx=5)

        # Statistics panel
        self.stats_frame = tk.Frame(self, bg="lightblue", pady=8)
        self.stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = tk.Label(self.stats_frame, text="Loading Barrett's surveillance statistics...", 
                                   font=("Arial", 11, "bold"), bg="lightblue")
        self.stats_label.pack()

        # Enhanced results table
        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Table with clinical columns
        columns = ("Patient", "MRN", "Latest Dysplasia", "Last Path Date", "Next EGD Due", 
                  "Days Until", "Guideline Rec", "Compliance Status", "Priority")
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configure columns with medical relevance
        col_widths = {"Patient": 150, "MRN": 80, "Latest Dysplasia": 120,
                     "Last Path Date": 100, "Next EGD Due": 100, "Days Until": 80,
                     "Guideline Rec": 200, "Compliance Status": 120, "Priority": 80}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor="w")

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack table
        self.tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

        # Clinical insights panel
        insights_frame = tk.LabelFrame(self, text="🎯 Clinical Insights & Recommendations", 
                                     font=("Arial", 11, "bold"), padx=10, pady=8)
        insights_frame.pack(fill="x", padx=10, pady=5)
        
        self.insights_text = tk.Text(insights_frame, height=4, wrap="word", 
                                   bg="lightyellow", font=("Arial", 9))
        self.insights_text.pack(fill="x")

        # Bind events
        self.tree.bind("<Double-Button-1>", self.open_patient_surveillance)

        # Add helpful note
        note_frame = tk.Frame(self, bg="white")
        note_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(note_frame, 
                text="💡 Tip: This report shows Barrett's patients based on most recent pathology with Barretts=Yes. Double-click any row to open patient record.",
                bg="white", fg="gray", font=("Arial", 9), wraplength=800, justify="left").pack(anchor="w")

    def get_surveillance_recommendation(self, dysplasia_grade):
        """Get surveillance recommendation based on ACG/AGA guidelines"""
        if not dysplasia_grade:
            return 36, "No dysplasia grade - default 3-year interval"
        
        dysplasia_grade = dysplasia_grade.strip().lower()
        
        if dysplasia_grade in ["high grade", "high-grade"]:
            return 3, "High-grade dysplasia - 3-month intervals per guidelines"
        elif dysplasia_grade in ["low grade", "low-grade"]:
            return 6, "Low-grade dysplasia - 6-month intervals per guidelines"
        elif dysplasia_grade in ["indeterminate"]:
            return 6, "Indeterminate dysplasia - 6-month intervals until clarified"
        elif dysplasia_grade in ["no dysplasia", "ngim"]:
            return 36, "Barrett's without dysplasia - 3-year intervals per guidelines"
        else:
            return 36, f"Unrecognized grade '{dysplasia_grade}' - default 3-year interval"

    def calculate_compliance_status(self, next_egd_date, recommended_months, last_path_date):
        """Calculate surveillance compliance status"""
        if not next_egd_date or next_egd_date == "Undecided":
            return "No Plan", "red"
        
        try:
            egd_date = datetime.strptime(next_egd_date, "%Y-%m-%d").date()
            today = date.today()
            days_until = (egd_date - today).days
            
            if days_until < -30:  # More than 30 days overdue
                return "Overdue", "red"
            elif days_until < 0:  # Overdue but <30 days
                return "Due Now", "orange"
            elif days_until <= 30:  # Due within 30 days
                return "Due Soon", "blue"
            else:
                return "Scheduled", "green"
                
        except:
            return "Invalid Date", "red"

    def load_surveillance_data(self):
        """Load and analyze Barrett's surveillance data"""
        self.run_surveillance_analysis()

    def run_surveillance_analysis(self):
        """Run comprehensive surveillance analysis"""
        try:
            days = int(self.days_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of days.")
            return

        today = date.today()
        upcoming_date = today + timedelta(days=days)

        conn = sqlite3.connect(DB_PATH)
        
        # Query to get Barrett's surveillance data
        query = """
        WITH LatestBarrettsPath AS (
            SELECT p.*, 
                   ROW_NUMBER() OVER (PARTITION BY p.PatientID ORDER BY p.PathologyDate DESC) as rn
            FROM tblPathology p
            WHERE p.Barretts = 1 AND p.PathologyDate IS NOT NULL
        ),
        CurrentSurveillance AS (
            SELECT s.PatientID, s.NextBarrettsEGD, s.Undecided,
                   ROW_NUMBER() OVER (PARTITION BY s.PatientID ORDER BY s.LastModified DESC) as rn
            FROM tblSurveillance s
        )
        SELECT DISTINCT
            pt.PatientID,
            pt.LastName || ', ' || pt.FirstName AS Name,
            pt.MRN,
            lbp.PathologyDate,
            lbp.DysplasiaGrade,
            cs.NextBarrettsEGD,
            cs.Undecided
        FROM tblPatients pt
        LEFT JOIN LatestBarrettsPath lbp ON pt.PatientID = lbp.PatientID AND lbp.rn = 1
        LEFT JOIN CurrentSurveillance cs ON pt.PatientID = cs.PatientID AND cs.rn = 1
        WHERE lbp.PatientID IS NOT NULL
        """

        # Apply dysplasia filter
        dysplasia_filter = self.dysplasia_var.get()
        if dysplasia_filter != "All":
            if dysplasia_filter == "Unknown":
                query += " AND (lbp.DysplasiaGrade IS NULL OR lbp.DysplasiaGrade = '')"
            else:
                query += f" AND lbp.DysplasiaGrade = '{dysplasia_filter}'"

        query += " ORDER BY pt.LastName, pt.FirstName"

        try:
            df = pd.read_sql_query(query, conn)
            conn.close()
        except Exception as e:
            conn.close()
            messagebox.showerror("Database Error", f"Error loading data: {str(e)}")
            return

        # Process and filter results
        self.current_data = []
        stats = {"high_grade": 0, "low_grade": 0, "no_dysplasia": 0, "overdue": 0, "due_soon": 0, "on_track": 0}
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        for _, row in df.iterrows():
            # Get surveillance recommendation
            dysplasia_grade = row['DysplasiaGrade'] or "Unknown"
            rec_months, rec_explanation = self.get_surveillance_recommendation(dysplasia_grade)
            
            # Calculate compliance status
            next_egd = row['NextBarrettsEGD']
            if row['Undecided']:
                next_egd = "Undecided"
            
            compliance_status, compliance_color = self.calculate_compliance_status(
                next_egd, rec_months, row['PathologyDate']
            )
            
            # Calculate days until surveillance
            if next_egd and next_egd != "Undecided":
                try:
                    egd_date = datetime.strptime(next_egd, "%Y-%m-%d").date()
                    days_until = (egd_date - today).days
                    if days_until >= 0:
                        days_text = f"in {days_until}d"
                    else:
                        days_text = f"{abs(days_until)}d ago"
                except:
                    days_text = "Invalid"
            else:
                days_text = "No Plan"

            # Apply date filter
            include_row = False
            if next_egd == "Undecided" and self.include_undecided.get():
                include_row = True
            elif next_egd and next_egd != "Undecided":
                try:
                    egd_date = datetime.strptime(next_egd, "%Y-%m-%d").date()
                    if egd_date <= upcoming_date:
                        include_row = True
                    elif egd_date < today and self.include_past_due.get():
                        include_row = True
                except:
                    include_row = True  # Include invalid dates for review

            if not include_row:
                continue

            # Determine priority
            if "high grade" in dysplasia_grade.lower():
                priority = "Critical"
                stats["high_grade"] += 1
            elif "low grade" in dysplasia_grade.lower():
                priority = "High"
                stats["low_grade"] += 1
            elif compliance_status == "Overdue":
                priority = "High"
                stats["overdue"] += 1
            elif "no dysplasia" in dysplasia_grade.lower() or "ngim" in dysplasia_grade.lower():
                priority = "Medium"
                stats["no_dysplasia"] += 1
            else:
                priority = "Medium"

            # Count compliance stats
            if compliance_status == "Overdue":
                stats["overdue"] += 1
            elif compliance_status in ["Due Now", "Due Soon"]:
                stats["due_soon"] += 1
            elif compliance_status == "Scheduled":
                stats["on_track"] += 1

            # Prepare row data
            values = (
                row['Name'],
                row['MRN'],
                dysplasia_grade,
                row['PathologyDate'] or "Unknown",
                next_egd or "No Plan",
                days_text,
                rec_explanation,
                compliance_status,
                priority
            )

            # Determine row color based on priority and compliance
            if priority == "Critical":
                tags = ("critical",)
            elif compliance_status == "Overdue":
                tags = ("overdue",)
            elif compliance_status == "Due Now":
                tags = ("due_now",)
            elif priority == "High":
                tags = ("high",)
            else:
                tags = ("normal",)

            # Insert row
            item_id = self.tree.insert("", "end", values=values, tags=tags)
            
            self.current_data.append({
                'item_id': item_id,
                'patient_id': row['PatientID'],
                'name': row['Name'],
                'dysplasia_grade': dysplasia_grade,
                'compliance_status': compliance_status,
                'priority': priority
            })

        # Configure row colors
        self.tree.tag_configure("critical", background="#ff4444", foreground="white")
        self.tree.tag_configure("overdue", background="#ff8888")
        self.tree.tag_configure("due_now", background="#ffaa00")
        self.tree.tag_configure("high", background="#99ccff")
        self.tree.tag_configure("normal", background="white")

        # Update statistics
        total_patients = len(self.current_data)
        stats_text = f"📊 Total Barrett's Patients: {total_patients} | "
        stats_text += f"🔴 High-Grade: {stats['high_grade']} | 🟡 Low-Grade: {stats['low_grade']} | "
        stats_text += f"🟢 No Dysplasia: {stats['no_dysplasia']} | ⚠️ Overdue: {stats['overdue']} | "
        stats_text += f"📅 Due Soon: {stats['due_soon']} | ✅ On Track: {stats['on_track']}"
        
        self.stats_label.config(text=stats_text)

        # Generate clinical insights
        self.generate_clinical_insights(stats, total_patients)

    def generate_clinical_insights(self, stats, total_patients):
        """Generate clinical insights and recommendations"""
        insights = []
        
        if total_patients == 0:
            insights.append("No Barrett's patients found matching current filters.")
        else:
            # High-grade dysplasia insights
            if stats['high_grade'] > 0:
                insights.append(f"🚨 URGENT: {stats['high_grade']} patients with high-grade dysplasia require 3-month surveillance intervals.")
            
            # Compliance insights
            compliance_rate = ((stats['on_track'] + stats['due_soon']) / total_patients) * 100 if total_patients > 0 else 0
            if compliance_rate < 70:
                insights.append(f"⚠️ ATTENTION: Surveillance compliance at {compliance_rate:.1f}% - consider systematic recall improvements.")
            elif compliance_rate >= 90:
                insights.append(f"✅ EXCELLENT: Surveillance compliance at {compliance_rate:.1f}% - maintain current protocols.")
            
            # Overdue insights
            if stats['overdue'] > 0:
                insights.append(f"📞 ACTION NEEDED: {stats['overdue']} patients overdue for surveillance - prioritize scheduling.")
            
            if total_patients > 50:
                insights.append("📈 Large Barrett's cohort - consider dedicated surveillance coordinator and standardized protocols.")

        # Update insights display
        self.insights_text.delete("1.0", tk.END)
        insight_text = "\n".join(insights) if insights else "No specific clinical insights at this time."
        self.insights_text.insert("1.0", insight_text)

    def show_high_grade_due(self):
        """Show high-grade dysplasia patients due for surveillance"""
        self.dysplasia_var.set("High Grade")
        self.days_var.set("90")
        self.include_past_due.set(1)
        self.include_undecided.set(1)
        self.run_surveillance_analysis()

    def show_upcoming_surveillance(self):
        """Show patients due in next 90 days"""
        self.dysplasia_var.set("All")
        self.days_var.set("90")
        self.include_past_due.set(0)
        self.include_undecided.set(0)
        self.run_surveillance_analysis()

    def show_overdue_surveillance(self):
        """Show overdue surveillance patients"""
        self.dysplasia_var.set("All")
        self.days_var.set("0")
        self.include_past_due.set(1)
        self.include_undecided.set(1)
        self.run_surveillance_analysis()

    def show_compliance_report(self):
        """Show compliance analysis"""
        self.dysplasia_var.set("All")
        self.days_var.set("365")
        self.include_past_due.set(1)
        self.include_undecided.set(1)
        self.run_surveillance_analysis()

    def open_patient_surveillance(self, event=None):
        """Open patient record"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # Find patient_id for selected item
        for data in self.current_data:
            if data['item_id'] == selected[0]:
                try:
                    import patient_master
                    patient_master.open_patient_master(data['patient_id'], window_size="1000x700")
                except ImportError:
                    messagebox.showinfo("Info", f"Would open patient record for {data['name']}")
                break

    def export_surveillance_plan(self):
        """Export surveillance plan to CSV"""
        if not self.current_data:
            messagebox.showinfo("No Data", "No surveillance data to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(["Patient", "MRN", "Latest Dysplasia", "Last Path Date", 
                               "Next EGD Due", "Days Until", "Guideline Recommendation", 
                               "Compliance Status", "Priority"])
                
                # Data
                for item in self.tree.get_children():
                    values = self.tree.item(item)["values"]
                    writer.writerow(values)
            
            messagebox.showinfo("Success", f"Exported Barrett's surveillance plan to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def print_physician_report(self):
        """Generate simple text-based report"""
        if not self.current_data:
            messagebox.showinfo("No Data", "No surveillance data to print.")
            return
        
        # Create print preview window
        preview = tk.Toplevel()
        preview.title("Barrett's Surveillance Report")
        preview.geometry("800x600")
        
        # Create text widget
        text_widget = tk.Text(preview, wrap="none", font=("Courier New", 9))
        text_widget.pack(fill="both", expand=True)
        
        # Generate report content
        report_content = "BARRETT'S ESOPHAGUS SURVEILLANCE REPORT\n"
        report_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report_content += "=" * 80 + "\n\n"
        
        # Summary statistics
        stats_data = self.get_summary_statistics()
        report_content += f"EXECUTIVE SUMMARY:\n"
        report_content += f"Total Barrett's Patients: {stats_data['total']}\n"
        report_content += f"High-Grade Dysplasia: {stats_data['high_grade']} patients\n"
        report_content += f"Low-Grade Dysplasia: {stats_data['low_grade']} patients\n"
        report_content += f"Overdue Surveillance: {stats_data['overdue']} patients\n"
        report_content += f"Surveillance Compliance Rate: {stats_data['compliance_rate']:.1f}%\n\n"
        
        # Header
        header = f"{'Patient':<25} {'MRN':<12} {'Dysplasia':<15} {'Next EGD':<12} {'Status':<12} {'Priority':<10}\n"
        report_content += header
        report_content += "-" * 80 + "\n"
        
        # Data rows
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            patient, mrn, dysplasia, last_path, next_egd, days, guideline, status, priority = values
            
            # Truncate long fields
            patient = patient[:24]
            dysplasia = dysplasia[:14]
            status = status[:11]
            
            row = f"{patient:<25} {mrn:<12} {dysplasia:<15} {next_egd:<12} {status:<12} {priority:<10}\n"
            report_content += row
        
        text_widget.insert("1.0", report_content)
        text_widget.config(state="disabled")

    def get_summary_statistics(self):
        """Get summary statistics for reporting"""
        if not self.current_data:
            return {'total': 0, 'high_grade': 0, 'low_grade': 0, 'overdue': 0, 'compliance_rate': 0}
        
        total = len(self.current_data)
        high_grade = sum(1 for p in self.current_data if "high grade" in p['dysplasia_grade'].lower())
        low_grade = sum(1 for p in self.current_data if "low grade" in p['dysplasia_grade'].lower())
        overdue = sum(1 for p in self.current_data if p['compliance_status'] == "Overdue")
        on_track = sum(1 for p in self.current_data if p['compliance_status'] in ["Scheduled", "Due Soon"])
        
        compliance_rate = (on_track / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'high_grade': high_grade,
            'low_grade': low_grade,
            'overdue': overdue,
            'compliance_rate': compliance_rate
        }


# Main classes for compatibility
class BarrettsReport(BarrettsSurveillanceCenter):
    """Compatibility class for existing code"""
    pass


def create_barretts_report(parent_frame):
    """Create the Barrett's surveillance command center"""
    return BarrettsSurveillanceCenter(parent_frame)