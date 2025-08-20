import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.database import Database
from utils.logging import log_info, log_debug, log_error
from styles import apply_styles
from datetime import datetime
from utils.ui_helpers import create_greeting_label, create_navigation_bar

class DashboardPage(tk.Frame):
    def __init__(self, parent, switch_page_callback, user_id):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.user_id = user_id
        self.db = Database()
        self.trans_visible = True  # Track visibility of transactions
        apply_styles()
        self.init_ui()

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Greeting label
        welcome_label = create_greeting_label(self, self.db, self.user_id)
        welcome_label.grid(row=0, column=0, sticky='e', padx=10, pady=(10,0))

        # Time period selection frame
        period_frame = ttk.Frame(self)
        period_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        ttk.Label(period_frame, text="Select Period:").pack(side=tk.LEFT, padx=5)
        self.period_var = tk.StringVar(value="Month")
        period_menu = ttk.OptionMenu(period_frame, self.period_var, "Month", "Day", "Week", "Month", "Year", 
                                   command=self.update_content)
        period_menu.pack(side=tk.LEFT, padx=5)
        # Toggle button for recent transactions
        self.toggle_trans_button = ttk.Button(period_frame, text="Hide Transactions", command=self.toggle_transactions)
        self.toggle_trans_button.pack(side=tk.LEFT, padx=5)

        balance_frame = ttk.Frame(self)
        balance_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.balance_label = ttk.Label(balance_frame, text="Balance: Calculating...")
        self.balance_label.pack()
        
        totals_frame = ttk.Frame(self)
        totals_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.totals_label = ttk.Label(totals_frame, text="Totals: Calculating...")
        self.totals_label.pack()

        chart_frame = ttk.Frame(self)
        chart_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        chart_frame.grid_columnconfigure(0, weight=1)
        chart_frame.grid_columnconfigure(1, weight=1)
        chart_frame.grid_rowconfigure(0, weight=1)

        self.fig_pie, ax_pie = plt.subplots(figsize=(4, 2))
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=chart_frame)
        self.canvas_pie.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5)

        self.fig_bar, ax_bar = plt.subplots(figsize=(4, 2))
        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=chart_frame)
        self.canvas_bar.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5)

        self.trans_frame = ttk.Frame(self)
        self.trans_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        self.trans_frame.grid_columnconfigure(0, weight=1)
        self.trans_frame.grid_rowconfigure(1, weight=1)
        ttk.Label(self.trans_frame, text="Recent Transactions", font=("Arial", 14)).grid(row=0, column=0, pady=5)
        self.tree = ttk.Treeview(self.trans_frame, columns=("Date", "Type", "Category", "Amount", "Mode", "Details"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Amount", text="Amount (KSh)")
        self.tree.heading("Mode", text="Mode")
        self.tree.heading("Details", text="Details")
        self.tree.column("Date", width=int(self.winfo_screenwidth() * 0.1))
        self.tree.column("Type", width=int(self.winfo_screenwidth() * 0.1))
        self.tree.column("Category", width=int(self.winfo_screenwidth() * 0.1))
        self.tree.column("Amount", width=int(self.winfo_screenwidth() * 0.1))
        self.tree.column("Mode", width=int(self.winfo_screenwidth() * 0.1))
        self.tree.column("Details", width=int(self.winfo_screenwidth() * 0.1))
        self.tree.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.trans_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        nav_frame = create_navigation_bar(self, self.switch_page_callback, current_page='Dashboard', planning_enabled=self.is_planning_enabled())
        nav_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        
        self.update_content()

    def is_planning_enabled(self):
        enabled = self.db.is_planning_enabled(self.user_id)
        log_debug(self.user_id, f"Checked planning enabled: {enabled}")
        return enabled

    def toggle_transactions(self):
        self.trans_visible = not self.trans_visible
        if self.trans_visible:
            self.trans_frame.grid()
            self.toggle_trans_button.config(text="Hide Transactions")
        else:
            self.trans_frame.grid_remove()
            self.toggle_trans_button.config(text="Show Transactions")
        log_info(self.user_id, f"Transactions visibility toggled to: {self.trans_visible}")

    def update_content(self, *args):
        try:
            period = self.period_var.get()
            transactions = self.db.get_transactions(self.user_id, period)
            cash_balance, mpesa_balance, income_total, expenses_total, savings_total = 0, 0, 0, 0, 0
            category_totals = {"Income": {}, "Expenses": {}, "Savings": {}}

            for trans in transactions:
                amount, mode, type, category = trans[4], trans[5], trans[2], trans[3]
                if type == "Income":
                    income_total += amount
                    category_totals["Income"][category] = category_totals["Income"].get(category, 0) + amount
                    if mode == "Cash":
                        cash_balance += amount
                    else:
                        mpesa_balance += amount
                elif type == "Expenses":
                    expenses_total += amount
                    category_totals["Expenses"][category] = category_totals["Expenses"].get(category, 0) + amount
                    if mode == "Cash":
                        cash_balance -= amount
                    else:
                        mpesa_balance -= amount
                else:
                    savings_total += amount
                    category_totals["Savings"][category] = category_totals["Savings"].get(category, 0) + amount
                    if mode == "Cash":
                        cash_balance -= amount
                    else:
                        mpesa_balance -= amount
            self.balance_label.config(text=f"Balance: Mpesa KSh {mpesa_balance:,}  Cash KSh {cash_balance:,}  Total KSh {mpesa_balance + cash_balance:,}")
            self.totals_label.config(text=f"Income: KSh {income_total:,}  Expenses: KSh {expenses_total:,}  Savings: KSh {savings_total:,}")

            self.fig_pie.clear()
            ax = self.fig_pie.add_subplot(111)
            if period == "Day":
                labels = []
                sizes = []
                colors = []
                for type, categories in category_totals.items():
                    type_colors = {"Income": "green", "Expenses": "red", "Savings": "blue"}
                    for category, amount in categories.items():
                        if amount > 0:
                            labels.append(f"{type}: {category}")
                            sizes.append(amount)
                            colors.append(type_colors[type])
                sizes = [s if s > 0 else 0.01 for s in sizes]
                ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
            else:
                labels = ["Income", "Expenses", "Savings"]
                sizes = [income_total, expenses_total, savings_total]
                sizes = [s if s > 0 else 0.01 for s in sizes]
                ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
            ax.set_title(f"{period} Breakdown")
            self.canvas_pie.draw()

            if period == "Day":
                trends = self.db.get_daily_trends(self.user_id)
                x_axis = [t[0] for t in trends]
                balances = [t[4] for t in trends]
                x_label = "Hour"
                title = "Daily Balance Trends"
            elif period == "Week":
                trends = self.db.get_weekly_trends(self.user_id)
                x_axis = [t[0] for t in trends]
                balances = [t[4] for t in trends]
                x_label = "Day"
                title = "Weekly Balance Trends"
            elif period == "Month":
                trends = self.db.get_monthly_trends(self.user_id)
                x_axis = [t[0] for t in trends]
                balances = [t[4] for t in trends]
                x_label = "Month"
                title = "Monthly Balance Trends"
            else:  # Year
                trends = self.db.get_yearly_trends(self.user_id)
                x_axis = [t[0] for t in trends]
                balances = [t[4] for t in trends]
                x_label = "Year"
                title = "Yearly Balance Trends"

            self.fig_bar.clear()
            ax = self.fig_bar.add_subplot(111)
            ax.bar(x_axis, balances, color="blue")
            ax.set_xlabel(x_label)
            ax.set_ylabel("Balance (KSh)")
            ax.set_title(title)
            self.fig_bar.tight_layout()
            self.canvas_bar.draw()

            self.tree.delete(*self.tree.get_children())
            # Use get_transactions with period filter and limit to 5 for recent transactions
            recent = self.db.get_transactions(self.user_id, period, category="All", mode="All", start_date=None, end_date=None)[:5]
            for trans in recent:
                date, type, category, amount, mode, details = trans[1:7]
                self.tree.insert("", "end", values=(date, type, category, f"KSh {amount:,}", mode, details))
            log_info(self.user_id, f"Updated Dashboard for {period}: {len(recent)} recent transactions")
        except Exception as e:
            log_error(self.user_id, f"Error updating dashboard content: {str(e)}")
            messagebox.showerror("Error", f"Failed to update dashboard: {str(e)}")
