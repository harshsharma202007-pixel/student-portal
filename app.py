import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Secret key for session handling
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretstudentportalkey2026')

# Database path (compatible with Render disk or root directory)
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(app.root_path, 'student_portal.db'))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table if not exists
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
    
    # Insert Demo Student if not already created
    demo_email = "student@gmail.com"
    cursor.execute("SELECT * FROM users WHERE email = ?", (demo_email,))
    user = cursor.fetchone()
    
    if not user:
        hashed_password = generate_password_hash("Student@123")
        cursor.execute("""
            INSERT INTO users (email, password, name, roll_number, course, semester, attendance, academic_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            demo_email,
            hashed_password,
            "Demo Student",
            "ITS2026-001",
            "B.Tech CSE Core",
            "3rd Semester",
            86.5,
            78.0
        ))
    
    conn.commit()
    conn.close()

# Initialize DB on startup
with app.app_context():
    init_db()

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash('Kripya email aur password dono enter karein.', 'error')
            return render_template('login.html')
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Galat email ya password. Kripya phir se koshish karein.', 'error')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Dashboard access karne ke liye pehle login karein.', 'error')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        session.clear()
        flash('User account nahi milo. Kripya login karein.', 'error')
        return redirect(url_for('login'))
        
    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Aap successfully logout ho chuke hain.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
