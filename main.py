import tkinter as tk
from tkinter import ttk
from pages.login import LoginPage
from pages.signup import SignupPage
from pages.planning import PlanningPage
from pages.tracking import TrackingPage
from pages.dashboard import DashboardPage
from pages.settings import SettingsPage
from utils.database import Database
from utils.logging import setup_logging, log_info
from styles import apply_styles

class PennyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Penny")
        self.current_user = None
        setup_logging()
        apply_styles()
        self.db = Database()
        self.init_ui()
        self.check_logged_in_user()

    def init_ui(self):
        """Initialize the main application UI."""
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.pages = {
            "Login": LoginPage(self.container, self.show_page, self.set_user),
            "Signup": SignupPage(self.container, self.show_page),
            "Planning": None,  # Initialized later in set_user
            "Tracking": None,
            "Dashboard": None,
            "Settings": None
        }

        # Pack pages and hide them initially
        for page_name, page in self.pages.items():
            if page:  # Only pack initialized pages (Login, Signup)
                page.pack(fill="both", expand=True)
                page.pack_forget()

        self.geometry("400x500")
        #self.wm_state('iconic')
        self.center_window(400, 500)

    def center_window(self, width, height):
        """Center the window on the screen."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        # Allow full-screen toggling
        self.resizable(True, True)

    def set_user(self, user_id):
        """Set the current user and initialize user-specific pages."""
        self.current_user = user_id
        # Destroy old user-specific pages if they exist
        for page_name in ["Planning", "Tracking", "Dashboard", "Settings"]:
            if self.pages[page_name]:
                self.pages[page_name].pack_forget()
                self.pages[page_name].destroy()

        # Create new instances with current_user
        self.pages["Planning"] = PlanningPage(self.container, self.show_page, self.current_user)
        self.pages["Tracking"] = TrackingPage(self.container, self.show_page, self.current_user)
        self.pages["Dashboard"] = DashboardPage(self.container, self.show_page, self.current_user)
        self.pages["Settings"] = SettingsPage(self.container, self.show_page, self.current_user)

        # Pack all pages and hide them
        for page_name, page in self.pages.items():
            page.pack(fill="both", expand=True)
            page.pack_forget()

        self.geometry("1000x700")
        self.center_window(1000, 700)
        self.show_page("Dashboard")
        log_info(self.current_user, "User logged in and switched to Dashboard")

    def show_page(self, page_name):
        """Show the specified page."""
        for page in self.pages.values():
            if page:  # Skip None pages
                page.pack_forget()
        if page_name == "Planning":
            enabled = self.db.is_planning_enabled(self.current_user)
            if not enabled:
                page_name = "Dashboard"
                log_info(self.current_user, "Planning disabled, redirecting to Dashboard")
        if page_name in ["Login", "Signup"]:
            self.geometry("400x500")
            self.center_window(400, 500)
        else:
            self.geometry("1000x700")
            self.center_window(1000, 700)
        self.pages[page_name].pack(fill="both", expand=True)
        log_info(self.current_user or 0, f"Switched to {page_name} page")

    def check_logged_in_user(self):
        """Check if a user is logged in and switch to Dashboard if found."""
        user_id = self.db.get_logged_in_user()
        if user_id:
            self.current_user = user_id
            self.set_user(user_id)
        else:
            self.show_page("Login")
            log_info(0, "No logged-in user found, showing Login page")

    def destroy(self):
        """Clean up resources before closing."""
        self.db.close()
        super().destroy()

if __name__ == "__main__":
    app = PennyApp()
    app.mainloop()
