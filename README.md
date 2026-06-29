# FinFlow — Personal Expense Tracker

A full-stack expense tracker built with **Python (Flask)** + **SQLite** + **HTML/CSS/JS**.

## Features
- 🔐 **Login & Register** — secure password hashing, SQLite-backed user accounts
- 📊 **Dashboard** — income/expense/balance stat cards, trend line chart, category donut chart, daily bar chart
- 📋 **Transactions** — add, view, filter (income/expense), delete
- 🎯 **Budget Setter** — set a monthly ₹ limit per category, see live progress bars, get an "over budget" warning
- 🤖 **AI Document Analyzer** — upload a **Google Pay / PhonePe / Paytm screenshot**, a receipt photo, or a `.txt`/`.csv` bank statement. The app uses **OCR (Tesseract)** to read the image text, then local pattern-matching extracts the type (income/expense), amount, category, and date — all **100% offline, no API key required**.

## Setup

### 1. Install Tesseract OCR (required for image analysis)
- **Windows:** download & install from https://github.com/UB-Mannheim/tesseract/wiki
- **Mac:** `brew install tesseract`
- **Linux (Ubuntu/Debian):** `sudo apt install tesseract-ocr`

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open your browser
Go to **http://localhost:5000** — you'll land on the login page. Click "Register" to create your first account.

## Project Structure
```
expense_tracker/
├── app.py                 # Flask app — all routes, DB logic, OCR engine
├── requirements.txt
├── finflow.db              # SQLite database (auto-created on first run)
├── uploads/                # temp storage for uploaded files (auto-cleared)
├── static/
│   └── style.css           # all styling — white theme, black navbar
└── templates/
    ├── base.html            # shared layout + navbar
    ├── login.html
    ├── register.html
    ├── dashboard.html       # charts via Chart.js (CDN)
    ├── transactions.html
    ├── add_transaction.html
    ├── budgets.html
    └── analyzer.html        # OCR upload + results UI
```

## How the AI Analyzer works (no API key needed)
1. You upload an image (screenshot) or text file, or paste text directly.
2. If it's an image, **Tesseract OCR** extracts raw text from it.
3. The app scans each line for:
   - An amount (₹, Rs., INR, or $ followed by a number)
   - Keywords like "paid", "debited", "received", "credited" to guess income vs expense
   - Merchant keywords (e.g. "swiggy", "amazon", "uber") to guess the category
   - A date pattern, falling back to today's date if none is found
4. Extracted transactions are shown for review, then you click **Import All** to save them to your account.

### Tips for best OCR results
- Use clear, well-lit screenshots (not blurry photos)
- Cropped screenshots showing just the transaction line work best
- For bank statements, plain `.txt` or `.csv` exports give the most accurate results

## Notes
- Change `app.secret_key` in `app.py` before deploying anywhere public.
- The database is a single file (`finflow.db`) — back it up by simply copying that file.
- Each user only sees their own transactions and budgets (enforced at the query level).
