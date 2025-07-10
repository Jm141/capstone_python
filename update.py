import sqlite3

DATABASE = "users.db"

is_approved = 1
is_admin = 1
try:
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET is_approved = ?, is_admin = ? WHERE id = ?", (is_approved,is_admin, 1))    
        conn.commit()
    print("User inserted successfully.")
except sqlite3.Error as e:
    print(f"An error occurred: {e}")