# Privacy Policy for Penny Budgeting Tool

**Effective Date: August 3, 2025**

At Penny, we value your privacy. This Privacy Policy explains how we handle your data when you use the Penny Budgeting Tool.

## 1. Information We Collect
- **User-Provided Information**: When you sign up, you provide:
  - Username
  - Email address
  - Password (stored as a SHA-256 hash)
  - Optional bio
- **Financial Data**: You may enter financial information, including:
  - Transactions (date, type, category, amount, mode, details)
  - Budget plans (month, type, category, amount, recurrence, due dates)
  - Categories (type, name)
- **Settings**: Preferences such as currency, savings mode, theme, notifications, and language.
- **Log Data**: We collect logs for debugging, stored in `penny_errors.log`, including:
  - Timestamps
  - User ID
  - Actions (e.g., login, transaction add)
  - Errors with stack traces

## 2. How We Use Your Information
- **Local Storage**: All data is stored locally in a SQLite database (`penny.db`) on your device.
- **Functionality**: Your data is used to:
  - Display budgets, transactions, and plans.
  - Generate charts and summaries on the Dashboard.
  - Apply your preferences (e.g., currency, theme).
- **Debugging**: Log data helps us diagnose issues and improve Penny.
- **No External Sharing**: Penny does not transmit your data to servers or third parties in version 0.1.

## 3. Data Storage and Security
- **Local Database**: Data is stored in `penny.db` on your device. You are responsible for securing your device.
- **Password Security**: Passwords are hashed using SHA-256 before storage.
- **Log Security**: Logs are stored in `penny_errors.log` with rotation to prevent excessive file size.
- **Limitations**: While we implement reasonable security measures (e.g., hashing), you are responsible for protecting your device from unauthorized access.

## 4. Your Choices
- **Data Access**: You can view and edit your data via the Settings and Planning pages.
- **Data Deletion**: Delete your data by:
  - Removing the `penny.db` file.
  - Uninstalling Penny.
- **Logs**: Delete `penny_errors.log` to remove debugging logs.

## 5. Children’s Privacy
Penny is not intended for users under 18. We do not knowingly collect data from children.

## 6. Changes to This Policy
We may update this Privacy Policy. Check the Effective Date to see the latest version. Continued use of Penny constitutes acceptance of the updated policy.

## 7. Contact
For privacy-related questions, contact us at privacy@pennyapp.example.com.

By using Penny, you acknowledge that you have read and understood this Privacy Policy.