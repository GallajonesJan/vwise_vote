from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
CORS(app)

# MySQL Configuration for Laragon
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Empty for default Laragon
app.config['MYSQL_DB'] = 'vwise_voting'

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== PARTYLIST ROUTES ====================

@app.route('/api/partylists', methods=['GET'])
def get_partylists():
    """Get all approved partylists"""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT partylist_id, partylist_name, president_name 
        FROM partylists 
        WHERE status = 'approved'
        ORDER BY partylist_name
    """)
    partylists = cur.fetchall()
    cur.close()
    
    result = []
    for p in partylists:
        result.append({
            'partylist_id': p[0],
            'partylist_name': p[1],
            'president_name': p[2]
        })
    
    return jsonify(result)

@app.route('/api/partylist/register', methods=['POST'])
def register_partylist():
    """Register a new partylist"""
    data = request.json
    
    cur = mysql.connection.cursor()
    
    # Check if partylist name already exists
    cur.execute("SELECT partylist_id FROM partylists WHERE partylist_name = %s", 
                (data['partylist_name'],))
    if cur.fetchone():
        cur.close()
        return jsonify({'error': 'Partylist name already exists'}), 400
    
    # Insert partylist
    cur.execute("""
        INSERT INTO partylists 
        (partylist_name, president_name, president_student_id, contact_email, 
         contact_number, platform, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'pending')
    """, (
        data['partylist_name'],
        data['president_name'],
        data['president_student_id'],
        data['contact_email'],
        data.get('contact_number', ''),
        data.get('platform', '')
    ))
    
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Partylist registration submitted successfully'}), 201

# ==================== CANDIDACY ROUTES ====================

@app.route('/api/candidacy/apply', methods=['POST'])
def apply_candidacy():
    """Submit candidacy application"""
    data = request.json
    
    cur = mysql.connection.cursor()
    
    # Check if user already applied for this position
    cur.execute("""
        SELECT candidate_id FROM candidates 
        WHERE student_id = %s AND position_id = %s
    """, (data['student_id'], data['position_id']))
    
    if cur.fetchone():
        cur.close()
        return jsonify({'error': 'You have already applied for this position'}), 400
    
    # Check if position already has 5 approved candidates
    cur.execute("""
        SELECT COUNT(*) FROM candidates 
        WHERE position_id = %s AND status = 'approved'
    """, (data['position_id'],))
    
    count = cur.fetchone()[0]
    if count >= 5:
        cur.close()
        return jsonify({'error': 'This position already has the maximum number of candidates (5)'}), 400
    
    # Get user_id from session or create dummy user (replace with actual auth)
    user_id = session.get('user_id', 1)  # Replace with actual user authentication
    
    # Determine partylist_id and is_independent
    partylist_id = None
    is_independent = True
    
    if data['affiliation_type'] == 'partylist':
        partylist_id = data.get('partylist_id')
        is_independent = False
    
    # Insert candidate application
    candidate_name = f"{data['first_name']} {data['last_name']}"
    
    cur.execute("""
        INSERT INTO candidates 
        (user_id, position_id, partylist_id, is_independent, candidate_name, 
         student_id, email, college, year_level, platform, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
    """, (
        user_id,
        data['position_id'],
        partylist_id,
        is_independent,
        candidate_name,
        data['student_id'],
        data['email'],
        data['college'],
        data['year_level'],
        data.get('platform', '')
    ))
    
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Candidacy application submitted successfully. Awaiting admin approval.'}), 201

# ==================== VOTING ROUTES ====================

@app.route('/api/candidates/approved', methods=['GET'])
def get_approved_candidates():
    """Get all approved candidates grouped by position"""
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT 
            c.candidate_id,
            c.candidate_name,
            c.is_independent,
            p.position_id,
            p.position_name,
            COALESCE(pl.partylist_name, 'Independent') as partylist_name,
            c.photo_url,
            c.platform
        FROM candidates c
        JOIN positions p ON c.position_id = p.position_id
        LEFT JOIN partylists pl ON c.partylist_id = pl.partylist_id
        WHERE c.status = 'approved'
        ORDER BY p.position_order, c.candidate_name
    """)
    
    candidates = cur.fetchall()
    cur.close()
    
    # Group candidates by position
    positions = {}
    for candidate in candidates:
        position_id = candidate[3]
        position_name = candidate[4]
        
        if position_id not in positions:
            positions[position_id] = {
                'position_id': position_id,
                'position_name': position_name,
                'candidates': []
            }
        
        positions[position_id]['candidates'].append({
            'candidate_id': candidate[0],
            'candidate_name': candidate[1],
            'is_independent': candidate[2],
            'partylist_name': candidate[5],
            'photo_url': candidate[6],
            'platform': candidate[7]
        })
    
    return jsonify(list(positions.values()))

@app.route('/api/vote/submit', methods=['POST'])
def submit_vote():
    """Submit votes for all positions"""
    data = request.json
    votes = data.get('votes', {})
    
    # Get user_id from session (replace with actual auth)
    user_id = session.get('user_id', 1)
    
    cur = mysql.connection.cursor()
    
    # Check if user has already voted
    cur.execute("SELECT has_voted FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    
    if user and user[0]:
        cur.close()
        return jsonify({'error': 'You have already voted'}), 400
    
    # Insert all votes
    try:
        for position_id, candidate_id in votes.items():
            cur.execute("""
                INSERT INTO votes (user_id, candidate_id, position_id)
                VALUES (%s, %s, %s)
            """, (user_id, candidate_id, position_id))
        
        # Mark user as voted
        cur.execute("UPDATE users SET has_voted = TRUE WHERE user_id = %s", (user_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'message': 'Votes submitted successfully'}), 201
        
    except Exception as e:
        mysql.connection.rollback()
        cur.close()
        return jsonify({'error': str(e)}), 500

# ==================== ADMIN ROUTES ====================

@app.route('/api/admin/candidates/pending', methods=['GET'])
def get_pending_candidates():
    """Get all pending candidate applications"""
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT 
            c.candidate_id,
            c.candidate_name,
            c.student_id,
            c.email,
            c.college,
            c.year_level,
            p.position_name,
            COALESCE(pl.partylist_name, 'Independent') as partylist_name,
            c.platform,
            c.applied_at
        FROM candidates c
        JOIN positions p ON c.position_id = p.position_id
        LEFT JOIN partylists pl ON c.partylist_id = pl.partylist_id
        WHERE c.status = 'pending'
        ORDER BY c.applied_at DESC
    """)
    
    candidates = cur.fetchall()
    cur.close()
    
    result = []
    for c in candidates:
        result.append({
            'candidate_id': c[0],
            'candidate_name': c[1],
            'student_id': c[2],
            'email': c[3],
            'college': c[4],
            'year_level': c[5],
            'position_name': c[6],
            'partylist_name': c[7],
            'platform': c[8],
            'applied_at': c[9].strftime('%Y-%m-%d %H:%M:%S') if c[9] else None
        })
    
    return jsonify(result)

@app.route('/api/admin/candidate/approve/<int:candidate_id>', methods=['POST'])
def approve_candidate(candidate_id):
    """Approve a candidate application"""
    cur = mysql.connection.cursor()
    
    # Check if position already has 5 approved candidates
    cur.execute("""
        SELECT position_id FROM candidates WHERE candidate_id = %s
    """, (candidate_id,))
    position = cur.fetchone()
    
    if position:
        cur.execute("""
            SELECT COUNT(*) FROM candidates 
            WHERE position_id = %s AND status = 'approved'
        """, (position[0],))
        
        count = cur.fetchone()[0]
        if count >= 5:
            cur.close()
            return jsonify({'error': 'This position already has 5 approved candidates'}), 400
    
    # Approve candidate
    cur.execute("""
        UPDATE candidates 
        SET status = 'approved', approved_at = NOW()
        WHERE candidate_id = %s
    """, (candidate_id,))
    
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Candidate approved successfully'})

@app.route('/api/admin/candidate/reject/<int:candidate_id>', methods=['POST'])
def reject_candidate(candidate_id):
    """Reject a candidate application"""
    data = request.json
    reason = data.get('reason', '')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE candidates 
        SET status = 'rejected', rejection_reason = %s
        WHERE candidate_id = %s
    """, (reason, candidate_id))
    
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Candidate rejected'})

# ==================== RESULTS ROUTES ====================

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get election results"""
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT 
            p.position_name,
            c.candidate_name,
            COALESCE(pl.partylist_name, 'Independent') as partylist_name,
            COUNT(v.vote_id) as vote_count
        FROM positions p
        LEFT JOIN candidates c ON p.position_id = c.position_id AND c.status = 'approved'
        LEFT JOIN votes v ON c.candidate_id = v.candidate_id
        LEFT JOIN partylists pl ON c.partylist_id = pl.partylist_id
        GROUP BY p.position_id, c.candidate_id
        ORDER BY p.position_order, vote_count DESC
    """)
    
    results = cur.fetchall()
    cur.close()
    
    # Group by position
    positions = {}
    for result in results:
        position_name = result[0]
        if position_name not in positions:
            positions[position_name] = []
        
        if result[1]:  # If candidate exists
            positions[position_name].append({
                'candidate_name': result[1],
                'partylist_name': result[2],
                'vote_count': result[3]
            })
    
    return jsonify(positions)

if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(debug=True, port=5000)