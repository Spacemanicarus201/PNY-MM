# data_entry/ui.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QInputDialog, QMessageBox,
    QLabel, QFileDialog, QDialog, QLineEdit, QSpinBox, QFormLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import qrcode
import io
from PIL.ImageQt import ImageQt
import re
from database.queries import add_product, get_stock


class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Product")
        self.setModal(True)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.color_edit = QLineEdit()
        self.size_edit = QLineEdit()
        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 1000000)
        self.stock_spin.setValue(1)
        self.price_spin = QSpinBox()
        self.price_spin.setRange(0, 1000000000)
        self.price_spin.setSuffix(" IDR")
        self.price_spin.setSingleStep(1000)
        self.code_edit = QLineEdit()

        layout.addRow("Name:", self.name_edit)
        layout.addRow("Color:", self.color_edit)
        layout.addRow("Size:", self.size_edit)
        layout.addRow("Initial Stock:", self.stock_spin)
        layout.addRow("Price (IDR):", self.price_spin)
        layout.addRow("Code (optional):", self.code_edit)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

    def values(self):
        return (
            self.name_edit.text().strip(),
            self.color_edit.text().strip(),
            self.size_edit.text().strip(),
            int(self.stock_spin.value()),
            int(self.price_spin.value()),
            self.code_edit.text().strip() or None,
        )

class DataEntryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Entry / Admin")
        self.setGeometry(200, 200, 700, 400)
        self.all_products = []  # Store all products for filtering

        self.layout = QVBoxLayout()

        # Table showing all products
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Code", "Name", "Color", "Size", "Stock"])
        self.layout.addWidget(self.table)
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search (ID/Code/Name):"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type ID, Code, or Product Name...")
        self.search_input.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)
        # Buttons
        button_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Product")
        self.btn_add.clicked.connect(self.add_product_ui)
        self.btn_edit = QPushButton("Edit Product")
        self.btn_edit.setCheckable(True)
        self.btn_edit.toggled.connect(self.toggle_edit_mode)
        self.btn_save_edits = QPushButton("Save Edits")
        self.btn_save_edits.setEnabled(False)
        self.btn_save_edits.clicked.connect(self.save_edits)
        self.btn_delete = QPushButton("Delete Product")
        self.btn_delete.clicked.connect(self.delete_selected_product)
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_edit)
        button_layout.addWidget(self.btn_save_edits)
        button_layout.addWidget(self.btn_delete)
        # Code preview area (QR) placed beside buttons
        code_layout = QHBoxLayout()
        code_layout.addLayout(button_layout)

        self.code_label = QLabel()
        self.code_label.setFixedSize(160, 160)
        self.code_label.setStyleSheet("border: 1px solid #ccc; background: #fff;")
        code_layout.addWidget(self.code_label)

        self.btn_download_qr = QPushButton("Download QR")
        self.btn_download_qr.setEnabled(False)
        self.btn_download_qr.clicked.connect(self.download_qr)
        code_layout.addWidget(self.btn_download_qr)

        self.layout.addLayout(code_layout)

        # Container
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.load_products()
        self.table.itemSelectionChanged.connect(self.on_table_select)

    def load_products(self):
        self.all_products = get_stock()
        self.display_products(self.all_products)
    
    def display_products(self, products):
        self.table.setRowCount(0)
        for row_idx, product in enumerate(products):
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(product):
                # Ensure price and discount appear as integers without decimals
                if col_idx in (5, 6) and isinstance(value, (int, float)):
                    item = QTableWidgetItem(str(int(value)))
                else:
                    item = QTableWidgetItem(str(value))
                # By default items are not editable; edit only when edit mode enabled
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

    def filter_products(self):
        """Filter products based on search query (ID, Code, or Name)."""
        search_text = self.search_input.text().strip().lower()
        if not search_text:
            self.display_products(self.all_products)
            return
        
        filtered = []
        for product in self.all_products:
            product_id, code, name, color, size, price, discount, stock = product
            # Match ID, Code, or Name (case-insensitive)
            if (str(product_id).lower().startswith(search_text) or
                (code and code.lower().find(search_text) != -1) or
                (name and name.lower().find(search_text) != -1)):
                filtered.append(product)
        
        self.display_products(filtered)

    def add_product_ui(self):
        dialog = AddProductDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        name, color, size, stock, code_input = dialog.values()
        result = add_product(name, color, size, stock, code_input)
        if result["success"]:
            QMessageBox.information(self, "Success", "Product added successfully!")
            self.load_products()
            # Show generated QR in preview and enable download
            code_for_qr = result.get("code") or code_input
            pix = self._qr_pixmap_for_code(code_for_qr) if code_for_qr else None
            if pix:
                self.code_label.setPixmap(pix.scaled(self.code_label.width(), self.code_label.height()))
                self.current_qr_image = pix
                self.current_qr_metadata = {"name": name, "color": color, "size": size}
                self.btn_download_qr.setEnabled(True)
        else:
            QMessageBox.warning(self, "Error", result.get("error", "Unknown error"))

    def on_table_select(self):
        sel = self.table.selectedItems()
        if not sel:
            return
        # Row selection -> code is in column 1 per table headers
        row = sel[0].row()
        code_item = self.table.item(row, 1)
        name_item = self.table.item(row, 2)
        color_item = self.table.item(row, 3)
        size_item = self.table.item(row, 4)
        price_item = self.table.item(row, 5)
        if code_item and code_item.text():
            code = code_item.text()
            pix = self._qr_pixmap_for_code(code)
            if pix:
                self.code_label.setPixmap(pix.scaled(self.code_label.width(), self.code_label.height()))
                self.current_qr_image = pix
                self.current_qr_metadata = {
                    "name": name_item.text() if name_item else "product",
                    "color": color_item.text() if color_item else "",
                    "size": size_item.text() if size_item else "",
                    "price": int(price_item.text()) if price_item and price_item.text() else 0
                }
                self.btn_download_qr.setEnabled(True)
        else:
            self.code_label.clear()
            self.btn_download_qr.setEnabled(False)

    def toggle_edit_mode(self, enabled: bool):
        # Enable editing for Name, Color, Size, Price, Discount, Stock columns (2,3,4,5,6,7)
        count = self.table.rowCount()
        for r in range(count):
            for c in (2, 3, 4, 5, 6, 7):
                item = self.table.item(r, c)
                if item:
                    if enabled:
                        item.setFlags(item.flags() | Qt.ItemIsEditable)
                    else:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.btn_save_edits.setEnabled(enabled)

    def save_edits(self):
        # Iterate through table rows and update changed rows
        from database.queries import update_product
        errors = []
        for r in range(self.table.rowCount()):
            id_item = self.table.item(r, 0)
            if not id_item:
                continue
            try:
                pid = int(id_item.text())
            except Exception:
                continue
            name_item = self.table.item(r, 2)
            color_item = self.table.item(r, 3)
            size_item = self.table.item(r, 4)
            price_item = self.table.item(r, 5)
            discount_item = self.table.item(r, 6)
            stock_item = self.table.item(r, 7)
            name = name_item.text() if name_item else None
            color = color_item.text() if color_item else None
            size = size_item.text() if size_item else None
            try:
                price = int(price_item.text()) if price_item else None
            except Exception:
                price = None
            try:
                discount = int(discount_item.text()) if discount_item else None
            except Exception:
                discount = None
            try:
                stock = int(stock_item.text()) if stock_item else None
            except Exception:
                stock = None
            res = update_product(pid, name=name, color=color, size=size, stock=stock, price=price, discount=discount)
            if not res.get("success"):
                errors.append(f"{pid}: {res.get('error')}")
        self.btn_edit.setChecked(False)
        self.toggle_edit_mode(False)
        self.load_products()
        if errors:
            QMessageBox.warning(self, "Update errors", "\n".join(errors))

    def delete_selected_product(self):
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.information(self, "Delete", "No product selected")
            return
        row = sel[0].row()
        id_item = self.table.item(row, 0)
        name_item = self.table.item(row, 2)
        if not id_item:
            return
        pid = id_item.text()
        name = name_item.text() if name_item else pid
        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete product {name} (id={pid})?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        from database.queries import delete_product
        res = delete_product(int(pid))
        if res.get("success"):
            QMessageBox.information(self, "Deleted", "Product deleted")
            self.load_products()
            self.code_label.clear()
            self.btn_download_qr.setEnabled(False)
        else:
            QMessageBox.warning(self, "Error", res.get("error", "Unknown error"))

    def _qr_pixmap_for_code(self, code_text: str) -> QPixmap:
        try:
            qr = qrcode.QRCode(box_size=4, border=2)
            qr.add_data(code_text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            qim = ImageQt(img)
            pix = QPixmap.fromImage(qim)
            return pix
        except Exception:
            return None

    def download_qr(self):
        if not hasattr(self, 'current_qr_image') or self.current_qr_image is None:
            return
        meta = getattr(self, 'current_qr_metadata', {"name": "product", "color": "", "size": ""})
        # sanitize filename
        base = f"{meta.get('name','product')}_{meta.get('color','')}_{meta.get('size','')}"
        safe = re.sub(r'[^A-Za-z0-9_.-]', '_', base)
        suggested = f"{safe}.png"
        path, _ = QFileDialog.getSaveFileName(self, "Save QR", suggested, "PNG Files (*.png)")
        if not path:
            return
        # Save current_qr_image (QPixmap) to file
        self.current_qr_image.save(path, "PNG")
