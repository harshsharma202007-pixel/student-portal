from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "student-project-secret-key"
DB = "students.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            marks REAL
        )
    """)
    # Demo login
    conn.execute(
        "INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)",
        ("student@gmail.com", "123456")
    )
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_email"] = email
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    students = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("dashboard.html", students=students)

@app.route("/add", methods=["POST"])
@login_required
def add_student():
    data = (
        request.form["name"].strip(),
        request.form["roll_no"].strip(),
        request.form["department"].strip(),
        request.form.get("email", "").strip(),
        request.form.get("phone", "").strip(),
        request.form.get("marks", "0") or 0
    )
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO students
            (name, roll_no, department, email, phone, marks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        flash("Student added successfully.")
    except sqlite3.IntegrityError:
        flash("This roll number already exists.")
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()
    flash("Student deleted.")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))