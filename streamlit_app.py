import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import sqlite3
import hashlib
import secrets
import uuid
import json
import re
import os
from datetime import datetime, date, timedelta

try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# =========================================================
# CONFIG
# =========================================================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edugenius.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploaded_docs")
GEMINI_MODEL = "gemini-2.0-flash"

st.set_page_config(
    page_title="EduGenius",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_env():
    """Read GOOGLE_API_KEY from .env (or the legacy _env filename)."""
    env = {}
    base = os.path.dirname(os.path.abspath(__file__))
    for fname in [".env", "_env"]:
        path = os.path.join(base, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            break
    return env


ENV = load_env()
GEMINI_API_KEY = ENV.get("GOOGLE_API_KEY", "")

# =========================================================
# DATABASE LAYER
# =========================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist yet (so a fresh/empty db still works),
    and add the 'content' column to documents for storing extracted PDF text."""
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR NOT NULL PRIMARY KEY, name VARCHAR NOT NULL, email VARCHAR NOT NULL,
        password_hash VARCHAR NOT NULL, role VARCHAR, created_at DATETIME
    );
    CREATE TABLE IF NOT EXISTS subjects (
        id VARCHAR NOT NULL PRIMARY KEY, name VARCHAR NOT NULL, description VARCHAR, user_id VARCHAR
    );
    CREATE TABLE IF NOT EXISTS documents (
        id VARCHAR NOT NULL PRIMARY KEY, subject_id VARCHAR, filename VARCHAR NOT NULL,
        file_path VARCHAR NOT NULL, chunk_count INTEGER, uploaded_at DATETIME
    );
    CREATE TABLE IF NOT EXISTS study_plans (
        id VARCHAR NOT NULL PRIMARY KEY, user_id VARCHAR, subject_id VARCHAR, title VARCHAR NOT NULL,
        start_date DATE, end_date DATE, schedule TEXT, status VARCHAR, created_at DATETIME
    );
    CREATE TABLE IF NOT EXISTS quizzes (
        id VARCHAR NOT NULL PRIMARY KEY, subject_id VARCHAR, title VARCHAR NOT NULL,
        questions TEXT, total_marks INTEGER, created_at DATETIME
    );
    CREATE TABLE IF NOT EXISTS chat_history (
        id VARCHAR NOT NULL PRIMARY KEY, user_id VARCHAR, subject_id VARCHAR, role VARCHAR NOT NULL,
        message TEXT NOT NULL, sources TEXT, timestamp DATETIME
    );
    CREATE TABLE IF NOT EXISTS progress_snapshots (
        id VARCHAR NOT NULL PRIMARY KEY, user_id VARCHAR, subject_id VARCHAR, completion_pct FLOAT,
        avg_quiz_score FLOAT, total_study_minutes INTEGER, snapshot_date DATE
    );
    CREATE TABLE IF NOT EXISTS study_tasks (
        id VARCHAR NOT NULL PRIMARY KEY, plan_id VARCHAR, subject_id VARCHAR, title VARCHAR NOT NULL,
        description VARCHAR, due_date DATE, priority VARCHAR, status VARCHAR,
        estimated_minutes INTEGER, actual_minutes INTEGER
    );
    CREATE TABLE IF NOT EXISTS quiz_results (
        id VARCHAR NOT NULL PRIMARY KEY, user_id VARCHAR, quiz_id VARCHAR, score FLOAT,
        answers TEXT, submitted_at DATETIME
    );
    CREATE TABLE IF NOT EXISTS study_sessions (
        id VARCHAR NOT NULL PRIMARY KEY, user_id VARCHAR, task_id VARCHAR,
        start_time DATETIME NOT NULL, end_time DATETIME, focus_score INTEGER, notes TEXT
    );
    """)
    cur.execute("PRAGMA table_info(documents)")
    cols = [r[1] for r in cur.fetchall()]
    if "content" not in cols:
        cur.execute("ALTER TABLE documents ADD COLUMN content TEXT")
    conn.commit()
    conn.close()
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def new_id():
    return uuid.uuid4().hex


# --- password hashing (stdlib only; also verifies legacy bcrypt hashes if bcrypt happens to be installed) ---
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()
    return f"pbkdf2${salt}${pw_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        if stored_hash.startswith("pbkdf2$"):
            _, salt, pw_hash = stored_hash.split("$")
            test_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()
            return secrets.compare_digest(test_hash, pw_hash)
        elif stored_hash.startswith("$2a$") or stored_hash.startswith("$2b$"):
            try:
                import bcrypt
                return bcrypt.checkpw(password.encode(), stored_hash.encode())
            except ImportError:
                return False
        return False
    except Exception:
        return False


def get_user_by_email(email):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(name, email, password, role):
    conn = get_conn()
    uid = new_id()
    conn.execute(
        "INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES (?,?,?,?,?,?)",
        (uid, name, email, hash_password(password), role, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return uid


def list_subjects(user_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM subjects WHERE user_id = ? ORDER BY name", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_subject(user_id, name, description):
    conn = get_conn()
    sid = new_id()
    conn.execute("INSERT INTO subjects (id, name, description, user_id) VALUES (?,?,?,?)",
                 (sid, name, description, user_id))
    conn.commit()
    conn.close()
    return sid


def extract_pdf_text(file_bytes):
    if not PDF_SUPPORT:
        return ""
    try:
        from io import BytesIO
        reader = PdfReader(BytesIO(file_bytes))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        return text.strip()
    except Exception:
        return ""


def save_document(subject_id, uploaded_file):
    file_bytes = uploaded_file.getvalue()
    doc_id = new_id()
    safe_name = f"{doc_id}_{uploaded_file.name}"
    path = os.path.join(UPLOAD_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(file_bytes)
    text = extract_pdf_text(file_bytes)
    conn = get_conn()
    conn.execute(
        "INSERT INTO documents (id, subject_id, filename, file_path, chunk_count, uploaded_at, content) "
        "VALUES (?,?,?,?,?,?,?)",
        (doc_id, subject_id, uploaded_file.name, path, 1 if text else 0, datetime.now().isoformat(), text)
    )
    conn.commit()
    conn.close()
    return doc_id, bool(text)


def list_documents(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT d.id, d.filename, d.chunk_count, d.uploaded_at, s.name as subject_name, s.id as subject_id "
        "FROM documents d JOIN subjects s ON d.subject_id = s.id WHERE s.user_id = ? ORDER BY d.uploaded_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_subject_context(subject_id, max_chars=12000):
    conn = get_conn()
    rows = conn.execute("SELECT content FROM documents WHERE subject_id = ? AND content IS NOT NULL", (subject_id,)).fetchall()
    conn.close()
    text = "\n\n---\n\n".join(r["content"] for r in rows if r["content"])
    return text[:max_chars]


def add_chat_message(user_id, subject_id, role, message):
    conn = get_conn()
    conn.execute(
        "INSERT INTO chat_history (id, user_id, subject_id, role, message, sources, timestamp) VALUES (?,?,?,?,?,?,?)",
        (new_id(), user_id, subject_id, role, message, "[]", datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_chat_history(user_id, subject_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, message FROM chat_history WHERE user_id = ? AND subject_id = ? ORDER BY timestamp",
        (user_id, subject_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_plan_with_tasks(user_id, subject_ids_by_name, title, start_d, end_d, tasks):
    conn = get_conn()
    plan_id = new_id()
    conn.execute(
        "INSERT INTO study_plans (id, user_id, subject_id, title, start_date, end_date, schedule, status, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (plan_id, user_id, None, title, start_d.isoformat(), end_d.isoformat(),
         json.dumps(tasks), "active", datetime.now().isoformat())
    )
    for t in tasks:
        subject_id = subject_ids_by_name.get(t.get("subject", ""))
        conn.execute(
            "INSERT INTO study_tasks (id, plan_id, subject_id, title, description, due_date, priority, "
            "status, estimated_minutes, actual_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (new_id(), plan_id, subject_id, t.get("title", "Study session"), t.get("description", ""),
             t.get("due_date"), t.get("priority", "medium"), "pending", t.get("estimated_minutes", 60), None)
        )
    conn.commit()
    conn.close()
    return plan_id


def list_plans(user_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM study_plans WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_tasks(user_id, only_pending=False):
    conn = get_conn()
    q = "SELECT st.* FROM study_tasks st JOIN study_plans sp ON st.plan_id = sp.id WHERE sp.user_id = ?"
    if only_pending:
        q += " AND st.status != 'completed'"
    q += " ORDER BY st.due_date"
    rows = conn.execute(q, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_task_status(task_id, status):
    conn = get_conn()
    conn.execute("UPDATE study_tasks SET status = ?, actual_minutes = COALESCE(actual_minutes, estimated_minutes) WHERE id = ?",
                 (status, task_id))
    conn.commit()
    conn.close()


def save_quiz(subject_id, title, questions):
    conn = get_conn()
    qid = new_id()
    conn.execute("INSERT INTO quizzes (id, subject_id, title, questions, total_marks, created_at) VALUES (?,?,?,?,?,?)",
                 (qid, subject_id, title, json.dumps(questions), len(questions), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return qid


def save_quiz_result(user_id, quiz_id, score, answers):
    conn = get_conn()
    conn.execute("INSERT INTO quiz_results (id, user_id, quiz_id, score, answers, submitted_at) VALUES (?,?,?,?,?,?)",
                 (new_id(), user_id, quiz_id, score, json.dumps(answers), datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_dashboard_stats(user_id):
    conn = get_conn()
    total_subjects = conn.execute("SELECT COUNT(*) c FROM subjects WHERE user_id = ?", (user_id,)).fetchone()["c"]

    completed_minutes = conn.execute(
        "SELECT COALESCE(SUM(COALESCE(st.actual_minutes, st.estimated_minutes, 0)),0) m "
        "FROM study_tasks st JOIN study_plans sp ON st.plan_id = sp.id "
        "WHERE sp.user_id = ? AND st.status = 'completed'", (user_id,)
    ).fetchone()["m"]
    study_hours = round(completed_minutes / 60.0, 1)

    avg_score_row = conn.execute("SELECT AVG(score) a FROM quiz_results WHERE user_id = ?", (user_id,)).fetchone()
    avg_quiz_score = round(avg_score_row["a"], 1) if avg_score_row["a"] is not None else 0

    tasks_completed = conn.execute(
        "SELECT COUNT(*) c FROM study_tasks st JOIN study_plans sp ON st.plan_id = sp.id "
        "WHERE sp.user_id = ? AND st.status = 'completed'", (user_id,)
    ).fetchone()["c"]

    weekly_hours = {d: 0 for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
    week_rows = conn.execute(
        "SELECT st.due_date, COALESCE(st.actual_minutes, st.estimated_minutes, 0) m "
        "FROM study_tasks st JOIN study_plans sp ON st.plan_id = sp.id "
        "WHERE sp.user_id = ? AND st.status = 'completed' AND st.due_date IS NOT NULL", (user_id,)
    ).fetchall()
    today = date.today()
    for r in week_rows:
        try:
            d = datetime.fromisoformat(r["due_date"]).date()
        except Exception:
            continue
        if 0 <= (today - d).days < 7:
            weekly_hours[d.strftime("%a")] += r["m"] / 60.0
    weekly_hours = {k: round(v, 1) for k, v in weekly_hours.items()}

    trend_rows = conn.execute(
        "SELECT score, submitted_at FROM quiz_results WHERE user_id = ? ORDER BY submitted_at DESC LIMIT 6",
        (user_id,)
    ).fetchall()
    trend_rows = list(reversed(trend_rows))
    score_trends = {f"Attempt {i+1}": r["score"] for i, r in enumerate(trend_rows)}

    subj_rows = conn.execute(
        "SELECT s.name, COUNT(st.id) total, SUM(CASE WHEN st.status='completed' THEN 1 ELSE 0 END) done "
        "FROM subjects s LEFT JOIN study_tasks st ON st.subject_id = s.id "
        "WHERE s.user_id = ? GROUP BY s.id", (user_id,)
    ).fetchall()
    subject_progress = {}
    for r in subj_rows:
        pct = round((r["done"] / r["total"]) * 100) if r["total"] else 0
        subject_progress[r["name"]] = pct

    conn.close()
    return {
        "total_subjects": total_subjects,
        "study_hours": study_hours,
        "avg_quiz_score": avg_quiz_score,
        "tasks_completed": tasks_completed,
        "weekly_hours": weekly_hours,
        "score_trends": score_trends,
        "subject_progress": subject_progress,
    }


# =========================================================
# GEMINI (called directly — no backend server needed)
# =========================================================
def call_gemini(prompt, json_mode=False, temperature=0.7):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return None, "No Gemini API key configured. Add GOOGLE_API_KEY to your .env file."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature}
    }
    if json_mode:
        payload["generationConfig"]["response_mime_type"] = "application/json"
    try:
        r = requests.post(url, json=payload, timeout=45)
        if r.status_code >= 400:
            return None, f"Gemini API error {r.status_code}: {r.text[:200]}"
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, None
    except requests.exceptions.RequestException as e:
        return None, f"Could not reach Gemini API: {e}"
    except (KeyError, IndexError):
        return None, "Gemini returned an unexpected response (possibly blocked by safety filters)."


def extract_json(text):
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


# =========================================================
# SESSION STATE
# =========================================================
def init_session_state():
    defaults = {
        "view": "home",
        "auth_tab": "Login",
        "user": None,
        "page": "Dashboard",
        "active_quiz": None,
        "quiz_results": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# =========================================================
# STYLING
# =========================================================
def apply_custom_css():
    st.markdown("""
        <style>
        :root {
            --primary-color: #6366f1;
            --secondary-color: #8b5cf6;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
        }
        .gradient-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 3rem !important; font-weight: 800 !important;
            margin-bottom: 0.5rem; text-align: center;
        }
        .st-card {
            background-color: var(--card-bg); border-radius: 12px; padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            margin-bottom: 1rem; border: 1px solid #e2e8f0;
        }
        .metric-card {
            background: linear-gradient(135deg, #ffffff, #f8fafc);
            border-left: 5px solid var(--primary-color); padding: 1.5rem;
            border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;
        }
        .priority-high { border-left: 4px solid #ef4444; }
        .priority-medium { border-left: 4px solid #f59e0b; }
        .priority-low { border-left: 4px solid #10b981; }

        .hero-wrap { text-align: center; padding: 3rem 1rem 2rem 1rem; }
        .hero-sub { color: var(--text-muted); font-size: 1.25rem; max-width: 640px; margin: 0 auto 2rem auto; }
        .feature-card {
            background: var(--card-bg); border-radius: 16px; padding: 1.75rem;
            border: 1px solid #e2e8f0; height: 100%; transition: transform .15s ease, box-shadow .15s ease;
        }
        .feature-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px -8px rgba(99,102,241,0.25); }
        .feature-icon { font-size: 2.2rem; margin-bottom: .5rem; }
        .feature-title { font-weight: 700; font-size: 1.05rem; margin-bottom: .35rem; color: var(--text-main); }
        .feature-desc { color: var(--text-muted); font-size: 0.92rem; }
        .step-badge {
            display:inline-flex; align-items:center; justify-content:center;
            width:42px; height:42px; border-radius:50%;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color:white; font-weight:800; margin-bottom:.5rem;
        }
        .cta-band {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 20px; padding: 2.5rem; text-align:center; color:white; margin-top: 2rem;
        }
        .cta-band h2 { color:white !important; margin-bottom:.25rem; }
        .cta-band p { color: rgba(255,255,255,0.85); }
        </style>
    """, unsafe_allow_html=True)


# =========================================================
# LANDING / HOME PAGE
# =========================================================
FEATURES = [
    ("🤖", "AI Tutor", "Ask questions about your own study materials and get answers grounded in what you uploaded — Socratic or Direct mode."),
    ("📅", "Study Planner", "Gemini builds a personalized schedule from your subjects, deadlines and weak areas."),
    ("📊", "Progress Dashboard", "Real numbers from your own activity — study hours, quiz scores, task completion, all computed live."),
    ("📝", "Quiz Generator", "AI-generated quizzes from your materials, graded instantly."),
    ("📄", "Document Manager", "Upload PDFs — they're parsed and used as live context for the AI Tutor."),
]

STEPS = [
    ("1", "Create your free account", "Takes 10 seconds — no card, no spam."),
    ("2", "Add a subject & upload materials", "Give the AI Tutor something real to work with."),
    ("3", "Study smarter", "Chat, plan, quiz, and track progress — all in one place."),
]


def render_home():
    st.markdown('<div class="hero-wrap">', unsafe_allow_html=True)
    st.markdown('<h1 class="gradient-header">🎓 EduGenius</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-sub">Your personal AI-powered education platform — tutoring, '
        'study planning and progress analytics, built around your own study materials.</p>',
        unsafe_allow_html=True
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Get Started Free", use_container_width=True, type="primary"):
                st.session_state.view = "auth"
                st.session_state.auth_tab = "Register"
                st.rerun()
        with cc2:
            if st.button("Login", use_container_width=True):
                st.session_state.view = "auth"
                st.session_state.auth_tab = "Login"
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Everything you need to study smarter")
    for row_start in range(0, len(FEATURES), 3):
        cols = st.columns(3)
        for col, (icon, title, desc) in zip(cols, FEATURES[row_start:row_start + 3]):
            with col:
                st.markdown(f"""
                    <div class="feature-card">
                        <div class="feature-icon">{icon}</div>
                        <div class="feature-title">{title}</div>
                        <div class="feature-desc">{desc}</div>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### How it works")
    cols = st.columns(3)
    for col, (num, title, desc) in zip(cols, STEPS):
        with col:
            st.markdown(f"""
                <div style="text-align:center; padding: 0 1rem;">
                    <div class="step-badge">{num}</div>
                    <div class="feature-title">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("""
        <div class="cta-band">
            <h2>Ready to boost your grades?</h2>
            <p>Create a free account and upload your first subject in under a minute.</p>
        </div>
    """, unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button("Create My Free Account", use_container_width=True, type="primary"):
            st.session_state.view = "auth"
            st.session_state.auth_tab = "Register"
            st.rerun()


# =========================================================
# AUTH (register-before-login enforced)
# =========================================================
def render_auth():
    top_l, top_r = st.columns([1, 5])
    with top_l:
        if st.button("← Back"):
            st.session_state.view = "home"
            st.rerun()

    st.markdown('<h1 class="gradient-header">EduGenius</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color: var(--text-muted);'>Your Personal AI-Powered Education Platform</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.subheader("Welcome Back 👋")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")

            if st.button("Login", use_container_width=True, type="primary"):
                if not (email and password):
                    st.error("Please fill in all fields.")
                else:
                    user = get_user_by_email(email)
                    if not user:
                        st.error("No account found for this email. Please register first.")
                    elif not verify_password(password, user["password_hash"]):
                        st.error("Incorrect password.")
                    else:
                        st.session_state.user = {
                            "id": user["id"], "name": user["name"],
                            "email": user["email"], "role": user["role"]
                        }
                        st.session_state.view = "app"
                        st.session_state.page = "Dashboard"
                        st.rerun()

        with tab2:
            st.subheader("Create an Account 🚀")
            r_name = st.text_input("Full Name", key="reg_name")
            r_email = st.text_input("Email", key="reg_email")
            r_password = st.text_input("Password", type="password", key="reg_pass")
            r_role = st.selectbox("Role", ["Student", "Teacher"], key="reg_role")

            if st.button("Register", use_container_width=True, type="primary"):
                if not (r_name and r_email and r_password):
                    st.error("Please fill in all fields.")
                elif len(r_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif get_user_by_email(r_email):
                    st.error("An account with this email already exists. Please log in instead.")
                else:
                    create_user(r_name, r_email, r_password, r_role.lower())
                    st.success("Account created! Please switch to the Login tab to sign in.")
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================
def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user['name']}")
        st.caption(st.session_state.user["email"])
        st.markdown("---")
        pages = {
            "Dashboard": "📊", "AI Tutor": "🤖", "Study Planner": "📅",
            "Quiz": "📝", "Documents": "📄", "Settings": "⚙️"
        }
        for page, icon in pages.items():
            if st.button(f"{icon} {page}", use_container_width=True,
                         type="primary" if st.session_state.page == page else "secondary"):
                st.session_state.page = page
                st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.view = "home"
            st.session_state.active_quiz = None
            st.session_state.quiz_results = None
            st.rerun()


# =========================================================
# DASHBOARD
# =========================================================
def render_dashboard():
    st.markdown('<h2 class="gradient-header" style="text-align:left; font-size:2rem !important;">Dashboard</h2>', unsafe_allow_html=True)
    uid = st.session_state.user["id"]
    data = get_dashboard_stats(uid)

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in zip(
        [c1, c2, c3, c4],
        ["Subjects", "Study Hours", "Avg Quiz Score", "Tasks Completed"],
        [data["total_subjects"], f'{data["study_hours"]}h', f'{data["avg_quiz_score"]}%', data["tasks_completed"]]
    ):
        with col:
            st.markdown(f'<div class="metric-card"><h3>{value}</h3><p style="color:var(--text-muted);">{label}</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.subheader("Weekly Study Hours")
        if any(data["weekly_hours"].values()):
            df = pd.DataFrame(list(data["weekly_hours"].items()), columns=["Day", "Hours"])
            st.plotly_chart(px.bar(df, x="Day", y="Hours"), use_container_width=True)
        else:
            st.info("Complete some study tasks to see this chart fill in.")
    with cc2:
        st.subheader("Quiz Score Trend")
        if data["score_trends"]:
            df = pd.DataFrame(list(data["score_trends"].items()), columns=["Attempt", "Score"])
            st.plotly_chart(px.line(df, x="Attempt", y="Score", markers=True), use_container_width=True)
        else:
            st.info("Take a quiz to start tracking your score trend.")

    st.subheader("Subject Progress")
    if data["subject_progress"]:
        for name, pct in data["subject_progress"].items():
            st.write(name)
            st.progress(pct / 100)
    else:
        st.info("Add a subject and some study tasks to see progress here.")

    st.subheader("Pending Tasks")
    tasks = list_tasks(uid, only_pending=True)
    if not tasks:
        st.info("No pending tasks — generate a study plan to get some.")
    for t in tasks[:8]:
        p_class = f"priority-{t.get('priority', 'medium')}"
        cols = st.columns([0.08, 0.92])
        with cols[0]:
            done = st.checkbox("", key=f"task_{t['id']}")
        with cols[1]:
            st.markdown(f'<div class="st-card {p_class}"><b>{t["title"]}</b><br>'
                        f'<span style="color:var(--text-muted);">Due {t.get("due_date") or "—"} · {t.get("priority","medium").title()} priority</span></div>',
                        unsafe_allow_html=True)
        if done:
            update_task_status(t["id"], "completed")
            st.rerun()


# =========================================================
# AI TUTOR
# =========================================================
def render_ai_tutor():
    st.markdown('<h2 class="gradient-header" style="text-align:left; font-size:2rem !important;">AI Tutor</h2>', unsafe_allow_html=True)
    uid = st.session_state.user["id"]
    subs = list_subjects(uid)
    if not subs:
        st.warning("Create a subject in Documents first, so the tutor has something to work with.")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        names = [s["name"] for s in subs]
        sel = st.selectbox("Subject", names)
        subject = next(s for s in subs if s["name"] == sel)
    with col2:
        mode = st.radio("Mode", ["Direct", "Socratic"])

    history = get_chat_history(uid, subject["id"])
    for m in history:
        with st.chat_message(m["role"]):
            st.write(m["message"])

    question = st.chat_input("Ask about your study materials...")
    if question:
        add_chat_message(uid, subject["id"], "user", question)
        with st.chat_message("user"):
            st.write(question)

        context = get_subject_context(subject["id"])
        style = ("Use the Socratic method: guide the student with probing questions rather than "
                 "giving the answer outright.") if mode == "Socratic" else "Answer directly and clearly."
        prompt = (
            f"You are an AI tutor for the subject '{subject['name']}'. {style}\n\n"
            f"Study material context (may be empty):\n{context or '(no documents uploaded yet)'}\n\n"
            f"Student question: {question}\n\n"
            "If the context doesn't cover the question, say so and answer using general knowledge instead."
        )
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer, err = call_gemini(prompt)
            if err:
                st.error(err)
            else:
                st.write(answer)
                add_chat_message(uid, subject["id"], "assistant", answer)


# =========================================================
# STUDY PLANNER
# =========================================================
def render_study_planner():
    st.markdown('<h2 class="gradient-header" style="text-align:left; font-size:2rem !important;">Study Planner</h2>', unsafe_allow_html=True)
    uid = st.session_state.user["id"]
    subs = list_subjects(uid)
    if not subs:
        st.warning("Create a subject in Documents first.")
        return

    with st.form("planner_form"):
        names = [s["name"] for s in subs]
        sel_subs = st.multiselect("Subjects", names, default=names)
        c1, c2 = st.columns(2)
        with c1:
            start_d = st.date_input("Start Date", date.today())
        with c2:
            end_d = st.date_input("End Date", date.today() + timedelta(days=7))
        weak_areas = st.text_area("Weak areas / focus notes (optional)")
        submitted = st.form_submit_button("Generate Plan", type="primary")

    if submitted:
        if end_d <= start_d:
            st.error("End date must be after start date.")
        elif not sel_subs:
            st.error("Select at least one subject.")
        else:
            prompt = (
                f"Create a study plan as a JSON array of tasks. Each task object must have exactly these keys: "
                f"title (string), subject (one of {sel_subs}), due_date (YYYY-MM-DD between {start_d} and {end_d}), "
                f"priority (\"high\", \"medium\" or \"low\"), estimated_minutes (integer).\n"
                f"Weak areas to prioritize: {weak_areas or 'none specified'}.\n"
                f"Spread tasks sensibly across the date range, 1-3 tasks per day. "
                f"Return ONLY the JSON array, no other text."
            )
            with st.spinner("Asking Gemini to build your plan..."):
                text, err = call_gemini(prompt, json_mode=True)
            if err:
                st.error(err)
            else:
                try:
                    tasks = extract_json(text)
                    subj_map = {s["name"]: s["id"] for s in subs}
                    create_plan_with_tasks(uid, subj_map, f"Plan {start_d} to {end_d}", start_d, end_d, tasks)
                    st.success(f"Created a plan with {len(tasks)} tasks!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't parse the generated plan: {e}")

    st.subheader("Your Plans")
    plans = list_plans(uid)
    if not plans:
        st.info("No plans yet.")
    for p in plans:
        with st.expander(f"{p['title']} — {p['status']}"):
            tasks = [t for t in list_tasks(uid) if t["plan_id"] == p["id"]]
            for t in tasks:
                icon = "✅" if t["status"] == "completed" else "⬜"
                st.write(f"{icon} **{t['title']}** — {t.get('due_date','—')} · {t.get('priority','medium')} priority")


# =========================================================
# QUIZ
# =========================================================
def render_quiz():
    st.markdown('<h2 class="gradient-header" style="text-align:left; font-size:2rem !important;">Quiz</h2>', unsafe_allow_html=True)
    uid = st.session_state.user["id"]
    subs = list_subjects(uid)
    if not subs:
        st.warning("Create a subject in Documents first.")
        return

    if st.session_state.active_quiz is None:
        names = [s["name"] for s in subs]
        sel = st.selectbox("Subject", names)
        subject = next(s for s in subs if s["name"] == sel)
        num_q = st.slider("Number of questions", 3, 10, 5)
        if st.button("Generate Quiz", type="primary"):
            context = get_subject_context(subject["id"])
            prompt = (
                f"Create a {num_q}-question multiple-choice quiz for the subject '{subject['name']}'.\n"
                f"Base it on this material if present, otherwise use general knowledge of the subject:\n"
                f"{context or '(no material uploaded)'}\n\n"
                "Return ONLY a JSON array. Each item must have exactly: "
                "id (integer starting at 1), text (question string), options (array of 4 strings), "
                "answer (must exactly match one of the options)."
            )
            with st.spinner("Generating quiz..."):
                text, err = call_gemini(prompt, json_mode=True)
            if err:
                st.error(err)
            else:
                try:
                    questions = extract_json(text)
                    quiz_id = save_quiz(subject["id"], f"{subject['name']} Quiz", questions)
                    st.session_state.active_quiz = {"id": quiz_id, "questions": questions}
                    st.session_state.quiz_results = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't parse the generated quiz: {e}")
    else:
        quiz = st.session_state.active_quiz
        st.subheader("Quiz in Progress")

        user_answers = {}
        for q in quiz.get("questions", []):
            st.markdown(f"**{q['text']}**")
            user_answers[q["id"]] = st.radio("Options", q["options"], key=f"q_{q['id']}")
            st.markdown("---")

        if st.button("Submit Quiz", type="primary"):
            score = 0
            for q in quiz.get("questions", []):
                if user_answers.get(q["id"]) == q["answer"]:
                    score += 1
            total = len(quiz.get("questions", []))
            pct = round((score / total) * 100, 1) if total else 0
            save_quiz_result(uid, quiz["id"], pct, user_answers)
            st.session_state.quiz_results = {"score": score, "total": total, "pct": pct, "answers": user_answers}
            st.rerun()

        if st.session_state.get("quiz_results"):
            results = st.session_state.quiz_results
            st.subheader("Results")
            for q in quiz.get("questions", []):
                ans = results["answers"].get(q["id"])
                if ans == q["answer"]:
                    st.success(f"{q['text']} — Correct! ({ans})")
                else:
                    st.error(f"{q['text']} — Incorrect. You chose '{ans}', correct is '{q['answer']}'.")
            st.write(f"### Final Score: {results['score']}/{results['total']} ({results['pct']}%)")
            if st.button("Back to Quiz Generator"):
                st.session_state.active_quiz = None
                st.session_state.quiz_results = None
                st.rerun()


# =========================================================
# DOCUMENTS
# =========================================================
def render_documents():
    st.markdown('<h2 class="gradient-header" style="text-align:left; font-size:2rem !important;">Documents</h2>', unsafe_allow_html=True)
    uid = st.session_state.user["id"]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("New Subject")
        s_name = st.text_input("Subject Name")
        s_desc = st.text_area("Description")
        if st.button("Create Subject", type="primary"):
            if s_name:
                create_subject(uid, s_name, s_desc)
                st.success("Subject created.")
                st.rerun()
            else:
                st.error("Subject name is required.")

    with col2:
        st.subheader("Upload Material")
        subs = list_subjects(uid)
        if subs:
            names = [s["name"] for s in subs]
            sel = st.selectbox("Subject", names, key="upload_subject")
            subject = next(s for s in subs if s["name"] == sel)
            up_file = st.file_uploader("Upload PDF", type=["pdf"])
            if up_file and st.button("Upload", type="primary"):
                doc_id, extracted = save_document(subject["id"], up_file)
                if extracted:
                    st.success("Uploaded and text extracted — the AI Tutor can now use it.")
                elif not PDF_SUPPORT:
                    st.warning("Uploaded, but install `pypdf` (`pip install pypdf`) to extract text for the AI Tutor.")
                else:
                    st.warning("Uploaded, but no extractable text was found (scanned/image-only PDF?).")
                st.rerun()
        else:
            st.info("Create a subject first.")

    st.markdown("---")
    st.subheader("Existing Subjects & Documents")
    subs = list_subjects(uid)
    docs = list_documents(uid)
    for s in subs:
        with st.expander(f"📁 {s['name']}"):
            st.caption(s.get("description") or "")
            sub_docs = [d for d in docs if d["subject_id"] == s["id"]]
            if sub_docs:
                for d in sub_docs:
                    st.write(f"📄 {d['filename']}")
            else:
                st.caption("No documents uploaded yet.")


# =========================================================
# SETTINGS
# =========================================================
def render_settings():
    st.markdown('<h2 class="gradient-header" style="text-align:left; font-size:2rem !important;">Settings</h2>', unsafe_allow_html=True)
    user = st.session_state.user
    st.text_input("Name", value=user["name"], disabled=True)
    st.text_input("Email", value=user["email"], disabled=True)
    st.text_input("Role", value=(user.get("role") or "").title(), disabled=True)

    st.markdown("---")
    st.subheader("System Status")
    st.write(f"**Data source:** local SQLite database (`{os.path.basename(DB_PATH)}`)")
    st.write(f"**Gemini API key configured:** {'✅ Yes' if GEMINI_API_KEY and GEMINI_API_KEY != 'your_gemini_api_key_here' else '❌ No — add GOOGLE_API_KEY to .env'}")
    st.write(f"**PDF text extraction (pypdf):** {'✅ Available' if PDF_SUPPORT else '❌ Not installed — run `pip install pypdf`'}")


# =========================================================
# MAIN
# =========================================================
def main():
    init_db()
    apply_custom_css()
    init_session_state()

    if st.session_state.user is not None:
        st.session_state.view = "app"

    if st.session_state.view == "home":
        render_home()
    elif st.session_state.view == "auth":
        render_auth()
    else:
        render_sidebar()
        page = st.session_state.page
        if page == "Dashboard":
            render_dashboard()
        elif page == "AI Tutor":
            render_ai_tutor()
        elif page == "Study Planner":
            render_study_planner()
        elif page == "Quiz":
            render_quiz()
        elif page == "Documents":
            render_documents()
        elif page == "Settings":
            render_settings()


if __name__ == "__main__":
    main()