from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path
from datetime import datetime
from ClassChecker import ClassChecker

app = Flask(__name__, static_folder='static')

# Database configuration
DATABASE_PATH = Path(__file__).parent / 'database.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    # Create subscriptions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            crn TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            last_checked TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(email, crn)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    conn = get_db()
    # Get all subscriptions ordered by created_at
    subscriptions = conn.execute('''
        SELECT * FROM subscriptions 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    # Group subscriptions by email
    grouped_subscriptions = {}
    for sub in subscriptions:
        sub_dict = dict(sub)
        email = sub_dict['email']
        if email not in grouped_subscriptions:
            grouped_subscriptions[email] = []
        grouped_subscriptions[email].append(sub_dict)
    
    return jsonify(grouped_subscriptions)

@app.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    data = request.get_json()
    email = data.get('email')
    crns = data.get('crns')
    
    if not email or not crns or not isinstance(crns, list):
        return jsonify({'error': 'Email and list of CRNs are required'}), 400
    
    conn = get_db()
    try:
        current_time = datetime.utcnow().isoformat()
        for crn in crns:
            conn.execute('''
                INSERT OR IGNORE INTO subscriptions 
                (email, crn, last_checked) 
                VALUES (?, ?, ?)
            ''', (email, crn, current_time))
        conn.commit()
        return jsonify({'message': 'Subscriptions created successfully'}), 201
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/subscriptions', methods=['DELETE'])
def delete_subscription():
    """Delete a subscription by email and CRN"""
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    crn = data.get('crn')

    if not email or not crn:
        return jsonify({'error': 'Email and CRN are required'}), 400

    conn = get_db()
    try:
        cur = conn.execute('''
            DELETE FROM subscriptions 
            WHERE email = ? AND crn = ?
        ''', (email, crn))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'message': 'No subscription found for given email and CRN'}), 404
        return jsonify({'message': 'Subscription removed successfully'})
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()  # Initialize database on startup
    app.run(debug=True, port=5001) 