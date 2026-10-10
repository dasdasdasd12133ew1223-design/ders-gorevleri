import sqlite3
import os
import hashlib
import hmac
import secrets
from contextlib import closing
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "DersGorevleri",
)
MEMBERS_DB = os.path.join(DATA_DIR, "members.db")
DB_FILE = os.path.join(DATA_DIR, "member_1.db")
PASSWORD_HASH_ITERATIONS = 600_000


def _migrate_legacy_data():
    os.makedirs(DATA_DIR, exist_ok=True)

    legacy_members = os.path.join(APP_DIR, "members.db")
    if os.path.isfile(legacy_members) and not os.path.exists(MEMBERS_DB):
        _copy_sqlite_database(legacy_members, MEMBERS_DB)

    legacy_tasks = os.path.join(APP_DIR, "tasks.db")
    member_one_tasks = os.path.join(DATA_DIR, "member_1.db")
    if os.path.isfile(legacy_tasks) and not os.path.exists(member_one_tasks):
        _copy_sqlite_database(legacy_tasks, member_one_tasks)

    legacy_members_dir = os.path.join(APP_DIR, "member_data")
    if os.path.isdir(legacy_members_dir):
        for filename in os.listdir(legacy_members_dir):
            if not filename.startswith("member_") or not filename.endswith(".db"):
                continue
            source = os.path.join(legacy_members_dir, filename)
            destination = os.path.join(DATA_DIR, filename)
            if os.path.isfile(source) and not os.path.exists(destination):
                _copy_sqlite_database(source, destination)


def _copy_sqlite_database(source_path, destination_path):
    with closing(sqlite3.connect(source_path)) as source:
        with closing(sqlite3.connect(destination_path)) as destination:
            source.backup(destination)


def init_membership_db():
    _migrate_legacy_data()
    with closing(sqlite3.connect(MEMBERS_DB)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_salt BLOB NOT NULL,
                    password_hash BLOB NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'Ücretsiz',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)


def remember_member(member_id):
    with closing(sqlite3.connect(MEMBERS_DB)) as conn:
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO app_state (key, value) VALUES ('remembered_member_id', ?)",
                (str(int(member_id)),),
            )


def get_remembered_member():
    with closing(sqlite3.connect(MEMBERS_DB)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("""
            SELECT m.id, m.email, m.plan
            FROM app_state s
            JOIN members m ON m.id = CAST(s.value AS INTEGER)
            WHERE s.key = 'remembered_member_id'
        """).fetchone()

    return dict(row) if row else None


def forget_member():
    with closing(sqlite3.connect(MEMBERS_DB)) as conn:
        with conn:
            conn.execute(
                "DELETE FROM app_state WHERE key = 'remembered_member_id'"
            )


def create_member(email, password):
    normalized_email = email.strip().lower()
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    try:
        with closing(sqlite3.connect(MEMBERS_DB)) as conn:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO members (email, password_salt, password_hash) VALUES (?, ?, ?)",
                    (normalized_email, salt, password_hash),
                )
                member_id = cursor.lastrowid
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            return None
        raise

    return {"id": member_id, "email": normalized_email, "plan": "Ücretsiz"}


def authenticate_member(email, password):
    with closing(sqlite3.connect(MEMBERS_DB)) as conn:
        conn.row_factory = sqlite3.Row
        member = conn.execute(
            "SELECT id, email, password_salt, password_hash, plan FROM members WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

    if member is None:
        return None

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        member["password_salt"],
        PASSWORD_HASH_ITERATIONS,
    )
    if not hmac.compare_digest(actual_hash, member["password_hash"]):
        return None

    return {"id": member["id"], "email": member["email"], "plan": member["plan"]}


def select_member_database(member_id):
    global DB_FILE
    os.makedirs(DATA_DIR, exist_ok=True)
    DB_FILE = os.path.join(DATA_DIR, f"member_{int(member_id)}.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Dersler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#4A90E2',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Görevler tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT, -- YYYY-MM-DD
            due_time TEXT, -- HH:MM
            priority TEXT DEFAULT 'Normal', -- Düşük, Normal, Yüksek
            is_completed INTEGER DEFAULT 0,
            reminded INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
        )
    """)
    
    # Varsayılan popüler dersler ekleyelim (eğer yoksa)
    default_courses = [
        ("Matematik", "#3B82F6"),
        ("Fizik", "#8B5CF6"),
        ("Kimya", "#EC4899"),
        ("Biyoloji", "#10B981"),
        ("Türkçe / Edebiyat", "#F59E0B"),
        ("Tarih / Coğrafya", "#6366F1"),
        ("İngilizce", "#14B8A6"),
        ("Yazılım / Bilgisayar", "#06B6D4"),
        ("Genel Planlar", "#64748B")
    ]
    
    for name, color in default_courses:
        cursor.execute("INSERT OR IGNORE INTO courses (name, color) VALUES (?, ?)", (name, color))
        
    conn.commit()
    conn.close()

# --- DERS İŞLEMLERİ ---
def get_all_courses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses ORDER BY name ASC")
    courses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return courses

def add_course(name, color="#3B82F6"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO courses (name, color) VALUES (?, ?)", (name.strip(), color))
        conn.commit()
        course_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        course_id = None
    conn.close()
    return course_id

def delete_course(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    cursor.execute("UPDATE tasks SET course_id = NULL WHERE course_id = ?", (course_id,))
    conn.commit()
    conn.close()

# --- GÖREV İŞLEMLERİ ---
def add_task(title, description="", course_id=None, due_date=None, due_time=None, priority="Normal"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, description, course_id, due_date, due_time, priority, is_completed, reminded)
        VALUES (?, ?, ?, ?, ?, ?, 0, 0)
    """, (title.strip(), description.strip(), course_id, due_date, due_time, priority))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def update_task(task_id, title, description, course_id, due_date, due_time, priority):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tasks 
        SET title = ?, description = ?, course_id = ?, due_date = ?, due_time = ?, priority = ?, reminded = 0
        WHERE id = ?
    """, (title.strip(), description.strip(), course_id, due_date, due_time, priority, task_id))
    conn.commit()
    conn.close()

def toggle_task_status(task_id, is_completed):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET is_completed = ? WHERE id = ?", (1 if is_completed else 0, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_tasks(filter_type="all", course_id=None, search_query=""):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT t.*, c.name as course_name, c.color as course_color
        FROM tasks t
        LEFT JOIN courses c ON t.course_id = c.id
        WHERE 1=1
    """
    params = []
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if filter_type == "today":
        query += " AND t.due_date = ? AND t.is_completed = 0"
        params.append(today_str)
    elif filter_type == "upcoming":
        query += " AND t.due_date > ? AND t.is_completed = 0"
        params.append(today_str)
    elif filter_type == "completed":
        query += " AND t.is_completed = 1"
    elif filter_type == "pending":
        query += " AND t.is_completed = 0"
    elif filter_type == "course" and course_id:
        query += " AND t.course_id = ?"
        params.append(course_id)
        
    if search_query:
        query += " AND (t.title LIKE ? OR t.description LIKE ?)"
        term = f"%{search_query.strip()}%"
        params.extend([term, term])
        
    query += " ORDER BY t.is_completed ASC, CASE WHEN t.due_date IS NULL THEN 1 ELSE 0 END, t.due_date ASC, t.due_time ASC, t.id DESC"
    
    cursor.execute(query, params)
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def get_due_reminders():
    """Tarihi/saati gelmiş ve henüz bildirim gönderilmemiş aktif görevleri döner."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    query = """
        SELECT t.*, c.name as course_name
        FROM tasks t
        LEFT JOIN courses c ON t.course_id = c.id
        WHERE t.is_completed = 0 
          AND t.reminded = 0 
          AND t.due_date IS NOT NULL 
          AND (
            t.due_date < ? 
            OR (t.due_date = ? AND (t.due_time IS NULL OR t.due_time <= ?))
          )
    """
    cursor.execute(query, (today_str, today_str, time_str))
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def mark_as_reminded(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET reminded = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE is_completed = 0")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE is_completed = 1")
    completed = cursor.fetchone()[0]
    conn.close()
    return {"pending": pending, "completed": completed}
