import tkinter as tk
from tkinter import ttk, messagebox
from utils.database import Database
from utils.logging import log_info, log_error
from styles import apply_styles
import re

class SignupPage(tk.Frame):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.db = Database()
        apply_styles()
        self.init_ui()

    def init_ui(self):
        self.pack(fill="both", expand=True)
        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both", padx=20, pady=20)
        main_frame = ttk.Frame(outer_frame, relief="groove", borderwidth=2, padding=10)
        main_frame.pack(padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Signup", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10)

        ttk.Label(main_frame, text="Username:").grid(row=1, column=0, sticky="e", pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.username_var).grid(row=1, column=1, pady=5)

        ttk.Label(main_frame, text="Email:").grid(row=2, column=0, sticky="e", pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.email_var).grid(row=2, column=1, pady=5)

        ttk.Label(main_frame, text="Password:").grid(row=3, column=0, sticky="e", pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=3, column=1, pady=5)
        self.show_password_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="", variable=self.show_password_var,
                        command=self.toggle_password).grid(row=3, column=2, sticky="w", pady=5)
        
        ttk.Label(main_frame, text="Confirm:").grid(row=4, column=0, sticky="e", pady=5)
        self.confirm_var = tk.StringVar()
        self.confirm_entry = ttk.Entry(main_frame, textvariable=self.confirm_var, show="*")
        self.confirm_entry.grid(row=4, column=1, pady=5)

        ttk.Label(main_frame, text="Password must be: At least 8 characters, contain uppercase, lowercase, number, and special character",
              wraplength=300, justify="left").grid(row=6, column=0, columnspan=3, pady=5)

        self.strength_var = tk.StringVar(value="Weak")
        strength_label = ttk.Label(main_frame, textvariable=self.strength_var, foreground="red")
        strength_label.grid(row=5, column=0, columnspan=2, pady=5)
        self.password_var.trace("w", lambda *args: self.update_password_strength(self.password_var, strength_label))

        ttk.Button(main_frame, text="Signup", style="Success.TButton", command=self.signup).grid(row=7, column=0, columnspan=3, pady=5)
        ttk.Button(main_frame, text="Login", command=lambda: self.switch_page_callback("Login")).grid(row=8, column=0, columnspan=3, pady=5)

        self.password_entry.bind("<Return>", lambda e: self.signup())

    def toggle_password(self):
        show = "" if self.show_password_var.get() else "*"
        self.password_entry.config(show=show)

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

    def signup(self):
        username = self.username_var.get().strip()
        email = self.email_var.get().strip()
        password = self.password_var.get()
        confirm_password = self.confirm_var.get()

        if not username or len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters")
            log_error(0, f"Signup failed: Invalid username length")
            return
        if not email or "@" not in email:
            messagebox.showerror("Error", "Invalid email format")
            log_error(0, f"Signup failed: Invalid email format: {email}")
            return
        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            log_error(0, f"Signup failed for {username}: Password too short")
            return
        if not (re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and
                re.search(r"\d", password) and re.search(r"[!@#$%^&*]", password)):
            messagebox.showerror("Error", "Password must contain uppercase, lowercase, number, and special character")
            log_error(0, f"Signup failed for {username}: Password does not meet requirements")
            return
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            log_error(0, f"Signup failed for {username}: Passwords do not match")
            return
        user_id = self.db.signup(username, email, password)
        if user_id:
            messagebox.showinfo("Success", "Signup successful! Please login.")
            log_info(user_id, f"User {username} signed up")
            self.switch_page_callback("Login")
        else:
            messagebox.showerror("Error", "Username or email already exists")
            log_error(0, f"Signup failed for {username}: Username or email exists")