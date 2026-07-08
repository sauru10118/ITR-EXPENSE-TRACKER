# 💰 FinFlow — AI-Powered Personal Expense Tracker

A modern full-stack personal finance application built with **Python (Flask)**, **SQLite**, **HTML**, **CSS**, and **JavaScript**. FinFlow helps users manage daily finances, monitor spending habits, set monthly budgets, and automatically extract transaction details from payment screenshots and receipts using offline OCR.

---

## ✨ Key Features

### 🔐 Secure Authentication

* User registration and login system
* Password hashing for enhanced security
* Individual user accounts with isolated financial data

### 📈 Interactive Dashboard

* Real-time financial overview
* Total Income, Expenses, and Current Balance cards
* Income vs Expense trend chart
* Expense category donut chart
* Daily spending bar chart

### 💳 Transaction Management

* Add income and expense records
* View complete transaction history
* Filter transactions by type
* Delete unwanted records
* Automatic balance calculation

### 🎯 Smart Budget Planner

* Create monthly category-wise budgets
* Live budget progress indicators
* Visual progress bars
* Instant "Over Budget" alerts
* Spending analysis by category

### 🤖 AI Document Analyzer (Offline)

Upload any of the following:

* Google Pay screenshots
* PhonePe screenshots
* Paytm screenshots
* Receipt images
* Bank statements (.txt / .csv)

The application uses:

* **Tesseract OCR** for text extraction
* Local pattern matching for transaction analysis

Automatically detects:

* Transaction Type (Income / Expense)
* Amount
* Category
* Date

✅ Works completely offline
✅ No API key required
✅ Privacy-friendly document processing

---

# 🚀 Tech Stack

| Technology    | Purpose                   |
| ------------- | ------------------------- |
| Python        | Backend                   |
| Flask         | Web Framework             |
| SQLite        | Database                  |
| HTML5         | Frontend Structure        |
| CSS3          | Styling                   |
| JavaScript    | Client-side Functionality |
| Chart.js      | Data Visualization        |
| Tesseract OCR | Text Extraction           |
| Jinja2        | Template Engine           |

---

# 📂 Project Structure

```text
expense_tracker/
│
├── app.py                     # Main Flask application
├── requirements.txt           # Python dependencies
├── finflow.db                 # SQLite database (auto-created)
├── uploads/                   # Temporary uploaded files
│
├── static/
│   └── style.css              # Application styling
│
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── transactions.html
    ├── add_transaction.html
    ├── budgets.html
    └── analyzer.html
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/FinFlow.git

cd FinFlow
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Start the Application

```bash
python app.py
```

---

## 4. Open in Browser

```
http://localhost:5000
```

Create a new account using the **Register** page and start tracking your finances.

---

# 📊 Dashboard Overview

* Financial Summary Cards
* Monthly Income & Expense Trends
* Category-wise Expense Distribution
* Daily Spending Analytics
* Current Balance Monitoring

---

# 📑 Transaction Features

* Add Income
* Add Expense
* Transaction History
* Filter by Type
* Delete Transactions
* Automatic Balance Updates

---

# 💹 Budget Management

* Monthly Category Budgets
* Live Spending Progress
* Budget Usage Percentage
* Overspending Notifications
* Category Performance Tracking

---

# 🤖 AI OCR Analyzer

Supported Files:

* PNG
* JPG
* JPEG
* TXT
* CSV

Automatically extracts:

* Transaction Amount
* Date
* Category
* Income / Expense Type

No internet connection required.

---

# 🔒 Security

* Passwords stored using secure hashing
* User-specific data isolation
* Session-based authentication
* Offline OCR processing for improved privacy

---

# 📦 Database

FinFlow uses **SQLite**, making deployment simple and lightweight.

Database file:

```
finflow.db
```

Backup is as easy as copying this single file.

---

# 📌 Future Enhancements

* Export to Excel and PDF
* Dark Mode
* Email Reports
* Multi-Currency Support
* Recurring Transactions
* Cloud Backup
* Mobile Responsive Dashboard
* AI Spending Insights
* Data Import from Bank Statements
* Expense Prediction using Machine Learning

---

# 🛠 Configuration

Before deploying the application:

* Change the `app.secret_key`
* Disable Flask Debug Mode
* Use a production WSGI server (Gunicorn or Waitress)
* Store uploaded files securely

---

# 📄 License

This project is open-source and intended for educational and personal learning purposes.

---

## ⭐ If you found this project helpful, consider giving it a star on GitHub!
