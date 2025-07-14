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
    # Add is_deleted to product table for soft delete
    c.execute("PRAGMA table_info(product)")
    product_columns = [col[1] for col in c.fetchall()]
    if 'is_deleted' not in product_columns:
        c.execute('ALTER TABLE product ADD COLUMN is_deleted INTEGER DEFAULT 0')
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
        price REAL NOT NULL,
        is_deleted INTEGER DEFAULT 0
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

def add_product(name, sku, quantity, price):
    """
    Adds a new product to the database. Raises sqlite3.IntegrityError if SKU is not unique.
    Args:
        name (str): Product name
        sku (str): Unique SKU
        quantity (int): Quantity in stock
        price (float): Product price
    """
    import sqlite3
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO product (name, sku, quantity, price) VALUES (?, ?, ?, ?)''', (name, sku, int(quantity), float(price)))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_all_products():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, name, sku, quantity, price FROM product WHERE is_deleted=0')
    products = c.fetchall()
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, name, sku, quantity, price FROM product WHERE id=? AND is_deleted=0', (product_id,))
    product = c.fetchone()
    conn.close()
    return product

def update_product(product_id, name, sku, quantity, price):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Check if the new SKU exists for a different product
    c.execute('SELECT id FROM product WHERE sku=? AND id!=? AND is_deleted=0', (sku, product_id))
    existing = c.fetchone()
    if existing:
        conn.close()
        raise Exception('SKU already exists for another product.')
    c.execute('''UPDATE product SET name=?, sku=?, quantity=?, price=? WHERE id=?''', (name, sku, quantity, price, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Soft delete: set is_deleted=1
    c.execute('UPDATE product SET is_deleted=1 WHERE id=?', (product_id,))
    conn.commit()
    conn.close()

def get_all_staff():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, first_name, middle_name, last_name, birthday, age, address, email FROM users WHERE is_admin=0 AND is_approved=1')
    staff = c.fetchall()
    conn.close()
    return staff

def record_sale(total):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO sales (total) VALUES (?)', (total,))
    sale_id = c.lastrowid
    conn.commit()
    conn.close()
    return sale_id

def add_sale_item(sale_id, product_id, quantity, price):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO sale_items (sale_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', (sale_id, product_id, quantity, price))
    conn.commit()
    conn.close()

def update_product_stock(product_id, quantity_sold):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE product SET quantity = quantity - ? WHERE id = ?', (quantity_sold, product_id))
    conn.commit()
    conn.close()