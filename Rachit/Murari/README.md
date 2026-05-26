# 🎓 AcademIQ — Academic Intelligence & Early Warning System

> A web-based academic monitoring platform that tracks student attendance and test scores in real time, automatically flags at-risk students, and provides actionable dashboards for students, faculty, and administrators.

---

## 📸 Screenshots

| Login | Admin Dashboard | Student Red Zone |
|---|---|---|
| Dark-themed login with demo credentials | 7 stat cards, risk donut, comparison chart | Critical alert banner + 3 subject charts |

---

## ✨ Features

### 👨‍🎓 Student Module
- Secure login with session management
- Personal dashboard with live performance charts (bar, radar)
- Subject-wise attendance summary with animated progress bars
- Test marks history and per-subject averages
- Smart alert page with **shortfall calculator** (how many classes needed to recover)
- Automated early warning banner: Safe ✅ / Warning ⚠️ / Critical 🔴

### 👩‍🏫 Faculty Module
- Dashboard with class risk distribution and student comparison chart
- **Attendance recording** — P / A / L per student, per date, per subject; instant "Mark All" buttons
- **Test management** — create tests with custom max marks, enter/update scores inline
- **Attentiveness rating** — interactive ⭐ star rating (1–5) with optional notes, pre-fills on revisit
- **Red Zone monitor** — detailed per-subject attendance bars, marks bars, and attentiveness scores for every at-risk student

### 🧑‍💼 Admin Module
- System-wide stats (students, faculty, subjects, tests conducted)
- User management — add, edit (with optional password reset), delete students/faculty/admins
- Subject management — create subjects, assign faculty, edit, delete
- Full analytics — risk distribution donut, per-student attendance and marks charts, critical student highlight panel

### 🚨 Early Warning Engine
| Condition | Status |
|---|---|
| Attendance ≥ 75% **and** Marks ≥ 40% | ✅ Safe |
| Attendance < 75% **or** Marks < 40% | ⚠️ Warning |
| Attendance < 75% **and** Marks < 40% | 🔴 Critical (Red Zone) |

### 🔐 Authentication
- Session-based login with Werkzeug password hashing
- Forgot password flow (generates a secure token, prints reset link to console in dev mode)
- Password reset via time-limited token (1 hour expiry)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3 · Flask 3.0 |
| Database | SQLite (via `sqlite3` stdlib) |
| Frontend | HTML5 · Vanilla CSS (custom design system) |
| Charts | Chart.js 4.4 (CDN) |
| Auth | Werkzeug `generate_password_hash` / `check_password_hash` |
| Fonts | Google Fonts — Inter |

---

## 📁 Project Structure

```
Murari/
├── app.py                        # Flask app + all routes
├── database.py                   # Schema creation + seed data
├── models.py                     # Query helpers (attendance %, marks %, status)
├── requirements.txt
├── academic.db                   # SQLite database (auto-created on first run)
│
├── static/
│   ├── css/
│   │   └── style.css             # Full design system (dark theme, glassmorphism)
│   └── js/
│       └── charts.js             # Chart.js wrappers, modals, animations
│
└── templates/
    ├── base.html                 # Layout shell — sidebar, topbar, flash messages
    ├── login.html
    ├── forgot_password.html
    ├── reset_password.html
    ├── student/
    │   ├── dashboard.html        # Status banner, 3 charts, subject cards
    │   ├── attendance.html       # Subject cards + history table
    │   ├── marks.html            # Avg cards + bar chart + test records
    │   └── alerts.html           # Compliance tables + shortfall calculator
    ├── faculty/
    │   ├── dashboard.html        # Stats, charts, student risk table
    │   ├── attendance.html       # P/A/L radio form + quick fill
    │   ├── marks.html            # Create test modal + inline score entry
    │   ├── attentiveness.html    # Star rating (1–5) + notes per student
    │   └── red_zone.html         # Detailed at-risk student cards
    └── admin/
        ├── dashboard.html        # System stats + charts + student table
        ├── users.html            # CRUD users (add/edit/delete modals)
        ├── subjects.html         # Subject management + faculty assignment
        └── analytics.html        # System-wide charts + performance report
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```powershell
# 1. Navigate to the project directory
cd "c:\Users\Asus\Desktop\Murari"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python app.py
```

The server will start at **http://127.0.0.1:5000**

The database (`academic.db`) is **created and seeded automatically** on first run.

---

## 🔑 Demo Accounts

| Role | Email | Password | Notes |
|---|---|---|---|
| Admin | `admin@school.edu` | `admin123` | Full system access |
| Faculty | `dr.smith@school.edu` | `faculty123` | Maths & Physics |
| Faculty | `prof.jones@school.edu` | `faculty123` | Chemistry, English, CS |
| Student ✅ | `alice@school.edu` | `student123` | Safe — 93% att, 87% marks |
| Student ⚠️ | `bob@school.edu` | `student123` | Warning — low marks |
| Student ⚠️ | `charlie@school.edu` | `student123` | Warning — low attendance |
| Student 🔴 | `diana@school.edu` | `student123` | **Critical Red Zone** |
| Student ✅ | `ethan@school.edu` | `student123` | Safe — 88% att, 73% marks |

---

## 📊 Sample Dataset

| Category | Count |
|---|---|
| Students | 5 |
| Faculty | 2 |
| Subjects | 5 |
| Tests per subject | 3 (Unit Test 1, Mid-Term, Unit Test 2) |
| Attendance records | ~60 school days per subject per student |
| Attentiveness records | ~60 sessions per subject per student |

---

## 🗄️ Database Schema

```
users            — id, name, email, password_hash, role, created_at
password_resets  — id, user_id, token, expires_at, used
subjects         — id, name, code, faculty_id
attendance       — id, student_id, subject_id, date, status (P/A/L)
tests            — id, subject_id, name, max_marks, date
test_scores      — id, test_id, student_id, marks_obtained
attentiveness    — id, student_id, subject_id, date, score (1-5), notes
```

---

## 🎨 Design System

- **Color palette**: Dark navy `#0a0f1e` base · Electric indigo `#6366f1` accent · Amber `#f59e0b` warning · Crimson `#ef4444` critical · Emerald `#10b981` success
- **Typography**: [Inter](https://fonts.google.com/specimen/Inter) via Google Fonts
- **Cards**: Glassmorphism with `backdrop-blur` and subtle borders
- **Animations**: Slide-up entrance animations, animated stat counters, smooth progress bar fills
- **Charts**: Chart.js doughnut, horizontal bar, grouped bar, radar
- **Responsive**: Mobile-first with collapsible sidebar

---

## 📡 API Endpoints

| Endpoint | Role | Description |
|---|---|---|
| `GET /api/student/charts` | Student | JSON for attendance + marks chart data |
| `GET /api/admin/charts` | Admin | JSON for status counts + student comparison |
| `GET /api/faculty/charts` | Faculty | JSON for student attendance + marks comparison |

---

## 🔒 Security Notes

- Passwords are **never stored in plaintext** — bcrypt-compatible Werkzeug hashing
- Role-based route protection via `@login_required(role=...)` decorator
- Admin cannot delete their own account
- Password reset tokens expire after **1 hour** and are single-use
- Flask `SECRET_KEY` should be changed to a secure random value in production

---

## 📄 License

This project is a prototype developed for academic demonstration purposes.
