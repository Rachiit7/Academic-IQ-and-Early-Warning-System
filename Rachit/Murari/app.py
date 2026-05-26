"""
app.py — Academic Intelligence & Early Warning System
Flask application entry-point with all routes.
"""

import secrets
from datetime import datetime, date, timedelta
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, init_db
import models

app = Flask(__name__)
app.secret_key = 'academic-intelligence-secret-key-2026-xK9mP2vQ'


# ─────────────────────────────────────────────────────────────────────────────
# Context helpers
# ─────────────────────────────────────────────────────────────────────────────

@app.context_processor
def inject_now():
    return {'now': datetime.now(), 'today': date.today().isoformat()}


# ─────────────────────────────────────────────────────────────────────────────
# Auth decorators
# ─────────────────────────────────────────────────────────────────────────────

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('You are not authorised to view that page.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}_dashboard"))
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}_dashboard"))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        db   = get_db()
        user = db.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        db.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['role']      = user['role']
            session['email']     = user['email']
            flash(f"Welcome back, {user['name'].split()[0]}!", 'success')
            return redirect(url_for(f"{user['role']}_dashboard"))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {name.split()[0]}! You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for(f"{session['role']}_dashboard"))

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        role     = request.form.get('role', 'student')

        # Validation
        errors = []
        if not name or len(name) < 2:
            errors.append('Full name must be at least 2 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if role not in ('student', 'faculty'):
            errors.append('Role must be Student or Faculty.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html',
                                   form_name=name, form_email=email, form_role=role)

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE LOWER(email) = ?", (email,)
        ).fetchone()

        if existing:
            db.close()
            flash('An account with that email already exists. Please log in.', 'danger')
            return render_template('register.html',
                                   form_name=name, form_email=email, form_role=role)

        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
            (name, email, generate_password_hash(password), role)
        )
        db.commit()
        new_user = db.execute(
            "SELECT * FROM users WHERE LOWER(email) = ?", (email,)
        ).fetchone()
        db.close()

        session['user_id']   = new_user['id']
        session['user_name'] = new_user['name']
        session['role']      = new_user['role']
        session['email']     = new_user['email']
        flash(f"Welcome to AcademIQ, {name.split()[0]}! Your account has been created.", 'success')
        return redirect(url_for(f"{role}_dashboard"))

    return render_template('register.html', form_name='', form_email='', form_role='student')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        db    = get_db()
        user  = db.execute("SELECT id, name FROM users WHERE LOWER(email) = ?", (email,)).fetchone()

        if user:
            token      = secrets.token_urlsafe(32)
            expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
            db.execute(
                "INSERT INTO password_resets (user_id, token, expires_at) VALUES (?,?,?)",
                (user['id'], token, expires_at)
            )
            db.commit()
            reset_link = url_for('reset_password', token=token, _external=True)
            # In production this would send an email; for dev we print it
            print(f"\n[PASSWORD RESET] Link for {email}:\n  {reset_link}\n")
            flash(
                'If that email exists, a reset link has been printed to the server console.',
                'info'
            )
        else:
            # Don't reveal whether the email exists
            flash('If that email exists, a reset link has been printed to the server console.', 'info')

        db.close()
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    db    = get_db()
    reset = db.execute(
        "SELECT * FROM password_resets WHERE token=? AND used=0", (token,)
    ).fetchone()

    if not reset or datetime.fromisoformat(reset['expires_at']) < datetime.now():
        db.close()
        flash('This reset link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm      = request.form.get('confirm', '')
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif new_password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            db.execute(
                "UPDATE users SET password_hash=? WHERE id=?",
                (generate_password_hash(new_password), reset['user_id'])
            )
            db.execute("UPDATE password_resets SET used=1 WHERE id=?", (reset['id'],))
            db.commit()
            db.close()
            flash('Password updated successfully! Please log in.', 'success')
            return redirect(url_for('login'))

    db.close()
    return render_template('reset_password.html', token=token)


# ─────────────────────────────────────────────────────────────────────────────
# ★ Student routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    sid         = session['user_id']
    att_summary = models.get_student_attendance_summary(sid)
    avg_marks   = models.get_subject_avg_marks(sid)
    status      = models.get_student_status(sid)
    attentive   = models.get_student_attentiveness(sid)
    return render_template(
        'student/dashboard.html',
        att_summary=att_summary,
        avg_marks=avg_marks,
        status=status,
        attentive=attentive,
    )


@app.route('/student/attendance')
@login_required(role='student')
def student_attendance():
    sid         = session['user_id']
    att_summary = models.get_student_attendance_summary(sid)

    db = get_db()
    records = db.execute('''
        SELECT a.date, a.status, s.name AS subject_name, s.code
        FROM attendance a
        JOIN subjects s ON s.id = a.subject_id
        WHERE a.student_id = ?
        ORDER BY a.date DESC, s.name
    ''', (sid,)).fetchall()
    db.close()

    return render_template('student/attendance.html',
                           att_summary=att_summary, records=records)


@app.route('/student/marks')
@login_required(role='student')
def student_marks():
    sid       = session['user_id']
    marks     = models.get_student_marks_detail(sid)
    avg_marks = models.get_subject_avg_marks(sid)
    return render_template('student/marks.html', marks=marks, avg_marks=avg_marks)


@app.route('/student/alerts')
@login_required(role='student')
def student_alerts():
    sid         = session['user_id']
    att_summary = models.get_student_attendance_summary(sid)
    avg_marks   = models.get_subject_avg_marks(sid)
    status      = models.get_student_status(sid)
    attentive   = models.get_student_attentiveness(sid)
    return render_template('student/alerts.html',
                           att_summary=att_summary,
                           avg_marks=avg_marks,
                           status=status,
                           attentive=attentive)


# ─────────────────────────────────────────────────────────────────────────────
# ★ Faculty routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/faculty/dashboard')
@login_required(role='faculty')
def faculty_dashboard():
    fid      = session['user_id']
    subjects = models.get_faculty_subjects(fid)
    students = models.get_all_students_status()
    red_zone = [s for s in students if s['status'] == 'critical']
    warning  = [s for s in students if s['status'] == 'warning']
    return render_template('faculty/dashboard.html',
                           subjects=subjects,
                           all_students=students,
                           red_zone=red_zone,
                           warning=warning)


@app.route('/faculty/attendance', methods=['GET', 'POST'])
@login_required(role='faculty')
def faculty_attendance():
    fid      = session['user_id']
    subjects = models.get_faculty_subjects(fid)
    students = models.get_all_students()

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        att_date   = request.form.get('att_date')
        db = get_db()
        for s in students:
            status = request.form.get(f'status_{s["id"]}', 'A')
            db.execute('''
                INSERT OR REPLACE INTO attendance (student_id, subject_id, date, status)
                VALUES (?,?,?,?)
            ''', (s['id'], subject_id, att_date, status))
        db.commit()
        db.close()
        flash(f'Attendance saved for {att_date}!', 'success')
        return redirect(url_for('faculty_attendance',
                                subject_id=subject_id, date=att_date))

    sel_sub  = request.args.get('subject_id', subjects[0]['id'] if subjects else None)
    sel_date = request.args.get('date', date.today().isoformat())
    existing = {}
    if sel_sub:
        existing = models.get_subject_attendance_on_date(int(sel_sub), sel_date)

    return render_template('faculty/attendance.html',
                           subjects=subjects,
                           students=students,
                           sel_sub=int(sel_sub) if sel_sub else None,
                           sel_date=sel_date,
                           existing=existing)


@app.route('/faculty/marks', methods=['GET', 'POST'])
@login_required(role='faculty')
def faculty_marks():
    fid      = session['user_id']
    subjects = models.get_faculty_subjects(fid)
    students = models.get_all_students()

    if request.method == 'POST':
        action = request.form.get('action')
        db = get_db()

        if action == 'add_test':
            sid_form  = request.form.get('subject_id')
            tname     = request.form.get('test_name', '').strip()
            max_marks = request.form.get('max_marks')
            tdate     = request.form.get('test_date')
            if tname and max_marks and tdate:
                db.execute(
                    "INSERT INTO tests (subject_id, name, max_marks, date) VALUES (?,?,?,?)",
                    (sid_form, tname, float(max_marks), tdate)
                )
                db.commit()
                flash(f'Test "{tname}" created!', 'success')
            else:
                flash('Please fill all test fields.', 'danger')

        elif action == 'save_scores':
            test_id = request.form.get('test_id')
            for s in students:
                val = request.form.get(f'marks_{s["id"]}')
                if val is not None and val.strip() != '':
                    db.execute('''
                        INSERT OR REPLACE INTO test_scores (test_id, student_id, marks_obtained)
                        VALUES (?,?,?)
                    ''', (test_id, s['id'], float(val)))
            db.commit()
            flash('Marks saved!', 'success')

        db.close()
        return redirect(url_for('faculty_marks'))

    sub_ids = [s['id'] for s in subjects]
    tests   = models.get_tests_for_subjects(sub_ids)
    scores  = {t['id']: models.get_scores_for_test(t['id']) for t in tests}

    return render_template('faculty/marks.html',
                           subjects=subjects,
                           students=students,
                           tests=tests,
                           scores=scores)


@app.route('/faculty/attentiveness', methods=['GET', 'POST'])
@login_required(role='faculty')
def faculty_attentiveness():
    fid      = session['user_id']
    subjects = models.get_faculty_subjects(fid)
    students = models.get_all_students()

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        att_date   = request.form.get('att_date')
        db = get_db()
        for s in students:
            score = request.form.get(f'score_{s["id"]}')
            notes = request.form.get(f'notes_{s["id"]}', '')
            if score:
                db.execute('''
                    INSERT OR REPLACE INTO attentiveness
                        (student_id, subject_id, date, score, notes)
                    VALUES (?,?,?,?,?)
                ''', (s['id'], subject_id, att_date, int(score), notes))
        db.commit()
        db.close()
        flash(f'Attentiveness saved for {att_date}!', 'success')
        return redirect(url_for('faculty_attentiveness',
                                subject_id=subject_id, date=att_date))

    sel_sub  = request.args.get('subject_id', subjects[0]['id'] if subjects else None)
    sel_date = request.args.get('date', date.today().isoformat())
    existing = {}
    if sel_sub:
        existing = models.get_subject_attentiveness_on_date(int(sel_sub), sel_date)

    return render_template('faculty/attentiveness.html',
                           subjects=subjects,
                           students=students,
                           sel_sub=int(sel_sub) if sel_sub else None,
                           sel_date=sel_date,
                           existing=existing)


@app.route('/faculty/red-zone')
@login_required(role='faculty')
def faculty_red_zone():
    all_students = models.get_all_students_status()
    at_risk = [s for s in all_students if s['status'] in ('critical', 'warning')]

    detailed = []
    for s in at_risk:
        att      = models.get_student_attendance_summary(s['id'])
        marks    = models.get_subject_avg_marks(s['id'])
        attentive= models.get_student_attentiveness(s['id'])
        detailed.append({**s, 'attendance': att, 'marks': marks, 'attentive': attentive})

    return render_template('faculty/red_zone.html', detailed=detailed)


# ─────────────────────────────────────────────────────────────────────────────
# ★ Admin routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    stats    = models.get_system_stats()
    students = models.get_all_students_status()
    safe     = sum(1 for s in students if s['status'] == 'safe')
    warning  = sum(1 for s in students if s['status'] == 'warning')
    critical = sum(1 for s in students if s['status'] == 'critical')
    return render_template('admin/dashboard.html',
                           stats=stats,
                           students=students,
                           safe=safe,
                           warning=warning,
                           critical=critical)


@app.route('/admin/users', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_users():
    db = get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            try:
                db.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
                    (request.form['name'], request.form['email'],
                     generate_password_hash(request.form['password']),
                     request.form['role'])
                )
                db.commit()
                flash(f"User '{request.form['name']}' added.", 'success')
            except Exception:
                flash('Error: email already registered.', 'danger')

        elif action == 'edit':
            uid  = request.form['user_id']
            pwd  = request.form.get('password', '').strip()
            if pwd:
                db.execute(
                    "UPDATE users SET name=?,email=?,role=?,password_hash=? WHERE id=?",
                    (request.form['name'], request.form['email'],
                     request.form['role'], generate_password_hash(pwd), uid)
                )
            else:
                db.execute(
                    "UPDATE users SET name=?,email=?,role=? WHERE id=?",
                    (request.form['name'], request.form['email'],
                     request.form['role'], uid)
                )
            db.commit()
            flash('User updated.', 'success')

        elif action == 'delete':
            uid = request.form['user_id']
            if int(uid) == session['user_id']:
                flash("You can't delete your own account.", 'danger')
            else:
                db.execute("DELETE FROM users WHERE id=?", (uid,))
                db.commit()
                flash('User deleted.', 'info')

        db.close()
        return redirect(url_for('admin_users'))

    users = models.get_all_users()
    db.close()
    return render_template('admin/users.html', users=users)


@app.route('/admin/subjects', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_subjects():
    db = get_db()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            try:
                db.execute(
                    "INSERT INTO subjects (name, code, faculty_id) VALUES (?,?,?)",
                    (request.form['name'], request.form['code'],
                     request.form.get('faculty_id') or None)
                )
                db.commit()
                flash('Subject added.', 'success')
            except Exception:
                flash('Error: subject code already exists.', 'danger')

        elif action == 'edit':
            db.execute(
                "UPDATE subjects SET name=?,code=?,faculty_id=? WHERE id=?",
                (request.form['name'], request.form['code'],
                 request.form.get('faculty_id') or None,
                 request.form['subject_id'])
            )
            db.commit()
            flash('Subject updated.', 'success')

        elif action == 'delete':
            db.execute("DELETE FROM subjects WHERE id=?", (request.form['subject_id'],))
            db.commit()
            flash('Subject deleted.', 'info')

        db.close()
        return redirect(url_for('admin_subjects'))

    subjects = models.get_all_subjects_with_faculty()
    faculty  = db.execute(
        "SELECT id, name FROM users WHERE role='faculty' ORDER BY name"
    ).fetchall()
    db.close()
    return render_template('admin/subjects.html', subjects=subjects, faculty=faculty)


@app.route('/admin/analytics')
@login_required(role='admin')
def admin_analytics():
    students = models.get_all_students_status()
    return render_template('admin/analytics.html', students=students)


# ─────────────────────────────────────────────────────────────────────────────
# ★ JSON / API endpoints (for Chart.js)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/student/charts')
@login_required(role='student')
def api_student_charts():
    sid  = session['user_id']
    att  = models.get_student_attendance_summary(sid)
    mrks = models.get_subject_avg_marks(sid)
    return jsonify({
        'attendance': {
            'labels': [a['subject_name'] for a in att],
            'data':   [a['percentage']   for a in att],
        },
        'marks': {
            'labels': [m['subject_name'] for m in mrks],
            'data':   [m['percentage']   for m in mrks],
        },
    })


@app.route('/api/admin/charts')
@login_required(role='admin')
def api_admin_charts():
    students = models.get_all_students_status()
    safe     = sum(1 for s in students if s['status'] == 'safe')
    warning  = sum(1 for s in students if s['status'] == 'warning')
    critical = sum(1 for s in students if s['status'] == 'critical')
    return jsonify({
        'status':     {'safe': safe, 'warning': warning, 'critical': critical},
        'students':   [s['name'].split()[0] for s in students],
        'attendance': [s['avg_att']   for s in students],
        'marks':      [s['avg_marks'] for s in students],
    })


@app.route('/api/faculty/charts')
@login_required(role='faculty')
def api_faculty_charts():
    students = models.get_all_students_status()
    return jsonify({
        'students':   [s['name'].split()[0] for s in students],
        'attendance': [s['avg_att']   for s in students],
        'marks':      [s['avg_marks'] for s in students],
        'statuses':   [s['status']    for s in students],
    })


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
