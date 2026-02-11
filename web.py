#!/usr/bin/env python3
"""
Free Game Checker - Web Interface
Manage settings, recipients, and view games
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import sqlite3
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))
from app import Database, load_config, check_and_send_games, EmailSender

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

CONFIG_FILE = '/etc/free-game-checker/config.json'
DB_FILE = '/var/lib/free-game-checker/games.db'

@app.route('/')
def index():
    """Main dashboard"""
    db = Database()
    config = load_config()
    
    # Get recent games
    games = db.get_recent_games(hours=168)  # Last week
    recipients = db.get_recipients()
    
    return render_template('index.html', 
                         games=games, 
                         recipients=recipients,
                         config=config,
                         game_count=len(games))

@app.route('/settings')
def settings():
    """Settings page"""
    config = load_config()
    db = Database()
    recipients = db.get_recipients()
    
    return render_template('settings.html', 
                         config=config,
                         recipients=recipients)

@app.route('/api/recipients', methods=['GET', 'POST', 'DELETE'])
def manage_recipients():
    """Manage email recipients"""
    db = Database()
    
    if request.method == 'GET':
        recipients = db.get_recipients()
        return jsonify({'recipients': recipients})
    
    elif request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            return jsonify({'error': 'Invalid email address'}), 400
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO recipients (email) VALUES (?)', (email,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': f'Added {email}'})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already exists'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        data = request.get_json()
        email = data.get('email', '')
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM recipients WHERE email = ?', (email,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': f'Removed {email}'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """Manage configuration"""
    
    if request.method == 'GET':
        config = load_config()
        return jsonify(config)
    
    elif request.method == 'POST':
        data = request.get_json()
        
        try:
            config = load_config()
            
            # Update config
            if 'email_password' in data:
                config['email_password'] = data['email_password']
            if 'schedule_day' in data:
                config['schedule_day'] = data['schedule_day']
            if 'schedule_time' in data:
                config['schedule_time'] = data['schedule_time']
            if 'enabled_stores' in data:
                config['enabled_stores'] = data['enabled_stores']
            
            # Save config
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            
            return jsonify({'success': True, 'message': 'Configuration updated'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Send a test email"""
    try:
        config = load_config()
        db = Database()
        
        # Get a few games for testing
        games = db.get_recent_games(hours=168)[:3]
        
        if not games:
            # Create a dummy game for testing
            games = [{
                'title': 'Test Game',
                'store': 'Test Store',
                'description': 'This is a test email from Free Game Checker',
                'image_url': '',
                'game_url': 'https://example.com',
                'original_price': '$9.99',
                'end_date': '',
                'store_logo': ''
            }]
        
        recipients = db.get_recipients()
        if not recipients:
            return jsonify({'error': 'No recipients configured'}), 400
        
        email_sender = EmailSender(config)
        email_sender.send_email(recipients, games)
        
        return jsonify({'success': True, 'message': f'Test email sent to {len(recipients)} recipient(s)'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-now', methods=['POST'])
def check_now():
    """Manually trigger a game check"""
    try:
        check_and_send_games()
        return jsonify({'success': True, 'message': 'Game check completed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stores/custom', methods=['GET', 'POST', 'DELETE'])
def manage_custom_stores():
    """Manage custom game stores"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT id, name, url, pattern, active FROM custom_stores')
        stores = []
        for row in cursor.fetchall():
            stores.append({
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'pattern': row[3],
                'active': row[4]
            })
        conn.close()
        return jsonify({'stores': stores})
    
    elif request.method == 'POST':
        data = request.get_json()
        name = data.get('name', '').strip()
        url = data.get('url', '').strip()
        pattern = data.get('pattern', '').strip()
        
        if not all([name, url, pattern]):
            return jsonify({'error': 'All fields are required'}), 400
        
        try:
            cursor.execute(
                'INSERT INTO custom_stores (name, url, pattern) VALUES (?, ?, ?)',
                (name, url, pattern)
            )
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': f'Added custom store: {name}'})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Store name already exists'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        data = request.get_json()
        store_id = data.get('id')
        
        try:
            cursor.execute('DELETE FROM custom_stores WHERE id = ?', (store_id,))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Custom store removed'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
