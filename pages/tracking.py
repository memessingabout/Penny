import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from utils.database import Database
from utils.logging import log_info, log_error, log_debug
from styles import apply_styles

class TrackingPage(tk.Frame):
    def __init__(self, parent, switch_page_callback, user_id):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.user_id = user_id
        self.db = Database()
        apply_styles()
        self.init_ui()

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        balance_frame = ttk.Frame(self)
        balance_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.balance_label = ttk.Label(balance_frame, text="Balance: Calculating...")
        self.balance_label.pack()

        totals_frame = ttk.Frame(self)
        totals_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.totals_label = ttk.Label(totals_frame, text="Totals: Calculating...")
        self.totals_label.pack()

        control_frame = ttk.Frame(self)
        control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        ttk.Button(control_frame, text="New Record", style="Success.TButton", command=self.open_new_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Quick Add", command=self.quick_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Undo Delete", command=self.undo_delete).pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(control_frame, textvariable=self.filter_var, values=["All", "Today", "Week", "Month", "Year", "Range"], state="readonly").pack(side=tk.LEFT, padx=5)
        self.start_date = DateEntry(control_frame, date_pattern="mm/dd/yyyy")
        self.start_date.pack(side=tk.LEFT, padx=5)
        self.end_date = DateEntry(control_frame, date_pattern="mm/dd/yyyy")
        self.end_date.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Apply Filter", command=self.update_content).pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(control_frame, text="Showing transactions for: All")
        self.status_label.pack(side=tk.LEFT, padx=5)

        table_frame = ttk.Frame(self)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=("Date", "Type", "Category", "Amount", "Mode", "Details", "Actions"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Amount", text="Amount (KSh)")
        self.tree.heading("Mode", text="Mode")
        self.tree.heading("Details", text="Details")
        self.tree.heading("Actions", text="Actions")
        self.tree.column("Date", width=100)
        self.tree.column("Type", width=100)
        self.tree.column("Category", width=150)
        self.tree.column("Amount", width=150)
        self.tree.column("Mode", width=100)
        self.tree.column("Details", width=200)
        self.tree.column("Actions", width=100)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        ttk.Button(nav_frame, text="Dashboard", command=lambda: self.switch_page_callback("Dashboard")).pack(side=tk.LEFT, padx=5)
        if self.is_planning_enabled():
            ttk.Button(nav_frame, text="Planning", command=lambda: self.switch_page_callback("Planning")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Tracking", style="Success.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Settings", command=lambda: self.switch_page_callback("Settings")).pack(side=tk.LEFT, padx=5)

        self.update_content()

    def is_planning_enabled(self):
        enabled = self.db.is_planning_enabled(self.user_id)
        log_debug(self.user_id, f"Checked planning enabled: {enabled}")
        return enabled

    def update_content(self):
        self.tree.delete(*self.tree.get_children())
        date_filter = self.filter_var.get()
        start_date = self.start_date.get() if date_filter == "Range" else None
        end_date = self.end_date.get() if date_filter == "Range" else None
        transactions = self.db.get_transactions(self.user_id, date_filter, start_date, end_date)

        cash_balance, mpesa_balance, income_total, expenses_total, savings_total = 0, 0, 0, 0, 0
        for trans in transactions:
            id, date, type, category, amount, mode, details, flagged = trans
            tag = "flagged" if flagged else ""
            self.tree.insert("", "end", values=(date, type, category, f"KSh {amount:,}", mode, details, "Delete"), tags=tag)
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
            if flagged:
                self.tree.tag_configure("flagged", background="yellow")
                self.tree.bind("<Double-1>", self.prompt_add_to_plan)

        self.balance_label.config(text=f"Balance: Mpesa KSh {mpesa_balance:,}  Cash KSh {cash_balance:,}  Total KSh {mpesa_balance + cash_balance:,}")
        self.totals_label.config(text=f"Income: KSh {income_total:,}  Expenses: KSh {expenses_total:,}  Savings: KSh {savings_total:,}")
        self.status_label.config(text=f"Showing transactions for: {date_filter}")
        log_info(self.user_id, f"Updated Tracking: {len(transactions)} transactions for {date_filter}")

    def quick_add(self):
        self.db.add_transaction(self.user_id, datetime.now().strftime("%b %d %Y"), "Income", "Salary", 50000, "Mpesa", "Monthly")
        self.update_content()
        log_info(self.user_id, "Quick Added Salary transaction")

    def undo_delete(self):
        if self.db.undo_delete(self.user_id):
            self.update_content()
            messagebox.showinfo("Success", "Transaction restored")
            log_info(self.user_id, "Undid last transaction deletion")
        else:
            messagebox.showerror("Error", "No transaction to restore")
            log_error(self.user_id, "Failed to undo transaction deletion")

    def prompt_add_to_plan(self, event):
        item = self.tree.selection()[0]
        values = self.tree.item(item, "values")
        if values[7] == "1":  # Flagged
            type, category = values[2], values[3]
            if messagebox.askyesno("Unplanned Category", f"Add {category} ({type}) to plan for {datetime.now().strftime('%B %Y')}?"):
                self.db.add_plan(self.user_id, datetime.now().strftime("%B %Y"), type, category, 0, "None", "")
                self.db.cursor.execute(
                    "UPDATE transactions SET flagged = 0 WHERE user_id = ? AND type = ? AND category = ?",
                    (self.user_id, type, category)
                )
                self.db.conn.commit()
                self.update_content()
                log_info(self.user_id, f"Added unplanned category {type}/{category} to plan")

    def open_new_record(self):
        popup = tk.Toplevel(self)
        popup.title("New Record")
        popup.geometry("300x400")
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Date:").pack(pady=5)
        date_var = DateEntry(popup, date_pattern="mm/dd/yyyy")
        date_var.pack(pady=5)

        ttk.Label(popup, text="Type:").pack(pady=5)
        type_var = tk.StringVar()
        ttk.Combobox(popup, textvariable=type_var, values=["Income", "Expenses", "Savings"], state="readonly").pack(pady=5)

        ttk.Label(popup, text="Category:").pack(pady=5)
        category_var = tk.StringVar()
        ttk.Entry(popup, textvariable=category_var).pack(pady=5)

        ttk.Label(popup, text="Amount (KSh):").pack(pady=5)
        amount_var = tk.StringVar()
        ttk.Entry(popup, textvariable=amount_var).pack(pady=5)

        ttk.Label(popup, text="Mode:").pack(pady=5)
        mode_var = tk.StringVar()
        ttk.Combobox(popup, textvariable=mode_var, values=["Cash", "Mpesa"], state="readonly").pack(pady=5)

        ttk.Label(popup, text="Details:").pack(pady=5)
        details_var = tk.StringVar()
        ttk.Entry(popup, textvariable=details_var).pack(pady=5)

        def save_record():
            try:
                amount = int(amount_var.get())
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                date_str = datetime.strptime(date_var.get(), "%m/%d/%Y").strftime("%b %d %Y")
                if self.db.add_transaction(self.user_id, date_str, type_var.get(), category_var.get(), amount, mode_var.get(), details_var.get()):
                    self.update_content()
                    popup.destroy()
                    log_info(self.user_id, f"Added transaction: {date_str}, {type_var.get()}/{category_var.get()}")
                else:
                    messagebox.showerror("Error", "Failed to add transaction")
                    log_error(self.user_id, f"Failed to add transaction: {date_str}, {type_var.get()}/{category_var.get()}")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                log_error(self.user_id, f"Transaction validation failed: {str(e)}")

        ttk.Button(popup, text="Save", style="Success.TButton", command=save_record).pack(pady=10)