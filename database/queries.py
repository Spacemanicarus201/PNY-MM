# database/queries.py
from database.db import get_connection
import uuid

# -------------------------
# Product functions
# -------------------------
def add_product(name, color, size, stock, price=None, code=None):
    """Add a new product with initial stock."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Insert product (code may be None). We'll generate a unique code after insert
        c.execute(
            "INSERT INTO products (code, name, color, size, price, stock) VALUES (?, ?, ?, ?, ?, ?)",
            (code, name, color, size, price or 0, stock)
        )
        product_id = c.lastrowid

        # If no code provided, generate a short UUID-based unique code
        if not code:
            unique = uuid.uuid4().hex[:10]
            generated_code = f"PNY{unique}"
            # update the product with the generated code
            c.execute("UPDATE products SET code=? WHERE id=?", (generated_code, product_id))
            code = generated_code

        # Log initial stock
        c.execute(
            "INSERT INTO stock_log (product_id, action, quantity) VALUES (?, ?, ?)",
            (product_id, "restock", stock)
        )
        conn.commit()
        return {"success": True, "product_id": product_id, "code": code}
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
        c.execute("SELECT id, code, name, color, size, price, discount, stock FROM products")
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


def update_product(product_id, name=None, color=None, size=None, stock=None, code=None, price=None, discount=None):
    """Update product fields. Only non-None arguments will be updated."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Build dynamic update
        fields = []
        params = []
        if code is not None:
            fields.append("code = ?")
            params.append(code)
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if color is not None:
            fields.append("color = ?")
            params.append(color)
        if size is not None:
            fields.append("size = ?")
            params.append(size)
        if price is not None:
            fields.append("price = ?")
            params.append(price)
        if discount is not None:
            fields.append("discount = ?")
            params.append(discount)
        if stock is not None:
            fields.append("stock = ?")
            params.append(stock)

        if not fields:
            return {"success": False, "error": "No fields to update"}

        params.append(product_id)
        sql = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
        c.execute(sql, tuple(params))
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def delete_product(product_id):
    """Delete a product and its stock log entries."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM stock_log WHERE product_id = ?", (product_id,))
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
