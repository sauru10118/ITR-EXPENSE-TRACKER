# FinFlow — Personal Expense Tracker

A full-stack, aesthetically rich expense tracker built with **Python (Flask)** + **SQLite** + **HTML/CSS/JS**.

## Features
- 🔐 **Login & Register** — Secure user accounts with **Real Email OTP Verification** powered by Gmail SMTP. Supports multiple accounts per email.
- 📊 **Dashboard** — Interactive income/expense stat cards, trend line charts, category donut charts, and daily bar charts.
- 📋 **Transactions** — Add, view, filter (income/expense), and delete records easily.
- 🎯 **Budget Setter** — Set monthly limits per category with visual progress bars and dynamic "over budget" warnings.
- 🤖 **AI Document Analyzer** — Upload screenshots (GPay/PhonePe) or text/csv bank statements. Uses Windows Native OCR and Gemini AI for intelligent, automated transaction extraction.

## Setup

### 1. Install Python dependencies
Make sure you have Python installed, then run:
```bash
pip install -r requirement.txt
```

### 2. Configure Email Settings (For OTP)
Open `app.py` and ensure the email and App Password variables are set to your Gmail account so the app can send real OTP verification emails during registration.

### 3. Run the app
```bash
python app.py
```

### 4. Open your browser
Go to **http://localhost:5000** — you'll land on the login page. Click "Register" to create your first account. You will receive an email with a 6-digit code to verify your account!

## Project Structure
```
expense_tracker/
├── app.py                 # Core Flask app — routes, DB logic, OTP & OCR integration
├── requirement.txt        # All Python dependencies
├── finflow.db             # SQLite database (auto-created on first run)
├── uploads/               # Temporary storage for uploaded files (auto-cleared)
├── static/
│   └── style.css          # Rich, modern UI styles with smooth gradients and hover effects
└── templates/
    ├── base.html          # Shared layout & navigation
    ├── login.html         # Login page
    ├── register.html      # Registration page
    ├── verify_otp.html    # Interactive 6-digit OTP verification page
    ├── dashboard.html     # Charts (Chart.js) and stat grid
    ├── transactions.html  # Transaction table and filters
    ├── add_transaction.html 
    ├── budgets.html       # Monthly budget forms
    └── analyzer.html      # AI upload and results UI
```

## Notes
- Change `app.secret_key` in `app.py` before deploying anywhere public.
- The database is a single file (`finflow.db`) — back it up by simply copying that file.
- Each user securely sees only their own transactions and budgets.
