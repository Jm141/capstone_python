import sqlite3
import os
from passlib.hash import scrypt
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'users.db'

def migrate_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Check if users table has role column
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'role' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "customer"')
    if 'login_attempts' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN login_attempts INTEGER DEFAULT 0')
    if 'last_login_attempt' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN last_login_attempt DATETIME')
    if 'is_locked' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN is_locked INTEGER DEFAULT 0')
    
    # Update existing users to have proper roles
    c.execute('UPDATE users SET role = "admin" WHERE is_admin = 1')
    c.execute('UPDATE users SET role = "seller" WHERE is_admin = 0 AND is_approved = 1')
    c.execute('UPDATE users SET role = "customer" WHERE is_admin = 0 AND is_approved = 0')
    
    # Check if products table has is_deleted column
    c.execute("PRAGMA table_info(products)")
    product_columns = [col[1] for col in c.fetchall()]
    if 'is_deleted' not in product_columns:
        c.execute('ALTER TABLE products ADD COLUMN is_deleted INTEGER DEFAULT 0')
    
    # Add customer_name to sales table for receipts
    c.execute("PRAGMA table_info(sales)")
    sales_columns = [col[1] for col in c.fetchall()]
    if 'customer_name' not in sales_columns:
        c.execute('ALTER TABLE sales ADD COLUMN customer_name TEXT')
    if 'customer_email' not in sales_columns:
        c.execute('ALTER TABLE sales ADD COLUMN customer_email TEXT')
    if 'created_by' not in sales_columns:
        c.execute('ALTER TABLE sales ADD COLUMN created_by INTEGER')
    
    # Check if there's an old 'product' table and migrate data if needed
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
    if c.fetchone():
        # Migrate data from old 'product' table to 'products' table
        c.execute("SELECT id, name, sku, quantity, price, is_deleted FROM product")
        old_products = c.fetchall()
        for product in old_products:
            c.execute('''INSERT OR IGNORE INTO products (id, name, sku, quantity, price, is_deleted) 
                         VALUES (?, ?, ?, ?, ?, ?)''', product)
        # Drop the old table
        c.execute("DROP TABLE product")
    
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Create users table with proper roles
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
            role TEXT DEFAULT 'customer',
            login_attempts INTEGER DEFAULT 0,
            last_login_attempt DATETIME,
            is_locked INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT UNIQUE NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        is_deleted INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Create sales table with customer information
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        customer_name TEXT,
        customer_email TEXT,
        total REAL NOT NULL,
        created_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')

    # Create sale_items table
    c.execute('''CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES sales(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    conn.commit()
    conn.close()
    migrate_db()
    
    # Create default admin user if no users exist
    create_default_admin()

def create_default_admin():
    """Create a default admin user if no users exist"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        # Create default admin with scrypt password
        password = "admin123"
        hashed_password = hash_password_scrypt(password)
        
        c.execute('''INSERT INTO users (first_name, middle_name, last_name, birthday, age, address, email, password, role)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  ('Admin', '', 'User', '1990-01-01', 30, 'Admin Address', 'admin@pos.com', hashed_password, 'admin'))
        conn.commit()
    conn.close()

def hash_password_scrypt(password):
    """Hash password using scrypt from passlib"""
    return scrypt.hash(password)

def verify_password_scrypt(password, hashed_password):
    """Verify password using scrypt from passlib"""
    try:
        return scrypt.verify(password, hashed_password)
    except:
        return False

def create_user(first_name, middle_name, last_name, birthday, age, address, email, password, role='customer'):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    hashed_password = hash_password_scrypt(password)
    c.execute('''INSERT INTO users (first_name, middle_name, last_name, birthday, age, address, email, password, role)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (first_name, middle_name, last_name, birthday, age, address, email, hashed_password, role))
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
    c.execute('SELECT id, first_name, middle_name, last_name, birthday, age, address, email, role, is_locked FROM users')
    users = c.fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, first_name, middle_name, last_name, birthday, age, address, email, role FROM users WHERE id=?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_user(user_id, first_name, middle_name, last_name, birthday, age, address, email, role):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''UPDATE users SET first_name=?, middle_name=?, last_name=?, birthday=?, age=?, address=?, email=?, role=? WHERE id=?''',
              (first_name, middle_name, last_name, birthday, age, address, email, role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()

def set_user_role(user_id, role):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE users SET role=? WHERE id=?', (role, user_id))
    conn.commit()
    conn.close()

def increment_login_attempts(email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE users SET login_attempts = login_attempts + 1, last_login_attempt = CURRENT_TIMESTAMP WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def reset_login_attempts(email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE users SET login_attempts = 0, is_locked = 0 WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def lock_user(email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE users SET is_locked = 1 WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def is_user_locked(email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT is_locked FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else False

def get_login_attempts(email):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT login_attempts FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def add_product(name, sku, quantity, price):
    """
    Adds a new product to the database. Raises sqlite3.IntegrityError if SKU is not unique.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO products (name, sku, quantity, price) VALUES (?, ?, ?, ?)''', (name, sku, int(quantity), float(price)))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_all_products():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, name, sku, quantity, price FROM products WHERE is_deleted=0')
    products = c.fetchall()
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, name, sku, quantity, price FROM products WHERE id=? AND is_deleted=0', (product_id,))
    product = c.fetchone()
    conn.close()
    return product

def update_product(product_id, name, sku, quantity, price):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Check if the new SKU exists for a different product
    c.execute('SELECT id FROM products WHERE sku=? AND id!=? AND is_deleted=0', (sku, product_id))
    existing = c.fetchone()
    if existing:
        conn.close()
        raise Exception('SKU already exists for another product.')
    c.execute('''UPDATE products SET name=?, sku=?, quantity=?, price=? WHERE id=?''', (name, sku, quantity, price, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Soft delete: set is_deleted=1
    c.execute('UPDATE products SET is_deleted=1 WHERE id=?', (product_id,))
    conn.commit()
    conn.close()

def get_all_staff():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT id, first_name, middle_name, last_name, birthday, age, address, email, role FROM users WHERE role IN ("admin", "seller")')
    staff = c.fetchall()
    conn.close()
    return staff

def record_sale(total, customer_name=None, customer_email=None, created_by=None):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO sales (total, customer_name, customer_email, created_by) VALUES (?, ?, ?, ?)', 
              (total, customer_name, customer_email, created_by))
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
    c.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?', (quantity_sold, product_id))
    conn.commit()
    conn.close()

def get_sales_history(user_role=None, user_id=None):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if user_role == 'customer':
        # Customers can only see their own transactions
        c.execute('''SELECT s.id, s.timestamp, s.customer_name, s.total, s.customer_email 
                     FROM sales s WHERE s.customer_email = (SELECT email FROM users WHERE id = ?)''', (user_id,))
    else:
        # Admin and sellers can see all transactions
        c.execute('''SELECT s.id, s.timestamp, s.customer_name, s.total, s.customer_email, u.first_name || ' ' || u.last_name as created_by
                     FROM sales s 
                     LEFT JOIN users u ON s.created_by = u.id
                     ORDER BY s.timestamp DESC''')
    
    sales = c.fetchall()
    conn.close()
    return sales

def get_sale_details(sale_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT si.quantity, si.price, p.name, p.sku
                 FROM sale_items si
                 JOIN products p ON si.product_id = p.id
                 WHERE si.sale_id = ?''', (sale_id,))
    items = c.fetchall()
    conn.close()
    return items

def get_sale_by_id(sale_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
    sale = c.fetchone()
    conn.close()
    return sale