from sqlalchemy import create_engine, event, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_DIR = ROOT / "env"
load_dotenv(ENV_DIR / ".env")
load_dotenv(ROOT / ".env")
load_dotenv(ENV_DIR / "AI_model.env")
load_dotenv(ROOT / "AI_model.env")
load_dotenv(ENV_DIR / "cloudflare.env")
load_dotenv(ROOT / "cloudflare.env")
load_dotenv(ENV_DIR / "restaurant.env")
load_dotenv(ROOT / "restaurant.env")
load_dotenv(ENV_DIR / "rate-limit.env")
load_dotenv(ROOT / "rate-limit.env")
load_dotenv(ENV_DIR / "curlec.env")
load_dotenv(ROOT / "curlec.env")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./afrc.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")
if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
    )
else:
    engine = create_engine(DATABASE_URL)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=15000")
        finally:
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    icon = Column(String, default="restaurant")
    sort_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Dish(Base):
    __tablename__ = "dishes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    alias = Column(String, default="")
    price = Column(Float)
    available = Column(Boolean, default=True)
    unit = Column(String, default="portion")
    description = Column(Text, default="")
    pieces_per_portion = Column(Integer, default=1)
    image_key = Column(String, default="")
    categories = Column(Text, default="[]")  # JSON array of up to 3 category names
    sort_order = Column(Integer, default=0, index=True)

class Cashier(Base):
    __tablename__ = "cashiers"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    pin = Column(String)  # 4 digit, store hashed in prod
    active = Column(Boolean, default=True)

class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

class AdminSession(Base):
    __tablename__ = "admin_sessions"
    token = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    ip = Column(String, default="")
    user_agent = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    cashier_id = Column(Integer)
    admin_username = Column(String(100), nullable=True)
    action = Column(String)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SessionBill(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    bill_number = Column(String, default="", index=True)
    raw_ai = Column(Text)
    final_bill = Column(Text)
    status = Column(String, default="open")
    void_reason = Column(String, default="")
    receipt_email = Column(String, default="")
    receipt_phone = Column(String, default="")
    curlec_order_id = Column(String, default="")
    curlec_payment_id = Column(String, default="")
    payment_gateway = Column(String, default="curlec")
    image_key = Column(String, default="")
    retake_count = Column(Integer, default=0)
    client_token = Column(String, default="", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

class ClientCooldown(Base):
    __tablename__ = "client_cooldowns"
    client_key = Column(String, primary_key=True)
    cooldown_until = Column(DateTime)
    reason = Column(String, default="")

class ScanAttempt(Base):
    __tablename__ = "scan_attempts"
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, default="", index=True)
    device_id = Column(String, default="", index=True)
    session_id = Column(String, default="", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class FailedScan(Base):
    __tablename__ = "failed_scans"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, default="", index=True)
    bill_number = Column(String, default="", index=True)
    is_retry = Column(Boolean, default=False, index=True)
    ip = Column(String, default="", index=True)
    device_id = Column(String, default="", index=True)
    rejection_code = Column(String, default="UNKNOWN", index=True)
    rejection_message = Column(String, default="")
    image_key = Column(String, default="")
    raw_ai_response = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class CheckoutIntent(Base):
    __tablename__ = "checkout_intents"
    id = Column(String(64), primary_key=True)
    curlec_order_id = Column(String(64), unique=True, index=True)
    payment_gateway = Column(String(32), default="curlec")
    items_json = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)
    client_token = Column(String(128), default="")
    device_id = Column(String(128), default="")
    receipt_phone = Column(String(32), default="")
    receipt_email = Column(String(128), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class BillRefund(Base):
    __tablename__ = "bill_refunds"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    bill_number = Column(String, default="")
    curlec_payment_id = Column(String, default="")
    curlec_refund_id = Column(String, default="")
    refund_amount = Column(Float, default=0.0)
    refunded_items = Column(Text, default="[]")
    reason = Column(String, default="")
    status = Column(String, default="processed")
    created_at = Column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    bill_number = Column(String, default="", index=True)
    phone = Column(String, default="")
    rating = Column(Integer, default=5)
    prefix_comment = Column(String, default="")
    comment = Column(String(80), default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

def format_bill_number(seq: int) -> str:
    seq = max(1, int(seq))
    prefix_idx, num = divmod(seq - 1, 9999)
    num += 1
    c1 = chr(ord("A") + ((prefix_idx // (26 * 26)) % 26))
    c2 = chr(ord("A") + ((prefix_idx // 26) % 26))
    c3 = chr(ord("A") + (prefix_idx % 26))
    return f"{c1}{c2}{c3}-{num:04d}"

def parse_bill_seq(bill_number: str) -> int:
    if not bill_number or "-" not in bill_number:
        return 0
    prefix, digits = bill_number.strip().upper().split("-", 1)
    if len(prefix) != 3 or not prefix.isalpha() or not digits.isdigit():
        return 0
    p_idx = (
        (ord(prefix[0]) - ord("A")) * 26 * 26
        + (ord(prefix[1]) - ord("A")) * 26
        + (ord(prefix[2]) - ord("A"))
    )
    return p_idx * 9999 + int(digits)

def next_bill_number(db) -> str:
    rows = db.query(SessionBill.bill_number).all()
    max_seq = max((parse_bill_seq(r[0]) for r in rows if r and r[0]), default=0)
    return format_bill_number(max_seq + 1)

def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(dishes)")]
        if "alias" not in columns:
            conn.exec_driver_sql("ALTER TABLE dishes ADD COLUMN alias TEXT DEFAULT ''")
        if "description" not in columns:
            conn.exec_driver_sql("ALTER TABLE dishes ADD COLUMN description TEXT DEFAULT ''")
        if "pieces_per_portion" not in columns:
            conn.exec_driver_sql("ALTER TABLE dishes ADD COLUMN pieces_per_portion INTEGER DEFAULT 1")
        if "image_key" not in columns:
            conn.exec_driver_sql("ALTER TABLE dishes ADD COLUMN image_key TEXT DEFAULT ''")
        if "categories" not in columns:
            conn.exec_driver_sql("ALTER TABLE dishes ADD COLUMN categories TEXT DEFAULT '[]'")
        if "sort_order" not in columns:
            conn.exec_driver_sql("ALTER TABLE dishes ADD COLUMN sort_order INTEGER DEFAULT 0")
        conn.exec_driver_sql("UPDATE dishes SET pieces_per_portion = 1 WHERE pieces_per_portion IS NULL")
        conn.exec_driver_sql("UPDATE dishes SET categories = '[]' WHERE categories IS NULL OR categories = ''")
        conn.exec_driver_sql("UPDATE dishes SET image_key = '' WHERE image_key IS NULL")
        conn.exec_driver_sql("UPDATE dishes SET sort_order = id WHERE sort_order IS NULL OR sort_order = 0")

        cat_columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(categories)")]
        if cat_columns and "icon" not in cat_columns:
            conn.exec_driver_sql("ALTER TABLE categories ADD COLUMN icon TEXT DEFAULT 'restaurant'")
        if cat_columns and "sort_order" not in cat_columns:
            conn.exec_driver_sql("ALTER TABLE categories ADD COLUMN sort_order INTEGER DEFAULT 0")

        session_columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(sessions)")]
        if session_columns and "bill_number" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN bill_number TEXT DEFAULT ''")
        if session_columns and "status" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN status TEXT DEFAULT 'open'")
        if session_columns and "void_reason" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN void_reason TEXT DEFAULT ''")
        if session_columns and "receipt_email" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN receipt_email TEXT DEFAULT ''")
        if session_columns and "receipt_phone" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN receipt_phone TEXT DEFAULT ''")
        if session_columns and "curlec_order_id" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN curlec_order_id TEXT DEFAULT ''")
        if session_columns and "curlec_payment_id" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN curlec_payment_id TEXT DEFAULT ''")
        if session_columns and "payment_gateway" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN payment_gateway TEXT DEFAULT 'curlec'")
        if session_columns and "image_key" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN image_key TEXT DEFAULT ''")
        if session_columns and "retake_count" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN retake_count INTEGER DEFAULT 0")
        if session_columns and "client_token" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN client_token TEXT DEFAULT ''")
        if session_columns and "updated_at" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN updated_at DATETIME")
        if session_columns and "paid_at" not in session_columns:
            conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN paid_at DATETIME")
        intent_columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(checkout_intents)")]
        if intent_columns and "payment_gateway" not in intent_columns:
            conn.exec_driver_sql("ALTER TABLE checkout_intents ADD COLUMN payment_gateway TEXT DEFAULT 'curlec'")
        cooldown_columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(client_cooldowns)")]
        if cooldown_columns and "reason" not in cooldown_columns:
            conn.exec_driver_sql("ALTER TABLE client_cooldowns ADD COLUMN reason TEXT DEFAULT ''")
        conn.exec_driver_sql(
            "DELETE FROM sessions WHERE status != 'paid'"
        )
    db = SessionLocal()
    # Backfill bill_number for any existing sessions missing one
    missing_bills = (
        db.query(SessionBill)
        .filter((SessionBill.bill_number == None) | (SessionBill.bill_number == ""))
        .order_by(SessionBill.created_at.asc())
        .all()
    )
    if missing_bills:
        existing_rows = db.query(SessionBill.bill_number).all()
        seq = max((parse_bill_seq(r[0]) for r in existing_rows if r and r[0]), default=0)
        for s in missing_bills:
            seq += 1
            s.bill_number = format_bill_number(seq)
        db.commit()

    # Seed default categories if empty
    if db.query(Category).count() == 0:
        default_cats = [
            Category(name="Coffee & Espresso", icon="coffee", sort_order=0),
            Category(name="Bakery & Pastries", icon="bakery_dining", sort_order=1),
            Category(name="Sandwiches & Bowls", icon="lunch_dining", sort_order=2),
            Category(name="Cold Drinks", icon="glass_cup", sort_order=3),
            Category(name="Desserts & Sweets", icon="cake", sort_order=4),
        ]
        db.add_all(default_cats)
        db.commit()

    # Seed default dishes if empty
    if db.query(Dish).count() == 0:
        seeds = [
            Dish(
                name="Iced Caramel Macchiato",
                price=5.75,
                available=True,
                description="Artisanal iced caramel macchiato with rich espresso layers, creamy milk, and amber caramel drizzle.",
                categories=json.dumps(["Coffee & Espresso", "Cold Drinks"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuBQ6F__P-OQ_nMs2B_IFbv1gdurxL98OEzZZnqn3kVaBaXalVkbgSWLwrNe1LuACH_mAxQAQZEOrOyHQkw17Pk-X9bsLDhZrfe_p5AMs7X_7H5KKqMv7PyI5UeaC3klBY6tpZf1VmWP9UA_KDu_ACt5oO3c2JlFIOK3KQCZc1fo1vATlXSZBVFT5u49V-r327Ph6HHZT3NUlJ3pnMRBYFJaPs77fxdj7cCQJCsQIMrA",
            ),
            Dish(
                name="Artisan Avocado Sourdough",
                price=11.50,
                available=True,
                description="Rustic sliced avocado toast topped with vibrant microgreens, cracked black pepper, and toasted sesame seeds on crusty sourdough.",
                categories=json.dumps(["Sandwiches & Bowls", "Bakery & Pastries"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuCbITZB5tgXLfCjCeExM6k1PTqLd9NfDj_LmnthMZcawDE4vh30g-WPNlYU23KWDdsC6TK49yzZw-y1CAOFKuoCbLwFstrlrioFOeJ6A3WincrIH445JFZyfKMifCPPqqha9NcqF_hXAAqyFN-2xqs4EIbjIzgwMpDOgGTQLy4tKSehpAqTFNCrqFwhfCgkOnIV6ZS1mQ5Jhr9UzJqjK4fom76w2gyzkJWZ1EUF3spO",
            ),
            Dish(
                name="Almond Croissant",
                price=4.25,
                available=True,
                description="Flaky golden brown French almond croissant topped with powdered sugar and toasted sliced almonds.",
                categories=json.dumps(["Bakery & Pastries", "Desserts & Sweets"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuC_6u27K0pv-n1qw7A0Br4VJTFa7iOSUtbzxtftDvmkfkfOO4I_tLEf3TdaJp-hIRcyKJ48EkvVI2AFpy36q3XcvQG6pTjioQtlKNTTd8RHNLOfXu-vaGO7C1MR_00qf_q8Qrx8fma0uB-Yj4egbhkE92ZJtc0WCK9Oj-LHOj3k34RbhGt6AL6P_sUZ0U38yKVi80GXeuBFm_6Vxy8H5IVGxNQswqx7CC0TwVS3pyDM",
            ),
            Dish(
                name="Cold Brew Nitro",
                price=5.25,
                available=True,
                description="Velvety cold brew nitro coffee cascading with a creamy stout-like head of foam.",
                categories=json.dumps(["Coffee & Espresso", "Cold Drinks"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuDH8NTaBn8DwxGY8Nx96cQ4zlJJWZjECknd3RIsGHJ-mBMmoiEbeV_JMIBo4TN07jJrOQjc1Op4XezGqNOo0WN8IyPQgVTqSbotbICooBwDSmfcJ2IFvaznyt7teXrN1nmlaQIYstiJ8idYbGiUFj4kAzBkNNSK4qWZQmN1WjcBrS_7l-CzdjTr6A9TvahBhbNOVxGALbrQECLn9IyK8b15VUJrABz0y8NH0uLh04Yh",
            ),
            Dish(
                name="Matcha Green Tea Latte",
                price=5.95,
                available=True,
                description="Ceremonial grade emerald matcha green tea latte with velvety steamed milk.",
                categories=json.dumps(["Coffee & Espresso"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuC4JmYoB_RP9j0UvsY4UCXaCKDonknboLW3yc1QcmadZp4Dv7cC5rU8mj7bARLNloY2Umfb3SUV72sxpl1E8rxp3LLIS12aI6jVgp4d_sQmLhyVif4RmMvoOpvYSs8XG7Qef2jEnbS-XH1ZA4LhVRXCLixFixa5IlmYKAmiS9onnZksT41zgoKAKxYcjV103uPb3VqiZAXQMAu1D8AS8EacAoKu5GWur-Vbswuzx6Qd",
            ),
            Dish(
                name="Smoked Turkey Panini",
                price=12.00,
                available=True,
                description="Toasted hot pressed panini with melted provolone cheese, smoked turkey breast, baby spinach, and pesto on golden ciabatta.",
                categories=json.dumps(["Sandwiches & Bowls"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuByGBG74jJaVkKhBMjAkxNDhm-1UKlJ-C2IuJqmm7n1BjpfABwrIKReclt9Z4FJPxuOlrnaRW65Ipw1-vb9DFLBn9soHvXHYdGqS_zXOLVkDkj--kef1Hzo8jSiDNVC0Y8fUCNDfbMYNUM4ZVaatMTlY61jHoLqwbvPj-nmm8Xf19KJ1kma6npXDo5AIxvCCKuJ1Hrhw_hXci-Fs-jiV-2CdIEtErfZj2G0Ag_IbKRW",
            ),
            Dish(
                name="Acai Superfood Bowl",
                price=9.80,
                available=True,
                description="Organic acai smoothie bowl topped with fresh sliced strawberries, blueberries, chia seeds, toasted granola, and shaved coconut.",
                categories=json.dumps(["Sandwiches & Bowls", "Desserts & Sweets"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuDiLrCf4VUifI40kgmOsRQShSOqs4rqwQDdrBIFDVwi7QX7hq6ZOQ7flKO7hlsNnGLBvL20ld8lUw6OcyNd5OSFdEZZ2FwIPfLBLdd3PRfFJh2_tRx_CO4W6TXDlRlqJ5Mz_sIJP2LEfyfew0JYzwCZwQ5BG5V72YOB0SqDVwQ0uZUyqCg58VzLsxyU4Wmb-YLpJ5mlq_x-JwUaB-M7pbiVR-lfYops7t9I2R6Ylpfy",
            ),
            Dish(
                name="Blueberry Scone",
                price=3.80,
                available=True,
                description="Crumbly homemade bakery blueberry scone drizzled with sweet lemon vanilla glaze.",
                categories=json.dumps(["Bakery & Pastries", "Desserts & Sweets"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuD9AIaoBAp8FxfiELRa-dExF3bDKM0at5XEV-jo3YZOANNowXpEdUncOmljLXqbj8pPYGNIfUlC1yyjmwEkppFYokOI4lKNS9D435OeZQ-7R9UjZU-MNIvKgftivXv5XapZpAfPgFpcZiQKdcGyQfJP4vSkXdXZ7Ozmz5MlxyD9Ph3Hy4SqE2E-tKt8sYjZhOl9U1ZQnB6ePR0ybMJMPLmapaaoAzjARZISAmnlDaT8",
            ),
            Dish(
                name="Chai Spiced Latte",
                price=5.10,
                available=True,
                description="Steaming hot spiced chai latte with a generous dusting of cinnamon powder and star anise.",
                categories=json.dumps(["Coffee & Espresso"]),
                image_key="https://lh3.googleusercontent.com/aida-public/AB6AXuBa-F5oSXNU2-0tyPzoV0h16v3EDCfnDQ0FAQS-YBLyqay-aprDXkxymkiyZbVJ3M6uJfK3U_CROaI6Tvg1MwoyjC-gFZDKhsJbOr-2XEKS1nQtJ6VMvR_xpyvyt8VRSwQ9N41b9o1qcLSI40X_wvR_ep3ugzqFVUQRaWknhn3cmfwkUe5LwArWLaMme1ddswO1enby97gyXAMmTkOx8En-G6mLCN0v42ZqTAqVL6h_",
            ),
        ]
        db.add_all(seeds)
        db.commit()
    db.close()
