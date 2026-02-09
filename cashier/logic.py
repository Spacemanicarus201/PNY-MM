# cashier/logic.py
from database.queries import get_stock, sell_product
from config import TAX_RATE

class CartManager:
    """Manages shopping cart for cashier system."""
    
    def __init__(self):
        self.cart = {}  # {product_id: {"product": product_data, "quantity": qty, "price": unit_price}}
        self.products_by_code = self._load_products_by_code()
    
    def _load_products_by_code(self):
        """Load all products indexed by ID for quick lookup (testing phase)."""
        products = get_stock()
        by_id = {}
        for product in products:
            product_id, code, name, color, size, stock = product
            by_id[str(product_id)] = {
                "id": product_id,
                "code": code,
                "name": name,
                "color": color,
                "size": size,
                "stock": stock
            }
        self.products_by_id = by_id
        return by_id
    
    def scan_code(self, code, unit_price=0.0):
        """Add product to cart by scanning ID (testing phase uses product ID)."""
        if code not in self.products_by_code:
            return {"success": False, "error": f"Product ID '{code}' not found. Available products: {', '.join(self.products_by_code.keys())}"}
        
        product = self.products_by_code[code]
        product_id = product["id"]
        
        if product["stock"] <= 0:
            return {"success": False, "error": f"Product '{product['name']}' is out of stock"}
        
        if product_id in self.cart:
            # Increase quantity
            if self.cart[product_id]["quantity"] >= product["stock"]:
                return {"success": False, "error": f"Only {product['stock']} units available"}
            self.cart[product_id]["quantity"] += 1
        else:
            # Add new item
            self.cart[product_id] = {
                "product": product,
                "quantity": 1,
                "price": unit_price
            }
        
        return {"success": True, "product": product, "quantity": self.cart[product_id]["quantity"]}
    
    def update_quantity(self, product_id, quantity):
        """Update quantity of item in cart."""
        if product_id not in self.cart:
            return {"success": False, "error": "Product not in cart"}
        
        if quantity <= 0:
            self.remove_item(product_id)
            return {"success": True, "message": "Item removed"}
        
        product = self.cart[product_id]["product"]
        if quantity > product["stock"]:
            return {"success": False, "error": f"Only {product['stock']} units available"}
        
        self.cart[product_id]["quantity"] = quantity
        return {"success": True, "quantity": quantity}
    
    def update_price(self, product_id, price):
        """Update unit price of item."""
        if product_id not in self.cart:
            return {"success": False, "error": "Product not in cart"}
        
        if price < 0:
            return {"success": False, "error": "Price cannot be negative"}
        
        self.cart[product_id]["price"] = price
        return {"success": True, "price": price}
    
    def remove_item(self, product_id):
        """Remove item from cart."""
        if product_id in self.cart:
            del self.cart[product_id]
            return {"success": True}
        return {"success": False, "error": "Product not in cart"}
    
    def get_cart(self):
        """Return current cart items."""
        return self.cart
    
    def get_totals(self):
        """Calculate and return cart totals."""
        subtotal = sum(
            item["quantity"] * item["price"]
            for item in self.cart.values()
        )
        tax = subtotal * TAX_RATE
        total = subtotal + tax
        
        return {
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "item_count": len(self.cart),
            "unit_count": sum(item["quantity"] for item in self.cart.values())
        }
    
    def checkout(self):
        """Process checkout and update stock."""
        if not self.cart:
            return {"success": False, "error": "Cart is empty"}
        
        try:
            for product_id, item in self.cart.items():
                result = sell_product(product_id, item["quantity"])
                if not result["success"]:
                    return {"success": False, "error": f"Failed to process sale: {result['error']}"}
            
            receipt = {
                "items": self.cart.copy(),
                "totals": self.get_totals()
            }
            
            # Clear cart
            self.cart = {}
            
            return {"success": True, "receipt": receipt}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_cart(self):
        """Clear the cart."""
        self.cart = {}
        return {"success": True}
