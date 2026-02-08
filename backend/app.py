import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import mysql.connector

# Get the absolute path of the 'backend' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to 'VWISE' then into 'frontend/components'
frontend_path = os.path.abspath(os.path.join(current_dir, '..', 'frontend', 'components'))

app = Flask(__name__, 
            template_folder=frontend_path,
            static_folder=frontend_path,
            static_url_path='/static')

# Force the browser to recognize CSS files correctly
import mimetypes
mimetypes.add_type('text/css', '.css')

app.secret_key = 'supersecretkey'

# MySQL connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='vwise_vote'
    )
    return conn

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_no = request.form.get('studentNumber')
        pwd = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM accounts WHERE studentNumber = %s AND password = %s"
        cursor.execute(query, (student_no, pwd))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['id']
            # Using .upper() prevents login failure if DB has 'admin' instead of 'ADMIN'
            if user['department'].upper() == 'ADMIN': 
                session['role'] = 'ADMIN'  # optional, for easier checks
                return redirect('/adminhome')  # or url_for('adminhome')

            else:
                return redirect(url_for('userhome'))
        else:
            return render_template('login.html', error='Invalid Credentials')
            
    return render_template('login.html')

@app.route('/adminhome', strict_slashes=False)
def adminhome():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('adminhome.html')

@app.route('/userdashboard')
def userhome():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('userhome.html')

@app.route('/add_account', methods=['POST'])
def add_account():
    data = request.json
    
    # Extracting all fields based on your new table structure
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

@app.route('/assets/svg/<path:filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(frontend_path, '../assets/svg'), filename)

if __name__ == '__main__':
    print("Running Flask app in folder:", os.getcwd())
    print("Templates folder:", os.path.abspath('../frontend/components'))
    app.run(debug=True)