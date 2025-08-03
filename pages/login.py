import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import Database
from utils.logging import log_info, log_error
from styles import apply_styles
import re

class LoginPage(tk.Frame):
    def __init__(self, parent, switch_page_callback, set_user_callback):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.set_user_callback = set_user_callback
        self.db = Database()
        apply_styles()
        self.init_ui()

    def init_ui(self):
        self.pack(fill="both", expand="True")
        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.main_frame = ttk.Frame(outer_frame, relief="groove", borderwidth=2, padding=10)
        self.main_frame.pack(padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.show_login()

    def show_login(self):
        # Clear the main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self.main_frame, text="Login", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10)

        ttk.Label(self.main_frame, text="Username:").grid(row=1, column=0, sticky="e", pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.username_var).grid(row=1, column=1, pady=5)

        ttk.Label(self.main_frame, text="Password:").grid(row=2, column=0, sticky="e", pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.main_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=2, column=1, sticky="w", pady=5)

        self.show_password_var = tk.BooleanVar()
        ttk.Checkbutton(self.main_frame, text="", variable=self.show_password_var,
                        command=self.toggle_password).grid(row=2, column=2, sticky="w", pady=5)

        ttk.Button(self.main_frame, text="Login", style="Success.TButton", command=self.login).grid(row=3, column=0, columnspan=3, pady=5)
        ttk.Button(self.main_frame, text="Signup", command=lambda: self.switch_page_callback("Signup")).grid(row=4, column=0, columnspan=3, pady=5)
        ttk.Button(self.main_frame, text="Forgot Password?", style="Link.TButton",
                   command=self.show_reset_password).grid(row=5, column=0, columnspan=3, pady=5)

        self.password_entry.bind("<Return>", lambda e: self.login())

    def show_reset_password(self):
        # Clear the main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self.main_frame, text="Reset Password", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10)

        ttk.Label(self.main_frame, text="Username:").grid(row=1, column=0, sticky="e", pady=5)
        username_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=username_var).grid(row=1, column=1, pady=5)

        ttk.Label(self.main_frame, text="Email:").grid(row=2, column=0, sticky="e", pady=5)
        email_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=email_var).grid(row=2, column=1, pady=5)

        ttk.Label(self.main_frame, text="Password:").grid(row=3, column=0, sticky="e", pady=5)
        new_password_var = tk.StringVar()
        new_password_entry = ttk.Entry(self.main_frame, textvariable=new_password_var, show="*")
        new_password_entry.grid(row=3, column=1, pady=5)

        show_password_var = tk.BooleanVar()
        ttk.Checkbutton(self.main_frame, text="", variable=show_password_var,
                        command=lambda: self.toggle_reset_password(new_password_entry, show_password_var)).grid(row=3, column=2, sticky="w", pady=5)

        ttk.Label(self.main_frame, text="Confirm:").grid(row=4, column=0, sticky="e", pady=5)
        confirm_password_var = tk.StringVar()
        confirm_password_entry = ttk.Entry(self.main_frame, textvariable=confirm_password_var, show="*")
        confirm_password_entry.grid(row=4, column=1, pady=5)

        ttk.Label(self.main_frame, text="Password must be: At least 8 characters, contain uppercase, lowercase, number, and special character",
              wraplength=300, justify="left").grid(row=6, column=0, columnspan=3, pady=5)

        self.strength_var = tk.StringVar(value="Weak")
        strength_label = ttk.Label(self.main_frame, textvariable=self.strength_var, foreground="red")
        strength_label.grid(row=5, column=0, columnspan=3, pady=5)
        new_password_var.trace("w", lambda *args: self.update_password_strength(new_password_var, strength_label))

        ttk.Button(self.main_frame, text="Reset Password", style="Success.TButton",
                   command=lambda: self.reset_password(username_var.get(), email_var.get(), new_password_var.get(), confirm_password_var.get())).grid(row=7, column=0, columnspan=3, pady=5)
        ttk.Button(self.main_frame, text="Back to Login", style="TButton",
                   command=self.show_login).grid(row=8, column=0, columnspan=3, pady=5)

        confirm_password_entry.bind("<Return>", lambda e: self.reset_password(username_var.get(), email_var.get(), new_password_var.get(), confirm_password_var.get()))

    def toggle_password(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def toggle_reset_password(self, new_password_entry, show_password_var):
        show = "" if show_password_var.get() else "*"
        new_password_entry.config(show=show)

    def update_password_strength(self, password_var, strength_label):
        password = password_var.get()
        strength, color = self.calculate_password_strength(password)
        self.strength_var.set(strength)
        strength_label.config(foreground=color)

    def calculate_password_strength(self, password):
        if len(password) < 8:
            return "Weak", "red"
        score = 0
        if re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"[a-z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1
        if re.search(r"[!@#$%^&*]", password):
            score += 1
        if score == 4:
            return "Strong", "green"
        elif score >= 2:
            return "Medium", "orange"
        return "Weak", "red"


    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        user_id = self.db.login(username, password)
        if user_id:
            self.set_user_callback(user_id)
        else:
            messagebox.showerror("Error", "Invalid username or password")
            log_error(0, f"Login attempt failed for {username}")

    def reset_password(self, username, email, new_password, confirm_password):
        if not username or not email:
            messagebox.showerror("Error", "Username and email are required")
            log_error(0, f"Password reset failed: Username or email empty")
            return
        if len(new_password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            log_error(0, f"Password reset failed for {username}: Password too short")
            return
        if not (re.search(r"[A-Z]", new_password) and re.search(r"[a-z]", new_password) and
                re.search(r"\d", new_password) and re.search(r"[!@#$%^&*]", new_password)):
            messagebox.showerror("Error", "Password must contain uppercase, lowercase, number, and special character")
            log_error(0, f"Password reset failed for {username}: Password does not meet requirements")
            return
        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            log_error(0, f"Password reset failed for {username}: Passwords do not match")
            return
        user_id = self.db.reset_password(username, email, new_password)
        if user_id:
            messagebox.showinfo("Success", "Password reset successful. Please login.")
            log_info(user_id, f"Password reset successful for {username}")
            self.show_login()
        else:
            messagebox.showerror("Error", "Invalid username or email")
            log_error(0, f"Password reset failed for {username}: Invalid username or email")
