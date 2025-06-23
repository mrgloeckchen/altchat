import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify, make_response
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import requests
from datetime import datetime
from database import (
    init_db, add_user, verify_user, user_exists, delete_user,
    get_phone_by_username, get_all_usernames, get_all_users_with_roles,
    get_all_user_phones, get_role, ban_user, temp_ban_user, unban_user,
    reset_user_password, rename_user, set_user_color, toggle_mod_status,
    promote_to_admin, log_admin_action, get_user_history, set_user_color, get_user_color_from_db
)
from random import choice

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, async_mode='eventlet')

ADMIN_PASSWORD = "iammrgloeckchen"
CHAT_LOG = "chatlog.txt"
online_users = set()
USER_COLORS = {}
COLOR_PALETTE = ["#00ff00", "#66ff66", "#00cc00", "#33ff33", "#99ff99"]

def get_user_color(username):
    if username not in USER_COLORS:
        USER_COLORS[username] = choice(COLOR_PALETTE)
    return USER_COLORS[username]

def save_message(username, message):
    timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    with open(CHAT_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {username}: {message}\n")

def load_messages():
    if not os.path.exists(CHAT_LOG):
        return []
    with open(CHAT_LOG, "r", encoding="utf-8") as f:
        return f.readlines()

def to_alt_language(text):
    mapping = {
        'a': 'å', 'b': '∫', 'c': 'ç', 'd': '∂', 'e': '€', 'f': 'ƒ', 'g': '©', 'h': 'ª',
        'i': '⁄', 'j': 'º', 'k': '∆', 'l': '@', 'm': 'µ', 'n': '~', 'o': 'ø', 'p': 'π',
        'q': '«', 'r': '®', 's': '‚', 't': '†', 'u': '¨', 'v': '√', 'w': '∑', 'x': '≈',
        'y': '¥', 'z': 'Ω', 'ä': 'æ', 'ö': 'œ', 'ü': '•', '1': '¡', '2': '“', '3': '¶',
        '4': '¢', '5': '[', '6': ']', '7': '/', '8': '{', '9': '}', '0': '≠', '?': '¿',
        ':': '…', ';': '∞'
    }
    return ''.join(mapping.get(char.lower(), char) for char in text)

@app.context_processor
def override_url_for():
    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.root_path, 'static', filename)
                if os.path.exists(file_path):
                    values['q'] = int(os.stat(file_path).st_mtime)
        return url_for(endpoint, **values)
    return dict(url_for=dated_url_for)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        admin_pass = request.form.get('admin_pass')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        if admin_pass != ADMIN_PASSWORD:
            flash('Admin-Passwort falsch!')
            return redirect(url_for('register'))
        if user_exists(username):
            flash('User existiert schon!')
            return redirect(url_for('register'))
        if add_user(username, password, phone):
            flash('User erfolgreich registriert!')
            return redirect(url_for('login'))
        else:
            flash('Fehler beim Anlegen des Users.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if verify_user(username, password):
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            flash('Login fehlgeschlagen!')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.pop('username', None)
    if username:
        online_users.discard(username)
        socketio.emit('message', {
            'username': 'System',
            'message': f'{username} hat den Chat verlassen.',
            'color': '#999999',
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        }, room='main_room')
    return render_template('logout.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    raw_messages = load_messages()
    current_user = session['username']
    return render_template('chat.html',
        username=current_user,
        messages=raw_messages,
        role=get_role(current_user),
        all_users=get_all_usernames()
    )

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )

@app.route('/admin')
def admin_panel():
    if 'username' not in session:
        return redirect(url_for('login'))
    role = get_role(session['username'])
    if role not in ['admin', 'mod']:
        return redirect(url_for('chat'))
    return render_template('admin.html',
        username=session['username'],
        role=role,
        users=get_all_users_with_roles()
    )

@app.route('/admin/set-color', methods=['POST'])
def admin_set_color():
    if 'username' not in session:
        return jsonify({'status': 'unauthorized'}), 403

    current_user = session['username']
    role = get_role(current_user)

    if role not in ['admin', 'mod']:
        return jsonify({'status': 'forbidden'}), 403

    data = request.get_json()
    target = data.get('username')
    color = data.get('color')

    if not target or not color:
        return jsonify({'status': 'invalid'}), 400

    set_user_color(target, color)
    log_admin_action(current_user, f"set color of {target} to {color}", target)
    return jsonify({'status': 'success'})

@app.route('/user_history/<username>')
def user_history(username):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    requester = session['username']
    if get_role(requester) not in ['admin', 'mod']:
        return jsonify({'error': 'Forbidden'}), 403
    history = get_user_history(username)
    return jsonify({'history': history})

@socketio.on('join')
def handle_join(data):
    username = session.get('username')
    if not username or username != data.get('username'):
        return
    online_users.add(username)
    join_room('main_room')
    emit('user_update', list(online_users), broadcast=True)
    emit('message', {
        'username': 'System',
        'message': f'{username} ist beigetreten.',
        'color': '#999999',
        'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    }, room='main_room')

@socketio.on('leave')
def handle_leave(data):
    username = session.get('username')
    if username:
        online_users.discard(username)
        leave_room('main_room')
        emit('user_update', list(online_users), broadcast=True)
        emit('message', {
            'username': 'System',
            'message': f'{username} hat den Chat verlassen.',
            'color': '#999999',
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        }, room='main_room')

@socketio.on('typing')
def handle_typing(data):
    username = session.get('username')
    if username:
        emit('typing', {'username': username}, room='main_room', include_self=False)

@socketio.on('message')
def handle_message(data):
    username = session.get('username')
    if username:
        raw_msg = data.get('message', '')
        alt_msg = to_alt_language(raw_msg)
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        save_message(username, alt_msg)
        emit('message', {
            'username': username,
            'message': alt_msg,
            'timestamp': timestamp,
            'color': get_user_color(username)
        }, room='main_room')
        for user in get_all_usernames():
            if user != username and user not in online_users:
                phone = get_phone_by_username(user)
                if phone:
                    try:
                        requests.post("http://localhost:3000/send", json={
                            "number": phone,
                            "message": f"Neue Nachricht von {username}"
                        })
                    except Exception as e:
                        print(f"Fehler beim WhatsApp-Senden an {user}: {e}")

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000)