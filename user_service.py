import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'users.db'

def migrate_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if 'is_approved' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN is_approved INTEGER DEFAULT 0')
    if 'is_admin' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            birthday TEXT NOT NULL,
            age INTEGER NOT NULL,
            address TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_approved INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    c.execute('''CREATE TABLE IF NOT EXISTS product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT UNIQUE NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        total REAL NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES sales(id),
        FOREIGN KEY (product_id) REFERENCES product(id)
    )'''
    )

    conn.commit()
    conn.close()
    migrate_db()

def create_user(first_name, middle_name, last_name, birthday, age, address, email, password):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    hashed_password = generate_password_hash(password)
    c.execute('''INSERT INTO users (first_name, middle_name, last_name, birthday, age, address, email, password, is_approved, is_admin)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)''',
              (first_name, middle_name, last_name, birthday, age, address, email, hashed_password))
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, first_name, middle_name, last_name, birthday, age, address, email, is_approved, is_admin FROM users')
    users = c.fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, first_name, middle_name, last_name, birthday, age, address, email FROM users WHERE id=?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_user(user_id, first_name, middle_name, last_name, birthday, age, address, email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''UPDATE users SET first_name=?, middle_name=?, last_name=?, birthday=?, age=?, address=?, email=? WHERE id=?''',
              (first_name, middle_name, last_name, birthday, age, address, email, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()

def set_user_approved(user_id, approved=True):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE users SET is_approved=? WHERE id=?', (1 if approved else 0, user_id))
    conn.commit()
    conn.close()

def set_user_admin(user_id, admin=True):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE users SET is_admin=? WHERE id=?', (1 if admin else 0, user_id))
    conn.commit()
    conn.close()