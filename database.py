import sqlite3
import os
import time

DB_NAME = "users.db"

ADMIN_LOG_FILE = "admin_logs.txt"

def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                role TEXT DEFAULT 'user',
                ban_until INTEGER,
                color TEXT
            )
        """)
        conn.commit()
        conn.close()

def log_admin_action(performer, target, action):
    timestamp = time.strftime('%d.%m.%Y %H:%M:%S')
    with open(ADMIN_LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {performer} -> {target}: {action}\n")

def get_user_history(username):
    if not os.path.exists(ADMIN_LOG_FILE):
        return []
    with open(ADMIN_LOG_FILE, "r", encoding="utf-8") as log_file:
        lines = log_file.readlines()
    return [line.strip() for line in lines if f"-> {username}:" in line]

def add_user(username, password, phone):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, phone) VALUES (?, ?, ?)",
            (username, password, phone)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()
    if user and (not user[5] or user[5] < int(time.time())):
        return True
    return False

def user_exists(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def delete_user(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def get_all_usernames():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]

def get_all_users_with_roles():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return [{"username": u[0], "role": u[1]} for u in users]


def get_all_user_phones():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, phone FROM users WHERE phone IS NOT NULL")
    result = cursor.fetchall()
    conn.close()
    return {username: phone for username, phone in result}

def get_phone_by_username(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_role(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else 'user'  # Default fallback


def ban_user(username, seconds):
    ban_until = int(time.time()) + seconds
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET ban_until = ? WHERE username = ?", (ban_until, username))
    conn.commit()
    conn.close()

def temp_ban_user(username, seconds):
    ban_user(username, seconds)

def unban_user(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET ban_until = NULL WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def reset_user_password(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = 'reset123' WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def rename_user(old_username, new_username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
    conn.commit()
    conn.close()

def set_user_color(username, color):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET color = ? WHERE username = ?", (color, username))
    conn.commit()
    conn.close()

def toggle_mod_status(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
    role = cursor.fetchone()[0]
    new_role = 'mod' if role != 'mod' else 'user'
    cursor.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
    conn.commit()
    conn.close()

def promote_to_admin(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'admin' WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def get_user_color(username):
    # Sonderfarben
    if username == "MrX":
        return "#ff0000"
    if username == "Aleajoleen07":
        return "#ff69b4"

    # Datenbank-Farbe?
    color = get_user_color_from_db(username)
    if color:
        return color

    # Zufallsfarbe, wenn nix gesetzt
    if username not in USER_COLORS:
        USER_COLORS[username] = choice(COLOR_PALETTE)
    return USER_COLORS[username]

def get_user_color_from_db(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT color FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else None
