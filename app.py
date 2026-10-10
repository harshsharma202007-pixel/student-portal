import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort 
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretstudentportalkey2026')
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(app.root_path, 'student_portal.db'))

INSERT_SQL = ("INSERT INTO users (email, password, name, roll_number, course, "
              "semester, attendance, academic_score, role) "
              "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "email TEXT UNIQUE NOT NULL, "
        "password TEXT NOT NULL, "
        "name TEXT NOT NULL, "
        "roll_number TEXT NOT NULL, "
        "course TEXT NOT NULL, "
        "semester TEXT NOT NULL, "
        "attendance REAL NOT NULL, "
        "academic_score REAL NOT NULL)"
      )
        cur.execute(
        "CREATE TABLE IF NOT EXISTS subjects ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "student_id INTEGER NOT NULL, "
        "subject_name TEXT NOT NULL, "
        "attendance REAL NOT NULL, "
        "marks REAL NOT NULL)"
        )

    cols = [c['name'] for c in cur.execute("PRAGMA table_info(users)").fetchall()]
    if 'role' not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")

    s = cur.execute("SELECT 1 FROM users WHERE email = ?", ("student@gmail.com",)).fetchone()
    if not s:
        cur.execute(INSERT_SQL, ("student@gmail.com", generate_password_hash("Student@123"),
                                 "Demo Student", "ITS2026-001", "B.Tech CSE Core",
                                 "3rd Semester", 86.5, 78.0, "student"))

    t_hash = generate_password_hash("Teacher@123")
    t = cur.execute("SELECT 1 FROM users WHERE email = ?", ("teacher@gmail.com",)).fetchone()
    if t:
        cur.execute("UPDATE users SET password = ?, role = 'teacher' WHERE email = ?",
                    (t_hash, "teacher@gmail.com"))
    else:
        cur.execute(INSERT_SQL, ("teacher@gmail.com", t_hash, "Demo Teacher",
                                 "-", "-", "-", 0, 0, "teacher"))

    conn.commit()
    conn.close()


with app.app_context():
    init_db()
def recalc_overall(conn, student_id):
    row = conn.execute(
        "SELECT AVG(attendance) AS a, AVG(marks) AS m, COUNT(*) AS n "
        "FROM subjects WHERE student_id = ?", (student_id,)).fetchone()
    if row['n']:
        conn.execute("UPDATE users SET attendance = ?, academic_score = ? WHERE id = ?",
                     (round(row['a'], 1), round(row['m'], 1), student_id))
    else:
        conn.execute("UPDATE users SET attendance = 0, academic_score = 0 WHERE id = ?",
                     (student_id,))


def home_for(role):
    return url_for('teacher') if role == 'teacher' else url_for('dashboard')


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(home_for(session.get('role')))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
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
        flash('unsuccessful.', 'error')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Dashboard access firstly login.', 'error')
        return redirect(url_for('login'))
    if session.get('role') == 'teacher':
        return redirect(url_for('teacher'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    subjects = conn.execute(
        "SELECT * FROM subjects WHERE student_id = ? ORDER BY subject_name",
        (session['user_id'],)).fetchall()
    conn.close()

    if not user:
        session.clear()
        flash('User account not found. try to login.', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=user,subjects=subjects)


def teacher_only():
    if 'user_id' not in session:
        flash('firstly login your account.', 'error')
        return redirect(url_for('login'))
    if session.get('role') != 'teacher':
        flash('this page only for teachers.', 'error')
        return redirect(url_for('dashboard'))
    return None
@app.route('/teacher/add', methods=['POST'])
def add_student():
    blocked = teacher_only()
    if blocked:
        return blocked

    f = request.form
    name = f.get('name', '').strip()
    email = f.get('email', '').strip().lower()
    password = f.get('password', '').strip()
    roll_number = f.get('roll_number', '').strip()
    course = f.get('course', '').strip()
    semester = f.get('semester', '').strip()

    if not all([name, email, password, roll_number, course, semester]):
        flash('Saari fields bharna zaroori hai.', 'error')
        return redirect(url_for('teacher'))

    conn = get_db_connection()
    try:
        cur = conn.execute(INSERT_SQL, (email, generate_password_hash(password), name,
                                        roll_number, course, semester, 0, 0, 'student'))
        conn.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        flash('Ye email pehle se maujood hai.', 'error')
        return redirect(url_for('teacher'))
    conn.close()
    flash(name + ' add ho gaya. Ab iske subjects add karein.', 'success')
    return redirect(url_for('student_subjects', student_id=new_id))




    conn = get_db_connection()
    try:
        conn.execute(INSERT_SQL, (email, generate_password_hash(password), name,
                                  roll_number, course, semester, attendance, score, 'student'))
        conn.commit()
        flash(name + ' add successfully.', 'success')
    except sqlite3.IntegrityError:
        flash('this email already available.', 'error')
    finally:
        conn.close()
    return redirect(url_for('teacher'))

@app.route('/teacher/student/<int:student_id>')
def student_subjects(student_id):
    blocked = teacher_only()
    if blocked:
        return blocked
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM users WHERE id = ? AND role = 'student'",
                           (student_id,)).fetchone()
    if not student:
        conn.close()
        abort(404)
    subjects = conn.execute(
        "SELECT * FROM subjects WHERE student_id = ? ORDER BY subject_name",
        (student_id,)).fetchall()
    conn.close()
    return render_template('student_subjects.html', student=student, subjects=subjects)


@app.route('/teacher/student/<int:student_id>/subject', methods=['POST'])
def save_subject(student_id):
    blocked = teacher_only()
    if blocked:
        return blocked

    subject_name = request.form.get('subject_name', '').strip()
    try:
        attendance = float(request.form.get('attendance', ''))
        marks = float(request.form.get('marks', ''))
    except ValueError:
        flash('Attendance aur marks number hone chahiye.', 'error')
        return redirect(url_for('student_subjects', student_id=student_id))

    if not subject_name:
        flash('Subject ka naam likhna zaroori hai.', 'error')
        return redirect(url_for('student_subjects', student_id=student_id))
    if not (0 <= attendance <= 100 and 0 <= marks <= 100):
        flash('Attendance aur marks 0 se 100 ke beech hone chahiye.', 'error')
        return redirect(url_for('student_subjects', student_id=student_id))

    conn = get_db_connection()
    student = conn.execute("SELECT id FROM users WHERE id = ? AND role = 'student'",
                           (student_id,)).fetchone()
    if not student:
        conn.close()
        abort(404)

    existing = conn.execute(
        "SELECT id FROM subjects WHERE student_id = ? AND LOWER(subject_name) = LOWER(?)",
        (student_id, subject_name)).fetchone()
    if existing:
        conn.execute("UPDATE subjects SET attendance = ?, marks = ? WHERE id = ?",
                     (attendance, marks, existing['id']))
        flash(subject_name + ' update ho gaya.', 'success')
    else:
        conn.execute("INSERT INTO subjects (student_id, subject_name, attendance, marks) "
                     "VALUES (?, ?, ?, ?)", (student_id, subject_name, attendance, marks))
        flash(subject_name + ' add ho gaya.', 'success')
    recalc_overall(conn, student_id)
    conn.commit()
    conn.close()
    return redirect(url_for('student_subjects', student_id=student_id))


@app.route('/teacher/subject/delete/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    blocked = teacher_only()
    if blocked:
        return blocked
    conn = get_db_connection()
    row = conn.execute("SELECT student_id FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    if not row:
        conn.close()
        abort(404)
    conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    recalc_overall(conn, row['student_id'])
    conn.commit()
    conn.close()
    flash('Subject delete ho gaya.', 'success')
    return redirect(url_for('student_subjects', student_id=row['student_id']))
@app.route('/teacher/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    blocked = teacher_only()
    if blocked:
        return blocked
    conn = get_db_connection()
    conn.execute("DELETE FROM subjects WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM users WHERE id = ? AND role = 'student'", (student_id,))
    conn.commit()
    conn.close()
    flash('Student get deleted.', 'success')
    return redirect(url_for('teacher'))


@app.route('/logout')
def logout():
    session.clear()
    flash('successfully logout.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
