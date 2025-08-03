import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.database import Database
from utils.logging import log_info, log_debug
from styles import apply_styles

class DashboardPage(tk.Frame):
    def __init__(self, parent, switch_page_callback, user_id):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.user_id = user_id
        self.db = Database()
        apply_styles()
        self.init_ui()

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        balance_frame = ttk.Frame(self)
        balance_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.balance_label = ttk.Label(balance_frame, text="Balance: Calculating...")
        self.balance_label.pack()
        
        totals_frame = ttk.Frame(self)
        totals_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.totals_label = ttk.Label(totals_frame, text="Totals: Calculating...")
        self.totals_label.pack()

        chart_frame = ttk.Frame(self)
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_columnconfigure(1, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        self.fig_pie, ax_pie = plt.subplots(figsize=(4, 2))
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=chart_frame)
        self.canvas_pie.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5)

        self.fig_bar, ax_bar = plt.subplots(figsize=(4, 2))
        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=chart_frame)
        self.canvas_bar.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5)

        trans_frame = ttk.Frame(self)
        trans_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        trans_frame.grid_columnconfigure(0, weight=1)
        trans_frame.grid_rowconfigure(1, weight=1)
        ttk.Label(trans_frame, text="Recent Transactions", font=("Arial", 14)).grid(row=0, column=0, pady=5)
        self.tree = ttk.Treeview(trans_frame, columns=("Date", "Type", "Category", "Amount", "Mode", "Details"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Amount", text="Amount (KSh)")
        self.tree.heading("Mode", text="Mode")
        self.tree.heading("Details", text="Details")
        self.tree.column("Date", width=100)
        self.tree.column("Type", width=100)
        self.tree.column("Category", width=150)
        self.tree.column("Amount", width=150)
        self.tree.column("Mode", width=100)
        self.tree.column("Details", width=200)
        self.tree.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(trans_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        ttk.Button(nav_frame, text="Dashboard", style="Success.TButton").pack(side=tk.LEFT, padx=5)
        if self.is_planning_enabled():
            ttk.Button(nav_frame, text="Planning", command=lambda: self.switch_page_callback("Planning")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Tracking", command=lambda: self.switch_page_callback("Tracking")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Settings", command=lambda: self.switch_page_callback("Settings")).pack(side=tk.LEFT, padx=5)

        self.update_content()

    def is_planning_enabled(self):
        enabled = self.db.is_planning_enabled(self.user_id)
        log_debug(self.user_id, f"Checked planning enabled: {enabled}")
        return enabled

    def update_content(self):
        transactions = self.db.get_transactions(self.user_id, "Month")
        cash_balance, mpesa_balance, income_total, expenses_total, savings_total = 0, 0, 0, 0, 0
        for trans in transactions:
            amount, mode, type = trans[4], trans[5], trans[2]
            if type == "Income":
                income_total += amount
                if mode == "Cash":
                    cash_balance += amount
                else:
                    mpesa_balance += amount
            elif type == "Expenses":
                expenses_total += amount
                if mode == "Cash":
                    cash_balance -= amount
                else:
                    mpesa_balance -= amount
            else:
                savings_total += amount
                if mode == "Cash":
                    cash_balance -= amount
                else:
                    mpesa_balance -= amount
        self.balance_label.config(text=f"Balance: Mpesa KSh {mpesa_balance:,}  Cash KSh {cash_balance:,}  Total KSh {mpesa_balance + cash_balance:,}")
        self.totals_label.config(text=f"Income: KSh {income_total:,}  Expenses: KSh {expenses_total:,}  Savings: KSh {savings_total:,}")

        labels = ["Income", "Expenses", "Savings"]
        sizes = [income_total, expenses_total, savings_total]
        sizes = [s if s > 0 else 0.01 for s in sizes]
        self.fig_pie.clear()
        ax = self.fig_pie.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        self.canvas_pie.draw()

        trends = self.db.get_monthly_trends(self.user_id)
        months = [t[0] for t in trends]
        balances = [t[4] for t in trends]
        self.fig_bar.clear()
        ax = self.fig_bar.add_subplot(111)
        ax.bar(months, balances, color="blue")
        ax.set_ylabel("Balance (KSh)")
        ax.set_title("Monthly Balance Trends")
        self.fig_bar.tight_layout()
        self.canvas_bar.draw()

        self.tree.delete(*self.tree.get_children())
        recent = self.db.get_recent_transactions(self.user_id)
        for trans in recent:
            date, type, category, amount, mode, details = trans
            self.tree.insert("", "end", values=(date, type, category, f"KSh {amount:,}", mode, details))
        log_info(self.user_id, f"Updated Dashboard: {len(recent)} recent transactions")