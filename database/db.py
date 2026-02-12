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
        price INTEGER DEFAULT 0,
        discount INTEGER DEFAULT 0,
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
    # Ensure price and discount columns exist for older DBs
    try:
        c.execute("PRAGMA table_info(products)")
        cols = [r[1] for r in c.fetchall()]
        if 'price' not in cols:
            c.execute("ALTER TABLE products ADD COLUMN price INTEGER DEFAULT 0")
            conn.commit()
        if 'discount' not in cols:
            c.execute("ALTER TABLE products ADD COLUMN discount INTEGER DEFAULT 0")
            conn.commit()
    except Exception:
        pass
    conn.close()

# Automatically create tables if DB is empty
create_tables()
