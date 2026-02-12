# database/stock.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QPushButton, QSpinBox,
                               QMessageBox, QHeaderView, QApplication, QLineEdit)
from PySide6.QtCore import Qt
from database.queries import get_stock, restock_product

class StockWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock / Inventory Management")
        self.setGeometry(200, 200, 900, 500)
        self.all_products = []  # Store all products for filtering
        
        self.init_ui()
        self.load_stock_data()
    
    def init_ui(self):
        """Initialize the stock management UI."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Stock Management - Restock Only")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Select a product and enter the quantity to restock. Only stock quantities can be modified.")
        instructions.setStyleSheet("font-style: italic; color: #555;")
        main_layout.addWidget(instructions)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search (ID/Code/Name):"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type ID, Code, or Product Name...")
        self.search_input.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)
        
        # Stock table
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(7)
        self.stock_table.setHorizontalHeaderLabels(["ID", "Name", "Code", "Color", "Size", "Current Stock", "Restock Qty"])
        
        # Set column widths
        self.stock_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.stock_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        main_layout.addWidget(self.stock_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Restock")
        apply_btn.setStyleSheet("background-color: green; color: white; font-weight: bold; padding: 10px;")
        apply_btn.clicked.connect(self.apply_restock)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_stock_data)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        main_widget.setLayout(main_layout)
    
    def load_stock_data(self):
        """Load all products with current stock levels."""
        self.all_products = get_stock()
        self.display_products(self.all_products)
    
    def display_products(self, products):
        """Display products in the table."""
        self.stock_table.setRowCount(0)
        for product in products:
            product_id, code, name, color, size, stock = product
            row = self.stock_table.rowCount()
            self.stock_table.insertRow(row)
            
            # ID (read-only)
            id_item = QTableWidgetItem(str(product_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.stock_table.setItem(row, 0, id_item)
            
            # Name (read-only)
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.stock_table.setItem(row, 1, name_item)
            
            # Code (read-only)
            code_item = QTableWidgetItem(code if code else "N/A")
            code_item.setFlags(code_item.flags() & ~Qt.ItemIsEditable)
            self.stock_table.setItem(row, 2, code_item)
            
            # Color (read-only)
            color_item = QTableWidgetItem(color if color else "N/A")
            color_item.setFlags(color_item.flags() & ~Qt.ItemIsEditable)
            self.stock_table.setItem(row, 3, color_item)
            
            # Size (read-only)
            size_item = QTableWidgetItem(size if size else "N/A")
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
            self.stock_table.setItem(row, 4, size_item)
            
            # Current Stock (read-only)
            stock_item = QTableWidgetItem(str(stock))
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)
            stock_item.setTextAlignment(Qt.AlignCenter)
            self.stock_table.setItem(row, 5, stock_item)
            
            # Restock Qty (editable spinbox)
            spinbox = QSpinBox()
            spinbox.setMinimum(0)
            spinbox.setMaximum(9999)
            spinbox.setValue(0)
            self.stock_table.setCellWidget(row, 6, spinbox)
            
            # Store product_id in the table for later use
            self.stock_table.item(row, 0).setData(Qt.UserRole, product_id)
    
    def filter_products(self):
        """Filter products based on search query (ID, Code, or Name)."""
        search_text = self.search_input.text().strip().lower()
        if not search_text:
            self.display_products(self.all_products)
            return
        
        filtered = []
        for product in self.all_products:
            product_id, code, name, color, size, stock = product
            # Match ID, Code, or Name (case-insensitive)
            if (str(product_id).lower().startswith(search_text) or
                (code and code.lower().find(search_text) != -1) or
                (name and name.lower().find(search_text) != -1)):
                filtered.append(product)
        
        self.display_products(filtered)
    
    def apply_restock(self):
        """Apply restock quantities to products."""
        restocked = []
        errors = []
        
        for row in range(self.stock_table.rowCount()):
            spinbox = self.stock_table.cellWidget(row, 6)
            quantity = spinbox.value()
            
            if quantity > 0:
                product_id_item = self.stock_table.item(row, 0)
                product_id = product_id_item.data(Qt.UserRole)
                product_name = self.stock_table.item(row, 1).text()
                
                result = restock_product(product_id, quantity)
                
                if result["success"]:
                    restocked.append(f"{product_name}: +{quantity} units")
                    spinbox.setValue(0)  # Reset spinbox
                else:
                    errors.append(f"{product_name}: {result['error']}")
        
        if not restocked and not errors:
            QMessageBox.information(self, "No Changes", "No quantities were entered for restock.")
            return
        
        message = ""
        if restocked:
            message += "Restocked:\n" + "\n".join(restocked)
        
        if errors:
            if message:
                message += "\n\nErrors:\n"
            message += "\n".join(errors)
        
        if restocked and not errors:
            QMessageBox.information(self, "Restock Complete", message)
        elif errors and restocked:
            QMessageBox.warning(self, "Partial Success", message)
        else:
            QMessageBox.critical(self, "Restock Failed", message)
        
        # Refresh the display
        self.load_stock_data()

# Optional: for standalone testing
if __name__ == "__main__":
    app = QApplication([])
    window = StockWindow()
    window.show()
    app.exec()
