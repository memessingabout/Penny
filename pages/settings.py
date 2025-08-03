import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import Database
from utils.logging import log_info, log_error, log_debug
from styles import apply_styles

class SettingsPage(tk.Frame):
    def __init__(self, parent, switch_page_callback, user_id):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.user_id = user_id
        self.db = Database()
        apply_styles()
        self.init_ui()

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Profile", font=("Arial", 14)).grid(row=0, column=0, columnspan=3, pady=10)
        self.username_var = tk.StringVar()
        ttk.Label(main_frame, text="Username:").grid(row=1, column=0, sticky="e", padx=5)
        ttk.Entry(main_frame, textvariable=self.username_var, state="readonly").grid(row=1, column=1, sticky="w", pady=5)
        ttk.Button(main_frame, text="Edit", command=lambda: self.edit_profile("username")).grid(row=1, column=2, padx=5)

        self.email_var = tk.StringVar()
        ttk.Label(main_frame, text="Email:").grid(row=2, column=0, sticky="e", padx=5)
        ttk.Entry(main_frame, textvariable=self.email_var, state="readonly").grid(row=2, column=1, sticky="w", pady=5)
        ttk.Button(main_frame, text="Edit", command=lambda: self.edit_profile("email")).grid(row=2, column=2, padx=5)

        self.bio_var = tk.StringVar()
        ttk.Label(main_frame, text="Bio:").grid(row=3, column=0, sticky="e", padx=5)
        ttk.Entry(main_frame, textvariable=self.bio_var, state="readonly").grid(row=3, column=1, sticky="w", pady=5)
        ttk.Button(main_frame, text="Edit", command=lambda: self.edit_profile("bio")).grid(row=3, column=2, padx=5)

        ttk.Label(main_frame, text="Preferences", font=("Arial", 14)).grid(row=4, column=0, columnspan=3, pady=10)
        ttk.Label(main_frame, text="Currency:").grid(row=5, column=0, sticky="e", padx=5)
        self.currency_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=self.currency_var, values=["KSh", "USD", "EUR"], state="readonly").grid(row=5, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="Savings Mode:").grid(row=6, column=0, sticky="e", padx=5)
        self.savings_mode_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=self.savings_mode_var, values=["Unallocated as Savings", "Fixed Savings"], state="readonly").grid(row=6, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="Planning Enabled:").grid(row=7, column=0, sticky="e", padx=5)
        self.planning_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, variable=self.planning_enabled_var).grid(row=7, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="Theme:").grid(row=8, column=0, sticky="e", padx=5)
        self.theme_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=self.theme_var, values=["Light", "Dark"], state="readonly").grid(row=8, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="Notifications:").grid(row=9, column=0, sticky="e", padx=5)
        self.notifications_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, variable=self.notifications_var).grid(row=9, column=1, sticky="w", pady=5)

        ttk.Label(main_frame, text="Language:").grid(row=10, column=0, sticky="e", padx=5)
        self.language_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=self.language_var, values=["English", "Swahili"], state="readonly").grid(row=10, column=1, sticky="w", pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="Save Preferences", style="Success.TButton", command=self.save_preferences).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Logout", style="Danger.TButton", command=self.logout).pack(side=tk.LEFT, padx=5)

        nav_frame = ttk.Frame(self)
        nav_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        ttk.Button(nav_frame, text="Dashboard", command=lambda: self.switch_page_callback("Dashboard")).pack(side=tk.LEFT, padx=5)
        if self.is_planning_enabled():
            ttk.Button(nav_frame, text="Planning", command=lambda: self.switch_page_callback("Planning")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Tracking", command=lambda: self.switch_page_callback("Tracking")).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Settings", style="Success.TButton").pack(side=tk.LEFT, padx=5)

        self.load_settings()

    def is_planning_enabled(self):
        enabled = self.db.is_planning_enabled(self.user_id)
        log_debug(self.user_id, f"Checked planning enabled: {enabled}")
        return enabled

    def load_settings(self):
        profile = self.db.get_user_profile(self.user_id)
        if profile:
            self.username_var.set(profile[0])
            self.email_var.set(profile[1])
            self.bio_var.set(profile[2] or "")
        settings = self.db.get_settings(self.user_id)
        if settings:
            self.currency_var.set(settings[0])
            self.savings_mode_var.set(settings[1])
            self.planning_enabled_var.set(bool(settings[2]))
            self.theme_var.set(settings[3])
            self.notifications_var.set(bool(settings[4]))
            self.language_var.set(settings[5])
        log_info(self.user_id, "Loaded settings and profile")

    def save_preferences(self):
        if self.db.update_settings(
            self.user_id,
            self.currency_var.get(),
            self.savings_mode_var.get(),
            self.planning_enabled_var.get(),
            self.theme_var.get(),
            self.notifications_var.get(),
            self.language_var.get()
        ):
            messagebox.showinfo("Success", "Preferences saved")
            self.switch_page_callback("Settings")
            log_info(self.user_id, "Saved preferences")
        else:
            messagebox.showerror("Error", "Failed to save preferences")
            log_error(self.user_id, "Failed to save preferences")

    def edit_profile(self, field):
        popup = tk.Toplevel(self)
        popup.title(f"Edit {field.capitalize()}")
        popup.geometry("300x150")
        popup.transient(self)
        popup.grab_set()

        ttk.Label(popup, text=f"New {field.capitalize()}:").pack(pady=5)
        new_value_var = tk.StringVar()
        ttk.Entry(popup, textvariable=new_value_var).pack(pady=5)

        def save():
            value = new_value_var.get().strip()
            if field == "username":
                if not value or len(value) < 3:
                    messagebox.showerror("Error", "Username must be at least 3 characters")
                    log_error(self.user_id, "Invalid username length")
                    return
                if self.db.username_exists(value, self.user_id):
                    messagebox.showerror("Error", "Username already taken")
                    log_error(self.user_id, f"Username {value} already taken")
                    return
                if self.db.update_user_profile(self.user_id, value, self.email_var.get(), self.bio_var.get()):
                    self.username_var.set(value)
                    popup.destroy()
                    log_info(self.user_id, f"Updated username to {value}")
                else:
                    messagebox.showerror("Error", "Failed to update username")
                    log_error(self.user_id, f"Failed to update username {value}")
            elif field == "email":
                if not value or "@" not in value:
                    messagebox.showerror("Error", "Invalid email format")
                    log_error(self.user_id, f"Invalid email format: {value}")
                    return
                if self.db.email_exists(value, self.user_id):
                    messagebox.showerror("Error", "Email already registered")
                    log_error(self.user_id, f"Email {value} already registered")
                    return
                if self.db.update_user_profile(self.user_id, self.username_var.get(), value, self.bio_var.get()):
                    self.email_var.set(value)
                    popup.destroy()
                    log_info(self.user_id, f"Updated email to {value}")
                else:
                    messagebox.showerror("Error", "Failed to update email")
                    log_error(self.user_id, f"Failed to update email {value}")
            elif field == "bio":
                if self.db.update_user_profile(self.user_id, self.username_var.get(), self.email_var.get(), value):
                    self.bio_var.set(value)
                    popup.destroy()
                    log_info(self.user_id, f"Updated bio to {value}")
                else:
                    messagebox.showerror("Error", "Failed to update bio")
                    log_error(self.user_id, f"Failed to update bio {value}")

        ttk.Button(popup, text="Save", style="Success.TButton", command=save).pack(pady=10)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.db.close()
            self.master.geometry("400x400")
            self.master.center_window(400, 400)
            self.switch_page_callback("Login")
            log_info(self.user_id, "User logged out")