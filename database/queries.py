# database/queries.py
from database.db import get_connection

# -------------------------
# Product functions
# -------------------------
def add_product(name, color, size, stock, code=None):
    """Add a new product with initial stock."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO products (code, name, color, size, stock) VALUES (?, ?, ?, ?, ?)",
            (code, name, color, size, stock)
        )
        product_id = c.lastrowid
        # Log initial stock
        c.execute(
            "INSERT INTO stock_log (product_id, action, quantity) VALUES (?, ?, ?)",
            (product_id, "restock", stock)
        )
        conn.commit()
        return {"success": True, "product_id": product_id}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def restock_product(product_id, quantity):
    """Add stock to an existing product."""
    if quantity <= 0:
        return {"success": False, "error": "Quantity must be positive"}
    conn = get_connection()
    c = conn.cursor()
    try:
        # Check if product exists
        c.execute("SELECT stock FROM products WHERE id=?", (product_id,))
        result = c.fetchone()
        if not result:
            return {"success": False, "error": "Product not found"}

        c.execute("UPDATE products SET stock = stock + ? WHERE id=?", (quantity, product_id))
        c.execute(
            "INSERT INTO stock_log (product_id, action, quantity) VALUES (?, ?, ?)",
            (product_id, "restock", quantity)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def sell_product(product_id, quantity):
    """Reduce stock for a product (sale)."""
    if quantity <= 0:
        return {"success": False, "error": "Quantity must be positive"}
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT stock FROM products WHERE id=?", (product_id,))
        result = c.fetchone()
        if not result:
            return {"success": False, "error": "Product not found"}
        current_stock = result[0]
        if quantity > current_stock:
            return {"success": False, "error": "Insufficient stock"}

        c.execute("UPDATE products SET stock = stock - ? WHERE id=?", (quantity, product_id))
        c.execute(
            "INSERT INTO stock_log (product_id, action, quantity) VALUES (?, ?, ?)",
            (product_id, "sale", -quantity)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

# -------------------------
# Fetching functions
# -------------------------
def get_stock():
    """Return all products with current stock."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT id, code, name, color, size, stock FROM products")
        rows = c.fetchall()
        return rows
    finally:
        conn.close()

def get_stock_log(product_id=None):
    """Return stock log. Filter by product_id if provided."""
    conn = get_connection()
    c = conn.cursor()
    try:
        if product_id:
            c.execute(
                "SELECT product_id, action, quantity, timestamp FROM stock_log WHERE product_id=? ORDER BY timestamp",
                (product_id,)
            )
        else:
            c.execute(
                "SELECT product_id, action, quantity, timestamp FROM stock_log ORDER BY timestamp"
            )
        return c.fetchall()
    finally:
        conn.close()
