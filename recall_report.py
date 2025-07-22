import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, timedelta, date
import csv
import patient_master

class SuperchargedRecallReport:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.result_data = []
        self.selected_recalls = []
        self.setup_ui()
        self.load_today_view()

    def setup_ui(self):
        """Create the supercharged recall report interface"""
        # Clear existing widgets
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        # Main title
        title_frame = tk.Frame(self.parent_frame, bg="darkblue", pady=8)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="📞 Recall Management Dashboard", 
                font=("Arial", 16, "bold"), fg="white", bg="darkblue").pack()

        # Quick action buttons
        action_frame = tk.Frame(self.parent_frame, pady=10)
        action_frame.pack(fill="x", padx=10)

        tk.Label(action_frame, text="🚀 Quick Views:", font=("Arial", 11, "bold")).pack(side="left")
        
        btn_today = tk.Button(action_frame, text="📅 Today's Priorities", command=self.load_today_view,
                            bg="red", fg="white", font=("Arial", 10, "bold"))
        btn_today.pack(side="left", padx=5)
        
        btn_week = tk.Button(action_frame, text="📊 This Week", command=self.load_week_view,
                           bg="orange", fg="white", font=("Arial", 10, "bold"))
        btn_week.pack(side="left", padx=5)
        
        btn_barrett = tk.Button(action_frame, text="🔬 Barrett's Only", command=self.load_barrett_view,
                              bg="darkgreen", fg="white", font=("Arial", 10, "bold"))
        btn_barrett.pack(side="left", padx=5)
        
        btn_overdue = tk.Button(action_frame, text="⚠️ Overdue", command=self.load_overdue_view,
                              bg="purple", fg="white", font=("Arial", 10, "bold"))
        btn_overdue.pack(side="left", padx=5)

        # Advanced filters
        filter_frame = tk.LabelFrame(self.parent_frame, text="🔍 Advanced Filters", 
                                   font=("Arial", 10, "bold"), padx=10, pady=5)
        filter_frame.pack(fill="x", padx=10, pady=5)

        # Filter controls row 1
        filter_row1 = tk.Frame(filter_frame)
        filter_row1.pack(fill="x", pady=2)

        tk.Label(filter_row1, text="Reason:").pack(side="left")
        self.reason_var = tk.StringVar(value="All")
        reason_combo = ttk.Combobox(filter_row1, textvariable=self.reason_var,
                                  values=["All", "Office Visit", "Endoscopy", "Barrett's Surveillance", 
                                         "Surveillance Form", "Post-op Follow-up", "Other"],
                                  state="readonly", width=15)
        reason_combo.pack(side="left", padx=5)

        tk.Label(filter_row1, text="Due in next:").pack(side="left", padx=(20, 5))
        self.days_var = tk.StringVar(value="30")
        days_entry = tk.Entry(filter_row1, textvariable=self.days_var, width=5)
        days_entry.pack(side="left", padx=2)
        tk.Label(filter_row1, text="days").pack(side="left")

        tk.Label(filter_row1, text="Priority:").pack(side="left", padx=(20, 5))
        self.priority_var = tk.StringVar(value="All")
        priority_combo = ttk.Combobox(filter_row1, textvariable=self.priority_var,
                                    values=["All", "Critical", "High", "Medium", "Low"],
                                    state="readonly", width=10)
        priority_combo.pack(side="left", padx=5)

        # Filter controls row 2
        filter_row2 = tk.Frame(filter_frame)
        filter_row2.pack(fill="x", pady=2)

        self.include_past = tk.IntVar(value=1)
        tk.Checkbutton(filter_row2, text="Include overdue", variable=self.include_past).pack(side="left")

        self.include_completed = tk.IntVar(value=0)
        tk.Checkbutton(filter_row2, text="Include completed", variable=self.include_completed).pack(side="left", padx=20)

        self.barrett_only = tk.IntVar(value=0)
        tk.Checkbutton(filter_row2, text="Barrett's patients only", variable=self.barrett_only).pack(side="left", padx=20)

        # Action buttons
        btn_frame = tk.Frame(filter_frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="🔍 Run Custom Filter", command=self.run_custom_filter,
                 font=("Arial", 10, "bold"), bg="blue", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="📊 Export to Excel", command=self.export_excel,
                 font=("Arial", 10, "bold"), bg="green", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="📋 Print Report", command=self.print_report,
                 font=("Arial", 10, "bold"), bg="gray", fg="white").pack(side="left", padx=5)

        # Summary stats
        self.stats_frame = tk.Frame(self.parent_frame, bg="lightblue", pady=5)
        self.stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = tk.Label(self.stats_frame, text="Loading statistics...", 
                                   font=("Arial", 11, "bold"), bg="lightblue")
        self.stats_label.pack()

        # Results table with enhanced columns
        table_frame = tk.Frame(self.parent_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create treeview with more columns
        columns = ("Select", "Priority", "Patient", "MRN", "Phone", "Recall Date", 
                  "Days", "Reason", "Barrett's Status", "Last Path", "Notes", "Actions")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        col_widths = {"Select": 50, "Priority": 60, "Patient": 120, "MRN": 80, "Phone": 100,
                     "Recall Date": 90, "Days": 60, "Reason": 110, "Barrett's Status": 120,
                     "Last Path": 90, "Notes": 150, "Actions": 80}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor="w")

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack tree and scrollbars
        self.tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")

        # Bulk actions frame
        bulk_frame = tk.LabelFrame(self.parent_frame, text="🔧 Bulk Actions", 
                                 font=("Arial", 10, "bold"), padx=10, pady=5)
        bulk_frame.pack(fill="x", padx=10, pady=5)

        bulk_row = tk.Frame(bulk_frame)
        bulk_row.pack()

        tk.Button(bulk_row, text="✅ Mark Selected Complete", command=self.bulk_complete,
                 bg="green", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        tk.Button(bulk_row, text="📅 Bulk Reschedule", command=self.bulk_reschedule,
                 bg="blue", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        tk.Button(bulk_row, text="🔄 Select All Visible", command=self.select_all,
                 bg="purple", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        tk.Button(bulk_row, text="❌ Clear Selection", command=self.clear_selection,
                 bg="gray", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)

        # Bind events
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-Button-1>", self.open_patient_record)

    def get_recall_priority(self, reason, patient_id):
        """Get recall priority level"""
        if not reason:
            return "Low", 4
        
        reason_lower = reason.lower()
        
        # Check for Barrett's history
        has_high_grade = False
        has_barrett = False
        
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
        if "endoscopy" in reason_lower or "surveillance" in reason_lower:
            if has_high_grade:
                return "Critical", 1
            elif has_barrett:
                return "High", 2
            else:
                return "Medium", 3
        elif "office visit" in reason_lower:
            return "Medium", 3
        else:
            return "Low", 4

    def get_barrett_status(self, patient_id):
        """Get Barrett's status for patient"""
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT PathologyDate, DysplasiaGrade 
                FROM tblPathology 
                WHERE PatientID = ? AND Barretts = 1 
                ORDER BY PathologyDate DESC LIMIT 1
            """, (patient_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                date_str, grade = result
                grade_text = grade or "No Grade"
                return f"{grade_text} ({date_str})"
            else:
                return "No Barrett's"
        except:
            return "Unknown"

    def get_patient_phone(self, patient_id):
        """Get patient phone number (placeholder - add phone field to database)"""
        # For now, return placeholder - you can add phone field to tblPatients later
        return "Call Office"

    def calculate_days_difference(self, recall_date):
        """Calculate days until/since recall date"""
        try:
            recall_dt = datetime.strptime(recall_date, "%Y-%m-%d").date()
            today = date.today()
            diff = (recall_dt - today).days
            
            if diff > 0:
                return f"in {diff}d"
            elif diff == 0:
                return "TODAY"
            else:
                return f"{abs(diff)}d ago"
        except:
            return "Invalid"

    def load_today_view(self):
        """Load today's priority recalls"""
        self.include_past.set(1)
        self.include_completed.set(0)
        self.days_var.set("0")
        self.priority_var.set("All")
        self.reason_var.set("All")
        self.barrett_only.set(0)
        self.run_filter()

    def load_week_view(self):
        """Load this week's recalls"""
        self.include_past.set(1)
        self.include_completed.set(0)
        self.days_var.set("7")
        self.priority_var.set("All")
        self.reason_var.set("All")
        self.barrett_only.set(0)
        self.run_filter()

    def load_barrett_view(self):
        """Load Barrett's patient recalls only"""
        self.include_past.set(1)
        self.include_completed.set(0)
        self.days_var.set("90")
        self.priority_var.set("All")
        self.reason_var.set("All")
        self.barrett_only.set(1)
        self.run_filter()

    def load_overdue_view(self):
        """Load overdue recalls only"""
        self.include_past.set(1)
        self.include_completed.set(0)
        self.days_var.set("0")
        self.priority_var.set("All")
        self.reason_var.set("All")
        self.barrett_only.set(0)
        self.run_filter()

    def run_custom_filter(self):
        """Run filter with current settings"""
        self.run_filter()

    def run_filter(self):
        """Execute the filter query and populate results"""
        try:
            days = int(self.days_var.get())
            # Add reasonable limits to prevent overflow
            if days < 0:
                days = 0
            elif days > 3650:  # Max 10 years
                days = 3650
                messagebox.showwarning("Date Range", "Maximum 10 years (3650 days) allowed. Using 3650 days.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of days.")
            self.days_var.set("30")  # Reset to default
            return

        try:
            deadline = date.today() + timedelta(days=days)
        except OverflowError:
            messagebox.showerror("Date Error", "Date range too large. Please enter a smaller number of days.")
            self.days_var.set("30")  # Reset to default
            return
        reason_filter = self.reason_var.get()
        priority_filter = self.priority_var.get()

        # Build query
        query = '''
            SELECT DISTINCT R.RecallID, R.RecallDate, R.RecallReason, R.Notes, R.Completed,
                   P.PatientID, P.FirstName, P.LastName, P.MRN
            FROM tblRecall R
            JOIN tblPatients P ON R.PatientID = P.PatientID
            WHERE 1=1
        '''
        params = []

        # Apply filters
        if reason_filter != "All":
            query += " AND R.RecallReason = ?"
            params.append(reason_filter)

        if not self.include_completed.get():
            query += " AND R.Completed = 0"

        # Date filter
        if self.include_past.get():
            query += " AND R.RecallDate <= ?"
            params.append(deadline.strftime("%Y-%m-%d"))
        else:
            query += " AND R.RecallDate BETWEEN DATE('now') AND ?"
            params.append(deadline.strftime("%Y-%m-%d"))

        # Barrett's filter
        if self.barrett_only.get():
            query += """ AND EXISTS (
                SELECT 1 FROM tblPathology 
                WHERE PatientID = P.PatientID AND Barretts = 1
            )"""

        query += " ORDER BY R.RecallDate ASC, P.LastName ASC"

        # Execute query
        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            cursor.execute(query, params)
            recalls = cursor.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Error loading recalls: {str(e)}")
            return

        # Process results
        self.result_data = []
        critical_count = high_count = medium_count = low_count = 0
        overdue_count = today_count = 0

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        for recall in recalls:
            recall_id, recall_date, reason, notes, completed, patient_id, first, last, mrn = recall
            
            # Get additional data
            priority_text, priority_num = self.get_recall_priority(reason, patient_id)
            barrett_status = self.get_barrett_status(patient_id)
            phone = self.get_patient_phone(patient_id)
            days_text = self.calculate_days_difference(recall_date)
            
            # Apply priority filter
            if priority_filter != "All" and priority_text != priority_filter:
                continue

            # Count statistics
            if priority_text == "Critical":
                critical_count += 1
            elif priority_text == "High":
                high_count += 1
            elif priority_text == "Medium":
                medium_count += 1
            else:
                low_count += 1

            if "ago" in days_text:
                overdue_count += 1
            elif days_text == "TODAY":
                today_count += 1

            # Prepare row data
            patient_name = f"{last}, {first}"
            notes_short = (notes[:30] + "...") if len(notes) > 30 else notes
            
            # Determine row colors
            if completed:
                tags = ("completed",)
            elif "ago" in days_text:
                if priority_text in ["Critical", "High"]:
                    tags = ("urgent_overdue",)
                else:
                    tags = ("overdue",)
            elif days_text == "TODAY":
                tags = ("today",)
            elif priority_text == "Critical":
                tags = ("critical",)
            elif priority_text == "High":
                tags = ("high",)
            else:
                tags = ("normal",)

            # Insert row
            values = ("", priority_text, patient_name, mrn, phone, recall_date,
                     days_text, reason, barrett_status, "", notes_short, "Open")
            
            item_id = self.tree.insert("", "end", values=values, tags=tags)
            
            # Store data for actions
            self.result_data.append({
                'item_id': item_id,
                'recall_id': recall_id,
                'patient_id': patient_id,
                'patient_name': patient_name,
                'recall_date': recall_date,
                'reason': reason,
                'completed': completed
            })

        # Configure row colors
        self.tree.tag_configure("urgent_overdue", background="#ff4444", foreground="white")
        self.tree.tag_configure("overdue", background="#ff8888")
        self.tree.tag_configure("today", background="#ffff00")
        self.tree.tag_configure("critical", background="#ff9999")
        self.tree.tag_configure("high", background="#99ccff")
        self.tree.tag_configure("completed", background="#cccccc", foreground="#666666")
        self.tree.tag_configure("normal", background="white")

        # Update statistics
        total_count = len(self.result_data)
        stats_text = f"📊 Total: {total_count} | 🔴 Critical: {critical_count} | 🔵 High: {high_count} | "
        stats_text += f"🟡 Medium: {medium_count} | ⚪ Low: {low_count} | ⚠️ Overdue: {overdue_count} | 📅 Today: {today_count}"
        
        self.stats_label.config(text=stats_text)

    def on_tree_click(self, event):
        """Handle tree click for selection"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            col = self.tree.identify_column(event.x)
            
            if col == "#1":  # Select column
                if item in self.selected_recalls:
                    self.selected_recalls.remove(item)
                    self.tree.set(item, "Select", "")
                else:
                    self.selected_recalls.append(item)
                    self.tree.set(item, "Select", "✓")

    def open_patient_record(self, event=None):
        """Open patient record in patient master"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # Find patient_id for selected item
        for data in self.result_data:
            if data['item_id'] == selected[0]:
                patient_master.open_patient_master(data['patient_id'], window_size="1000x700")
                break

    def select_all(self):
        """Select all visible items"""
        self.selected_recalls = []
        for item in self.tree.get_children():
            self.selected_recalls.append(item)
            self.tree.set(item, "Select", "✓")

    def clear_selection(self):
        """Clear all selections"""
        for item in self.selected_recalls:
            self.tree.set(item, "Select", "")
        self.selected_recalls = []

    def bulk_complete(self):
        """Mark selected recalls as complete"""
        if not self.selected_recalls:
            messagebox.showwarning("No Selection", "Please select recalls to mark complete.")
            return
        
        if not messagebox.askyesno("Confirm", f"Mark {len(self.selected_recalls)} recalls as complete?"):
            return

        try:
            conn = sqlite3.connect("gerd_center.db")
            cursor = conn.cursor()
            
            for item in self.selected_recalls:
                # Find recall_id for this item
                for data in self.result_data:
                    if data['item_id'] == item:
                        cursor.execute("UPDATE tblRecall SET Completed = 1 WHERE RecallID = ?", 
                                     (data['recall_id'],))
                        break
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Marked {len(self.selected_recalls)} recalls as complete.")
            self.clear_selection()
            self.run_filter()  # Refresh
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update recalls: {str(e)}")

    def bulk_reschedule(self):
        """Bulk reschedule selected recalls"""
        if not self.selected_recalls:
            messagebox.showwarning("No Selection", "Please select recalls to reschedule.")
            return
        
        # Create reschedule dialog
        dialog = tk.Toplevel()
        dialog.title("Bulk Reschedule")
        dialog.geometry("300x150")
        dialog.grab_set()
        
        tk.Label(dialog, text="New recall date:", font=("Arial", 10, "bold")).pack(pady=10)
        
        try:
            date_entry = DateEntry(dialog, width=12, date_pattern="yyyy-mm-dd")
            date_entry.pack(pady=5)
        except Exception as e:
            # Fallback if DateEntry fails
            messagebox.showerror("Error", f"Date picker unavailable: {str(e)}")
            dialog.destroy()
            return
        
        def do_reschedule():
            try:
                new_date = date_entry.get_date().strftime("%Y-%m-%d")
                
                conn = sqlite3.connect("gerd_center.db")
                cursor = conn.cursor()
                
                for item in self.selected_recalls:
                    # Find recall_id for this item
                    for data in self.result_data:
                        if data['item_id'] == item:
                            cursor.execute("UPDATE tblRecall SET RecallDate = ? WHERE RecallID = ?", 
                                         (new_date, data['recall_id']))
                            break
                
                conn.commit()
                conn.close()
                
                dialog.destroy()
                messagebox.showinfo("Success", f"Rescheduled {len(self.selected_recalls)} recalls to {new_date}.")
                self.clear_selection()
                self.run_filter()  # Refresh
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reschedule recalls: {str(e)}")
        
        tk.Button(dialog, text="Reschedule", command=do_reschedule, 
                 bg="blue", fg="white", font=("Arial", 10, "bold")).pack(pady=10)

    def export_excel(self):
        """Export current results to Excel/CSV"""
        if not self.result_data:
            messagebox.showinfo("No Data", "No recalls to export.")
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
                writer.writerow(["Priority", "Patient", "MRN", "Recall Date", "Days", 
                               "Reason", "Barrett's Status", "Notes", "Completed"])
                
                # Data
                for item in self.tree.get_children():
                    values = self.tree.item(item)["values"]
                    writer.writerow(values[1:])  # Skip select column
            
            messagebox.showinfo("Success", f"Exported {len(self.result_data)} recalls to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def print_report(self):
        """Print current report"""
        if not self.result_data:
            messagebox.showinfo("No Data", "No recalls to print.")
            return
        
        # Create print preview window
        preview = tk.Toplevel()
        preview.title("Print Preview - Recall Report")
        preview.geometry("800x600")
        
        # Create text widget
        text_widget = tk.Text(preview, wrap="none", font=("Courier New", 9))
        text_widget.pack(fill="both", expand=True)
        
        # Generate report content
        report_content = "RECALL MANAGEMENT REPORT\n"
        report_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report_content += "=" * 100 + "\n\n"
        
        # Header
        header = f"{'Priority':<10} {'Patient':<20} {'MRN':<12} {'Date':<12} {'Reason':<15} {'Barrett Status':<20} {'Notes':<30}\n"
        report_content += header
        report_content += "-" * 100 + "\n"
        
        # Data rows
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            priority, patient, mrn, phone, recall_date, days, reason, barrett, last_path, notes, actions = values[1:]
            
            row = f"{priority:<10} {patient:<20} {mrn:<12} {recall_date:<12} {reason:<15} {barrett:<20} {notes:<30}\n"
            report_content += row
        
        text_widget.insert("1.0", report_content)
        text_widget.config(state="disabled")


def build_report_view(parent_frame):
    """Build the supercharged recall report view"""
    SuperchargedRecallReport(parent_frame)