# database/db.py
import sqlite3
from pathlib import Path

# Ensure DB folder exists
DB_FOLDER = Path(__file__).parent.parent
DB_FOLDER.mkdir(exist_ok=True)

# SQLite DB file
DB_PATH = DB_FOLDER / "db"

def get_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def create_tables():
    """Create products and stock_log tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    # Products table
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        name TEXT NOT NULL,
        color TEXT,
        size TEXT,
        stock INTEGER DEFAULT 0
    )
    """)

    # Stock log table
    c.execute("""
    CREATE TABLE IF NOT EXISTS stock_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    conn.commit()
    conn.close()

# Automatically create tables if DB is empty
create_tables()
