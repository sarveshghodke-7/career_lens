import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from typing import Optional, Dict, Any, List

from database import BaseDatabaseManager, SQLiteDatabaseManager
from ats_logic import (
    BaseTextExtractor,
    OcrTextExtractor,
    ResumeScoringEngine,
    AnalysisResult,
    CareerLensError,
    OcrExtractionError,
    AnalysisError
)

class AuthDialog(tk.Toplevel):
    """
    User Authentication Modal Dialog.
    Enables User Registration, Login, and Quick Demo Login for evaluation.
    """
    def __init__(self, parent: tk.Tk, db_manager: BaseDatabaseManager, on_login_success):
        super().__init__(parent)
        self.db_manager = db_manager
        self.on_login_success = on_login_success
        self.title("CareerLens - User Authentication")
        self.geometry("450x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Modern header
        header_frame = tk.Frame(self, bg="#1e3a8a", pady=15)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="CareerLens Authentication", font=("Segoe UI", 16, "bold"), fg="white", bg="#1e3a8a").pack()
        tk.Label(header_frame, text="Log in or register to track your resume scans", font=("Segoe UI", 9), fg="#93c5fd", bg="#1e3a8a").pack()

        # Tabs for Login vs Register
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=15, pady=10)

        self.login_frame = ttk.Frame(notebook, padding=15)
        self.register_frame = ttk.Frame(notebook, padding=15)

        notebook.add(self.login_frame, text="Login")
        notebook.add(self.register_frame, text="Register New User")

        self.build_login_tab()
        self.build_register_tab()

    def build_login_tab(self):
        tk.Label(self.login_frame, text="Email Address:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        self.login_email = tk.Entry(self.login_frame, font=("Segoe UI", 10), width=40)
        self.login_email.insert(0, "sanskar@jnec.edu")
        self.login_email.pack(fill="x", pady=(0, 10))

        tk.Label(self.login_frame, text="Password:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 2))
        self.login_password = tk.Entry(self.login_frame, font=("Segoe UI", 10), show="•", width=40)
        self.login_password.insert(0, "password123")
        self.login_password.pack(fill="x", pady=(0, 15))

        login_btn = tk.Button(self.login_frame, text="Log In", bg="#1e3a8a", fg="white",
                              font=("Segoe UI", 11, "bold"), cursor="hand2", command=self.handle_login)
        login_btn.pack(fill="x", pady=5)

        # Quick Demo Login Divider
        tk.Label(self.login_frame, text="── Or Quick Select Project Profile ──", fg="gray", font=("Segoe UI", 9)).pack(pady=10)

        demo_frame = tk.Frame(self.login_frame)
        demo_frame.pack(fill="x")

        tk.Button(demo_frame, text="Sanskar Shinde (Candidate)", bg="#f1f5f9", font=("Segoe UI", 9),
                  command=lambda: self.quick_login("sanskar@jnec.edu")).pack(fill="x", pady=2)
        tk.Button(demo_frame, text="Rohan Tarke (Candidate)", bg="#f1f5f9", font=("Segoe UI", 9),
                  command=lambda: self.quick_login("rohan@jnec.edu")).pack(fill="x", pady=2)
        tk.Button(demo_frame, text="Campus Recruiter (Recruiter)", bg="#f1f5f9", font=("Segoe UI", 9),
                  command=lambda: self.quick_login("recruiter@techcorp.com")).pack(fill="x", pady=2)
        tk.Button(demo_frame, text="System Admin (Admin)", bg="#f1f5f9", font=("Segoe UI", 9),
                  command=lambda: self.quick_login("admin@careerlens.ai")).pack(fill="x", pady=2)

    def build_register_tab(self):
        tk.Label(self.register_frame, text="Full Name:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.reg_name = tk.Entry(self.register_frame, font=("Segoe UI", 10))
        self.reg_name.pack(fill="x", pady=(0, 8))

        tk.Label(self.register_frame, text="Email Address:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.reg_email = tk.Entry(self.register_frame, font=("Segoe UI", 10))
        self.reg_email.pack(fill="x", pady=(0, 8))

        tk.Label(self.register_frame, text="Password:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.reg_password = tk.Entry(self.register_frame, font=("Segoe UI", 10), show="•")
        self.reg_password.pack(fill="x", pady=(0, 8))

        tk.Label(self.register_frame, text="User Role:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.reg_role = ttk.Combobox(self.register_frame, values=["candidate", "recruiter", "admin"], state="readonly")
        self.reg_role.set("candidate")
        self.reg_role.pack(fill="x", pady=(0, 15))

        reg_btn = tk.Button(self.register_frame, text="Create Account", bg="#16a34a", fg="white",
                            font=("Segoe UI", 10, "bold"), cursor="hand2", command=self.handle_register)
        reg_btn.pack(fill="x")

    def handle_login(self):
        email = self.login_email.get().strip()
        pwd = self.login_password.get()
        user = self.db_manager.authenticate_user(email, pwd)
        if user:
            messagebox.showinfo("Login Successful", f"Welcome back, {user['full_name']}!")
            self.on_login_success(user)
            self.destroy()
        else:
            messagebox.showerror("Login Failed", "Invalid email or password.")

    def quick_login(self, email: str):
        user = self.db_manager.authenticate_user(email, "password123")
        if not user:
            user = self.db_manager.authenticate_user(email, "admin123")
        if user:
            self.on_login_success(user)
            self.destroy()
        else:
            messagebox.showerror("Error", f"Could not authenticate demo user {email}")

    def handle_register(self):
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        pwd = self.reg_password.get()
        role = self.reg_role.get()

        if not name or not email or not pwd:
            messagebox.showwarning("Incomplete Form", "Please fill in all fields.")
            return

        try:
            user = self.db_manager.register_user(email=email, password=pwd, full_name=name, role=role)
            messagebox.showinfo("Registration Successful", f"Account created for {name} ({role})! Logging in now.")
            self.on_login_success(user)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Registration Error", str(e))


class CareerLensApp:
    """
    OOP Concept: Controller/Presentation Layer.
    Controls the GUI and integrates Vision, NLP, and normalized Relational Storage
    across all 5 3NF tables (users, resumes, job_descriptions, ats_history, skill_matches).
    """
    def __init__(self, root: tk.Tk, db_manager: BaseDatabaseManager, extractor: BaseTextExtractor, scoring_engine: ResumeScoringEngine):
        self.root = root
        self.root.title("CareerLens - AI Resume Scorer & Skill Gap Analyzer")
        self.root.geometry("820x880")
        self.root.minsize(760, 780)

        # Injected Dependencies
        self.db_manager = db_manager
        self.extractor = extractor
        self.scoring_engine = scoring_engine

        self.selected_file_path = None
        self.canvas_widget = None

        # Authenticate default demo user initially
        default_user = self.db_manager.authenticate_user("sanskar@jnec.edu", "password123")
        if not default_user:
            users = self.db_manager.get_all_users()
            self.current_user = users[0] if users else None
        else:
            self.current_user = default_user

        # Top User Status & Navigation Bar
        self.build_top_nav_bar()

        # Tabbed Main Interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)

        # Tab 1: AI Resume Analyzer
        self.tab_analyzer = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_analyzer, text="  AI Resume Analyzer  ")

        # Tab 2: Analytics Dashboard
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text="  Analytics Dashboard  ")

        # Tab 3: DBMS Table Inspector (3NF Verification)
        self.tab_dbms = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dbms, text="  DBMS 5-Table Inspector  ")

        self.build_analyzer_tab()
        self.build_dashboard_tab()
        self.build_dbms_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def build_top_nav_bar(self):
        """Builds top bar displaying logged-in user and switch account button."""
        self.nav_frame = tk.Frame(self.root, bg="#1e3a8a", padx=15, pady=8)
        self.nav_frame.pack(fill="x")

        # Left: App Brand
        brand_label = tk.Label(self.nav_frame, text="CareerLens", font=("Segoe UI", 14, "bold"), fg="white", bg="#1e3a8a")
        brand_label.pack(side="left")

        tagline = tk.Label(self.nav_frame, text="| CV/Resume Analyser (DBMS Project)", font=("Segoe UI", 9), fg="#93c5fd", bg="#1e3a8a")
        tagline.pack(side="left", padx=(5, 0))

        # Right: User info & Switch/Login button
        self.user_label = tk.Label(self.nav_frame, font=("Segoe UI", 9, "bold"), fg="white", bg="#1e3a8a")
        self.user_label.pack(side="right", padx=(10, 0))

        auth_btn = tk.Button(self.nav_frame, text="Switch User / Login", font=("Segoe UI", 8, "bold"),
                             bg="#3b82f6", fg="white", relief="flat", padx=8, cursor="hand2", command=self.open_auth_dialog)
        auth_btn.pack(side="right")

        self.update_user_display()

    def update_user_display(self):
        if self.current_user:
            role_badge = f"({self.current_user['role'].capitalize()})"
            self.user_label.config(text=f"👤 {self.current_user['full_name']} {role_badge}")
        else:
            self.user_label.config(text="👤 Guest Mode (Not logged in)")

    def open_auth_dialog(self):
        AuthDialog(self.root, self.db_manager, self.on_login_success)

    def on_login_success(self, user: Dict[str, Any]):
        self.current_user = user
        self.update_user_display()
        self.draw_chart()
        self.load_dbms_table_data()

    def build_analyzer_tab(self) -> None:
        frame = tk.Frame(self.tab_analyzer, padx=15, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="CareerLens Resume-Skill Analysis", font=("Segoe UI", 16, "bold"), fg="#1e3a8a").pack(anchor="w")
        tk.Label(frame, text="Ingests visual resume, extracts text via OCR, and calculates exact & semantic ATS compatibility.",
                 font=("Segoe UI", 9), fg="gray").pack(anchor="w", pady=(0, 10))

        # Target Job Title Field
        meta_frame = tk.Frame(frame)
        meta_frame.pack(fill="x", pady=2)
        tk.Label(meta_frame, text="Target Job Title:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.jd_title_entry = tk.Entry(meta_frame, font=("Segoe UI", 9), width=35)
        self.jd_title_entry.insert(0, "Backend Software Engineer")
        self.jd_title_entry.pack(side="left", padx=10)

        tk.Label(meta_frame, text="Target Company:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(10, 0))
        self.jd_company_entry = tk.Entry(meta_frame, font=("Segoe UI", 9), width=25)
        self.jd_company_entry.insert(0, "TechCorp Global")
        self.jd_company_entry.pack(side="left", padx=10)

        # Job Description Text Box
        tk.Label(frame, text="Paste Target Job Description (JD):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 2))
        self.jd_text = tk.Text(frame, height=7, width=80, font=("Segoe UI", 9))
        self.jd_text.pack(fill="x", pady=2)

        # Default sample JD
        default_jd = (
            "We are seeking a Backend Software Engineer. Strong experience with Python, Django, REST APIs, "
            "and PostgreSQL database management is required. Candidates must have experience with AWS cloud "
            "infrastructure, Git version control, and scalable system deployment."
        )
        self.jd_text.insert(tk.END, default_jd)

        # Resume File Ingestion Frame
        tk.Label(frame, text="Upload Resume (Image File):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))

        file_frame = tk.Frame(frame, bg="#f8fafc", bd=1, relief="groove", padx=10, pady=8)
        file_frame.pack(fill="x", pady=3)

        self.file_btn = tk.Button(file_frame, text="📁 Choose Resume Image", bg="#e2e8f0",
                                  font=("Segoe UI", 9, "bold"), cursor="hand2", command=self.browse_file)
        self.file_btn.pack(side="left")

        self.file_label = tk.Label(file_frame, text="No file selected (Supports .png, .jpg, .jpeg)", fg="gray", bg="#f8fafc", font=("Segoe UI", 9))
        self.file_label.pack(side="left", padx=12)

        # Quick Select Sample Image Button if backend_engineer.png exists
        if os.path.exists("backend_engineer.png"):
            sample_btn = tk.Button(file_frame, text="Load Sample Resume", font=("Segoe UI", 8), bg="#dbeafe",
                                   command=lambda: self.select_sample_file("backend_engineer.png"))
            sample_btn.pack(side="right")

        # Action Analyze Button
        self.analyze_btn = tk.Button(frame, text="🚀 Analyze & Calculate ATS Score (Persist to 5 Tables)",
                                     bg="#1e3a8a", fg="white", font=("Segoe UI", 11, "bold"),
                                     cursor="hand2", pady=8, command=self.run_analysis)
        self.analyze_btn.pack(pady=12, fill="x")

        # Results Display Text Box
        tk.Label(frame, text="Analysis & Diagnostic Results:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.results_text = tk.Text(frame, height=13, width=80, state="disabled", bg="#f8fafc",
                                    font=("Consolas", 9), padx=8, pady=8)
        self.results_text.pack(fill="both", expand=True, pady=3)

    def select_sample_file(self, filename: str):
        full_path = os.path.abspath(filename)
        if os.path.exists(full_path):
            self.selected_file_path = full_path
            self.file_label.config(text=f"Selected: {os.path.basename(full_path)}", fg="#1e3a8a")

    def build_dashboard_tab(self) -> None:
        self.dash_frame = tk.Frame(self.tab_dashboard, padx=15, pady=10)
        self.dash_frame.pack(fill="both", expand=True)

        header_box = tk.Frame(self.dash_frame)
        header_box.pack(fill="x", pady=(0, 10))

        tk.Label(header_box, text="ATS Performance Analytics & Scan History",
                 font=("Segoe UI", 16, "bold"), fg="#1e3a8a").pack(side="left")

        self.clear_btn = tk.Button(header_box, text="🗑️ Clear Scan History", bg="#ef4444", fg="white",
                                   font=("Segoe UI", 9, "bold"), cursor="hand2", padx=8, command=self.clear_history)
        self.clear_btn.pack(side="right")

        # Container for Matplotlib Chart
        self.chart_container = tk.Frame(self.dash_frame, height=260)
        self.chart_container.pack(fill="x", pady=5)

        # Scan History Table Section
        tk.Label(self.dash_frame, text="Recent Scans & Granular Diagnostics (from ats_history & skill_matches):",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))

        table_frame = tk.Frame(self.dash_frame)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "filename", "score", "exact", "semantic", "missing", "job_title", "date")
        self.history_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=6)

        self.history_tree.heading("id", text="Scan ID")
        self.history_tree.heading("filename", text="Resume File")
        self.history_tree.heading("score", text="ATS Score")
        self.history_tree.heading("exact", text="Exact Matches")
        self.history_tree.heading("semantic", text="Semantic Matches")
        self.history_tree.heading("missing", text="Missing Skills")
        self.history_tree.heading("job_title", text="Target Job")
        self.history_tree.heading("date", text="Scan Timestamp")

        self.history_tree.column("id", width=60, anchor="center")
        self.history_tree.column("filename", width=140)
        self.history_tree.column("score", width=80, anchor="center")
        self.history_tree.column("exact", width=95, anchor="center")
        self.history_tree.column("semantic", width=110, anchor="center")
        self.history_tree.column("missing", width=90, anchor="center")
        self.history_tree.column("job_title", width=130)
        self.history_tree.column("date", width=140, anchor="center")

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=tree_scroll.set)

        self.history_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self.history_tree.bind("<Double-1>", self.on_history_row_double_click)

        self.draw_chart()

    def build_dbms_tab(self) -> None:
        """
        Builds Tab 3: DBMS 5-Table Inspector.
        Provides live academic demonstration of all 5 tables in Third Normal Form (3NF).
        """
        frame = tk.Frame(self.tab_dbms, padx=15, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="DBMS Lab: 5 Relational Tables Inspector (3NF)",
                 font=("Segoe UI", 16, "bold"), fg="#1e3a8a").pack(anchor="w")
        tk.Label(frame, text="Select any normalized entity to inspect its live records, primary/foreign keys, and constraints.",
                 font=("Segoe UI", 9), fg="gray").pack(anchor="w", pady=(0, 10))

        ctrl_frame = tk.Frame(frame)
        ctrl_frame.pack(fill="x", pady=5)

        tk.Label(ctrl_frame, text="Select Table Entity:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.table_selector = ttk.Combobox(
            ctrl_frame,
            values=["users", "resumes", "job_descriptions", "ats_history", "skill_matches"],
            state="readonly",
            width=22,
            font=("Segoe UI", 10)
        )
        self.table_selector.set("users")
        self.table_selector.pack(side="left", padx=10)

        refresh_btn = tk.Button(ctrl_frame, text="🔄 Query Table Data", bg="#3b82f6", fg="white",
                                font=("Segoe UI", 9, "bold"), cursor="hand2", command=self.load_dbms_table_data)
        refresh_btn.pack(side="left", padx=5)

        self.table_status_label = tk.Label(ctrl_frame, text="", font=("Segoe UI", 9, "italic"), fg="#1e3a8a")
        self.table_status_label.pack(side="left", padx=15)

        # Table data view
        self.dbms_tree_frame = tk.Frame(frame)
        self.dbms_tree_frame.pack(fill="both", expand=True, pady=10)

        self.dbms_tree = None
        self.load_dbms_table_data()

    def load_dbms_table_data(self):
        """Loads and displays records from the selected table in Tab 3."""
        table_name = self.table_selector.get()
        if not table_name:
            return

        try:
            data = self.db_manager.get_table_records(table_name, limit=100)
            columns = data["columns"]
            rows = data["rows"]
            total = data["total_count"]

            self.table_status_label.config(text=f"Table: {table_name} | Total Records: {total} | 3NF Schema")

            # Rebuild Treeview with appropriate columns
            for widget in self.dbms_tree_frame.winfo_children():
                widget.destroy()

            tree = ttk.Treeview(self.dbms_tree_frame, columns=columns, show="headings")
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor="w")

            for row in rows:
                values = [str(row.get(col, "")) for col in columns]
                tree.insert("", "end", values=values)

            scroll_y = ttk.Scrollbar(self.dbms_tree_frame, orient="vertical", command=tree.yview)
            scroll_x = ttk.Scrollbar(self.dbms_tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

            tree.pack(side="top", fill="both", expand=True)
            scroll_y.pack(side="right", fill="y")
            scroll_x.pack(side="bottom", fill="x")

        except Exception as e:
            messagebox.showerror("DBMS Query Error", f"Failed to load table {table_name}:\n{str(e)}")

    def draw_chart(self) -> None:
        """Fetches score history and renders the Matplotlib performance line chart."""
        history = self.db_manager.get_score_history()

        # Update table rows
        if hasattr(self, "history_tree"):
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            for row in reversed(history):  # newest first in table
                self.history_tree.insert("", "end", values=(
                    row["id"],
                    row["filename"],
                    f"{row['score']}%",
                    row.get("exact_count", 0),
                    row.get("semantic_count", 0),
                    row.get("missing_count", 0),
                    row.get("job_title") or "N/A",
                    row.get("created_at", "")
                ))

        # Clear old chart widget if it exists
        if self.canvas_widget:
            self.canvas_widget.destroy()
            self.canvas_widget = None

        if not history:
            for widget in self.chart_container.winfo_children():
                widget.destroy()
            lbl = tk.Label(self.chart_container, text="No scan data available yet. Analyze a resume to see performance trends!",
                           fg="gray", font=("Segoe UI", 10))
            lbl.pack(pady=40)
            return

        for widget in self.chart_container.winfo_children():
            widget.destroy()

        labels = [row['filename'][:10] + "..." if len(row['filename']) > 10 else row['filename'] for row in history]
        scores = [row['score'] for row in history]

        fig = Figure(figsize=(7, 2.7), dpi=100)
        ax = fig.add_subplot(111)

        x_indices = list(range(len(scores)))
        ax.plot(x_indices, scores, marker='o', linestyle='-', color='#1e3a8a', linewidth=2, markersize=7)
        ax.set_ylim(0, 100)
        ax.set_ylabel('ATS Score (%)', fontsize=9)
        ax.set_title('Recent ATS Scans Performance Trajectory', fontsize=10, fontweight="bold")
        ax.grid(True, linestyle='--', alpha=0.5)

        ax.set_xticks(x_indices)
        ax.set_xticklabels(labels, fontsize=8)
        fig.autofmt_xdate(rotation=35)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

    def on_history_row_double_click(self, event):
        """Shows detailed skill matches breakdown when double-clicking a history item."""
        selected = self.history_tree.selection()
        if not selected:
            return
        item_vals = self.history_tree.item(selected[0], "values")
        scan_id = int(item_vals[0])

        details = self.db_manager.get_scan_details(scan_id)
        if not details:
            messagebox.showinfo("Scan Details", f"No detailed skill records found for Scan ID {scan_id}.")
            return

        # Modal window with detailed skills
        popup = tk.Toplevel(self.root)
        popup.title(f"Scan Details (ID #{scan_id}) - {details['filename']}")
        popup.geometry("520x450")
        popup.transient(self.root)

        tk.Label(popup, text=f"Scan #{scan_id}: {details['filename']}", font=("Segoe UI", 12, "bold"), fg="#1e3a8a").pack(pady=(10, 2))
        tk.Label(popup, text=f"Target Job: {details.get('job_title') or 'N/A'} | ATS Score: {details['score']}%", font=("Segoe UI", 10)).pack(pady=(0, 10))

        match_frame = tk.Frame(popup, padx=10, pady=5)
        match_frame.pack(fill="both", expand=True)

        cols = ("keyword", "match_type", "similarity_score")
        tree = ttk.Treeview(match_frame, columns=cols, show="headings", height=12)
        tree.heading("keyword", text="Keyword / Skill")
        tree.heading("match_type", text="Match Type")
        tree.heading("similarity_score", text="Similarity (0-1)")

        tree.column("keyword", width=200)
        tree.column("match_type", width=120, anchor="center")
        tree.column("similarity_score", width=120, anchor="center")

        for m in details.get("matches", []):
            tree.insert("", "end", values=(m["keyword"], m["match_type"].upper(), f"{m['similarity_score']:.2f}"))

        scroll = ttk.Scrollbar(match_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def on_tab_changed(self, event) -> None:
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 1:
            self.draw_chart()
        elif selected_tab == 2:
            self.load_dbms_table_data()

    def clear_history(self) -> None:
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to delete all resume scan history?\n(This will delete records from ats_history and skill_matches)."):
            try:
                self.db_manager.clear_history()
                messagebox.showinfo("Success", "Scan history and skill match diagnostics cleared successfully!")
                self.draw_chart()
                self.load_dbms_table_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {str(e)}")

    def browse_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select Resume Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if filename:
            self.selected_file_path = filename
            self.file_label.config(text=f"Selected: {os.path.basename(filename)}", fg="#1e3a8a")

    def run_analysis(self) -> None:
        job_description = self.jd_text.get("1.0", tk.END).strip()
        job_title = self.jd_title_entry.get().strip() or "General Role"
        job_company = self.jd_company_entry.get().strip() or "Target Organization"

        if not job_description:
            messagebox.showwarning("Input Error", "Please paste or enter the target job description.")
            return
        if not self.selected_file_path:
            messagebox.showwarning("Input Error", "Please select a resume image file.")
            return

        self.analyze_btn.config(text="Processing with Vision & NLP... Please wait.", state="disabled")
        self.root.update()

        try:
            # 1. OCR Text Extraction via polymorphic BaseTextExtractor
            resume_text = self.extractor.extract_text(self.selected_file_path)

            # 2. NLP Scoring Engine (exact + semantic vector similarity)
            result = self.scoring_engine.calculate_ats_score(resume_text, job_description)

            # 3. 3NF Relational Persistence across tables
            user_id = self.current_user["user_id"] if self.current_user else None
            filename = os.path.basename(self.selected_file_path)

            # Save to resumes table
            resume_id = self.db_manager.save_resume(
                user_id=user_id,
                file_name=filename,
                file_path=self.selected_file_path,
                raw_text=resume_text
            )

            # Save to job_descriptions table
            jd_id = self.db_manager.save_job_description(
                user_id=user_id,
                title=job_title,
                company=job_company,
                raw_text=job_description
            )

            # Save to ats_history and skill_matches tables
            history_id = self.db_manager.save_result(
                filename=filename,
                score=result.score,
                resume_id=resume_id,
                jd_id=jd_id,
                exact_matches=result.exact_matches,
                semantic_matches=result.semantic_matches,
                missing_keywords=result.missing_keywords
            )

            # 4. Display results in UI
            self.display_results(result, history_id)

        except OcrExtractionError as ocr_err:
            messagebox.showerror("OCR Error", f"Failed to extract text from image:\n{str(ocr_err)}")
        except AnalysisError as anal_err:
            messagebox.showerror("Analysis Error", f"Failed to analyze resume:\n{str(anal_err)}")
        except CareerLensError as cl_err:
            messagebox.showerror("App Error", f"A CareerLens system error occurred:\n{str(cl_err)}")
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n{str(e)}")
        finally:
            self.analyze_btn.config(text="🚀 Analyze & Calculate ATS Score (Persist to 5 Tables)", state="normal")

    def display_results(self, result: AnalysisResult, history_id: int) -> None:
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)

        exact_str = ", ".join(result.exact_matches[:12]) if result.exact_matches else "None"
        semantic_str = ", ".join(result.semantic_matches[:12]) if result.semantic_matches else "None"
        missing_str = ", ".join(result.missing_keywords[:12]) if result.missing_keywords else "None"

        user_name = self.current_user["full_name"] if self.current_user else "Guest"

        result_content = "========================================================================\n"
        result_content += f"              CAREERLENS AI NLP ANALYSIS COMPLETE (Scan #{history_id})\n"
        result_content += f"              Evaluated For: {user_name} | Score: {result.score}%\n"
        result_content += "========================================================================\n\n"
        result_content += f"📊 ATS COMPATIBILITY SCORE : {result.score}%\n"
        result_content += f"✅ EXACT MATCHES ({len(result.exact_matches)}):\n   {exact_str}\n\n"
        result_content += f"🤖 SEMANTIC AI MATCHES ({len(result.semantic_matches)}):\n   {semantic_str}\n\n"
        result_content += f"⚠️ MISSING CRITICAL SKILLS ({len(result.missing_keywords)}):\n   {missing_str}\n\n"
        result_content += "------------------------------------------------------------------------\n"
        result_content += "💾 RELATIONAL STORAGE CONFIRMATION (3NF):\n"
        result_content += f" • Table [resumes]: Stored image metadata and extracted raw text.\n"
        result_content += f" • Table [job_descriptions]: Stored target role specifications.\n"
        result_content += f" • Table [ats_history]: Inserted record ID #{history_id} with score {result.score}%.\n"
        result_content += f" • Table [skill_matches]: Recorded {len(result)} keyword items (exact/semantic/missing).\n"
        result_content += "========================================================================\n"

        self.results_text.insert(tk.END, result_content)
        self.results_text.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()

    # Dependency Injection
    db_manager = SQLiteDatabaseManager()
    extractor = OcrTextExtractor()
    scoring_engine = ResumeScoringEngine()

    app = CareerLensApp(root, db_manager=db_manager, extractor=extractor, scoring_engine=scoring_engine)
    root.mainloop()