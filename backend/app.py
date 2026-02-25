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

# Session configuration for CORS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Configure CORS - allow all since we're using session-based auth
CORS(app, supports_credentials=True)
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
# Database initialization - Election Settings Table
# ----------------------------
def init_election_settings():
    """Initialize election_settings table if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS election_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                election_start_date DATETIME DEFAULT NULL,
                election_end_date DATETIME DEFAULT NULL,
                election_status VARCHAR(20) DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        # Insert default row if table is empty
        cursor.execute("SELECT COUNT(*) FROM election_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO election_settings (election_status)
                VALUES ('none')
            """)
        conn.commit()
        print("✅ Election settings table initialized")
    except Exception as e:
        print(f"Error initializing election settings: {e}")
    finally:
        cursor.close()
        conn.close()

# Initialize on startup
init_election_settings()

# ----------------------------
# Election Schedule API Endpoints
# ----------------------------

@app.route('/api/election/status', methods=['GET'])
def get_election_status():
    """Get current election status and schedule"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT election_start_date, election_end_date, election_status
            FROM election_settings
            ORDER BY id DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if result:
            return jsonify({
                'election_start_date': result['election_start_date'].isoformat() if result['election_start_date'] else None,
                'election_end_date': result['election_end_date'].isoformat() if result['election_end_date'] else None,
                'election_status': result['election_status']
            })
        else:
            return jsonify({
                'election_start_date': None,
                'election_end_date': None,
                'election_status': 'none'
            })
    except Exception as e:
        print(f"Error getting election status: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

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


@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Debug endpoint to check session status"""
    return jsonify({
        'has_session': 'user_id' in session,
        'user_id': session.get('user_id'),
        'role': session.get('role'),
        'session_data': dict(session)
    })

@app.route('/api/admin/election/settings', methods=['PUT', 'OPTIONS'])
def update_election_settings():
    """Update election schedule and status (admin only)"""
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'PUT, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 200
    
    # Check if user is admin
    print(f"DEBUG: Session data: {dict(session)}")
    print(f"DEBUG: user_id in session: {'user_id' in session}")
    print(f"DEBUG: role in session: {session.get('role')}")
    
    if 'user_id' not in session or session.get('role') != 'ADMIN':
        print(f"DEBUG: Authentication failed!")
        return jsonify({'error': 'Admin authentication required'}), 401
    
    data = request.json

    
    election_start_date = data.get('election_start_date')
    election_end_date = data.get('election_end_date')
    election_status = data.get('election_status', 'upcoming')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Parse datetime strings to datetime objects if they exist
        start_date = None
        end_date = None
        
        if election_start_date:
            from datetime import datetime
            start_date = datetime.fromisoformat(election_start_date.replace('Z', '+00:00'))
        if election_end_date:
            from datetime import datetime
            end_date = datetime.fromisoformat(election_end_date.replace('Z', '+00:00'))
        
        cursor.execute("""
            UPDATE election_settings
            SET election_start_date = %s,
                election_end_date = %s,
                election_status = %s
            ORDER BY id DESC
            LIMIT 1
        """, (start_date, end_date, election_status))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Election settings updated successfully!'})
    except Exception as e:
        print(f"Error updating election settings: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/bulk-register', methods=['POST'])
def bulk_register_users():
    """Bulk register users from Excel upload"""
    if 'user_id' not in session or session.get('role') != 'ADMIN':
        return jsonify({'error': 'Admin authentication required'}), 401
    
    data = request.json
    users = data.get('users', [])
    
    if not users:
        return jsonify({'error': 'No users provided'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    success_count = 0
    
    try:
        for user in users:
            try:
                cursor.execute("""
                    INSERT INTO accounts (studentNumber, password, firstname, middlename, lastname, 
                                        email, yearlevel, department)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    password = VALUES(password),
                    firstname = VALUES(firstname),
                    middlename = VALUES(middlename),
                    lastname = VALUES(lastname),
                    email = VALUES(email),
                    yearlevel = VALUES(yearlevel),
                    department = VALUES(department)
                """, (
                    user.get('student_id'),
                    user.get('password'),
                    user.get('full_name', '').split()[0] if user.get('full_name') else '',
                    user.get('full_name', '').split()[1] if len(user.get('full_name', '').split()) > 1 else '',
                    user.get('full_name', '').split()[-1] if len(user.get('full_name', '').split()) > 1 else '',
                    user.get('email'),
                    user.get('year_level'),
                    user.get('department')
                ))
                success_count += 1
            except Exception as e:
                print(f"Error inserting user {user.get('student_id')}: {e}")
                continue
        
        conn.commit()
        return jsonify({'success': True, 'success_count': success_count})
    except Exception as e:
        print(f"Error bulk registering: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/bulk-partylist', methods=['POST'])
def bulk_add_partylists():
    """Bulk add partylists from Excel upload"""
    if 'user_id' not in session or session.get('role') != 'ADMIN':
        return jsonify({'error': 'Admin authentication required'}), 401
    
    data = request.json
    partylists = data.get('partylists', [])
    
    if not partylists:
        return jsonify({'error': 'No partylists provided'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    success_count = 0
    
    try:
        for partylist in partylists:
            try:
                cursor.execute("""
                    INSERT INTO partylists (partylist_name, platform, president_name, 
                                          president_student_id, contact_email, approved)
                    VALUES (%s, %s, %s, %s, %s, 1)
                """, (
                    partylist.get('name'),
                    partylist.get('slogan', ''),
                    partylist.get('president'),
                    partylist.get('president_id', ''),
                    partylist.get('contact_email', '')
                ))
                success_count += 1
            except Exception as e:
                print(f"Error inserting partylist {partylist.get('name')}: {e}")
                continue
        
        conn.commit()
        return jsonify({'success': True, 'success_count': success_count})
    except Exception as e:
        print(f"Error bulk adding partylists: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/turnout', methods=['GET'])
def get_turnout():
    """Get voter turnout statistics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get total students (all accounts except ADMIN)
        cursor.execute("SELECT COUNT(*) as total FROM accounts WHERE department != 'ADMIN'")
        total = cursor.fetchone()['total']
        
        # Get students who voted (distinct users who submitted votes, joined with accounts)
        cursor.execute("""
            SELECT COUNT(DISTINCT v.user_id) as voted 
            FROM votes v 
            INNER JOIN accounts a ON v.user_id = a.id 
            WHERE a.department != 'ADMIN'
        """)
        result = cursor.fetchone()
        voted = result['voted'] if result['voted'] is not None else 0
        
        # Calculate turnout percentage
        turnout_pct = (voted / total * 100) if total > 0 else 0
        
        return jsonify({
            'total_students': total,
            'voted_count': voted,
            'turnout_percentage': round(turnout_pct, 2)
        })
    except Exception as e:
        print(f"Error getting turnout: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/results/detailed', methods=['GET'])
def get_detailed_results():
    """Get detailed election results"""
    if 'user_id' not in session or session.get('role') != 'ADMIN':
        return jsonify({'error': 'Admin authentication required'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                c.id,
                c.first_name,
                c.last_name,
                c.position,
                c.college,
                c.year_level,
                CONCAT(c.first_name, ' ', c.last_name) as full_name,
                c.position as position_name,
                COUNT(v.id) as vote_count,
                CASE 
                    WHEN (SELECT COUNT(*) FROM votes WHERE position = c.position) > 0 
                    THEN (COUNT(v.id) / (SELECT COUNT(*) FROM votes WHERE position = c.position) * 100)
                    ELSE 0 
                END as vote_percentage
            FROM candidates c
            LEFT JOIN votes v ON c.id = v.candidate_id
            WHERE c.approved = 1
            GROUP BY c.id, c.first_name, c.last_name, c.position, c.college, c.year_level
            ORDER BY c.position, vote_count DESC
        """)
        
        results = cursor.fetchall()
        
        # Handle None values
        for result in results:
            if result['vote_count'] is None:
                result['vote_count'] = 0
            if result['vote_percentage'] is None:
                result['vote_percentage'] = 0.0
        
        return jsonify(results)
    except Exception as e:
        print(f"Error getting results: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

def can_vote():
    """Check if voting is currently allowed based on schedule and status"""
    from datetime import datetime
    import pytz
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT election_start_date, election_end_date, election_status
            FROM election_settings
            ORDER BY id DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if not result:
            return {'can_vote': False, 'reason': 'Election not configured'}
        
        # Check if election status is active
        if result['election_status'] != 'active':
            return {'can_vote': False, 'reason': f'Election is {result["election_status"]}'}
        
        # Get current time
        now = datetime.now()
        
        # Check if start date is set and if current time is after start
        if result['election_start_date'] and now < result['election_start_date']:
            return {
                'can_vote': False,
                'reason': 'Voting has not started yet',
                'start_time': result['election_start_date'].isoformat()
            }
        
        # Check if end date is set and if current time is after end
        if result['election_end_date'] and now > result['election_end_date']:
            return {
                'can_vote': False,
                'reason': 'Voting has ended',
                'end_time': result['election_end_date'].isoformat()
            }
        
        return {'can_vote': True}
    except Exception as e:
        print(f"Error checking vote eligibility: {e}")
        return {'can_vote': False, 'reason': str(e)}
    finally:
        cursor.close()
        conn.close()

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
    # Check election status
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT election_start_date, election_end_date, election_status
            FROM election_settings
            ORDER BY id DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        election_info = {
            'election_status': result['election_status'] if result else 'none',
            'election_start_date': result['election_start_date'].isoformat() if result and result['election_start_date'] else None,
            'election_end_date': result['election_end_date'].isoformat() if result and result['election_end_date'] else None
        }
        
        return render_template('votenow.html', election_info=election_info)
    except Exception as e:
        print(f"Error checking election status: {e}")
        return render_template('votenow.html', election_info={'election_status': 'none'})
    finally:
        cursor.close()
        conn.close()


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