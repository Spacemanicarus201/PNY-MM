# data_entry/ui.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QInputDialog, QMessageBox
)
from database.queries import add_product, get_stock

class DataEntryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Entry / Admin")
        self.setGeometry(200, 200, 700, 400)

        self.layout = QVBoxLayout()

        # Table showing all products
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Color", "Size", "Stock"])
        self.layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Product")
        self.btn_add.clicked.connect(self.add_product_ui)
        self.btn_edit = QPushButton("Edit Product")  # can implement later
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_edit)
        self.layout.addLayout(button_layout)

        # Container
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.load_products()

    def load_products(self):
        self.table.setRowCount(0)
        products = get_stock()
        for row_idx, product in enumerate(products):
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(product):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def add_product_ui(self):
        # Simple input dialogs for demo
        name, ok = QInputDialog.getText(self, "Add Product", "Product Name:")
        if not ok or not name:
            return

        color, ok = QInputDialog.getText(self, "Add Product", "Color:")
        if not ok: return

        size, ok = QInputDialog.getText(self, "Add Product", "Size:")
        if not ok: return

        stock, ok = QInputDialog.getInt(self, "Add Product", "Initial Stock:", 1, 0)
        if not ok: return

        # Code (optional)
        code, ok = QInputDialog.getText(self, "Add Product", "Code / QR (optional):")
        if not ok:
            code = None

        result = add_product(name, color, size, stock, code)
        if result["success"]:
            QMessageBox.information(self, "Success", "Product added successfully!")
            self.load_products()
        else:
            QMessageBox.warning(self, "Error", result.get("error", "Unknown error"))
