# Penny Budgeting Tool (Version 0.1)

Penny is a desktop application for personal budgeting, built with Python and Tkinter. It helps users track income, expenses, and savings, create financial plans, and visualize spending trends.

## Features
- **Dashboard**: View balances, monthly trends (bar/pie charts), and recent transactions.
- **Planning**: Create budgets for income, expenses, and savings (up to 2035), with category management and zero-based budgeting status.
- **Tracking**: Record and filter transactions, with undo delete and flagging for unplanned categories.
- **Settings**: Customize currency, savings mode, theme, notifications, language, and profile.
- **Security**: Local SQLite database (`penny.db`) with hashed passwords (SHA-256).
- **Logging**: Detailed error logging (`penny_errors.log`) with rotation.
- **UI**: 1000x700 main window, 400x400 login/signup, responsive navigation (Dashboard, Planning, Tracking, Settings).

## Installation
1. **Prerequisites**:
   - Python 3.8+
   - Install dependencies: `pip install tkcalendar matplotlib`
2. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd penny
   ```

3. **Directory Structure**:
```text
penny/
├── main.py
├── pages/
│   ├── login.py
│   ├── signup.py
│   ├── planning.py
│   ├── tracking.py
│   ├── dashboard.py
│   ├── settings.py
├── utils/
│   ├── database.py
│   ├── logging.py
├── styles.py
├── penny.db
├── penny_errors.log
├── TERMS_AND_CONDITIONS.md
├── PRIVACY_POLICY.md
├── README.md
├── LICENSE
```
4. **Run the App**:
```Bash
python main.py
```

## Usage
1. **Signup/Login**:
- Create an account (username, email, password ≥ 6 characters).
- Use the Show Password checkbox to verify input.
- Login/Signup buttons are on separate lines.

2. **Dashboard**:
- View balances (Cash/Mpesa), totals, and charts.
- See up to 5 recent transactions.

3. **Planning**:
- Select months (January–December, Total , 2025–2035).
- Add/edit/delete categories with tooltips.
- Set plans with recurrence (Weekly: day, Monthly: date, None).
- Copy plans between months.
- Bold zero-based budget status (Balanced/Overbudget/Underbudget).

4. **Tracking**:
- Add transactions (date in mm/dd/yyyy, stored as %b %d %Y).
- Filter by All/Today/Week/Month/Year/Range.
- Quick Add (default: KSh 50,000 Salary) and Undo Delete.
- Flagged transactions (yellow) prompt adding to plans.

5. **Settings**:
- Edit profile (username, email, bio).
- Set preferences (currency, savings mode, planning enabled, theme, notifications, language).
- Logout to return to Login page.

### Testing
1. **Setup**:
- Ensure `penny.db` is created on first run.
- Check `penny_errors.log` for debugging.

2. **Test Cases**:
- **Login/Signup**: Verify Show Password, button layout, and error handling (e.g., weak password).
- **Navigation**: Confirm order (Dashboard, Planning, Tracking, Settings) and Planning toggle.
- **Planning**: Test month dropdown (2025–2035), category edit/delete, recurrence validation, and logging.
- **Tracking**: Validate date format, filters, flagging, and undo delete.
- **Dashboard**: Check charts, balances, and recent transactions.
- **Settings**: Test profile edits, preference saving, and logout (resizes to 400x400).

3. **Debugging**:
- Monitor `penny_errors.log` for INFO/ERROR/DEBUG logs.
Test edge cases: empty categories, 2035 plans, invalid dates.

## Future Enhancements
- Add filter presets (e.g., Last 30 Days).
- Suggest recurring categories based on transaction history.
- Implement CAPTCHA for failed logins.
- Add session timeout.
- Enhance chart interactivity.

## License
Penny is licensed under the MIT License. See `LICENSE` for details.

## Contact
For support or contributions, email support@pennyapp.example.com or open an issue on the repository.

