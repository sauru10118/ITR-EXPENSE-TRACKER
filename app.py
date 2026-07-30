"""
FinFlow — Personal Expense Tracker
Flask + Flask-SQLAlchemy 3.1.1 + Gemini AI Vision Analyzer

Setup:
    pip install Flask-SQLAlchemy==3.1.1 google-genai pillow python-dotenv
    python app.py
"""

import os
import random
import re
import smtplib
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
from google import genai

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
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

CATEGORIES = ["Food", "Transport", "Housing", "Entertainment", "Health",
              "Shopping", "Salary", "Freelance", "Investment", "Other"]


# ── Email OTP Configuration ──────────────────────────────────────────────────
# Gmail App Password setup:
#   1. Go to https://myaccount.google.com/apppasswords
#   2. Generate an App Password for "Mail"
#   3. Paste the 16-character password below (no spaces)
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "sauru10118@gmail.com")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
OTP_EXPIRY_MINUTES = 5

def generate_otp():
    """Generate a random 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_otp_email(recipient_email, otp_code, username):
    """Send OTP verification email via Gmail SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"FinFlow <{EMAIL_SENDER}>"
        msg["To"] = recipient_email
        msg["Subject"] = f"🔐 FinFlow — Your verification code is {otp_code}"

        # Plain-text fallback
        text_body = f"""Hi {username},

Your FinFlow email verification code is: {otp_code}

This code expires in {OTP_EXPIRY_MINUTES} minutes. Do not share it with anyone.

If you didn't request this, please ignore this email.

— FinFlow Team"""

        # HTML version
        html_body = f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif; max-width:480px; margin:0 auto; background:#f7f8fc; padding:32px 24px; border-radius:20px;">
          <div style="text-align:center; font-size:32px; margin-bottom:8px;">💸</div>
          <div style="text-align:center; font-size:22px; font-weight:800; color:#1a1d2e; margin-bottom:4px;">FinFlow Verification</div>
          <div style="text-align:center; font-size:13px; color:#8890a8; margin-bottom:24px;">Hi <strong>{username}</strong>, use the code below to verify your email</div>
          <div style="text-align:center; margin:20px 0;">
            <div style="display:inline-block; background:linear-gradient(135deg,#6c63ff,#a78bfa); color:#fff; font-size:32px; font-weight:900; letter-spacing:12px; padding:18px 32px; border-radius:16px; box-shadow:0 8px 24px rgba(108,99,255,0.35);">
              {otp_code}
            </div>
          </div>
          <div style="text-align:center; font-size:12px; color:#8890a8; margin-top:18px;">
            This code expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.<br>
            If you didn't request this, please ignore this email.
          </div>
          <div style="text-align:center; font-size:11px; color:#b0b8d1; margin-top:24px; border-top:1px solid #e8eaf0; padding-top:16px;">
            FinFlow — Personal Expense Tracker
          </div>
        </div>
        """

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipient_email, msg.as_string())

        print(f"OTP email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


# ── Gemini AI Configuration ──────────────────────────────────────────────────

# Paste your actual API key directly inside the quotes below if available
GEMINI_API_KEY = "PASTE_YOUR_API_KEY_HERE"


# ── Database setup (Flask-SQLAlchemy 3.1.1) ──────────────────────────────────
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.String(50), nullable=False)

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        """Helper to convert object to dict for backward compatibility with templates"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Budget(db.Model):
    __tablename__ = "budgets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)

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


# ── Smart AI & Document Analyzer ──────────────────────────────────────────────
def parse_text_offline(text):
    """Fallback offline parser: extracts transactions from plain text / statements / OCR using regex."""
    if not text:
        return []
        
    income_keywords = ['received', 'credited', 'credit', 'salary', 'refund', 'cashback', 'bonus', 'added', 'deposit', 'dividend', 'income', 'freelance', 'earned', 'got', 'money received']
    
    cat_map = {
        'Food': ['swiggy', 'zomato', 'restaurant', 'food', 'cafe', 'dominos', 'pizza', 'mcdonalds', 'starbucks', 'dining', 'groceries', 'blinkit', 'zepto', 'instamart', 'supermarket'],
        'Transport': ['uber', 'ola', 'rapido', 'cab', 'auto', 'petrol', 'fuel', 'metro', 'flight', 'irctc', 'train', 'bus', 'toll', 'parking'],
        'Housing': ['rent', 'electricity', 'water', 'wifi', 'broadband', 'maintenance', 'gas', 'house', 'apartment'],
        'Entertainment': ['netflix', 'spotify', 'movie', 'cinema', 'bookmyshow', 'prime', 'game', 'youtube', 'steam', 'hotstar'],
        'Health': ['pharmacy', 'hospital', 'doctor', 'medicine', 'apollo', '1mg', 'gym', 'fitness', 'medical', 'lab', 'dental'],
        'Shopping': ['amazon', 'flipkart', 'myntra', 'meesho', 'clothes', 'shopping', 'store', 'fashion', 'zara', 'uniqlo'],
        'Salary': ['salary', 'payroll', 'stipend', 'wages', 'employer'],
        'Freelance': ['upwork', 'fiverr', 'freelance', 'consulting', 'client', 'project'],
        'Investment': ['zerodha', 'groww', 'upstox', 'mutual fund', 'stocks', 'crypto', 'sip', 'dividend', 'shares']
    }

    # Pre-clean date patterns, time patterns, ref IDs
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b'
    ]
    time_pattern = r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b'
    ref_pattern = r'\b(?:UPI|Ref|Txn|Transaction|Order|Id|No)[.:#]?\s*#?\d+\b'

    raw_lines = [l.strip() for l in text.split('\n') if l.strip()]
    transactions = []

    for i, line in enumerate(raw_lines):
        # Extract date if present
        date_str = date.today().isoformat()
        for dp in date_patterns:
            dm = re.search(dp, line, re.IGNORECASE)
            if dm:
                date_str = dm.group(0)
                break

        # Scrub non-amount numbers (dates, times, ref ids)
        line_clean = line
        for dp in date_patterns:
            line_clean = re.sub(dp, '', line_clean, flags=re.IGNORECASE)
        line_clean = re.sub(time_pattern, '', line_clean, flags=re.IGNORECASE)
        line_clean = re.sub(ref_pattern, '', line_clean, flags=re.IGNORECASE)

        # Look for amounts: explicitly formatted with symbol or decimal float
        currency_amount_regex = r'(?:[₹\$]|Rs\.?|INR)\s*(\d+(?:,\d+)*(?:\.\d{1,2})?)\b|\b(\d+(?:,\d+)*(?:\.\d{1,2})?)\s*(?:[₹\$]|Rs\.?|INR)\b|\b(\d+(?:,\d+)*\.\d{1,2})\b'
        amt_matches = re.findall(currency_amount_regex, line_clean, re.IGNORECASE)

        # Fallback to plain integers if line explicitly has payment terms
        if not amt_matches and any(k in line.lower() for k in ['paid', 'sent', 'received', 'credited', 'debited', 'spent', 'rs', '₹']):
            amt_matches = re.findall(r'\b(\d+(?:,\d+)*)\b', line_clean)
            amt_matches = [(m, '', '') if isinstance(m, str) else m for m in amt_matches]

        valid_amts = []
        for match in amt_matches:
            val_str = [g for g in match if g][0].replace(',', '')
            try:
                val = float(val_str)
                if 0 < val < 10000000 and val not in [2024, 2025, 2026, 2027]:
                    valid_amts.append(val)
            except (ValueError, IndexError):
                pass

        if not valid_amts:
            continue

        amount = valid_amts[0]

        # Context around this line
        start_idx = max(0, i - 2)
        end_idx = min(len(raw_lines), i + 3)
        context_block = ' '.join(raw_lines[start_idx:end_idx])
        context_lower = context_block.lower()

        ttype = 'expense'
        if any(kw in context_lower for kw in income_keywords) and not any(kw in context_lower for kw in ['paid to', 'sent to', 'debited']):
            ttype = 'income'

        category = 'Other'
        for cat, keywords in cat_map.items():
            if any(kw in context_lower for kw in keywords):
                category = cat
                break

        desc = line
        if len(line.strip()) <= 12 and i > 0:
            desc = f'{raw_lines[i-1]} {line}'

        desc_clean = re.sub(r'(?:[₹\$]|Rs\.?|INR)?\s*\d+(?:,\d+)*(?:\.\d{1,2})?', '', desc, flags=re.IGNORECASE)
        for dp in date_patterns:
            desc_clean = re.sub(dp, '', desc_clean, flags=re.IGNORECASE)
        desc_clean = re.sub(time_pattern, '', desc_clean, flags=re.IGNORECASE)
        desc_clean = re.sub(ref_pattern, '', desc_clean, flags=re.IGNORECASE)
        desc_clean = re.sub(r'[-:,_]+', ' ', desc_clean)
        desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
        if not desc_clean:
            desc_clean = f'{category} {ttype.capitalize()}'
        elif len(desc_clean) > 40:
            desc_clean = desc_clean[:40]

        transactions.append({
            'type': ttype,
            'amount': amount,
            'category': category,
            'description': desc_clean,
            'date': date_str
        })

    return transactions


def run_winrt_ocr(image_path):
    """Uses Windows native WinRT OCR engine for instant offline OCR."""
    try:
        import asyncio
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.storage import StorageFile, FileAccessMode
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.globalization import Language

        async def _async_ocr():
            abs_path = os.path.abspath(image_path)
            file = await StorageFile.get_file_from_path_async(abs_path)
            stream = await file.open_async(FileAccessMode.READ)
            decoder = await BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            try:
                lang = Language('en-US')
                engine = OcrEngine.try_create_from_language(lang)
            except Exception:
                engine = None
            if not engine:
                engine = OcrEngine.try_create_from_user_profile_language()
            if not engine:
                return ""
            res = await engine.recognize_async(bitmap)
            return res.text or ""

        return asyncio.run(_async_ocr())
    except Exception as e:
        print(f"WinRT OCR Notice: {e}")
        return ""


def analyze_with_ai(file_path=None, raw_text=None):
    """Multi-tier document & transaction analyzer:
    1. Gemini AI (if valid API key present in env or code)
    2. Native WinRT OCR / EasyOCR / Tesseract OCR (if image uploaded)
    3. Smart offline rule-based parser
    """
    
    # Tier 1: Gemini AI attempt
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or GEMINI_API_KEY
    if api_key and api_key != "PASTE_YOUR_API_KEY_HERE":
        try:
            ai_client = genai.Client(api_key=api_key)
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
            Respond ONLY with the raw JSON array. Do not include markdown formatting.
            """
            if file_path:
                img = Image.open(file_path)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                response = ai_client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=[prompt, img]
                )
            else:
                response = ai_client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=[prompt, raw_text]
                )
                
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            parsed = json.loads(clean_text)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception as e:
            print(f"Gemini AI Notice: {e}, using offline analyzer.")

    # Tier 2: Image OCR (if image provided)
    extracted_text = raw_text or ""
    if file_path and not extracted_text:
        # 1. Try WinRT Native Windows OCR (Built-in Windows 10/11 OCR engine)
        try:
            extracted_text = run_winrt_ocr(file_path)
        except Exception as winrt_err:
            print(f"WinRT Notice: {winrt_err}")

        # 2. Try EasyOCR as fallback
        if not extracted_text:
            try:
                import easyocr
                reader = easyocr.Reader(['en'], gpu=False)
                results = reader.readtext(file_path, detail=0)
                if results:
                    extracted_text = "\n".join(results)
            except Exception as easy_err:
                print(f"EasyOCR Notice: {easy_err}")

        # 3. Try PyTesseract as fallback
        if not extracted_text:
            try:
                import pytesseract
                possible_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
                    os.path.expanduser(r'~\AppData\Local\Tesseract-OCR\tesseract.exe')
                ]
                for p in possible_paths:
                    if os.path.exists(p):
                        pytesseract.pytesseract.tesseract_cmd = p
                        break
                
                img = Image.open(file_path)
                extracted_text = pytesseract.image_to_string(img)
            except Exception as ocr_err:
                print(f"PyTesseract Notice: {ocr_err}")

    # Tier 3: Smart offline regex & rule parser
    return parse_text_offline(extracted_text)


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

        # Check if username already taken
        existing = db.session.execute(
            db.select(User).where(User.username == username)
        ).scalar_one_or_none()
        if existing:
            flash("Username already exists.", "error")
            return render_template("register.html")

        # Generate OTP and store pending registration in session
        otp = generate_otp()
        session["pending_reg"] = {
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
            "otp": otp,
            "otp_created": datetime.now().isoformat(),
            "attempts": 0
        }

        # Send OTP email
        sent = send_otp_email(email, otp, username)
        if sent:
            flash("Verification code sent to your email!", "success")
        else:
            # Dev fallback: show OTP on-screen when email can't be sent
            session["otp_dev_fallback"] = True
            flash(f"Email service unavailable. Your OTP code is: {otp}", "success")

        return redirect(url_for("verify_otp"))

    return render_template("register.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending = session.get("pending_reg")
    if not pending:
        flash("No pending registration. Please register first.", "error")
        return redirect(url_for("register"))

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()

        # Check expiry
        otp_created = datetime.fromisoformat(pending["otp_created"])
        if datetime.now() - otp_created > timedelta(minutes=OTP_EXPIRY_MINUTES):
            session.pop("pending_reg", None)
            flash("OTP has expired. Please register again.", "error")
            return redirect(url_for("register"))

        # Track failed attempts
        pending["attempts"] = pending.get("attempts", 0) + 1
        if pending["attempts"] > 5:
            session.pop("pending_reg", None)
            flash("Too many failed attempts. Please register again.", "error")
            return redirect(url_for("register"))

        session["pending_reg"] = pending

        if entered_otp == pending["otp"]:
            # OTP verified — create user account
            new_user = User(
                username=pending["username"],
                email=pending["email"],
                password_hash=pending["password_hash"],
                created_at=datetime.now().isoformat()
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                session.pop("pending_reg", None)
                flash("Email verified! Account created successfully. Please log in.", "success")
                return redirect(url_for("login"))
            except IntegrityError:
                db.session.rollback()
                session.pop("pending_reg", None)
                flash("Username already exists.", "error")
                return redirect(url_for("register"))
        else:
            remaining = 5 - pending["attempts"]
            flash(f"Invalid OTP. {remaining} attempt(s) remaining.", "error")

    return render_template("verify_otp.html", email=pending["email"])

@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    pending = session.get("pending_reg")
    if not pending:
        flash("No pending registration. Please register first.", "error")
        return redirect(url_for("register"))

    # Generate new OTP
    new_otp = generate_otp()
    pending["otp"] = new_otp
    pending["otp_created"] = datetime.now().isoformat()
    pending["attempts"] = 0
    session["pending_reg"] = pending

    sent = send_otp_email(pending["email"], new_otp, pending["username"])
    if sent:
        flash("New verification code sent!", "success")
    else:
        session["otp_dev_fallback"] = True
        flash(f"Email service unavailable. Your new OTP code is: {new_otp}", "success")

    return redirect(url_for("verify_otp"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        # Search by username
        user = db.session.execute(
            db.select(User).where(User.username == identifier)
        ).scalar_one_or_none()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))
        
        flash("Invalid username or password.", "error")

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
    
