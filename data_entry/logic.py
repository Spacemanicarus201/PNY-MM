from database.queries import add_product, get_stock, restock_product

class DataEntryManager:
    def get_products(self):
        return get_stock()

    def add_product(self, name, color, size, stock, price=None, code=None):
        return add_product(name, color, size, stock, price, code)

    def restock(self, product_id, quantity):
        return restock_product(product_id, quantity)
