import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretstudentportalkey2026')

DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(app.root_path, 'student_portal.db'))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            course TEXT NOT NULL,
            semester TEXT NOT NULL,
            attendance REAL NOT NULL,
            academic_score REAL NOT NULL
        )
    """)

    # Purani table mein role column add karo (agar nahi hai)
    cols = [c['name'] for c in cursor.execute("PRAGMA table_info(users)").fetchall()]
    if 'role' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")

    # Demo student
    if not cursor.execute("SELECT 1 FROM users WHERE email = ?", ("student@gmail.com",)).fetchone():
        cursor.execute("""
            INSERT INTO users (email, password, name, roll_number, course, semester,
                               attendance, academic_score, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'student')
        """, ("student@gmail.com", generate_password_hash("Student@123"),
              "Demo Student", "ITS2026-001", "B.Tech CSE Core", "3rd Semester", 86.5, 78.0))

    # Demo teacher
    if not cursor.execute("SELECT 1 FROM users WHERE email = ?", ("teacher@gmail.com",)).fetchone():
        cursor.execute("""
            INSERT INTO users (email, password, name, roll_number, course, semester,
                               attendance, academic_score, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'teacher')
        """, ("teacher@gmail.com", generate_password_hash("Teacher@123"),
              "Demo Teacher", "-", "-", "-", 0, 0)
                           cursor.execute(
        "UPDATE users SET role = 'teacher' WHERE email = ?",
        ("teacher@gmail.com",)
                           ) )

    conn.commit()
    conn.close()

with app.app_context():
    init_db()

def home_for(role):
    return url_for('teacher') if role == 'teacher' else url_for('dashboard')

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(home_for(session.get('role')))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Kripya email aur password dono enter karein.', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            flash('Login successful! Welcome back.', 'success')
            return redirect(home_for(user['role']))
        flash('Galat email ya password. Kripya phir se koshish karein.', 'error')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Dashboard access karne ke liye pehle login karein.', 'error')
        return redirect(url_for('login'))
    if session.get('role') == 'teacher':
        return redirect(url_for('teacher'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()

    if not user:
        session.clear()
        flash('User account nahi mila. Kripya login karein.', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=user)

def teacher_only():
    if 'user_id' not in session:
        flash('Pehle login karein.', 'error')
        return redirect(url_for('login'))
    if session.get('role') != 'teacher':
        flash('Ye page sirf teacher ke liye hai.', 'error')
        return redirect(url_for('dashboard'))
    return None

@app.route('/teacher')
def teacher():
    blocked = teacher_only()
    if blocked:
        return blocked
    conn = get_db_connection()
    students = conn.execute(
        "SELECT * FROM users WHERE role = 'student' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('teacher.html', students=students)

@app.route('/teacher/add', methods=['POST'])
def add_student():
    blocked = teacher_only()
    if blocked:
        return blocked

    f = request.form
    name = f.get('name', '').strip()
    email = f.get('email', '').strip()
    password = f.get('password', '').strip()
    roll_number = f.get('roll_number', '').strip()
    course = f.get('course', '').strip()
    semester = f.get('semester', '').strip()

    try:
        attendance = float(f.get('attendance', ''))
        score = float(f.get('academic_score', ''))
    except ValueError:
        flash('Attendance aur score number hone chahiye.', 'error')
        return redirect(url_for('teacher'))

    if not all([name, email, password, roll_number, course, semester]):
        flash('Saari fields bharna zaroori hai.', 'error')
        return redirect(url_for('teacher'))
    if not (0 <= attendance <= 100 and 0 <= score <= 100):
        flash('Attendance aur score 0 se 100 ke beech hone chahiye.', 'error')
        return redirect(url_for('teacher'))

    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO users (email, password, name, roll_number, course, semester,
                               attendance, academic_score, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'student')
        """, (email, generate_password_hash(password), name, roll_number,
              course, semester, attendance, score))
        conn.commit()
        flash(f'{name} ko add kar diya gaya.', 'success')
    except sqlite3.IntegrityError:
        flash('Ye email pehle se maujood hai.', 'error')
    finally:
        conn.close()
    return redirect(url_for('teacher'))

@app.route('/teacher/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    blocked = teacher_only()
    if blocked:
        return blocked
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ? AND role = 'student'", (student_id,))
    conn.commit()
    conn.close()
    flash('Student delete ho gaya.', 'success')
    return redirect(url_for('teacher'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Aap successfully logout ho chuke hain.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
