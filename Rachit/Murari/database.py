import sqlite3
import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DATABASE = os.path.join(os.path.dirname(__file__), 'academic.db')


def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)   # wait up to 10s before raising lock error
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")        # WAL allows concurrent reads + one writer
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    _create_tables(conn)
    _seed_data(conn)
    conn.close()
    print("[DB] Database initialised successfully.")


def _create_tables(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL CHECK(role IN ('student','faculty','admin')),
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS password_resets (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token      TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used       INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            code       TEXT UNIQUE NOT NULL,
            faculty_id INTEGER REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            date       TEXT NOT NULL,
            status     TEXT NOT NULL CHECK(status IN ('P','A','L')),
            UNIQUE(student_id, subject_id, date)
        );

        CREATE TABLE IF NOT EXISTS tests (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            name       TEXT NOT NULL,
            max_marks  REAL NOT NULL,
            date       TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS test_scores (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id        INTEGER REFERENCES tests(id) ON DELETE CASCADE,
            student_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
            marks_obtained REAL NOT NULL,
            UNIQUE(test_id, student_id)
        );

        CREATE TABLE IF NOT EXISTS attentiveness (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
            date       TEXT NOT NULL,
            score      INTEGER CHECK(score BETWEEN 1 AND 5),
            notes      TEXT,
            UNIQUE(student_id, subject_id, date)
        );
    ''')
    conn.commit()


def _seed_data(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] > 0:
        print("[DB] Seed data already present – skipping.")
        return

    print("[DB] Seeding fresh data …")
    random.seed(42)

    # ── Users ──────────────────────────────────────
    users_data = [
        ('Pranav',       'admin@school.edu',    generate_password_hash('admin123'),   'admin'),
        ('Rishav','dr.smith@school.edu', generate_password_hash('faculty123'), 'faculty'),
        ('Yash','prof.jones@school.edu',generate_password_hash('faculty123'),'faculty'),
        ('Satyajit',   'alice@school.edu',    generate_password_hash('student123'), 'student'),
        ('Bablu',    'bob@school.edu',      generate_password_hash('student123'), 'student'),
        ('Naman',   'charlie@school.edu',  generate_password_hash('student123'), 'student'),
        ('Kunal',    'diana@school.edu',    generate_password_hash('student123'), 'student'),
        ('Sahil',      'ethan@school.edu',    generate_password_hash('student123'), 'student'),
    ]
    c.executemany(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
        users_data
    )
    conn.commit()

    c.execute("SELECT id FROM users WHERE role='faculty' ORDER BY id")
    faculty_ids = [r[0] for r in c.fetchall()]
    smith_id, jones_id = faculty_ids[0], faculty_ids[1]

    c.execute("SELECT id FROM users WHERE role='student' ORDER BY id")
    student_ids = [r[0] for r in c.fetchall()]
    Naman, Bablu, Kunal, Yash, Sahil = student_ids

    # ── Subjects ────────────────────────────────────
    subjects_data = [
        ('Mathematics',        'MATH101', smith_id),
        ('Physics',            'PHY101',  smith_id),
        ('Chemistry',          'CHEM101', jones_id),
        ('English Literature', 'ENG101',  jones_id),
        ('Computer Science',   'CS101',   jones_id),
    ]
    c.executemany(
        "INSERT INTO subjects (name, code, faculty_id) VALUES (?,?,?)",
        subjects_data
    )
    conn.commit()

    c.execute("SELECT id FROM subjects ORDER BY id")
    subject_ids = [r[0] for r in c.fetchall()]
    math_id, phy_id, chem_id, eng_id, cs_id = subject_ids

    # ── Tests (3 per subject) ───────────────────────
    base = datetime(2026, 1, 10)
    test_defs = [
        ('Unit Test 1', 20,  0),
        ('Mid-Term',    50, 25),
        ('Unit Test 2', 30, 50),
    ]
    tests_data = []
    for sid in subject_ids:
        for name, mx, days in test_defs:
            tests_data.append((sid, name, mx, (base + timedelta(days=days)).strftime('%Y-%m-%d')))

    c.executemany(
        "INSERT INTO tests (subject_id, name, max_marks, date) VALUES (?,?,?,?)",
        tests_data
    )
    conn.commit()

    c.execute("SELECT id, subject_id, max_marks FROM tests ORDER BY id")
    test_rows = c.fetchall()

    # ── Mark profiles (% of max_marks) ─────────────
    mark_profiles = {
        Naman:   {math_id:0.87, phy_id:0.83, chem_id:0.88, eng_id:0.91, cs_id:0.85},
        Bablu:     {math_id:0.30, phy_id:0.33, chem_id:0.76, eng_id:0.78, cs_id:0.36},
        Kunal: {math_id:0.72, phy_id:0.70, chem_id:0.74, eng_id:0.76, cs_id:0.71},
        Yash:   {math_id:0.28, phy_id:0.31, chem_id:0.33, eng_id:0.35, cs_id:0.27},
        Sahil:   {math_id:0.74, phy_id:0.71, chem_id:0.73, eng_id:0.77, cs_id:0.70},
    }

    scores_data = []
    for tid, sub_id, max_marks in test_rows:
        for stu_id in student_ids:
            pct = mark_profiles[stu_id][sub_id]
            obtained = round(max(0.0, min(float(max_marks),
                              max_marks * (pct + random.uniform(-0.04, 0.04)))), 1)
            scores_data.append((tid, stu_id, obtained))

    c.executemany(
        "INSERT OR IGNORE INTO test_scores (test_id, student_id, marks_obtained) VALUES (?,?,?)",
        scores_data
    )
    conn.commit()

    # ── Attendance profiles ─────────────────────────
    att_profiles = {
        Naman:   {s: 0.93 for s in subject_ids},
        Bablu:     {s: 0.80 for s in subject_ids},
        Kunal: {math_id:0.57, phy_id:0.54, chem_id:0.67, eng_id:0.59, cs_id:0.62},
        Yash:   {s: 0.54 for s in subject_ids},
        Sahil:   {s: 0.88 for s in subject_ids},
    }

    today = datetime.now()
    att_data = []
    for offset in range(59, -1, -1):
        day = today - timedelta(days=offset)
        if day.weekday() >= 5:
            continue
        day_str = day.strftime('%Y-%m-%d')
        for sub_id in subject_ids:
            for stu_id in student_ids:
                pct = att_profiles[stu_id][sub_id]
                r = random.random()
                if r < pct:
                    status = 'P'
                elif r < pct + 0.05:
                    status = 'L'
                else:
                    status = 'A'
                att_data.append((stu_id, sub_id, day_str, status))

    c.executemany(
        "INSERT OR IGNORE INTO attendance (student_id, subject_id, date, status) VALUES (?,?,?,?)",
        att_data
    )
    conn.commit()

    # ── Attentiveness records ───────────────────────
    att2_profiles = {alice: 4.5, bob: 3.0, charlie: 3.5, diana: 2.0, ethan: 4.1}
    notes_pool = [
        'Excellent participation', 'Good focus', 'Active in discussions',
        'Distracted at times', 'Needs improvement', 'Outstanding',
        'Average engagement', 'Requires attention', ''
    ]

    att2_data = []
    for offset in range(59, -1, -1):
        day = today - timedelta(days=offset)
        if day.weekday() >= 5:
            continue
        day_str = day.strftime('%Y-%m-%d')
        for sub_id in subject_ids:
            for stu_id in student_ids:
                avg = att2_profiles[stu_id]
                score = max(1, min(5, round(avg + random.uniform(-0.8, 0.8))))
                note = random.choice(notes_pool)
                att2_data.append((stu_id, sub_id, day_str, score, note))

    c.executemany(
        "INSERT OR IGNORE INTO attentiveness (student_id, subject_id, date, score, notes) VALUES (?,?,?,?,?)",
        att2_data
    )
    conn.commit()
    print("[DB] Seed complete.")
