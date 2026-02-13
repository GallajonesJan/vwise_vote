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


@app.route('/get-candidates-simple', methods=['GET'])
def get_candidates_simple():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            id,
            first_name,
            last_name,
            college,
            position,
            photo
        FROM candidates
        WHERE approved = 1
        ORDER BY CAST(position AS UNSIGNED), last_name ASC
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(rows)


@app.route('/get-candidates', methods=['GET'])
def get_candidates():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all approved candidates
    cursor.execute("""
        SELECT id, first_name, last_name, student_id, college, year_level,
               position, affiliation_type, platform
        FROM candidates
        WHERE approved = 1
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print("=== DEBUG: Raw candidates from database ===")
    for row in rows:
        print(f"ID: {row['id']}, Name: {row['first_name']} {row['last_name']}, Position: {row['position']} (type: {type(row['position'])})")
    
    # Position mapping
    position_names = {
        '1': 'President',
        '2': 'Vice President',
        '3': 'Secretary',
        '4': 'Assistant Secretary',
        '5': 'Treasurer',
        '6': 'Auditor',
        '7': 'PIO (Public Information Officer)',
        '8': 'COE Representative',
        '9': 'CBAA Representative',
        '10': 'CTE Representative',
        '11': 'CCS Representative',
        '12': 'CCJE Representative',
        '13': 'CIT Representative',
        '14': 'CAS Representative',
        '15': 'CHMT Representative'
    }
    
    # Also handle integer keys
    position_names_int = {
        1: 'President',
        2: 'Vice President',
        3: 'Secretary',
        4: 'Assistant Secretary',
        5: 'Treasurer',
        6: 'Auditor',
        7: 'PIO (Public Information Officer)',
        8: 'COE Representative',
        9: 'CBAA Representative',
        10: 'CTE Representative',
        11: 'CCS Representative',
        12: 'CCJE Representative',
        13: 'CIT Representative',
        14: 'CAS Representative',
        15: 'CHMT Representative'
    }
    
    # Format the data to include full_name, party, and position_name for display
    for row in rows:
        row['full_name'] = f"{row['first_name']} {row['last_name']}"
        row['party'] = row['affiliation_type'].title() if row['affiliation_type'] else 'Independent'
        
        # Try to get position name from both string and int mappings
        pos_key = row['position']
        row['position_name'] = position_names.get(str(pos_key), position_names_int.get(pos_key, str(pos_key)))
        
        # Ensure position is treated as integer for sorting
        try:
            row['position_int'] = int(row['position'])
        except (ValueError, TypeError):
            row['position_int'] = 999  # Put invalid positions at the end
        
        print(f"Processed: {row['full_name']}, Position: {row['position']}, Position Int: {row['position_int']}, Position Name: {row['position_name']}")

    # Sort by position number
    rows.sort(key=lambda x: x['position_int'])
    
    print("=== DEBUG: After sorting ===")
    for row in rows:
        print(f"{row['position_int']}: {row['position_name']} - {row['full_name']}")
    
    # Group candidates by position NAME - maintain order with OrderedDict
    from collections import OrderedDict
    data = OrderedDict()
    
    for row in rows:
        pos_name = row['position_name']
        if pos_name not in data:
            data[pos_name] = []
        data[pos_name].append(row)

    print("=== DEBUG: Final grouped data ===")
    for pos_name in data.keys():
        print(f"Position: {pos_name}, Count: {len(data[pos_name])}")

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
        SELECT id, first_name, last_name, student_id, email, college, year_level,
               position, affiliation_type, platform, photo, approved, created_at
        FROM candidates
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    
    # Format the data to include full_name for display
    for row in rows:
        row['full_name'] = f"{row['first_name']} {row['last_name']}"
        # Use affiliation_type as "party" for display
        row['party'] = row['affiliation_type'].title() if row['affiliation_type'] else 'Independent'
    
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

@app.route('/submit-candidacy', methods=['POST'])
@login_required()
def submit_candidacy():
    data = request.json
    
    print("Received candidacy data:", data)  # Debug log
    
    # Extract form data
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    student_id = data.get('student_id')
    email = data.get('email')
    college = data.get('college')
    year_level = data.get('year_level')
    position = data.get('position')
    affiliation_type = data.get('affiliation_type')
    platform = data.get('platform')
    
    # Photo is optional - set default or leave empty
    photo = data.get('photo', '')
    
    # Note: partylist_id is not stored in database
    # We only track affiliation_type (partylist or independent)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Query WITHOUT partylist_id
        query = """
            INSERT INTO candidates 
            (first_name, last_name, student_id, email, college, year_level, 
             position, affiliation_type, platform, photo, approved, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, NOW())
        """
        
        cursor.execute(query, (
            first_name, last_name, student_id, email, college, year_level,
            position, affiliation_type, platform, photo
        ))
        
        conn.commit()
        print("Candidacy inserted successfully!")  # Debug log
        
        return jsonify({
            "success": True, 
            "message": "Candidacy application submitted successfully! Awaiting admin approval."
        }), 201
        
    except mysql.connector.Error as e:
        print("Database error:", str(e))  # Debug log
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        print("General error:", str(e))  # Debug log
        return jsonify({"error": str(e)}), 400
    
    finally:
        cursor.close()
        conn.close()

@app.route('/get-partylists', methods=['GET'])
def get_partylists():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if partylists table exists, if not return empty array
        cursor.execute("SHOW TABLES LIKE 'partylists'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            return jsonify([])
        
        cursor.execute("SELECT id, partylist_name as name FROM partylists WHERE approved = 1 ORDER BY partylist_name")
        partylists = cursor.fetchall()
        return jsonify(partylists)
    
    except Exception as e:
        print("Error fetching partylists:", str(e))
        return jsonify([])
    
    finally:
        cursor.close()
        conn.close()

@app.route('/submit-partylist', methods=['POST'])
@login_required()
def submit_partylist():
    data = request.json
    
    print("Received partylist data:", data)
    
    # Extract form data
    partylist_name = data.get('partylist_name')
    platform = data.get('platform')
    president_name = data.get('president_name')
    president_student_id = data.get('president_student_id')
    contact_email = data.get('contact_email')
    contact_number = data.get('contact_number', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            INSERT INTO partylists 
            (partylist_name, platform, president_name, president_student_id, 
             contact_email, contact_number, approved, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 0, NOW())
        """
        
        cursor.execute(query, (
            partylist_name, platform, president_name, president_student_id,
            contact_email, contact_number
        ))
        
        conn.commit()
        print("Partylist registered successfully!")
        
        return jsonify({
            "success": True, 
            "message": "Partylist registration submitted successfully! Awaiting admin approval."
        }), 201
        
    except mysql.connector.Error as e:
        print("Database error:", str(e))
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        print("General error:", str(e))
        return jsonify({"error": str(e)}), 400
    
    finally:
        cursor.close()
        conn.close()

@app.route('/get-pending-partylists', methods=['GET'])
@login_required(role='ADMIN')
def get_pending_partylists():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, partylist_name, platform, president_name, president_student_id,
               contact_email, contact_number, approved, created_at
        FROM partylists
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(rows)

@app.route('/approve-partylist/<int:partylist_id>', methods=['POST'])
@login_required(role='ADMIN')
def approve_partylist(partylist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE partylists 
            SET approved = 1 
            WHERE id = %s
        """, (partylist_id,))
        
        conn.commit()
        return jsonify({"success": True, "message": "Partylist approved successfully!"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/reject-partylist/<int:partylist_id>', methods=['POST'])
@login_required(role='ADMIN')
def reject_partylist(partylist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE partylists 
            SET approved = 0 
            WHERE id = %s
        """, (partylist_id,))
        
        conn.commit()
        return jsonify({"success": True, "message": "Partylist approval revoked!"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/delete-partylist/<int:partylist_id>', methods=['DELETE'])
@login_required(role='ADMIN')
def delete_partylist(partylist_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM partylists WHERE id = %s", (partylist_id,))
        conn.commit()
        return jsonify({"success": True, "message": "Partylist deleted successfully!"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------------------
# User Profile Routes
# ----------------------------

@app.route('/get-user-profile', methods=['GET'])
@login_required()
def get_user_profile():
    """Get the current user's profile data"""
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, firstname, middlename, lastname, email, studentNumber, yearlevel, department
            FROM accounts 
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify(user)
    
    except Exception as e:
        print("Error fetching user profile:", str(e))
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/update-user-profile', methods=['PUT'])
@login_required()
def update_user_profile():
    """Update the current user's profile data"""
    user_id = session.get('user_id')
    data = request.json
    
    firstname = data.get('firstname')
    middlename = data.get('middlename')
    lastname = data.get('lastname')
    email = data.get('email')
    yearlevel = data.get('yearlevel')
    department = data.get('department')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # If password is provided, update it; otherwise keep the old password
        if password and password.strip():
            query = """
                UPDATE accounts 
                SET firstname = %s, middlename = %s, lastname = %s, 
                    email = %s, yearlevel = %s, department = %s, password = %s
                WHERE id = %s
            """
            cursor.execute(query, (firstname, middlename, lastname, email, 
                                 yearlevel, department, password, user_id))
        else:
            query = """
                UPDATE accounts 
                SET firstname = %s, middlename = %s, lastname = %s, 
                    email = %s, yearlevel = %s, department = %s
                WHERE id = %s
            """
            cursor.execute(query, (firstname, middlename, lastname, email, 
                                 yearlevel, department, user_id))
        
        conn.commit()
        return jsonify({"success": True, "message": "Profile updated successfully!"})
    
    except Exception as e:
        print("Error updating user profile:", str(e))
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

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