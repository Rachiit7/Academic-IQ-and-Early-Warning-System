"""
models.py — Query helpers for the Academic Intelligence System.
All functions return plain dicts or lists of dicts (JSON-serialisable).
"""

from database import get_db

ATTENDANCE_THRESHOLD = 75.0   # % below this → attendance warning
MARKS_THRESHOLD = 40.0        # % below this → marks warning


# ─────────────────────────────────────────────────────────────────────────────
# Student helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_student_attendance_summary(student_id: int) -> list[dict]:
    """Return per-subject attendance stats for one student."""
    db = get_db()
    rows = db.execute('''
        SELECT s.id, s.name, s.code,
               COUNT(a.id)                                          AS total,
               SUM(CASE WHEN a.status IN ('P','L') THEN 1 ELSE 0 END) AS present
        FROM subjects s
        LEFT JOIN attendance a
               ON a.subject_id = s.id AND a.student_id = ?
        GROUP BY s.id
        ORDER BY s.name
    ''', (student_id,)).fetchall()
    db.close()

    result = []
    for r in rows:
        total   = r['total']   or 0
        present = r['present'] or 0
        absent  = total - present
        pct     = round(present / total * 100, 1) if total else 0.0
        result.append({
            'subject_id':   r['id'],
            'subject_name': r['name'],
            'subject_code': r['code'],
            'total':        total,
            'present':      present,
            'absent':       absent,
            'percentage':   pct,
            'warning':      pct < ATTENDANCE_THRESHOLD,
        })
    return result


def get_student_marks_detail(student_id: int) -> list[dict]:
    """Return every test score for one student (with subject & test meta)."""
    db = get_db()
    rows = db.execute('''
        SELECT s.id AS subject_id, s.name AS subject_name,
               t.id AS test_id, t.name AS test_name, t.max_marks, t.date,
               ts.marks_obtained
        FROM test_scores ts
        JOIN tests    t ON t.id  = ts.test_id
        JOIN subjects s ON s.id  = t.subject_id
        WHERE ts.student_id = ?
        ORDER BY s.name, t.date
    ''', (student_id,)).fetchall()
    db.close()

    result = []
    for r in rows:
        pct = round(r['marks_obtained'] / r['max_marks'] * 100, 1) if r['max_marks'] else 0.0
        result.append({
            'subject_id':     r['subject_id'],
            'subject_name':   r['subject_name'],
            'test_id':        r['test_id'],
            'test_name':      r['test_name'],
            'max_marks':      r['max_marks'],
            'marks_obtained': r['marks_obtained'],
            'percentage':     pct,
            'date':           r['date'],
            'warning':        pct < MARKS_THRESHOLD,
        })
    return result


def get_subject_avg_marks(student_id: int) -> list[dict]:
    """Return per-subject aggregate marks % for one student."""
    db = get_db()
    rows = db.execute('''
        SELECT s.id, s.name,
               SUM(ts.marks_obtained) AS obtained,
               SUM(t.max_marks)       AS total_max
        FROM subjects s
        LEFT JOIN tests      t  ON t.subject_id  = s.id
        LEFT JOIN test_scores ts ON ts.test_id    = t.id
                                AND ts.student_id = ?
        GROUP BY s.id
        ORDER BY s.name
    ''', (student_id,)).fetchall()
    db.close()

    result = []
    for r in rows:
        total_max = r['total_max'] or 0
        obtained  = r['obtained']  or 0
        pct = round(obtained / total_max * 100, 1) if total_max else 0.0
        result.append({
            'subject_id':   r['id'],
            'subject_name': r['name'],
            'obtained':     obtained,
            'total_max':    total_max,
            'percentage':   pct,
            'warning':      pct < MARKS_THRESHOLD,
        })
    return result


def get_student_attentiveness(student_id: int) -> list[dict]:
    """Return per-subject average attentiveness score."""
    db = get_db()
    rows = db.execute('''
        SELECT s.id, s.name,
               ROUND(AVG(a.score), 2) AS avg_score,
               COUNT(a.id)            AS sessions
        FROM subjects s
        LEFT JOIN attentiveness a
               ON a.subject_id = s.id AND a.student_id = ?
        GROUP BY s.id
        ORDER BY s.name
    ''', (student_id,)).fetchall()
    db.close()

    return [
        {
            'subject_id':   r['id'],
            'subject_name': r['name'],
            'avg_score':    round(r['avg_score'] or 0, 2),
            'sessions':     r['sessions'] or 0,
        }
        for r in rows
    ]


def get_student_status(student_id: int) -> str:
    """Return 'safe', 'warning', or 'critical'."""
    att   = get_student_attendance_summary(student_id)
    marks = get_subject_avg_marks(student_id)

    low_att   = any(a['warning'] for a in att)
    low_marks = any(m['warning'] for m in marks)

    if low_att and low_marks:
        return 'critical'
    if low_att or low_marks:
        return 'warning'
    return 'safe'


def get_all_students_status() -> list[dict]:
    """Return status info for every student."""
    db = get_db()
    students = db.execute(
        "SELECT id, name, email FROM users WHERE role='student' ORDER BY name"
    ).fetchall()
    db.close()

    result = []
    for s in students:
        att   = get_student_attendance_summary(s['id'])
        marks = get_subject_avg_marks(s['id'])
        status = get_student_status(s['id'])
        avg_att   = round(sum(a['percentage'] for a in att)   / len(att),   1) if att   else 0
        avg_marks = round(sum(m['percentage'] for m in marks) / len(marks), 1) if marks else 0
        result.append({
            'id':           s['id'],
            'name':         s['name'],
            'email':        s['email'],
            'status':       status,
            'avg_att':      avg_att,
            'avg_marks':    avg_marks,
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Faculty helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_faculty_subjects(faculty_id: int) -> list:
    """Return subjects assigned to this faculty, or all subjects as fallback."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM subjects WHERE faculty_id = ? ORDER BY name",
        (faculty_id,)
    ).fetchall()
    if not rows:
        # Faculty has no assigned subjects — return all subjects so the
        # dropdown is never empty (common for newly registered faculty).
        rows = db.execute("SELECT * FROM subjects ORDER BY name").fetchall()
    db.close()
    return rows


def get_all_students() -> list:
    db = get_db()
    rows = db.execute(
        "SELECT id, name, email FROM users WHERE role='student' ORDER BY name"
    ).fetchall()
    db.close()
    return rows


def get_subject_attendance_on_date(subject_id: int, date_str: str) -> dict:
    """Return {student_id: status} mapping for a given subject + date."""
    db = get_db()
    rows = db.execute(
        "SELECT student_id, status FROM attendance WHERE subject_id=? AND date=?",
        (subject_id, date_str)
    ).fetchall()
    db.close()
    return {r['student_id']: r['status'] for r in rows}


def get_subject_attentiveness_on_date(subject_id: int, date_str: str) -> dict:
    db = get_db()
    rows = db.execute(
        "SELECT student_id, score, notes FROM attentiveness WHERE subject_id=? AND date=?",
        (subject_id, date_str)
    ).fetchall()
    db.close()
    return {r['student_id']: {'score': r['score'], 'notes': r['notes']} for r in rows}


def get_tests_for_subjects(subject_ids: list) -> list:
    if not subject_ids:
        return []
    db = get_db()
    placeholders = ','.join('?' * len(subject_ids))
    rows = db.execute(f'''
        SELECT t.*, s.name AS subject_name
        FROM tests t JOIN subjects s ON s.id = t.subject_id
        WHERE t.subject_id IN ({placeholders})
        ORDER BY t.date DESC
    ''', subject_ids).fetchall()
    db.close()
    return rows


def get_scores_for_test(test_id: int) -> dict:
    db = get_db()
    rows = db.execute(
        "SELECT student_id, marks_obtained FROM test_scores WHERE test_id=?",
        (test_id,)
    ).fetchall()
    db.close()
    return {r['student_id']: r['marks_obtained'] for r in rows}


# ─────────────────────────────────────────────────────────────────────────────
# Admin helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_system_stats() -> dict:
    db = get_db()
    total_students = db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    total_faculty  = db.execute("SELECT COUNT(*) FROM users WHERE role='faculty'").fetchone()[0]
    total_subjects = db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    total_tests    = db.execute("SELECT COUNT(*) FROM tests").fetchone()[0]
    db.close()
    return {
        'students': total_students,
        'faculty':  total_faculty,
        'subjects': total_subjects,
        'tests':    total_tests,
    }


def get_all_users() -> list:
    db = get_db()
    rows = db.execute(
        "SELECT id, name, email, role, created_at FROM users ORDER BY role, name"
    ).fetchall()
    db.close()
    return rows


def get_all_subjects_with_faculty() -> list:
    db = get_db()
    rows = db.execute('''
        SELECT s.*, u.name AS faculty_name
        FROM subjects s
        LEFT JOIN users u ON u.id = s.faculty_id
        ORDER BY s.name
    ''').fetchall()
    db.close()
    return rows
