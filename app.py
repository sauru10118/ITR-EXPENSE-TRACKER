"""
FinFlow — Personal Expense Tracker
Flask + Flask-SQLAlchemy 3.1.1 + Gemini AI Vision Analyzer

Setup:
    pip install Flask-SQLAlchemy==3.1.1 google-genai pillow
    python app.py
"""

import os
import json
from datetime import datetime, date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from google import genai

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv)

# ── Config ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "finflow.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "txt", "csv"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "finflow-dev-secret-change-this-in-production"
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload limit

# Flask-SQLAlchemy Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CATEGORIES = ["Food", "Transport", "Housing", "Entertainment", "Health",
              "Shopping", "Salary", "Freelance", "Investment", "Other"]


# ── Gemini AI Configuration ──────────────────────────────────────────────────

GEMINI_API_KEY = os.environ('gemini_api_key')

client = genai.Client()


# ── Database setup (Flask-SQLAlchemy 3.1.1) ──────────────────────────────────
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Database Models
class User(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)

class Transaction(db.Model):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)

    def to_dict(self):
        """Helper to convert object to dict for backward compatibility with templates"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Budget(db.Model):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    monthly_limit: Mapped[float] = mapped_column(Float, nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Initialize Database tables
with app.app_context():
    db.create_all()


# ── Auth helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ── Simple AI Analyzer (Gemini) ──────────────────────────────────────────────
def analyze_with_ai(file_path=None, raw_text=None):
    """Passes the image or text to Gemini and gets a clean JSON array back."""
    
    prompt = """
    Analyze this financial document, receipt, screenshot, or text. Extract the transactions into a strict JSON array.
    Each object must exactly match this format:
    {
      "type": "income" or "expense",
      "amount": numeric_value,
      "category": "Food", "Transport", "Housing", "Entertainment", "Health", "Shopping", "Salary", "Freelance", "Investment", or "Other",
      "description": "Short 3-5 word summary",
      "date": "YYYY-MM-DD"
    }
    Respond ONLY with the raw JSON array. Do not include markdown formatting like ```json.
    """
    
    try:
        if file_path:
            img = Image.open(file_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[prompt, img]
            )
        else:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[prompt, raw_text]
            )
            
        # Clean up the response to ensure it parses correctly
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"Gemini AI Error: {e}")
        return []


# ── Routes: Auth ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            created_at=datetime.now().isoformat()
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except IntegrityError:
            db.session.rollback()
            flash("Username or email already exists.", "error")
            return render_template("register.html")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        # Search by username OR email
        user = db.session.execute(
            db.select(User).where((User.username == identifier) | (User.email == identifier))
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))
        
        flash("Invalid username/email or password.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Routes: Dashboard ────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    
    txns_objs = db.session.execute(
        db.select(Transaction).where(Transaction.user_id == uid).order_by(Transaction.date.desc())
    ).scalars().all()
    
    budgets_objs = db.session.execute(
        db.select(Budget).where(Budget.user_id == uid)
    ).scalars().all()

    txns = [t.to_dict() for t in txns_objs]
    budgets = [b.to_dict() for b in budgets_objs]

    total_income = sum(t["amount"] for t in txns if t["type"] == "income")
    total_expense = sum(t["amount"] for t in txns if t["type"] == "expense")
    balance = total_income - total_expense

    cat_totals = {}
    for t in txns:
        if t["type"] == "expense":
            cat_totals[t["category"]] = cat_totals.get(t["category"], 0) + t["amount"]

    daily = {}
    for t in txns:
        d = t["date"]
        daily.setdefault(d, {"date": d, "income": 0, "expense": 0})
        daily[d][t["type"]] += t["amount"]
    daily_series = sorted(daily.values(), key=lambda x: x["date"])

    this_month = datetime.now().strftime("%Y-%m")
    budget_progress = []
    for b in budgets:
        spent = sum(
            t["amount"] for t in txns
            if t["category"] == b["category"] and t["type"] == "expense" and t["date"].startswith(this_month)
        )
        pct = min(100, round((spent / b["monthly_limit"]) * 100, 1)) if b["monthly_limit"] > 0 else 0
        
        # New color logic
        if pct < 25: color_class = "bar-green"
        elif pct < 50: color_class = "bar-blue"
        elif pct < 80: color_class = "bar-orange"
        else: color_class = "bar-red"
        
        budget_progress.append({
            "category": b["category"], "limit": b["monthly_limit"],
            "spent": spent, "pct": pct, "color": color_class, "over": spent > b["monthly_limit"]
        })

    return render_template(
        "dashboard.html",
        username=session.get("username"),
        transactions=txns,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        cat_totals=cat_totals,
        daily_series=daily_series,
        budget_progress=budget_progress,
        categories=CATEGORIES,
    )


# ── Routes: Transactions ─────────────────────────────────────────────────────
@app.route("/transactions")
@login_required
def transactions_page():
    uid = session["user_id"]
    filt = request.args.get("filter", "all")
    
    query = db.select(Transaction).where(Transaction.user_id == uid).order_by(Transaction.date.desc())
    if filt in ("income", "expense"):
        query = query.where(Transaction.type == filt)
        
    txns_objs = db.session.execute(query).scalars().all()
    txns = [t.to_dict() for t in txns_objs]

    return render_template("transactions.html", transactions=txns, filt=filt, username=session.get("username"))

@app.route("/transactions/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    if request.method == "POST":
        new_txn = Transaction(
            user_id=session["user_id"],
            type=request.form["type"],
            amount=float(request.form["amount"]),
            category=request.form["category"],
            description=request.form.get("description", ""),
            date=request.form["date"],
            created_at=datetime.now().isoformat()
        )
        db.session.add(new_txn)
        db.session.commit()
        
        flash("Transaction added!", "success")
        return redirect(url_for("transactions_page"))
    
    return render_template("add_transaction.html", categories=CATEGORIES, today=date.today().isoformat(), username=session.get("username"))

@app.route("/transactions/delete/<int:txn_id>", methods=["POST"])
@login_required
def delete_transaction(txn_id):
    txn = db.session.get(Transaction, txn_id)
    if txn and txn.user_id == session["user_id"]:
        db.session.delete(txn)
        db.session.commit()
    return redirect(request.referrer or url_for("transactions_page"))


# ── Routes: Budgets ───────────────────────────────────────────────────────────
@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets_page():
    uid = session["user_id"]
    
    if request.method == "POST":
        category = request.form["category"]
        limit = float(request.form["monthly_limit"])
        
        existing_budget = db.session.execute(
            db.select(Budget).where(Budget.user_id == uid).where(Budget.category == category)
        ).scalar_one_or_none()
        
        if existing_budget:
            existing_budget.monthly_limit = limit
        else:
            new_budget = Budget(user_id=uid, category=category, monthly_limit=limit)
            db.session.add(new_budget)
            
        db.session.commit()
        flash(f"Budget for {category} set to ₹{limit:.0f}", "success")

    budgets_objs = db.session.execute(db.select(Budget).where(Budget.user_id == uid)).scalars().all()
    budgets = [b.to_dict() for b in budgets_objs]
    
    this_month = datetime.now().strftime("%Y-%m")
    
    txns_objs = db.session.execute(
        db.select(Transaction)
        .where(Transaction.user_id == uid)
        .where(Transaction.type == 'expense')
        .where(Transaction.date.like(f"{this_month}%"))
    ).scalars().all()

    spent_by_cat = {}
    for t in txns_objs:
        spent_by_cat[t.category] = spent_by_cat.get(t.category, 0) + t.amount

    rows = []
    for b in budgets:
        spent = spent_by_cat.get(b["category"], 0)
        pct = min(100, round((spent / b["monthly_limit"]) * 100, 1)) if b["monthly_limit"] > 0 else 0
        if pct < 25: color_class = "bar-green"
        elif pct < 50: color_class = "bar-blue"
        elif pct < 80: color_class = "bar-orange"
        else: color_class = "bar-red"
        rows.append({"category": b["category"], "limit": b["monthly_limit"], "spent": spent, "pct": pct, "color": color_class, "over": spent > b["monthly_limit"]})

    set_categories = {b["category"] for b in budgets}
    available = [c for c in CATEGORIES if c not in set_categories]

    return render_template("budgets.html", budgets=rows, available=available, username=session.get("username"))

@app.route("/budgets/delete/<category>", methods=["POST"])
@login_required
def delete_budget(category):
    budget = db.session.execute(
        db.select(Budget).where(Budget.user_id == session["user_id"]).where(Budget.category == category)
    ).scalar_one_or_none()
    
    if budget:
        db.session.delete(budget)
        db.session.commit()
        
    return redirect(url_for("budgets_page"))


# ── Routes: AI / Gemini Analyzer ──────────────────────────────────────────────
@app.route("/analyzer", methods=["GET"])
@login_required
def analyzer_page():
    return render_template("analyzer.html", username=session.get("username"))

@app.route("/analyzer/process", methods=["POST"])
@login_required
def analyzer_process():
    text_input = request.form.get("text_input", "").strip()
    results = []

    if "file" in request.files and request.files["file"].filename:
        file = request.files["file"]
        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file type."}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_DIR, f"{session['user_id']}_{datetime.now().timestamp()}_{filename}")
        file.save(filepath)

        ext = filename.rsplit(".", 1)[1].lower()
        try:
            if ext in {"png", "jpg", "jpeg", "webp"}:
                results = analyze_with_ai(file_path=filepath)
            else:
                with open(filepath, "r", errors="ignore") as f:
                    results = analyze_with_ai(raw_text=f.read())
        finally:
            os.remove(filepath)

    elif text_input:
        results = analyze_with_ai(raw_text=text_input)
    else:
        return jsonify({"error": "Please upload a file or paste text."}), 400

    if not results:
        return jsonify({"error": "No transactions detected or AI failed to read the document."}), 200

    return jsonify({"transactions": results, "raw_text": "Processed by Gemini AI Vision"})

@app.route("/analyzer/import", methods=["POST"])
@login_required
def analyzer_import():
    data = request.get_json()
    items = data.get("transactions", [])
    
    new_txns = []
    for t in items:
        new_txn = Transaction(
            user_id=session["user_id"],
            type=t["type"],
            amount=float(t["amount"]),
            category=t["category"],
            description=t.get("description", ""),
            date=t["date"],
            created_at=datetime.now().isoformat()
        )
        new_txns.append(new_txn)
        
    if new_txns:
        db.session.add_all(new_txns)
        db.session.commit()
        
    return jsonify({"imported": len(items)})


if __name__ == "__main__":
    print("=" * 60)
    print("  FinFlow (SQLAlchemy + Gemini edition) is running!")
    print("  Open your browser at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)