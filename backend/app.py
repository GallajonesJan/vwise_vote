import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import mysql.connector
import mimetypes
from functools import wraps
from flask import jsonify
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

@app.route('/votenow')
@login_required()
def votenow():
    return render_template('votenow.html')

@app.route('/votenow.html')
def votenow_html_redirect():
    return redirect(url_for('votenow'))

@app.route('/viewcandidates')
@login_required()
def viewcandidates():
    return render_template('viewcandidates.html')

@app.route('/viewcandidates.html')
def viewcandidates_html_redirect():
    return redirect(url_for('viewcandidates'))

@app.route('/viewparties')
@login_required()
def viewparties():
    return render_template('viewparties.html')

@app.route('/viewparties.html')
def viewparties_html_redirect():
    return redirect(url_for('viewparties'))

@app.route('/candidacy')
@login_required()
def candidacy():
    return render_template('candidacy.html')

@app.route('/candidacy.html')
def candidacy_html_redirect():
    return redirect(url_for('candidacy'))

@app.route('/partylist')
@login_required()
def partylist():
    return render_template('partylist.html')

@app.route('/partylist.html')
def partylist_html_redirect():
    return redirect(url_for('partylist'))

@app.route('/profile')
@login_required()
def profile():
    return render_template('profile.html')

@app.route('/profile.html')
def profile_html_redirect():
    return redirect(url_for('profile'))

@app.route('/submit-vote', methods=['POST'])
@login_required()  # Ensure only logged-in users can vote
def submit_vote():
    votes = request.json
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Optional: check if user has already voted
        cursor.execute("SELECT COUNT(*) AS count FROM votes WHERE user_id = %s", (user_id,))
        already_voted = cursor.fetchone()[0]
        if already_voted > 0:
            return jsonify({"error": "You have already voted!"}), 400

        # Insert each vote
        for position, data in votes.items():
            candidate_id = data['candidate_id']
            cursor.execute("""
                INSERT INTO votes (user_id, candidate_id, position, voted_at)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, candidate_id, position))
        
        conn.commit()
        return jsonify({"success": True, "message": "Vote submitted successfully!"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()




@app.route('/get-candidates', methods=['GET'])
def get_candidates():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, full_name, party, position
        FROM candidates
        WHERE approved = 1
        ORDER BY position
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Group candidates by position
    data = {}
    for row in rows:
        pos = row['position']
        data.setdefault(pos, []).append(row)

    return jsonify(data)

@app.route('/ping')
def ping():
    return 'pong'

@app.route('/adminapproval')
@login_required(role='ADMIN')
def adminapproval():
    return render_template('adminapproval.html')

@app.route('/adminapproval.html')
def adminapproval_html_redirect():
    return redirect(url_for('adminapproval'))

@app.route('/get-pending-candidates', methods=['GET'])
@login_required(role='ADMIN')
def get_pending_candidates():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, full_name, party, position, created_at, approved
        FROM candidates
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(rows)

@app.route('/approve-candidate/<int:candidate_id>', methods=['POST'])
@login_required(role='ADMIN')
def approve_candidate(candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE candidates 
            SET approved = 1 
            WHERE id = %s
        """, (candidate_id,))
        
        conn.commit()
        return jsonify({"success": True, "message": "Candidate approved successfully!"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/reject-candidate/<int:candidate_id>', methods=['POST'])
@login_required(role='ADMIN')
def reject_candidate(candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE candidates 
            SET approved = 0 
            WHERE id = %s
        """, (candidate_id,))
        
        conn.commit()
        return jsonify({"success": True, "message": "Candidate approval revoked!"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/delete-candidate/<int:candidate_id>', methods=['DELETE'])
@login_required(role='ADMIN')
def delete_candidate(candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Candidate deleted successfully!"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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
