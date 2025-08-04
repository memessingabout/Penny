import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from datetime import datetime
import re
import json
from utils.database import Database
from utils.logging import log_info, log_error, log_debug
from styles import apply_styles

class PlanningPage(tk.Frame):
    def __init__(self, parent, switch_page_callback, user_id):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.user_id = user_id
        self.db = Database()
        self.current_year = datetime.now().year  # Class-level current_year
        apply_styles()
        self.tooltip = None
        self.weekday_index = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        self.ordinal_map = {'1st': 1, 'first': 1, '2nd': 2, 'second': 2, '3rd': 3, 'third': 3,
                           '4th': 4, 'fourth': 4, '5th': 5, 'fifth': 5}
        self.init_ui()

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)

        # Year dropdown
        self.year_var = tk.StringVar(value=str(self.current_year))
        years = [str(self.current_year)]
        next_year = self.current_year
        while self.db.has_december_plan(self.user_id, next_year):
            years.append(str(next_year + 1))
            next_year += 1
        ttk.Label(header_frame, text="Year:").pack(side=tk.LEFT, padx=3)
        self.year_combo = ttk.Combobox(header_frame, textvariable=self.year_var, values=years,
                                      state="readonly", width=10)
        self.year_combo.pack(side=tk.LEFT, padx=3)

        # Month dropdown
        self.month_var = tk.StringVar(value=datetime.now().strftime("%B"))
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December", "Total Year"]
        ttk.Label(header_frame, text="Month:").pack(side=tk.LEFT, padx=3)
        ttk.Combobox(header_frame, textvariable=self.month_var, values=months,
                    state="readonly", width=15).pack(side=tk.LEFT, padx=3)

        # Status label
        self.status_label = ttk.Label(header_frame, text="Status: Balanced", font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Control frame
        control_frame = ttk.Frame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        ttk.Button(control_frame, text="New Plan", style="Success.TButton",
                  command=self.open_new_plan).pack(side=tk.LEFT, padx=3)
        ttk.Button(control_frame, text="Copy Plan", command=self.copy_plan).pack(side=tk.LEFT, padx=3)

        # Table frame
        table_frame = ttk.Frame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=2)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=("Category", "Amount", "Recurrence", "Due"),
                                show="tree headings", height=15)
        self.tree.heading("#0", text="Type")
        self.tree.heading("Category", text="Category", anchor="center")
        self.tree.heading("Amount", text="Amount (KSh)", anchor="center")
        self.tree.heading("Recurrence", text="Recurrence", anchor="center")
        self.tree.heading("Due", text="Due", anchor="center")
        self.tree.column("#0", width=100, anchor="center")
        self.tree.column("Category", width=150, anchor="center")
        self.tree.column("Amount", width=150, anchor="center")
        self.tree.column("Recurrence", width=100, anchor="center")
        self.tree.column("Due", width=100, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.tag_configure("type", font=("Arial", 10, "bold"))
        self.tree.bind("<Button-3>", self.show_tooltip)
        style = ttk.Style()
        style.configure("Treeview", rowheight=20)

        # Navigation frame
        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
        ttk.Button(nav_frame, text="Dashboard", command=lambda: self.switch_page_callback("Dashboard")).pack(side=tk.LEFT, padx=3)
        ttk.Button(nav_frame, text="Planning", style="Success.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(nav_frame, text="Tracking", command=lambda: self.switch_page_callback("Tracking")).pack(side=tk.LEFT, padx=3)
        ttk.Button(nav_frame, text="Settings", command=lambda: self.switch_page_callback("Settings")).pack(side=tk.LEFT, padx=3)

        # Bind year/month changes
        self.year_var.trace("w", lambda *args: self.update_content())
        self.month_var.trace("w", lambda *args: self.update_content())
        self.update_content()

    def update_content(self):
        self.tree.delete(*self.tree.get_children())
        period = f"{self.month_var.get()} {self.year_var.get()}" if self.month_var.get() != "Total Year" else self.year_var.get()
        
        # Handle Total Year case
        if self.month_var.get() == "Total Year":
            year = int(self.year_var.get())
            months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
            plans = []
            for month in months:
                month_period = f"{month} {year}"
                plans.extend(self.db.get_plans(self.user_id, month_period))
        else:
            plans = self.db.get_plans(self.user_id, period)

        # Aggregate duplicate categories
        aggregated_plans = {}
        for plan in plans:
            type, category, amount, recurrence, due = plan
            key = (type, category)
            if key not in aggregated_plans:
                aggregated_plans[key] = {"amount": 0, "recurrence": recurrence, "due": due}
            aggregated_plans[key]["amount"] += amount

        # Sort plans by amount
        income_plans, expenses_plans, savings_plans = [], [], []
        for (type, category), data in aggregated_plans.items():
            due = "" if data["recurrence"] == "None" else data["due"] or ""
            plan_data = (category, data["amount"], data["recurrence"] or "None", due)
            if type == "Income":
                income_plans.append(plan_data)
            elif type == "Expenses":
                expenses_plans.append(plan_data)
            else:
                savings_plans.append(plan_data)

        income_plans.sort(key=lambda x: x[1], reverse=True)
        expenses_plans.sort(key=lambda x: x[1], reverse=True)
        savings_plans.sort(key=lambda x: x[1], reverse=True)

        # Insert into tree
        income_total, expenses_total, savings_total = 0, 0, 0
        income_node = self.tree.insert("", "end", text="Income", values=("", f"KSh {income_total:,}", "", ""),
                                     tags=("type",), open=True)
        expenses_node = self.tree.insert("", "end", text="Expenses", values=("", f"KSh {expenses_total:,}", "", ""),
                                       tags=("type",), open=True)
        savings_node = self.tree.insert("", "end", text="Savings", values=("", f"KSh {savings_total:,}", "", ""),
                                      tags=("type",), open=True)

        for category, amount, recurrence, due in income_plans:
            self.tree.insert(income_node, "end", values=(category, f"KSh {amount:,}", recurrence, due),
                           tags=("Income", category))
            income_total += amount

        for category, amount, recurrence, due in expenses_plans:
            self.tree.insert(expenses_node, "end", values=(category, f"KSh {amount:,}", recurrence, due),
                           tags=("Expenses", category))
            expenses_total += amount

        for category, amount, recurrence, due in savings_plans:
            self.tree.insert(savings_node, "end", values=(category, f"KSh {amount:,}", recurrence, due),
                           tags=("Savings", category))
            savings_total += amount

        self.tree.item(income_node, values=("", f"KSh {income_total:,}", "", ""))
        self.tree.item(expenses_node, values=("", f"KSh {expenses_total:,}", "", ""))
        self.tree.item(savings_node, values=("", f"KSh {savings_total:,}", "", ""))

        balance = income_total - expenses_total - savings_total
        if balance == 0:
            status = "Balanced"
            style = "StatusBalanced.TLabel"
        elif balance < 0:
            status = f"Overbudget by KSh {-balance:,}"
            style = "StatusOverbudget.TLabel"
        else:
            status = f"Underbudget by KSh {balance:,}"
            style = "StatusUnderbudget.TLabel"
        self.status_label.config(text=f"Status: {status}", style=style, font=("Arial", 12, "bold"))
        log_info(self.user_id, f"Updated Planning content for {period}: Balance KSh {balance}")

    def show_tooltip(self, event):
        item = self.tree.identify_row(event.y)
        if not item or item in self.tree.get_children(""):
            return
        tags = self.tree.item(item, "tags")
        if "type" in tags:
            return
        type, category = tags

        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        x, y = self.tree.winfo_pointerxy()
        self.tooltip.wm_geometry(f"+{x+10}+{y+10}")

        ttk.Button(self.tooltip, text="Edit",
                 command=lambda: self.open_new_plan(type=type, category=category)).pack()
        ttk.Button(self.tooltip, text="Delete", style="Danger.TButton",
                 command=lambda: self.delete_category(type, category)).pack()

        self.tooltip.bind("<Leave>", lambda e: self.tooltip.destroy())
        log_debug(self.user_id, f"Showed tooltip for category {type}/{category}")

    def delete_category(self, type, category):
        if messagebox.askyesno("Confirm", f"Delete category {type}/{category}? This action is irreversible."):
            if self.db.delete_category(self.user_id, type, category):
                self.update_content()
                log_info(self.user_id, f"Deleted category: {type}/{category}")
            else:
                messagebox.showerror("Error", "Cannot delete category: used in transactions")
                log_error(self.user_id, f"Failed to delete category {type}/{category}")

    def get_days_in_month(self, month, year):
        """Return the number of days in the given month and year."""
        try:
            month_idx = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"].index(month) + 1
            if month == "February":
                days = 29 if calendar.isleap(year) else 28
                log_debug(self.user_id, f"Calculating days for February {year}: {days}")
                return days
            return [31, None, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month_idx - 1]
        except ValueError:
            log_error(self.user_id, f"Invalid month: {month}")
            return 31

    def get_ordinal_suffix(self, day):
        """Return the correct ordinal suffix for a day (1st, 2nd, 3rd, etc.)."""
        if 10 <= day % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day}{suffix}"

    def parse_custom_input(self, input_text):
        """Parse and validate custom recurrence input using regex."""
        patterns = [
            {
                "type": "interval",
                "regex": r"^every\s+(\d+)\s+days?(?:\s+from\s+(\d+))?$",
                "validate": lambda m: (
                    1 <= int(m.group(1)) <= 31 and 
                    (m.group(2) is None or 1 <= int(m.group(2)) <= 31),
                    "Invalid interval or start day. Use 'every N days [from M]' where N and M are 1–31."
                ),
                "details": lambda m: {"type": "interval", "interval": int(m.group(1)), "start_day": int(m.group(2)) if m.group(2) else 1}
            },
            {
                "type": "multiple_days",
                "regex": r"^on\s+days?\s+(\d+(?:\s*,\s*\d+)*)$",
                "validate": lambda m: (
                    all(1 <= int(day.strip()) <= 31 for day in m.group(1).split(',')),
                    "Invalid days. Use 'on days 1, 15, 25' with days 1–31."
                ),
                "details": lambda m: {"type": "multiple_days", "days": [int(day.strip()) for day in m.group(1).split(',')]}
            },
            {
                "type": "nth_weekday",
                "regex": r"^(1st|first|2nd|second|3rd|third|4th|fourth|5th|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$",
                "validate": lambda m: True,
                "details": lambda m: {"type": "nth_weekday", "weekday": m.group(2), "nth": self.ordinal_map[m.group(1)]}
            },
            {
                "type": "last_weekday",
                "regex": r"^last\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$",
                "validate": lambda m: True,
                "details": lambda m: {"type": "last_weekday", "weekday": m.group(1)}
            },
            {
                "type": "nth_week",
                "regex": r"^every\s+(\d+)\s+weeks?\s+on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+from\s+(\d+))?$",
                "validate": lambda m: (
                    1 <= int(m.group(1)) <= 4 and 
                    (m.group(3) is None or 1 <= int(m.group(3)) <= 31),
                    "Invalid week interval or start day. Use 'every N weeks on weekday [from M]' where N is 1–4 and M is 1–31."
                ),
                "details": lambda m: {
                    "type": "nth_week",
                    "weekday": m.group(2),
                    "interval": int(m.group(1)),
                    "start_day": int(m.group(3)) if m.group(3) else 1
                }
            },
            {
                "type": "weekday_combinations",
                "regex": r"^(?:(1st|first|2nd|second|3rd|third|4th|fourth|5th|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+and\s+)?)+$",
                "validate": lambda m: (
                    len(re.findall(r"(1st|first|2nd|second|3rd|third|4th|fourth|5th|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", input_text)) >= 2,
                    "Invalid weekday combinations. Use '1st and 3rd Monday' or similar with at least two instances."
                ),
                "details": lambda m: {
                    "type": "weekday_combinations",
                    "instances": [
                        {"weekday": w, "nth": self.ordinal_map[o]}
                        for o, w in re.findall(r"(1st|first|2nd|second|3rd|third|4th|fourth|5th|fifth)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", input_text)
                    ]
                }
            }
        ]
        
        for pattern in patterns:
            match = re.match(pattern["regex"], input_text.lower(), re.IGNORECASE)
            if match:
                is_valid, error_message = pattern["validate"](match)
                if is_valid:
                    return pattern["details"](match), None
                return None, error_message
        return None, "Invalid custom recurrence. Use formats like 'every 5 days from 3', 'on days 1, 15', '2nd Tuesday', 'last Friday', 'every 2 weeks on Monday from 4', or '1st and 3rd Monday'."

    def open_new_plan(self, type=None, category=None):
        popup = tk.Toplevel(self)
        popup.title("Edit Plan" if type and category else "New Plan")
        popup.geometry("300x400")
        popup.transient(self)
        popup.grab_set()
        popup.protocol("WM_DELETE_WINDOW", lambda: [popup.destroy(), self.focus_set()])

        # Grid layout for aligned inputs
        popup.grid_columnconfigure(1, weight=1)
        row = 0

        # Type
        ttk.Label(popup, text="Type:").grid(row=row, column=0, padx=3, pady=2, sticky="e")
        type_var = tk.StringVar(value=type or "Income")
        type_combo = ttk.Combobox(popup, textvariable=type_var, values=["Income", "Expenses", "Savings"],
                                 state="readonly")
        type_combo.grid(row=row, column=1, padx=3, pady=2, sticky="w")
        row += 1

        # Category
        ttk.Label(popup, text="Category:").grid(row=row, column=0, padx=3, pady=2, sticky="e")
        category_var = tk.StringVar(value=category or "")
        category_combo = ttk.Combobox(popup, textvariable=category_var)
        category_combo.grid(row=row, column=1, padx=3, pady=2, sticky="w")

        def update_categories(*args):
            categories = self.db.get_categories(self.user_id, type_var.get())
            log_debug(self.user_id, f"Updating categories for type {type_var.get()}: {categories}")
            category_combo["values"] = sorted(categories) if categories else [""]
            if categories and not category_var.get():
                category_var.set(categories[0])
            elif not categories:
                category_var.set("")
        type_combo.bind("<<ComboboxSelected>>", update_categories)
        update_categories()
        row += 1

        # Amount
        ttk.Label(popup, text="Amount (KSh):").grid(row=row, column=0, padx=3, pady=2, sticky="e")
        amount_var = tk.StringVar()
        ttk.Entry(popup, textvariable=amount_var).grid(row=row, column=1, padx=3, pady=2, sticky="w")
        if not amount_var.get() and category:
            prev_month = self.get_previous_month()
            prev_amount = self.db.get_plan_amount(self.user_id, prev_month, type_var.get(), category)
            if prev_amount:
                amount_var.set(str(prev_amount))
        row += 1

        # Recurrence
        ttk.Label(popup, text="Recurrence:").grid(row=row, column=0, padx=3, pady=2, sticky="e")
        recurrence_var = tk.StringVar(value="None" if not type else "Daily")
        recurrence_combo = ttk.Combobox(popup, textvariable=recurrence_var,
                                       values=["None", "Daily", "Monthly", "Custom"],
                                       state="readonly")
        recurrence_combo.grid(row=row, column=1, padx=3, pady=2, sticky="w")
        row += 1

        # Due/Days frame
        due_frame = ttk.Frame(popup)
        due_frame.grid(row=row, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
        due_label = ttk.Label(due_frame, text="Due:")
        due_label.grid(row=0, column=0, padx=3, pady=2, sticky="e")
        due_var = tk.StringVar()

        # Daily checkboxes
        days_frame = ttk.Frame(due_frame)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_vars = {day: tk.BooleanVar() for day in days}
        for i, day in enumerate(days):
            ttk.Checkbutton(days_frame, text=day, variable=day_vars[day]).grid(row=0, column=i, padx=1)

        # Monthly due dropdown
        def update_due_combo():
            if self.month_var.get() == "Total Year":
                days = 31
            else:
                days = self.get_days_in_month(self.month_var.get(), int(self.year_var.get()))
                log_debug(self.user_id, f"Updating due combo for {self.month_var.get()} {self.year_var.get()}: {days} days")
                due_combo["values"] = [self.get_ordinal_suffix(i) for i in range(1, days + 1)] + ["last"]
                if due_var.get() not in due_combo["values"]:
                    due_var.set(due_combo["values"][0] if due_combo["values"] else "")

        due_combo = ttk.Combobox(due_frame, textvariable=due_var, state="readonly")
        update_due_combo()

        # Custom recurrence input
        custom_var = tk.StringVar()
        custom_entry = ttk.Entry(due_frame, textvariable=custom_var, width=25)

        def update_due_ui(*args):
            recurrence = recurrence_var.get()
            for widget in due_frame.winfo_children()[1:]:
                widget.grid_remove()
            due_label.config(text="Due:")
            if recurrence == "Daily":
                days_frame.grid(row=0, column=1, sticky="w")
                due_label.config(text="Days:")
            elif recurrence == "Monthly":
                update_due_combo()
                due_combo.grid(row=0, column=1, sticky="w")
            elif recurrence == "Custom":
                custom_entry.grid(row=0, column=1, sticky="w")
                due_label.config(text="Custom (e.g., 'every 5 days from 3'):")
        recurrence_combo.bind("<<ComboboxSelected>>", update_due_ui)
        self.month_var.trace("w", lambda *args: update_due_combo() if recurrence_var.get() == "Monthly" else None)
        self.year_var.trace("w", lambda *args: update_due_combo() if recurrence_var.get() == "Monthly" else None)
        row += 1

        # Auto-fill for editing
        if type and category:
            plan = self.db.get_plan_details(self.user_id, f"{self.month_var.get()} {self.year_var.get()}", type, category)
            if plan:
                recurrence_var.set(plan.get("recurrence", "None") or "None")
                due_var.set(plan.get("due", ""))
                if plan.get("custom_period"):
                    try:
                        custom_details = json.loads(plan.get("custom_period"))
                        if custom_details.get("type") == "interval":
                            custom_var.set(f"every {custom_details['interval']} days from {custom_details['start_day']}")
                        elif custom_details.get("type") == "multiple_days":
                            custom_var.set(f"on days {', '.join(map(str, custom_details['days']))}")
                        elif custom_details.get("type") == "nth_weekday":
                            custom_var.set(f"{custom_details['nth']}th {custom_details['weekday']}")
                        elif custom_details.get("type") == "last_weekday":
                            custom_var.set(f"last {custom_details['weekday']}")
                        elif custom_details.get("type") == "nth_week":
                            custom_var.set(f"every {custom_details['interval']} weeks on {custom_details['weekday']} from {custom_details['start_day']}")
                        elif custom_details.get("type") == "weekday_combinations":
                            instances = [f"{inst['nth']}th {inst['weekday']}" for inst in custom_details['instances']]
                            custom_var.set(" and ".join(instances))
                    except json.JSONDecodeError:
                        custom_var.set(plan.get("custom_period", ""))
                amount_var.set(str(plan.get("amount", "")))
                if plan.get("recurrence") == "Daily" and plan.get("due"):
                    for day in plan.get("due").split(","):
                        if day.strip() in day_vars:
                            day_vars[day.strip()].set(True)
                update_due_ui()

        def save_plan():
            try:
                log_debug(self.user_id, "Attempting to save plan")
                amount = int(amount_var.get())
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                recurrence = recurrence_var.get()
                due = due_var.get().strip() if recurrence in ["Daily", "Monthly"] else ""
                custom_period = None

                if recurrence == "Daily":
                    selected_days = [day for day, var in day_vars.items() if var.get()]
                    due = ",".join(selected_days) or "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
                    log_debug(self.user_id, f"Daily recurrence selected days: {due}")
                elif recurrence == "Monthly":
                    if not due:
                        raise ValueError("Due date required for monthly recurrence")
                    if due == "last":
                        pass  # Valid
                    elif not due.endswith(("st", "nd", "rd", "th")) or not due[:-2].isdigit() or not (1 <= int(due[:-2]) <= self.get_days_in_month(self.month_var.get(), int(self.year_var.get()))):
                        raise ValueError(f"Due date must be a valid day for {self.month_var.get()} (e.g., '10th' or 'last')")
                elif recurrence == "Custom":
                    custom_input = custom_var.get().strip()
                    if not custom_input:
                        raise ValueError("Custom recurrence details required")
                    custom_details, error = self.parse_custom_input(custom_input)
                    if error:
                        raise ValueError(error)
                    custom_period = json.dumps(custom_details)
                    log_debug(self.user_id, f"Parsed custom recurrence: {custom_period}")
                elif recurrence == "None":
                    due = ""
                    custom_period = None

                period = f"{self.month_var.get()} {self.year_var.get()}" if self.month_var.get() != "Total Year" else self.year_var.get()
                log_debug(self.user_id, f"Saving plan: period={period}, type={type_var.get()}, category={category_var.get()}, amount={amount}, recurrence={recurrence}, due={due}, custom_period={custom_period}")
                
                if self.db.add_plan(self.user_id, period, type_var.get(), category_var.get(),
                                 amount, recurrence, due, custom_period):
                    self.update_content()
                    popup.destroy()
                    log_info(self.user_id, f"Saved plan: {period}, {type_var.get()}/{category_var.get()}")
                    if self.month_var.get() == "December":
                        years = [str(self.current_year)]
                        next_year = self.current_year
                        while self.db.has_december_plan(self.user_id, next_year):
                            years.append(str(next_year + 1))
                            next_year += 1
                        self.year_combo["values"] = years
                else:
                    messagebox.showerror("Error", "Failed to save plan")
                    log_error(self.user_id, f"Failed to save plan: {period}, {type_var.get()}/{category_var.get()}")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                log_error(self.user_id, f"Plan validation failed: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
                log_error(self.user_id, f"Unexpected error in save_plan: {str(e)}")

        ttk.Button(popup, text="Save", style="Success.TButton", command=save_plan).grid(row=row, column=0, columnspan=2, pady=5)
        update_due_ui()

    def get_previous_month(self):
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        current_month = self.month_var.get()
        current_year = int(self.year_var.get())
        month_idx = months.index(current_month)
        if month_idx == 0:
            return f"December {current_year - 1}"
        return f"{months[month_idx - 1]} {current_year}"

    def copy_plan(self):
        popup = tk.Toplevel(self)
        popup.title("Copy Plan")
        popup.geometry("300x200")
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text="From Period:").pack(pady=5)
        from_period_var = tk.StringVar(value=f"{self.month_var.get()} {self.year_var.get()}")
        ttk.Combobox(popup, textvariable=from_period_var, values=self.get_periods(),
                    state="readonly").pack(pady=5)

        ttk.Label(popup, text="To Period:").pack(pady=5)
        to_period_var = tk.StringVar()
        ttk.Combobox(popup, textvariable=to_period_var, values=self.get_periods(),
                    state="readonly").pack(pady=5)

        def save_copy():
            if self.db.copy_plan(self.user_id, from_period_var.get(), to_period_var.get()):
                self.month_var.set(to_period_var.get().split()[0])
                self.year_var.set(to_period_var.get().split()[-1])
                self.update_content()
                popup.destroy()
                log_info(self.user_id, f"Copied plan from {from_period_var.get()} to {to_period_var.get()}")
                if to_period_var.get().startswith("December"):
                    years = [str(self.current_year)]
                    next_year = self.current_year
                    while self.db.has_december_plan(self.user_id, next_year):
                        years.append(str(next_year + 1))
                        next_year += 1
                    self.year_combo["values"] = years
            else:
                messagebox.showerror("Error", "Failed to copy plan")
                log_error(self.user_id, f"Failed to copy plan from {from_period_var.get()} to {to_period_var.get()}")

        ttk.Button(popup, text="Copy", style="Success.TButton", command=save_copy).pack(pady=5)

    def get_periods(self):
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        periods = [f"{month} {self.current_year}" for month in months]
        next_year = self.current_year
        while self.db.has_december_plan(self.user_id, next_year):
            periods.extend([f"{month} {next_year + 1}" for month in months])
            next_year += 1
        return periods
