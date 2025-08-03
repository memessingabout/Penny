import sqlite3
import hashlib
import re
from datetime import datetime, timedelta
from utils.logging import log_info, log_error, log_debug

class Database:
    def __init__(self, db_name="penny.db"):
        """Initialize database connection."""
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Create necessary database tables."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                bio TEXT,
                verified INTEGER DEFAULT 0,
                is_logged_in INTEGER DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                lock_until TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                currency TEXT DEFAULT 'KSh',
                savings_mode TEXT DEFAULT 'Unallocated as Savings',
                planning_enabled INTEGER DEFAULT 1,
                theme TEXT DEFAULT 'Light',
                notifications INTEGER DEFAULT 1,
                language TEXT DEFAULT 'English',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                UNIQUE(user_id, type, category),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount INTEGER NOT NULL,
                mode TEXT NOT NULL,
                details TEXT,
                flagged INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                month TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount INTEGER NOT NULL,
                recurrence TEXT,
                due TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS deleted_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                transaction_id INTEGER,
                date TEXT,
                type TEXT,
                category TEXT,
                amount INTEGER,
                mode TEXT,
                details TEXT,
                flagged INTEGER,
                deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.conn.commit()
        log_info(0, "Database tables created or verified")

    def hash_password(self, password):
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def signup(self, username, email, password):
        """Register a new user with password validation."""
        if len(password) < 8:
            log_error(0, f"Signup failed for {username}: Password too short")
            return None
        if not (re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and
                re.search(r"\d", password) and re.search(r"[!@#$%^&*]", password)):
            log_error(0, f"Signup failed for {username}: Password does not meet requirements")
            return None
        try:
            password_hash = self.hash_password(password)
            self.cursor.execute(
                "INSERT INTO users (username, email, password_hash, is_logged_in) VALUES (?, ?, ?, 1)",
                (username, email, password_hash)
            )
            user_id = self.cursor.lastrowid
            self.cursor.execute(
                "INSERT INTO settings (user_id) VALUES (?)",
                (user_id,)
            )
            self.conn.commit()
            log_info(user_id, f"User {username} signed up successfully")
            return user_id
        except sqlite3.IntegrityError as e:
            log_error(0, f"Signup failed for {username}: {str(e)}")
            return None

    def login(self, username, password):
        """Authenticate a user with rate limiting."""
        try:
            self.cursor.execute(
                "SELECT user_id, password_hash, failed_attempts, lock_until FROM users WHERE username = ?",
                (username,)
            )
            result = self.cursor.fetchone()
            if not result:
                log_error(0, f"Login failed: User {username} not found")
                return None

            user_id, stored_hash, failed_attempts, lock_until = result
            if lock_until and datetime.now() < lock_until:
                log_error(0, f"Login failed for {username}: Account locked")
                return None

            password_hash = self.hash_password(password)
            if password_hash == stored_hash:
                self.cursor.execute(
                    "UPDATE users SET failed_attempts = 0, is_logged_in = 1 WHERE user_id = ?",
                    (user_id,)
                )
                self.conn.commit()
                log_info(user_id, f"User {username} logged in")
                return user_id
            else:
                failed_attempts += 1
                lock_until = datetime.now() + timedelta(minutes=15) if failed_attempts >= 5 else None
                self.cursor.execute(
                    "UPDATE users SET failed_attempts = ?, lock_until = ? WHERE user_id = ?",
                    (failed_attempts, lock_until, user_id)
                )
                self.conn.commit()
                log_error(0, f"Login failed for {username}: Invalid password")
                return None
        except sqlite3.Error as e:
            log_error(0, f"Database error during login: {str(e)}")
            return None

    def logout(self, user_id):
        """Log out a user by resetting their login state."""
        try:
            self.cursor.execute(
                "UPDATE users SET is_logged_in = 0 WHERE user_id = ?",
                (user_id,)
            )
            self.conn.commit()
            log_info(user_id, "User logged out")
        except sqlite3.Error as e:
            log_error(user_id, f"Logout failed: {str(e)}")

    def reset_password(self, username, email, new_password):
        """Reset a user's password with rate limiting and validation."""
        if len(new_password) < 8:
            log_error(0, f"Password reset failed for {username}: Password too short")
            return None
        if not (re.search(r"[A-Z]", new_password) and re.search(r"[a-z]", new_password) and
                re.search(r"\d", new_password) and re.search(r"[!@#$%^&*]", new_password)):
            log_error(0, f"Password reset failed for {username}: Password does not meet requirements")
            return None
        try:
            self.cursor.execute(
                "SELECT user_id, email, failed_attempts, lock_until FROM users WHERE username = ?",
                (username,)
            )
            result = self.cursor.fetchone()
            if not result:
                log_error(0, f"Password reset failed: User {username} not found")
                return None

            user_id, stored_email, failed_attempts, lock_until = result
            if lock_until and datetime.now() < lock_until:
                log_error(0, f"Password reset failed for {username}: Account locked")
                return None

            if email == stored_email:
                password_hash = self.hash_password(new_password)
                self.cursor.execute(
                    "UPDATE users SET password_hash = ?, failed_attempts = 0 WHERE user_id = ?",
                    (password_hash, user_id)
                )
                self.conn.commit()
                log_info(user_id, f"Password reset for {username}")
                return user_id
            else:
                failed_attempts += 1
                lock_until = datetime.now() + timedelta(minutes=15) if failed_attempts >= 3 else None
                self.cursor.execute(
                    "UPDATE users SET failed_attempts = ?, lock_until = ? WHERE user_id = ?",
                    (failed_attempts, lock_until, user_id)
                )
                self.conn.commit()
                log_error(0, f"Password reset failed for {username}: Invalid email")
                return None
        except sqlite3.Error as e:
            log_error(0, f"Database error during reset: {str(e)}")
            return None

    def get_logged_in_user(self):
        """Retrieve the currently logged-in user, if any."""
        try:
            self.cursor.execute("SELECT user_id FROM users WHERE is_logged_in = 1")
            result = self.cursor.fetchone()
            if result:
                log_debug(result[0], "Retrieved logged-in user")
                return result[0]
            log_debug(0, "No logged-in user found")
            return None
        except sqlite3.Error as e:
            log_error(0, f"Error checking logged-in user: {str(e)}")
            return None

    def username_exists(self, username, exclude_user_id=None):
        """Check if a username exists, optionally excluding a user ID."""
        query = "SELECT 1 FROM users WHERE username = ?"
        params = [username]
        if exclude_user_id:
            query += " AND user_id != ?"
            params.append(exclude_user_id)
        self.cursor.execute(query, params)
        exists = bool(self.cursor.fetchone())
        log_debug(0 if not exclude_user_id else exclude_user_id, f"Checked username {username}: exists={exists}")
        return exists

    def email_exists(self, email, exclude_user_id=None):
        """Check if an email exists, optionally excluding a user ID."""
        query = "SELECT 1 FROM users WHERE email = ?"
        params = [email]
        if exclude_user_id:
            query += " AND user_id != ?"
            params.append(exclude_user_id)
        self.cursor.execute(query, params)
        exists = bool(self.cursor.fetchone())
        log_debug(0 if not exclude_user_id else exclude_user_id, f"Checked email {email}: exists={exists}")
        return exists

    def get_user_profile(self, user_id):
        """Retrieve a user's profile information."""
        try:
            self.cursor.execute("SELECT username, email, bio FROM users WHERE user_id = ?", (user_id,))
            profile = self.cursor.fetchone()
            log_debug(user_id, f"Retrieved profile: {profile}")
            return profile
        except sqlite3.Error as e:
            log_error(user_id, f"Error retrieving profile: {str(e)}")
            return None

    def update_user_profile(self, user_id, username, email, bio):
        """Update a user's profile information."""
        try:
            self.cursor.execute(
                "UPDATE users SET username = ?, email = ?, bio = ? WHERE user_id = ?",
                (username, email, bio, user_id)
            )
            self.conn.commit()
            log_info(user_id, f"Updated profile: username={username}, email={email}")
            return True
        except sqlite3.IntegrityError as e:
            log_error(user_id, f"Update profile failed: {str(e)}")
            return False

    def get_settings(self, user_id):
        """Retrieve user settings."""
        try:
            self.cursor.execute(
                "SELECT currency, savings_mode, planning_enabled, theme, notifications, language FROM settings WHERE user_id = ?",
                (user_id,)
            )
            settings = self.cursor.fetchone()
            log_debug(user_id, f"Retrieved settings: {settings}")
            return settings
        except sqlite3.Error as e:
            log_error(user_id, f"Error retrieving settings: {str(e)}")
            return None

    def update_settings(self, user_id, currency, savings_mode, planning_enabled, theme, notifications, language):
        """Update user settings."""
        try:
            self.cursor.execute(
                "UPDATE settings SET currency = ?, savings_mode = ?, planning_enabled = ?, theme = ?, notifications = ?, language = ? WHERE user_id = ?",
                (currency, savings_mode, planning_enabled, theme, notifications, language, user_id)
            )
            self.conn.commit()
            log_info(user_id, f"Updated settings: currency={currency}, planning_enabled={planning_enabled}")
            return True
        except sqlite3.IntegrityError as e:
            log_error(user_id, f"Update settings failed: {str(e)}")
            return False

    def is_planning_enabled(self, user_id):
        """Check if planning is enabled for the user."""
        try:
            self.cursor.execute("SELECT planning_enabled FROM settings WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            enabled = result[0] if result else True
            log_debug(user_id, f"Planning enabled: {enabled}")
            return enabled
        except sqlite3.Error as e:
            log_error(user_id, f"Error checking planning enabled: {str(e)}")
            return True

    def get_categories(self, user_id, type=None):
        """Retrieve categories for a user."""
        query = "SELECT category FROM categories WHERE user_id = ?"
        params = [user_id]
        if type:
            query += " AND type = ?"
            params.append(type)
        try:
            self.cursor.execute(query, params)
            categories = [row[0] for row in self.cursor.fetchall()]
            log_debug(user_id, f"Retrieved categories for type {type}: {categories}")
            return categories
        except sqlite3.Error as e:
            log_error(user_id, f"Error retrieving categories: {str(e)}")
            return []

    def add_category(self, user_id, type, category):
        """Add a new category for a user."""
        try:
            self.cursor.execute(
                "INSERT INTO categories (user_id, type, category) VALUES (?, ?, ?)",
                (user_id, type, category)
            )
            self.conn.commit()
            log_info(user_id, f"Added category: {type}/{category}")
            return True
        except sqlite3.IntegrityError:
            log_debug(user_id, f"Category {type}/{category} already exists")
            return False

    def update_category(self, user_id, old_type, old_category, new_type, new_category):
        """Update a category for a user."""
        try:
            self.cursor.execute(
                "UPDATE categories SET type = ?, category = ? WHERE user_id = ? AND type = ? AND category = ?",
                (new_type, new_category, user_id, old_type, old_category)
            )
            self.cursor.execute(
                "UPDATE plans SET type = ?, category = ? WHERE user_id = ? AND type = ? AND category = ?",
                (new_type, new_category, user_id, old_type, old_category)
            )
            self.cursor.execute(
                "UPDATE transactions SET type = ?, category = ? WHERE user_id = ? AND type = ? AND category = ?",
                (new_type, new_category, user_id, old_type, old_category)
            )
            self.conn.commit()
            log_info(user_id, f"Updated category: {old_type}/{old_category} to {new_type}/{new_category}")
            return True
        except sqlite3.IntegrityError as e:
            log_error(user_id, f"Update category failed: {str(e)}")
            return False

    def delete_category(self, user_id, type, category):
        """Delete a category if not used in transactions or plans."""
        try:
            self.cursor.execute(
                "SELECT 1 FROM transactions WHERE user_id = ? AND type = ? AND category = ?",
                (user_id, type, category)
            )
            if self.cursor.fetchone():
                log_error(user_id, f"Cannot delete category {type}/{category}: used in transactions")
                return False
            self.cursor.execute(
                "SELECT 1 FROM plans WHERE user_id = ? AND type = ? AND category = ?",
                (user_id, type, category)
            )
            if self.cursor.fetchone():
                log_error(user_id, f"Cannot delete category {type}/{category}: used in plans")
                return False
            self.cursor.execute(
                "DELETE FROM categories WHERE user_id = ? AND type = ? AND category = ?",
                (user_id, type, category)
            )
            self.conn.commit()
            log_info(user_id, f"Deleted category: {type}/{category}")
            return True
        except sqlite3.Error as e:
            log_error(user_id, f"Delete category failed: {str(e)}")
            return False

    def get_plans(self, user_id, month):
        """Retrieve budget plans for a user and month."""
        try:
            if month.startswith("Total"):
                year = month.split()[-1]
                query = "SELECT type, category, SUM(amount), recurrence, due FROM plans WHERE user_id = ? AND month LIKE ? GROUP BY type, category, recurrence, due ORDER BY type, SUM(amount) DESC"
                params = (user_id, f"% {year}")
            else:
                query = "SELECT type, category, amount, recurrence, due FROM plans WHERE user_id = ? AND month = ? ORDER BY type, amount DESC"
                params = (user_id, month)
            self.cursor.execute(query, params)
            plans = self.cursor.fetchall()
            log_debug(user_id, f"Retrieved plans for {month}: {len(plans)} entries")
            return plans
        except sqlite3.Error as e:
            log_error(user_id, f"Error retrieving plans: {str(e)}")
            return []

    def add_plan(self, user_id, month, type, category, amount, recurrence, due):
        """Add a budget plan for a user."""
        try:
            self.cursor.execute(
                "INSERT INTO plans (user_id, month, type, category, amount, recurrence, due) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, month, type, category, amount, recurrence, due)
            )
            self.add_category(user_id, type, category)
            self.conn.commit()
            log_info(user_id, f"Added plan: {month}, {type}/{category}, KSh {amount}")
            return True
        except sqlite3.Error as e:
            log_error(user_id, f"Add plan failed: {str(e)}")
            return False

    def copy_plan(self, user_id, from_month, to_month):
        """Copy budget plans from one month to another."""
        try:
            self.cursor.execute(
                "SELECT type, category, amount, recurrence, due FROM plans WHERE user_id = ? AND month = ?",
                (user_id, from_month)
            )
            plans = self.cursor.fetchall()
            for plan in plans:
                self.cursor.execute(
                    "INSERT INTO plans (user_id, month, type, category, amount, recurrence, due) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, to_month, *plan)
                )
            self.conn.commit()
            log_info(user_id, f"Copied plan from {from_month} to {to_month}")
            return True
        except sqlite3.Error as e:
            log_error(user_id, f"Copy plan failed: {str(e)}")
            return False

    def get_transactions(self, user_id, date_filter, start_date=None, end_date=None):
        """Retrieve transactions based on a date filter."""
        try:
            query = "SELECT id, date, type, category, amount, mode, details, flagged FROM transactions WHERE user_id = ?"
            params = [user_id]
            if date_filter == "Today":
                query += " AND date = ?"
                params.append(datetime.now().strftime("%b %d %Y"))
            elif date_filter == "Week":
                query += " AND date >= ? AND date <= ?"
                params.extend([self.get_week_start(), self.get_week_end()])
            elif date_filter == "Month":
                query += " AND date LIKE ?"
                params.append(f"{datetime.now().strftime('%b')} % {datetime.now().year}")
            elif date_filter == "Year":
                query += " AND date LIKE ?"
                params.append(f"% {datetime.now().year}")
            elif date_filter == "Range" and start_date and end_date:
                start_date_converted = datetime.strptime(start_date, "%m/%d/%Y").strftime("%b %d %Y")
                end_date_converted = datetime.strptime(end_date, "%m/%d/%Y").strftime("%b %d %Y")
                query += " AND date >= ? AND date <= ?"
                params.extend([start_date_converted, end_date_converted])
            query += " ORDER BY date DESC"
            self.cursor.execute(query, params)
            transactions = self.cursor.fetchall()
            log_debug(user_id, f"Retrieved {len(transactions)} transactions for filter {date_filter}")
            return transactions
        except sqlite3.Error as e:
            log_error(user_id, f"Error retrieving transactions: {str(e)}")
            return []

    def get_recent_transactions(self, user_id, limit=5):
        """Retrieve recent transactions for a user."""
        try:
            self.cursor.execute(
                "SELECT date, type, category, amount, mode, details FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT ?",
                (user_id, limit)
            )
            transactions = self.cursor.fetchall()
            log_debug(user_id, f"Retrieved {len(transactions)} recent transactions")
            return transactions
        except sqlite3.Error as e:
            log_error(user_id, f"Error retrieving recent transactions: {str(e)}")
            return []

    def get_monthly_trends(self, user_id, months=6):
        """Retrieve monthly financial trends for a user."""
        try:
            trends = []
            current_date = datetime.now()
            for i in range(months):
                month = (current_date.month - i - 1) % 12 + 1
                year = current_date.year - (1 if current_date.month - i - 1 < 1 else 0)
                month_str = datetime(year, month, 1).strftime("%b %Y")
                self.cursor.execute(
                    "SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND date LIKE ? GROUP BY type",
                    (user_id, f"{month_str}%")
                )
                result = dict(self.cursor.fetchall())
                income = result.get("Income", 0)
                expenses = result.get("Expenses", 0)
                savings = result.get("Savings", 0)
                balance = income - expenses - savings
                trends.append((month_str, income, expenses, savings, balance))
            log_debug(user_id, f"Retrieved trends for {months} months")
            return trends[::-1]
        except sqlite3.Error as e:
            log_error(user_id, f"Error retrieving monthly trends: {str(e)}")
            return []

    def add_transaction(self, user_id, date, type, category, amount, mode, details):
        """Add a new transaction for a user."""
        try:
            self.cursor.execute(
                "SELECT 1 FROM plans WHERE user_id = ? AND type = ? AND category = ? AND month = ?",
                (user_id, type, category, datetime.now().strftime("%B %Y"))
            )
            flagged = 0 if self.cursor.fetchone() else 1
            self.cursor.execute(
                "INSERT INTO transactions (user_id, date, type, category, amount, mode, details, flagged) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, date, type, category, amount, mode, details, flagged)
            )
            self.add_category(user_id, type, category)
            self.conn.commit()
            log_info(user_id, f"Added transaction: {date}, {type}/{category}, KSh {amount}")
            return True
        except sqlite3.Error as e:
            log_error(user_id, f"Add transaction failed: {str(e)}")
            return False

    def delete_transaction(self, user_id, transaction_id):
        """Delete a transaction and store it in deleted_transactions."""
        try:
            self.cursor.execute(
                "SELECT id, date, type, category, amount, mode, details, flagged FROM transactions WHERE user_id = ? AND id = ?",
                (user_id, transaction_id)
            )
            transaction = self.cursor.fetchone()
            if transaction:
                self.cursor.execute(
                    "INSERT INTO deleted_transactions (user_id, transaction_id, date, type, category, amount, mode, details, flagged) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, transaction[0], *transaction[1:])
                )
                self.cursor.execute(
                    "DELETE FROM transactions WHERE user_id = ? AND id = ?",
                    (user_id, transaction_id)
                )
                self.conn.commit()
                log_info(user_id, f"Deleted transaction: ID {transaction_id}")
                return True
            log_error(user_id, f"Transaction ID {transaction_id} not found")
            return False
        except sqlite3.Error as e:
            log_error(user_id, f"Delete transaction failed: {str(e)}")
            return False

    def undo_delete(self, user_id):
        """Undo the last deleted transaction."""
        try:
            self.cursor.execute(
                "SELECT transaction_id, date, type, category, amount, mode, details, flagged FROM deleted_transactions WHERE user_id = ? ORDER BY deleted_at DESC LIMIT 1",
                (user_id,)
            )
            transaction = self.cursor.fetchone()
            if transaction:
                self.cursor.execute(
                    "INSERT INTO transactions (id, user_id, date, type, category, amount, mode, details, flagged) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (transaction[0], user_id, *transaction[1:])
                )
                self.cursor.execute(
                    "DELETE FROM deleted_transactions WHERE user_id = ? AND transaction_id = ?",
                    (user_id, transaction[0])
                )
                self.conn.commit()
                log_info(user_id, f"Undid deletion of transaction: ID {transaction[0]}")
                return True
            log_error(user_id, "No transaction to undo")
            return False
        except sqlite3.Error as e:
            log_error(user_id, f"Undo delete failed: {str(e)}")
            return False

    def get_week_start(self):
        """Get the start date of the current week."""
        from datetime import timedelta
        today = datetime.now()
        return (today - timedelta(days=today.weekday())).strftime("%b %d %Y")

    def get_week_end(self):
        """Get the end date of the current week."""
        from datetime import timedelta
        today = datetime.now()
        return (today + timedelta(days=6 - today.weekday())).strftime("%b %d %Y")

    def close(self):
        """Close the database connection."""
        self.conn.close()
        log_info(0, "Database connection closed")