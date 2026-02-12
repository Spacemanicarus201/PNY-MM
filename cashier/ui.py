# cashier/ui.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                               QApplication, QSpinBox, QDoubleSpinBox, QHeaderView,
                               QMessageBox, QDialog, QFormLayout, QComboBox, QTextEdit)
from PySide6.QtCore import Qt, QTimer
from cashier.logic import CartManager
from database.reports import log_sale
from config import STORE_NAME, STORE_ADDRESS, CONTACT_NUMBER, TAX_RATE, TAX_INCLUSIVE

class CashierWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cashier System")
        self.setGeometry(100, 100, 1200, 700)
        
        self.cart_manager = CartManager()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the cashier UI."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        
        # Left side: Cart display
        left_layout = QVBoxLayout()
        
        # Cart title
        cart_title = QLabel("Shopping Cart")
        cart_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(cart_title)
        
        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(7)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Code", "Qty", "Unit Price", "Discount (%)", "Total", "Remove"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        left_layout.addWidget(self.cart_table)
        
        # Totals section
        totals_layout = QHBoxLayout()
        
        self.subtotal_label = QLabel("Subtotal: $0.00")
        self.tax_label = QLabel(f"Tax ({int(TAX_RATE*100)}%): $0.00")
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        
        totals_layout.addWidget(self.subtotal_label)
        totals_layout.addWidget(self.tax_label)
        totals_layout.addWidget(self.total_label)
        
        left_layout.addLayout(totals_layout)
        
        # Checkout buttons
        button_layout = QHBoxLayout()
        
        checkout_btn = QPushButton("Checkout")
        checkout_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        checkout_btn.clicked.connect(self.checkout)
        
        clear_btn = QPushButton("Clear Cart")
        clear_btn.clicked.connect(self.clear_cart)
        
        button_layout.addWidget(checkout_btn)
        button_layout.addWidget(clear_btn)
        
        left_layout.addLayout(button_layout)
        
        # Right side: Product scanning and details
        right_layout = QVBoxLayout()
        
        # Product scan section
        scan_title = QLabel("Scan/Add Product")
        scan_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(scan_title)
        
        # Code input
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("Product ID:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter product ID (from data entry)...")
        self.code_input.returnPressed.connect(self.scan_product)
        code_layout.addWidget(self.code_input)
        right_layout.addLayout(code_layout)
        
        # Price input (auto-filled from product price, disabled/locked)
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Unit Price (IDR):"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.0)
        self.price_input.setMaximum(999999999.0)
        self.price_input.setValue(0.0)
        self.price_input.setSingleStep(1000.0)
        self.price_input.setReadOnly(True)  # Lock price - cannot change
        self.price_input.setEnabled(False)  # Disabled
        price_layout.addWidget(self.price_input)
        right_layout.addLayout(price_layout)

        # Discount input (user can apply manual discount)
        discount_layout = QHBoxLayout()
        discount_layout.addWidget(QLabel("Discount (%):"))
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMinimum(0.0)
        self.discount_input.setMaximum(100.0)
        self.discount_input.setValue(0.0)
        self.discount_input.setSingleStep(1.0)
        discount_layout.addWidget(self.discount_input)
        self.btn_add_discount = QPushButton("Add Discount")
        self.btn_add_discount.clicked.connect(self.apply_discount)
        discount_layout.addWidget(self.btn_add_discount)
        right_layout.addLayout(discount_layout)
        
        # Scan button
        scan_btn = QPushButton("Add to Cart")
        scan_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold; padding: 10px;")
        scan_btn.clicked.connect(self.scan_product)
        right_layout.addWidget(scan_btn)
        
        # Product details display
        details_title = QLabel("Product Details")
        details_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        right_layout.addWidget(details_title)
        
        self.details_text = QLabel("Scan a product to see details")
        self.details_text.setWordWrap(True)
        self.details_text.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        right_layout.addWidget(self.details_text)
        
        right_layout.addStretch()
        
        # Add both sides to main layout
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        
        main_widget.setLayout(main_layout)
    
    def scan_product(self):
        """Handle product scanning."""
        code = self.code_input.text().strip()
        
        if not code:
            QMessageBox.warning(self, "Input Error", "Please enter a product code")
            return
        
        # Use product's stored price (price_input is disabled/locked)
        result = self.cart_manager.scan_code(code, 0.0)
        
        if result["success"]:
            product = result["product"]
            quantity = result["quantity"]
            
            # Update product details with price and discount from database
            details = f"""
            <b>Product Added to Cart</b><br>
            Name: {product['name']}<br>
            Code: {product['code']}<br>
            Color: {product['color']}<br>
            Size: {product['size']}<br>
            Unit Price: {int(product.get('price', 0)):,} IDR<br>
            Base Discount: {int(product.get('discount', 0))}%<br>
            Quantity in Cart: {quantity}<br>
            Available Stock: {product['stock']}
            """
            self.details_text.setText(details)
            
            # Clear code input and reset discount input to 0
            self.code_input.clear()
            self.code_input.setFocus()
            self.discount_input.setValue(0.0)
            
            # Update displays
            self.update_cart_display()
            self.update_totals()
        else:
            QMessageBox.warning(self, "Scan Error", result["error"])
            self.details_text.setText(f"<span style='color: red;'>{result['error']}</span>")

    def apply_discount(self):
        """Apply discount to the last scanned/selected product."""
        # Get the currently selected item in cart, or apply to most recently added
        sel = self.cart_table.selectedItems()
        if not sel:
            QMessageBox.information(self, "No Selection", "Please select a product in the cart to apply discount")
            return
        
        row = sel[0].row()
        if row < 0:
            return
        
        # Extract product_id from cart - we need to map row to product_id
        cart = self.cart_manager.get_cart()
        product_ids = list(cart.keys())
        if row >= len(product_ids):
            return
        
        product_id = product_ids[row]
        discount_pct = self.discount_input.value()
        
        # Apply discount to cart item (store as additional discount field)
        if product_id in cart:
            cart[product_id]['additional_discount'] = discount_pct
            self.discount_input.setValue(0.0)
            self.update_cart_display()
            self.update_totals()
            QMessageBox.information(self, "Discount Applied", f"Discount of {discount_pct}% applied")
        else:
            QMessageBox.warning(self, "Error", "Product not found in cart")
    
    def update_cart_display(self):
        """Update the cart table display."""
        self.cart_table.setRowCount(0)
        
        for product_id, item in self.cart_manager.get_cart().items():
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            
            product = item["product"]
            quantity = item["quantity"]
            price = item["price"]
            additional_discount = item.get('additional_discount', 0)
            total = quantity * price
            
            # Product name
            self.cart_table.setItem(row, 0, QTableWidgetItem(product["name"]))
            
            # Code
            self.cart_table.setItem(row, 1, QTableWidgetItem(product["code"]))
            
            # Quantity
            qty_item = QTableWidgetItem(str(quantity))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 2, qty_item)
            
            # Unit price (IDR format)
            price_item = QTableWidgetItem(f"{int(price):,}")
            price_item.setTextAlignment(Qt.AlignRight)
            self.cart_table.setItem(row, 3, price_item)

            # Discount
            discount_item = QTableWidgetItem(f"{additional_discount}%")
            discount_item.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 4, discount_item)

            # Total
            total_item = QTableWidgetItem(f"{int(total):,}")
            total_item.setTextAlignment(Qt.AlignRight)
            self.cart_table.setItem(row, 5, total_item)
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, pid=product_id: self.remove_item(pid))
            self.cart_table.setCellWidget(row, 6, remove_btn)
    
    def update_totals(self):
        """Update the totals display."""
        totals = self.cart_manager.get_totals()
        
        self.subtotal_label.setText(f"Subtotal: {int(totals['subtotal']):,} IDR")
        self.tax_label.setText(f"Tax ({int(TAX_RATE*100)}%): {int(totals['tax']):,} IDR")
        self.total_label.setText(f"Total: {int(totals['total']):,} IDR")

    def remove_item(self, product_id):
        """Remove item from cart."""
        self.cart_manager.remove_item(product_id)
        self.update_cart_display()
        self.update_totals()

    def clear_cart(self):
        """Clear the entire cart."""
        reply = QMessageBox.question(self, "Clear Cart", "Are you sure you want to clear the cart?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.cart_manager.clear_cart()
            self.update_cart_display()
            self.update_totals()
            self.details_text.setText("Cart cleared")

    def checkout(self):
        """Process checkout."""
        if not self.cart_manager.get_cart():
            QMessageBox.warning(self, "Empty Cart", "Cart is empty. Add products before checkout.")
            return
        # Collect payment info first
        totals = self.cart_manager.get_totals()
        pay_dlg = PaymentDialog(self, total_amount=totals['total'])
        if pay_dlg.exec() != QDialog.Accepted:
            return
        payment = pay_dlg.result_data

        # Perform checkout (updates stock)
        result = self.cart_manager.checkout()
        if not result["success"]:
            QMessageBox.critical(self, "Checkout Error", result["error"])
            return

        receipt = result["receipt"]

        # Compute change and augment metadata
        change = round(payment["amount_paid"] - totals["total"], 2)
        metadata = {
            "cashier_name": payment.get("cashier_name"),
            "payment_method": payment.get("payment_method"),
            "amount_paid": payment.get("amount_paid"),
            "change": change
        }

        # Log sale with metadata
        log_result = log_sale(receipt, metadata=metadata)
        invoice = log_result.get("invoice_number") if log_result.get("success") else None
        log_msg = ""
        if log_result.get("success"):
            log_msg = f"\nReport saved: {log_result['report_path']}"
        else:
            log_msg = f"\nWarning: Could not save report: {log_result.get('error')}"

        # Build receipt HTML
        from datetime import datetime
        dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        store_block = f"<b>{STORE_NAME}</b><br>{STORE_ADDRESS}<br>Tel: {CONTACT_NUMBER}<br>"
        invoice_block = f"<b>Invoice:</b> {invoice or '-'}<br><b>Date:</b> {dt_str}<br><b>Cashier:</b> {metadata.get('cashier_name') or '-'}<br><b>Payment:</b> {metadata.get('payment_method')}<br><br>"

        items_html = ""
        for pid, item in receipt['items'].items():
            prod = item['product']
            name = prod.get('name')
            code = prod.get('code') or '-'
            color = prod.get('color') or ''
            size = prod.get('size') or ''
            qty = item['quantity']
            price = item['price']
            line = qty * price
            items_html += f"{name} - {color} - {size} <br>Code: {code} &nbsp; Qty: {qty} &nbsp; @ ${price:.2f} &nbsp; = ${line:.2f}<br><br>"

        subtotal = totals['subtotal']
        tax = totals['tax']
        total = totals['total']
        amount_paid = metadata.get('amount_paid')
        change_display = metadata.get('change')

        tax_note = "Termasuk PPN 12%" if TAX_INCLUSIVE else "PPN 12%"

        # Build centered receipt HTML (do not include internal report path)
        receipt_html = f"""
        <div style="text-align:center; font-family: Arial, Helvetica, sans-serif;">
          <div style="font-weight:700; font-size:16px;">{STORE_NAME}</div>
          <div>{STORE_ADDRESS}</div>
          <div>Tel: {CONTACT_NUMBER}</div>
          <hr>
          <div><b>Invoice:</b> {invoice or '-'}</div>
          <div><b>Date:</b> {dt_str}</div>
          <div><b>Cashier:</b> {metadata.get('cashier_name') or '-'}</div>
          <div><b>Payment:</b> {metadata.get('payment_method')}</div>
          <hr>
          <div style="text-align:left; display:inline-block; width:90%;">
            <b>Items:</b><br>
            {items_html}
            <hr>
            Subtotal: ${subtotal:.2f}<br>
            Discounts: $0.00<br>
            {tax_note}: ${tax:.2f}<br>
            <b>Grand Total: ${total:.2f}</b><br>
            Payment Method: {metadata.get('payment_method')}<br>
            Bayar: ${amount_paid:.2f}<br>
            Kembali: ${change_display:.2f}<br>
          </div>
        </div>
        """
        dlg = ReceiptDialog(receipt_html, parent=self)
        dlg.exec()

        # Reset display
        self.cart_manager.clear_cart()
        self.update_cart_display()
        self.update_totals()
        self.details_text.setText("Cart cleared. Ready for next customer.")
        self.code_input.clear()
        self.code_input.setFocus()


class PaymentDialog(QDialog):
    """Dialog to collect payment information before checkout."""
    def __init__(self, parent=None, total_amount=0.0):
        super().__init__(parent)
        self.setWindowTitle("Payment")
        self.total_amount = total_amount
        self.result_data = None
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()

        self.cashier_input = QLineEdit()
        layout.addRow("Cashier Name:", self.cashier_input)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "QRIS", "Debit", "Credit Card"])
        layout.addRow("Payment Method:", self.payment_method)

        self.amount_paid = QDoubleSpinBox()
        self.amount_paid.setMinimum(0.0)
        self.amount_paid.setMaximum(9999999.99)
        self.amount_paid.setValue(self.total_amount)
        self.amount_paid.setSingleStep(1000)
        layout.addRow("Amount Paid:", self.amount_paid)

        btn_layout = QHBoxLayout()
        ok = QPushButton("OK")
        ok.clicked.connect(self.on_ok)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(ok)
        btn_layout.addWidget(cancel)
        layout.addRow(btn_layout)

        self.setLayout(layout)

    def on_ok(self):
        amount = self.amount_paid.value()
        if amount < self.total_amount:
            QMessageBox.warning(self, "Payment Error", "Amount paid is less than total amount.")
            return
        self.result_data = {
            "cashier_name": self.cashier_input.text().strip() or None,
            "payment_method": self.payment_method.currentText(),
            "amount_paid": amount
        }
        self.accept()


class ReceiptDialog(QDialog):
    """Displays receipt and provides Print button placeholder."""
    def __init__(self, receipt_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Receipt")
        self.resize(500, 600)
        layout = QVBoxLayout()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setHtml(receipt_html)
        layout.addWidget(self.text)
        btn_layout = QHBoxLayout()
        self.print_btn = QPushButton("Print")
        # Placeholder: connect to future print integration
        self.print_btn.clicked.connect(self.on_print)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.print_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def on_print(self):
        QMessageBox.information(self, "Print", "Print integration placeholder.")
    

# Optional: for standalone testing
if __name__ == "__main__":
    app = QApplication([])
    window = CashierWindow()
    window.show()
    app.exec()
