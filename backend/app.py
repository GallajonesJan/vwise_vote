import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import mysql.connector
import mimetypes
from functools import wraps
from flask_cors import CORS

# Force browser to recognize CSS correctly
mimetypes.add_type('text/css', '.css')

# Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.abspath(os.path.join(current_dir, '..', 'frontend', 'components'))
assets_svg_path = os.path.abspath(os.path.join(current_dir, '..', 'frontend', 'assets', 'svg'))

# Flask app
app = Flask(
    __name__,
    template_folder=frontend_path,
    static_folder=frontend_path,
    static_url_path='/static'
)
app.secret_key = 'supersecretkey'
CORS(app)
# ----------------------------
# Database connection
# ----------------------------
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='vwise_vote'
    )
    return conn

# ----------------------------
# Helper: login required decorator
# ----------------------------

def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))

            if role and session.get('role') != role.upper():
                return redirect(url_for('login'))

            return func(*args, **kwargs)
        return wrapper
    return decorator

# ----------------------------
# Routes
# ----------------------------

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_no = request.form.get('studentNumber')
        pwd = request.form.get('password')
        print("Login attempt:", student_no, pwd)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM accounts WHERE studentNumber = %s AND password = %s"
        cursor.execute(query, (student_no, pwd))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        print("User fetched:", user)

        if user:
            session['user_id'] = user['id']
            # Strip spaces and uppercase
            session['role'] = user['department'].strip().upper()
            print("Session role after login:", session['role'])

            if session['role'] == 'ADMIN':
                return redirect(url_for('adminhome'))
            else:
                return redirect(url_for('userhome'))

        else:
            print("Login failed")
            return render_template('login.html', error='Invalid Credentials')

    return render_template('login.html')

@app.route('/adminhome')
@login_required(role='ADMIN')
def adminhome():
    return render_template('adminhome.html')

@app.route('/userdashboard')
@login_required()
def userhome():
    return render_template('userhome.html')

@app.route('/add_account', methods=['POST'])
@login_required(role='ADMIN')
def add_account():
    data = request.json

    firstname = data.get('firstname')
    middlename = data.get('middlename')
    lastname = data.get('lastname')
    email = data.get('email')
    studentNumber = data.get('studentNumber')
    yearlevel = data.get('yearlevel')
    department = data.get('department')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            INSERT INTO accounts 
            (firstname, middlename, lastname, email, studentNumber, yearlevel, department, password) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (firstname, middlename, lastname, email, 
                               studentNumber, yearlevel, department, password))
        conn.commit()
        return {"message": "Account created successfully!"}, 201
    except Exception as e:
        return {"error": str(e)}, 400
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Serve SVGs
@app.route('/assets/svg/<path:filename>')
def custom_static(filename):
    return send_from_directory(assets_svg_path, filename)

# Redirect old .html URLs to clean routes
@app.route('/login.html')
def login_html_redirect():
    return redirect(url_for('login'))

@app.route('/adminhome.html')
def adminhome_html_redirect():
    return redirect(url_for('adminhome'))

@app.route('/userhome.html')
def userhome_html_redirect():
    return redirect(url_for('userhome'))

# ----------------------------
# Run Flask
# ----------------------------
if __name__ == '__main__':
    print("Running Flask app in folder:", os.getcwd())
    print("Templates folder:", frontend_path)
    app.run(debug=True)
