import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils.database import Database
from utils.logging import log_info, log_error, log_debug
from styles import apply_styles

class PlanningPage(tk.Frame):
    def __init__(self, parent, switch_page_callback, user_id):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.user_id = user_id
        self.db = Database()
        apply_styles()
        self.tooltip = None
        self.init_ui()

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.month_var = tk.StringVar(value=datetime.now().strftime("%B"))
        ttk.Combobox(header_frame, textvariable=self.month_var, values=self.get_months(),
                     state="readonly").pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(header_frame, text="Status: Balanced (KSh 0)", font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=5)

        control_frame = ttk.Frame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        ttk.Button(control_frame, text="New Plan", style="Success.TButton", command=self.open_new_plan).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Copy Plan", command=self.copy_plan).pack(side=tk.LEFT, padx=5)

        table_frame = ttk.Frame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=("Category", "Amount", "Recurrence", "Due"), show="tree headings")
        self.tree.heading("#0", text="Type")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Amount", text="Amount (KSh)")
        self.tree.heading("Recurrence", text="Recurrence")
        self.tree.heading("Due", text="Due")
        self.tree.column("#0", width=100)
        self.tree.column("Category", width=150)
        self.tree.column("Amount", width=150)
        self.tree.column("Recurrence", width=100)
        self.tree.column("Due", width=100)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<Button-3>", self.show_tooltip)

        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        ttk.Button(nav_frame, text="Dashboard", command=lambda: self.switch_page_callback("Dashboard")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Planning", style="Success.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Tracking", command=lambda: self.switch_page_callback("Tracking")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Settings", command=lambda: self.switch_page_callback("Settings")).pack(side=tk.LEFT, padx=5)

        self.update_content()

    def get_months(self):
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        current_year = datetime.now().year
        result = [f"Total {current_year}"]
        for year in range(current_year, current_year + 11):
            for month in months:
                result.append(f"{month} {year}")
        log_debug(self.user_id, f"Generated {len(result)} months for dropdown")
        return result

    def update_content(self):
        self.tree.delete(*self.tree.get_children())
        month = self.month_var.get()
        plans = self.db.get_plans(self.user_id, month)
        income_total, expenses_total, savings_total = 0, 0, 0
        income_node = self.tree.insert("", "end", text="Income", open=True)
        expenses_node = self.tree.insert("", "end", text="Expenses", open=True)
        savings_node = self.tree.insert("", "end", text="Savings", open=True)

        for plan in plans:
            type, category, amount, recurrence, due = plan
            node = income_node if type == "Income" else expenses_node if type == "Expenses" else savings_node
            self.tree.insert(node, "end", values=(category, f"KSh {amount:,}", recurrence or "None", due or ""), tags=(type, category))
            if type == "Income":
                income_total += amount
            elif type == "Expenses":
                expenses_total += amount
            else:
                savings_total += amount

        self.tree.insert(income_node, 0, values=("Total", f"KSh {income_total:,}", "", ""))
        self.tree.insert(expenses_node, 0, values=("Total", f"KSh {expenses_total:,}", "", ""))
        self.tree.insert(savings_node, 0, values=("Total", f"KSh {savings_total:,}", "", ""))

        balance = income_total - expenses_total - savings_total
        status = "Balanced" if balance == 0 else "Overbudget" if balance < 0 else "Underbudget"
        style = f"Status{status}.TLabel"
        self.status_label.config(text=f"Status: {status} (KSh {balance:,})", style=style, font=("Arial", 12, "bold"))
        log_info(self.user_id, f"Updated Planning content for {month}: Balance KSh {balance}")

    def show_tooltip(self, event):
        item = self.tree.identify_row(event.y)
        if not item or item in (self.tree.get_children("")):
            return
        tags = self.tree.item(item, "tags")
        if not tags:
            return
        type, category = tags

        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        x, y = self.tree.winfo_pointerxy()
        self.tooltip.wm_geometry(f"+{x+10}+{y+10}")

        ttk.Button(self.tooltip, text="Edit", command=lambda: self.edit_category(type, category)).pack()
        ttk.Button(self.tooltip, text="Delete", style="Danger.TButton", command=lambda: self.delete_category(type, category)).pack()

        self.tooltip.bind("<Leave>", lambda e: self.tooltip.destroy())
        log_debug(self.user_id, f"Showed tooltip for category {type}/{category}")

    def edit_category(self, old_type, old_category):
        popup = tk.Toplevel(self)
        popup.title("Edit Category")
        popup.geometry("300x200")
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Type:").pack(pady=5)
        type_var = tk.StringVar(value=old_type)
        ttk.Combobox(popup, textvariable=type_var, values=["Income", "Expenses", "Savings"], state="readonly").pack(pady=5)

        ttk.Label(popup, text="Category:").pack(pady=5)
        category_var = tk.StringVar(value=old_category)
        ttk.Entry(popup, textvariable=category_var).pack(pady=5)

        def save():
            new_type = type_var.get()
            new_category = category_var.get().strip()
            if not new_category:
                messagebox.showerror("Error", "Category cannot be empty")
                return
            if self.db.update_category(self.user_id, old_type, old_category, new_type, new_category):
                self.update_content()
                popup.destroy()
                log_info(self.user_id, f"Edited category: {old_type}/{old_category} to {new_type}/{new_category}")
            else:
                messagebox.showerror("Error", "Failed to update category")
                log_error(self.user_id, f"Failed to edit category {old_type}/{old_category}")

        ttk.Button(popup, text="Save", style="Success.TButton", command=save).pack(pady=10)

    def delete_category(self, type, category):
        if messagebox.askyesno("Confirm", f"Delete category {type}/{category}?"):
            if self.db.delete_category(self.user_id, type, category):
                self.update_content()
                log_info(self.user_id, f"Deleted category: {type}/{category}")
            else:
                messagebox.showerror("Error", "Cannot delete category: used in transactions or plans")
                log_error(self.user_id, f"Failed to delete category {type}/{category}")

    def open_new_plan(self):
        popup = tk.Toplevel(self)
        popup.title("New Plan")
        popup.geometry("300x400")
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="Month:").pack(pady=5)
        month_var = tk.StringVar(value=self.month_var.get())
        ttk.Combobox(popup, textvariable=month_var, values=self.get_months(), state="readonly").pack(pady=5)

        ttk.Label(popup, text="Type:").pack(pady=5)
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(popup, textvariable=type_var, values=["Income", "Expenses", "Savings"], state="readonly")
        type_combo.pack(pady=5)

        ttk.Label(popup, text="Category:").pack(pady=5)
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(popup, textvariable=category_var)
        category_combo.pack(pady=5)
        def update_categories():
            categories = self.db.get_categories(self.user_id, type_var.get())
            category_combo["values"] = categories
            if categories:
                category_var.set(categories[0])
        type_combo.bind("<<ComboboxSelected>>", lambda e: update_categories())
        update_categories()

        ttk.Label(popup, text="Amount (KSh):").pack(pady=5)
        amount_var = tk.StringVar()
        ttk.Entry(popup, textvariable=amount_var).pack(pady=5)

        ttk.Label(popup, text="Recurrence:").pack(pady=5)
        recurrence_var = tk.StringVar()
        recurrence_combo = ttk.Combobox(popup, textvariable=recurrence_var, values=["None", "Weekly", "Monthly"], state="readonly")
        recurrence_combo.pack(pady=5)

        ttk.Label(popup, text="Due:").pack(pady=5)
        due_var = tk.StringVar()
        due_entry = ttk.Entry(popup, textvariable=due_var, state="disabled")
        due_entry.pack(pady=5)

        def update_due_state():
            if recurrence_var.get() in ["Weekly", "Monthly"]:
                due_entry["state"] = "normal"
            else:
                due_entry["state"] = "disabled"
                due_var.set("")
        recurrence_combo.bind("<<ComboboxSelected>>", lambda e: update_due_state())

        def save_plan():
            try:
                amount = int(amount_var.get())
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                recurrence = recurrence_var.get()
                due = due_var.get().strip()
                if recurrence == "Weekly" and due not in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                    raise ValueError("Due day must be a valid weekday")
                if recurrence == "Monthly" and not due.endswith("th") and not due.isdigit():
                    raise ValueError("Due date must be a number with 'th' (e.g., '10th')")
                if self.db.add_plan(self.user_id, month_var.get(), type_var.get(), category_var.get(), amount, recurrence, due):
                    self.update_content()
                    popup.destroy()
                    log_info(self.user_id, f"Added new plan: {month_var.get()}, {type_var.get()}/{category_var.get()}")
                else:
                    messagebox.showerror("Error", "Failed to add plan")
                    log_error(self.user_id, f"Failed to add plan: {month_var.get()}, {type_var.get()}/{category_var.get()}")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                log_error(self.user_id, f"Plan validation failed: {str(e)}")

        ttk.Button(popup, text="Save", style="Success.TButton", command=save_plan).pack(pady=10)

    def copy_plan(self):
        popup = tk.Toplevel(self)
        popup.title("Copy Plan")
        popup.geometry("300x200")
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="From Month:").pack(pady=5)
        from_month_var = tk.StringVar(value=self.month_var.get())
        ttk.Combobox(popup, textvariable=from_month_var, values=self.get_months(), state="readonly").pack(pady=5)

        ttk.Label(popup, text="To Month:").pack(pady=5)
        to_month_var = tk.StringVar()
        ttk.Combobox(popup, textvariable=to_month_var, values=self.get_months(), state="readonly").pack(pady=5)

        def save_copy():
            if self.db.copy_plan(self.user_id, from_month_var.get(), to_month_var.get()):
                self.month_var.set(to_month_var.get())
                self.update_content()
                popup.destroy()
                log_info(self.user_id, f"Copied plan from {from_month_var.get()} to {to_month_var.get()}")
            else:
                messagebox.showerror("Error", "Failed to copy plan")
                log_error(self.user_id, f"Failed to copy plan from {from_month_var.get()} to {to_month_var.get()}")

        ttk.Button(popup, text="Copy", style="Success.TButton", command=save_copy).pack(pady=10)