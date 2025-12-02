import sqlite3
import hashlib
import os
from datetime import datetime

# FORCE DB LOCATION TO SCRIPT DIRECTORY
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'financify.db')
SECRET_SALT = "s0m3_r4nd0m_s4lt_v4lu3" 

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    salted_password = password + SECRET_SALT
    return hashlib.sha256(salted_password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        account_name TEXT NOT NULL,
        account_type TEXT,
        current_balance REAL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        account_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        tags TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (account_id) REFERENCES accounts(account_id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (
        budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        UNIQUE(user_id, category, month, year),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )''')
    
    conn.commit()
    conn.close()

# --- USER & ACCOUNT ---
def register_user(username, password):
    if not username or not password: return False, "Fields cannot be empty"
    if len(password) < 4: return False, "Password too short (min 4)"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password(password)))
        new_id = cursor.lastrowid
        cursor.execute("INSERT INTO accounts (user_id, account_name, account_type, current_balance) VALUES (?, ?, ?, ?)", (new_id, 'Checking', 'Checking', 0))
        conn.commit()
        return True, "Success"
    except sqlite3.IntegrityError: return False, "Username taken"
    finally: conn.close()

def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and verify_password(user['password_hash'], password): return True, "Success", user['user_id']
    return False, "Invalid credentials", None

def check_and_create_default_account(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM accounts WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO accounts (user_id, account_name, account_type, current_balance) VALUES (?, ?, ?, ?)", (user_id, 'Checking', 'Checking', 0))
        conn.commit()
    conn.close()

def get_accounts(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT account_id, account_name, current_balance FROM accounts WHERE user_id = ?", (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data

def wipe_user_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE accounts SET current_balance = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- TRANSACTIONS ---
def check_transaction_exists(user_id, date, amount, description, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM transactions WHERE user_id=? AND date=? AND amount=? AND description=?", (user_id, date, amount, description))
    return cursor.fetchone() is not None

def add_transaction(user_id, account_id, date, amount, trans_type, category, description, tags, conn_ext=None):
    try:
        amt = float(amount)
        if trans_type == 'Expense': amt = -abs(amt)
        else: amt = abs(amt)
        amt = round(amt, 2)
    except ValueError: return False, "Invalid amount", None
    
    conn = conn_ext if conn_ext else get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT current_balance FROM accounts WHERE account_id = ?", (account_id,))
        row = cursor.fetchone()
        if not row: return False, "Account error", None
        old_bal = row['current_balance']
        
        cursor.execute("INSERT INTO transactions (user_id, account_id, date, amount, type, category, description, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       (user_id, account_id, date, amt, trans_type, category, description, tags))
        new_id = cursor.lastrowid
        cursor.execute("UPDATE accounts SET current_balance = ? WHERE account_id = ?", (round(old_bal + amt, 2), account_id))
        
        if not conn_ext: conn.commit()
        return True, "Added", new_id
    except Exception as e:
        if not conn_ext: conn.rollback()
        return False, str(e), None
    finally:
        if not conn_ext: conn.close()

def delete_transaction(transaction_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT account_id, amount FROM transactions WHERE transaction_id = ? AND user_id = ?", (transaction_id, user_id))
        trans = cursor.fetchone()
        if not trans: return False, "Not found"
        cursor.execute("UPDATE accounts SET current_balance = round(current_balance - ?, 2) WHERE account_id = ?", (trans['amount'], trans['account_id']))
        cursor.execute("DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,))
        conn.commit()
        return True, "Deleted"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally: conn.close()

def update_transaction(transaction_id, user_id, new_details):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT account_id, amount FROM transactions WHERE transaction_id = ? AND user_id = ?", (transaction_id, user_id))
        old = cursor.fetchone()
        if not old: raise Exception("Not found")
        cursor.execute("UPDATE accounts SET current_balance = round(current_balance - ?, 2) WHERE account_id = ?", (old['amount'], old['account_id']))
        
        new_amt = float(new_details['amount'])
        if new_details['type'] == 'Expense': new_amt = -abs(new_amt)
        else: new_amt = abs(new_amt)
        new_amt = round(new_amt, 2)
        
        cursor.execute("UPDATE accounts SET current_balance = round(current_balance + ?, 2) WHERE account_id = ?", (new_amt, new_details['account_id']))
        cursor.execute("UPDATE transactions SET date=?, amount=?, type=?, category=?, description=?, account_id=? WHERE transaction_id=?", 
                       (new_details['date'], new_amt, new_details['type'], new_details['category'], new_details['description'], new_details['account_id'], transaction_id))
        conn.commit()
        return True, "Updated"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally: conn.close()

def get_transactions_by_filter(user_id, search_term=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT t.transaction_id, t.date, t.type, t.amount, t.category, t.description, a.account_name, t.account_id FROM transactions t JOIN accounts a ON t.account_id = a.account_id WHERE t.user_id = ?"
    params = [user_id]
    if search_term:
        query += " AND (t.category LIKE ? OR t.description LIKE ? OR a.account_name LIKE ?)"
        term = f"%{search_term}%"
        params.extend([term, term, term])
    query += " ORDER BY t.date DESC, t.transaction_id DESC"
    cursor.execute(query, tuple(params))
    res = cursor.fetchall()
    conn.close()
    return res

# --- DASHBOARD & CHARTS ---
def get_dashboard_numbers(user_id, month, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    m, y = f"{month:02d}", str(year)
    cursor.execute("SELECT amount FROM budgets WHERE user_id=? AND month=? AND year=? AND category='##TOTAL##'", (user_id, month, year))
    row = cursor.fetchone()
    bud = row['amount'] if row else 0.0
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE user_id=? AND type='Income' AND strftime('%Y', date)=? AND strftime('%m', date)=?", (user_id, y, m))
    row = cursor.fetchone()
    inc = row[0] if row[0] else 0.0
    
    cursor.execute("SELECT SUM(abs(amount)) FROM transactions WHERE user_id=? AND type='Expense' AND strftime('%Y', date)=? AND strftime('%m', date)=?", (user_id, y, m))
    row = cursor.fetchone()
    spn = row[0] if row[0] else 0.0
    conn.close()
    return {'budget': bud, 'income': inc, 'spent': spn, 'remaining': bud - spn, 'net': inc - spn}

def get_expense_data_for_pie_chart(user_id, month, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(abs(amount)) as total FROM transactions WHERE user_id=? AND type='Expense' AND strftime('%Y', date)=? AND strftime('%m', date)=? GROUP BY category HAVING total > 0", (user_id, str(year), f"{month:02d}"))
    res = cursor.fetchall()
    conn.close()
    return res

def get_monthly_comparison_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, 
               SUM(CASE WHEN type='Income' THEN amount ELSE 0 END) as income,
               SUM(CASE WHEN type='Expense' THEN abs(amount) ELSE 0 END) as expense
        FROM transactions 
        WHERE user_id=? AND date >= date('now', '-6 months') 
        GROUP BY month ORDER BY month ASC
    """, (user_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def get_recent_transactions(user_id, limit=5):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, category, amount, type FROM transactions WHERE user_id = ? ORDER BY date DESC, transaction_id DESC LIMIT ?", (user_id, limit))
    data = cursor.fetchall()
    conn.close()
    return data

# --- BUDGETS ---
def set_monthly_budget(user_id, month, year, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO budgets (user_id, category, amount, month, year) VALUES (?, '##TOTAL##', ?, ?, ?)", (user_id, amount, month, year))
    conn.commit()
    conn.close()

def set_category_budget(user_id, category, amount, month, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO budgets (user_id, category, amount, month, year) VALUES (?, ?, ?, ?, ?)", (user_id, category, amount, month, year))
    conn.commit()
    conn.close()
    return True, "Saved"

def delete_category_budget(user_id, category, month, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM budgets WHERE user_id=? AND category=? AND month=? AND year=?", (user_id, category, month, year))
    conn.commit()
    conn.close()
    return True, "Deleted"

def get_category_budgets_with_spending(user_id, month, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    WITH Spending AS (SELECT category, SUM(abs(amount)) as spent FROM transactions WHERE user_id=? AND type='Expense' AND strftime('%Y', date)=? AND strftime('%m', date)=? GROUP BY category)
    SELECT b.category, b.amount as budget, COALESCE(s.spent, 0) as spent FROM budgets b LEFT JOIN Spending s ON b.category = s.category WHERE b.user_id=? AND b.month=? AND b.year=? AND b.category != '##TOTAL##'
    UNION ALL
    SELECT s.category, 0 as budget, s.spent FROM Spending s LEFT JOIN budgets b ON s.category = b.category AND b.user_id=? AND b.month=? AND b.year=? WHERE b.budget_id IS NULL
    """
    params = (user_id, str(year), f"{month:02d}", user_id, month, year, user_id, month, year)
    cursor.execute(query, params)
    res = cursor.fetchall()
    conn.close()
    return res

if __name__ == '__main__':
    initialize_database()
    
