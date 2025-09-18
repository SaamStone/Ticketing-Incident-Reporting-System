import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import csv
from datetime import datetime

DB_NAME = 'incidents.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            reporter TEXT NOT NULL,
            priority TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            assigned_to TEXT,
            created_date TEXT NOT NULL,
            updated_date TEXT,
            resolved_date TEXT,
            resolution_notes TEXT
        )
    ''')
    conn.commit()

    # Insert sample data if empty
    c.execute('SELECT COUNT(*) FROM incidents')
    count = c.fetchone()[0]
    if count == 0:
        sample_data = [
            ('Email server down', 'Users cannot access email', 'John Doe', 'High', 'Network', 'Resolved', 'IT Team',
             (datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
             (datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
             (datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
             'Server rebooted'),
            ('Printer not working', 'Office printer offline', 'Jane Smith', 'Medium', 'Hardware', 'In-Progress', 'Tech Support',
             (datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
             (datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
             None,
             None),
            ('Software installation request', 'Need new software installed', 'Bob Johnson', 'Low', 'Software', 'Open', None,
             (datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
             None,
             None,
             None)
        ]
        c.executemany('''
            INSERT INTO incidents (title, description, reporter, priority, category, status, assigned_to, created_date, updated_date, resolved_date, resolution_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
        conn.commit()
    conn.close()

class IncidentTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IT Incident Tracking System")
        self.geometry("1000x700")
        self.resizable(True, True)

        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row

        self.create_widgets()

    def create_widgets(self):
        tab_control = ttk.Notebook(self)
        self.tab_create = ttk.Frame(tab_control)
        self.tab_view = ttk.Frame(tab_control)
        self.tab_reports = ttk.Frame(tab_control)

        tab_control.add(self.tab_create, text='Create Incident')
        tab_control.add(self.tab_view, text='View Incidents')
        tab_control.add(self.tab_reports, text='Reports')
        tab_control.pack(expand=1, fill='both')

        self.create_create_tab()
        self.create_view_tab()
        self.create_reports_tab()

    # --- Create Incident Tab ---
    def create_create_tab(self):
        frame = self.tab_create

        # Form labels and entries
        labels = ['Title*', 'Description', 'Reporter*', 'Priority*', 'Category*']
        for i, text in enumerate(labels):
            ttk.Label(frame, text=text).grid(row=i, column=0, sticky='w', padx=10, pady=5)

        self.title_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.reporter_var = tk.StringVar()
        self.priority_var = tk.StringVar(value='Medium')
        self.category_var = tk.StringVar(value='Software')

        ttk.Entry(frame, textvariable=self.title_var, width=50).grid(row=0, column=1, padx=10, pady=5)
        ttk.Entry(frame, textvariable=self.description_var, width=50).grid(row=1, column=1, padx=10, pady=5)
        ttk.Entry(frame, textvariable=self.reporter_var, width=50).grid(row=2, column=1, padx=10, pady=5)

        priorities = ['Low', 'Medium', 'High', 'Critical']
        ttk.Combobox(frame, textvariable=self.priority_var, values=priorities, state='readonly').grid(row=3, column=1, padx=10, pady=5)

        categories = ['Hardware', 'Software', 'Network', 'Security', 'Other']
        ttk.Combobox(frame, textvariable=self.category_var, values=categories, state='readonly').grid(row=4, column=1, padx=10, pady=5)

        ttk.Button(frame, text="Create Incident", command=self.create_incident).grid(row=5, column=1, pady=20, sticky='e')

    def create_incident(self):
        title = self.title_var.get().strip()
        description = self.description_var.get().strip()
        reporter = self.reporter_var.get().strip()
        priority = self.priority_var.get()
        category = self.category_var.get()

        if not title or not reporter or not priority or not category:
            messagebox.showerror("Error", "Please fill in all required fields (*)")
            return

        c = self.conn.cursor()
        c.execute('''
            INSERT INTO incidents (title, description, reporter, priority, category, status, created_date)
            VALUES (?, ?, ?, ?, ?, 'Open', ?)
        ''', (title, description, reporter, priority, category, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
        messagebox.showinfo("Success", "Incident created successfully!")
        self.clear_create_form()
        self.load_incidents()
        self.load_reports()

    def clear_create_form(self):
        self.title_var.set('')
        self.description_var.set('')
        self.reporter_var.set('')
        self.priority_var.set('Medium')
        self.category_var.set('Software')

    # --- View Incidents Tab ---
    def create_view_tab(self):
        frame = self.tab_view

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="Refresh", command=self.load_incidents).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Update Status", command=self.update_status).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Assign Ticket", command=self.assign_ticket).pack(side='left', padx=5)

        # Treeview for incidents
        columns = ('ID', 'Title', 'Reporter', 'Priority', 'Category', 'Status', 'Assigned To', 'Created Date')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor='w')
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)

        # Incident details
        self.details_text = tk.Text(frame, height=10, state='disabled')
        self.details_text.pack(fill='x', padx=10, pady=5)

        self.tree.bind('<<TreeviewSelect>>', self.show_incident_details)

        self.load_incidents()

    def load_incidents(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        c = self.conn.cursor()
        c.execute('SELECT * FROM incidents ORDER BY created_date DESC')
        rows = c.fetchall()
        for r in rows:
            self.tree.insert('', 'end', values=(r['id'], r['title'], r['reporter'], r['priority'], r['category'], r['status'], r['assigned_to'] or 'Unassigned', r['created_date']))
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.config(state='disabled')

    def show_incident_details(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        incident_id = item['values'][0]
        c = self.conn.cursor()
        c.execute('SELECT * FROM incidents WHERE id=?', (incident_id,))
        r = c.fetchone()
        if r:
            details = f"Title: {r['title']}\n"
            details += f"Description: {r['description'] or 'N/A'}\n"
            details += f"Reporter: {r['reporter']}\n"
            details += f"Priority: {r['priority']}\n"
            details += f"Category: {r['category']}\n"
            details += f"Status: {r['status']}\n"
            details += f"Assigned To: {r['assigned_to'] or 'Unassigned'}\n"
            details += f"Created Date: {r['created_date']}\n"
            details += f"Updated Date: {r['updated_date'] or 'N/A'}\n"
            details += f"Resolved Date: {r['resolved_date'] or 'N/A'}\n"
            details += f"Resolution Notes: {r['resolution_notes'] or 'N/A'}\n"
            self.details_text.config(state='normal')
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert(tk.END, details)
            self.details_text.config(state='disabled')

    def get_selected_incident_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an incident first.")
            return None
        item = self.tree.item(selected[0])
        return item['values'][0]

    def update_status(self):
        incident_id = self.get_selected_incident_id()
        if incident_id is None:
            return
        c = self.conn.cursor()
        c.execute('SELECT status FROM incidents WHERE id=?', (incident_id,))
        current_status = c.fetchone()[0]
        new_status = simpledialog.askstring("Update Status", f"Current status: {current_status}\nEnter new status (Open/In-Progress/Resolved):")
        if new_status not in ('Open', 'In-Progress', 'Resolved'):
            messagebox.showerror("Error", "Invalid status! Use: Open, In-Progress, or Resolved")
            return
        resolution_notes = None
        resolved_date = None
        if new_status == 'Resolved':
            resolution_notes = simpledialog.askstring("Resolution Notes", "Enter resolution notes:")
            resolved_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            UPDATE incidents SET status=?, resolution_notes=?, resolved_date=?, updated_date=?
            WHERE id=?
        ''', (new_status, resolution_notes, resolved_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), incident_id))
        self.conn.commit()
        messagebox.showinfo("Success", "Incident status updated.")
        self.load_incidents()
        self.load_reports()

    def assign_ticket(self):
        incident_id = self.get_selected_incident_id()
        if incident_id is None:
            return
        assignee = simpledialog.askstring("Assign Ticket", "Assign to (technician name):")
        if not assignee:
            return
        c = self.conn.cursor()
        c.execute('UPDATE incidents SET assigned_to=?, updated_date=? WHERE id=?', (assignee, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), incident_id))
        self.conn.commit()
        messagebox.showinfo("Success", "Incident assigned.")
        self.load_incidents()
        self.load_reports()

    # --- Reports Tab ---
    def create_reports_tab(self):
        frame = self.tab_reports

        self.stats_frame = ttk.Frame(frame)
        self.stats_frame.pack(fill='x', padx=10, pady=10)

        self.report_text = tk.Text(frame, height=20, state='disabled')
        self.report_text.pack(fill='both', expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=10, pady=5)
        ttk.Button(btn_frame, text="Export Incidents to CSV", command=self.export_csv).pack(side='left', padx=5)

        self.load_reports()

    def load_reports(self):
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) FROM incidents')
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM incidents WHERE status='Open'")
        open_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM incidents WHERE status='In-Progress'")
        in_progress_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM incidents WHERE status='Resolved'")
        resolved_count = c.fetchone()[0]

        # Average resolution time in days
        c.execute("SELECT created_date, resolved_date FROM incidents WHERE status='Resolved' AND resolved_date IS NOT NULL")
        times = c.fetchall()
        avg_resolution = 'N/A'
        if times:
            total_days = 0
            for created, resolved in times:
                dt_created = datetime.strptime(created, '%Y-%m-%d %H:%M:%S')
                dt_resolved = datetime.strptime(resolved, '%Y-%m-%d %H:%M:%S')
                total_days += (dt_resolved - dt_created).days
            avg_resolution = f"{total_days / len(times):.1f} days"

        sla_compliance = f"{(resolved_count / total * 100):.1f}%" if total > 0 else '0%'

        # Clear previous stats
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        stats = [
            ('Total Incidents', total),
            ('Open', open_count),
            ('In Progress', in_progress_count),
            ('Resolved', resolved_count),
            ('Avg Resolution Time', avg_resolution),
            ('SLA Compliance', sla_compliance)
        ]

        for i, (label, value) in enumerate(stats):
            f = ttk.Frame(self.stats_frame, borderwidth=1, relief='solid', padding=10)
            f.grid(row=0, column=i, padx=5, sticky='nsew')
            ttk.Label(f, text=value, font=('Arial', 20, 'bold')).pack()
            ttk.Label(f, text=label).pack()

        # Generate detailed report text
        c.execute('SELECT * FROM incidents ORDER BY created_date DESC')
        incidents = c.fetchall()
        report_lines = []
        for inc in incidents:
            line = f"ID: {inc['id']} | Title: {inc['title']} | Status: {inc['status']} | Priority: {inc['priority']} | Assigned To: {inc['assigned_to'] or 'Unassigned'}"
            report_lines.append(line)

        self.report_text.config(state='normal')
        self.report_text.delete('1.0', tk.END)
        self.report_text.insert(tk.END, '\n'.join(report_lines))
        self.report_text.config(state='disabled')

    def export_csv(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM incidents ORDER BY created_date DESC')
        incidents = c.fetchall()
        if not incidents:
            messagebox.showinfo("Info", "No incidents to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')])
        if not file_path:
            return
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Title', 'Description', 'Reporter', 'Priority', 'Category', 'Status', 'Assigned To', 'Created Date', 'Updated Date', 'Resolved Date', 'Resolution Notes'])
            for inc in incidents:
                writer.writerow([
                    inc['id'], inc['title'], inc['description'], inc['reporter'], inc['priority'], inc['category'], inc['status'],
                    inc['assigned_to'] or '', inc['created_date'], inc['updated_date'] or '', inc['resolved_date'] or '', inc['resolution_notes'] or ''
                ])
        messagebox.showinfo("Success", f"Incidents exported to {file_path}")

    def on_closing(self):
        self.conn.close()
        self.destroy()

if __name__ == '__main__':
    init_db()
    app = IncidentTrackerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
