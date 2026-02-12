# main.py
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from cashier.ui import CashierWindow      # from cashier folder
from database.stock import StockWindow     # from database folder
from data_entry.ui import DataEntryWindow # from data_entry folder
from reports.ui import ReportsWindow       # from reports folder


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher")
        self.setFixedSize(300, 250)

        layout = QVBoxLayout()

        btn_cashier = QPushButton("Cashier")
        btn_cashier.clicked.connect(self.open_cashier)
        layout.addWidget(btn_cashier)

        btn_stock = QPushButton("Stock / Restock")
        btn_stock.clicked.connect(self.open_stock)
        layout.addWidget(btn_stock)

        btn_data = QPushButton("Data Entry")
        btn_data.clicked.connect(self.open_data_entry)
        layout.addWidget(btn_data)

        btn_reports = QPushButton("Sales Reports")
        btn_reports.clicked.connect(self.open_reports)
        layout.addWidget(btn_reports)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_cashier(self):
        self.cashier_window = CashierWindow()
        self.cashier_window.show()

    def open_stock(self):
        self.stock_window = StockWindow()
        self.stock_window.show()

    def open_data_entry(self):
        self.data_window = DataEntryWindow()
        self.data_window.show()

    def open_reports(self):
        self.reports_window = ReportsWindow()
        self.reports_window.show()

if __name__ == "__main__":
    app = QApplication([])
    launcher = Launcher()
    launcher.show()
    app.exec()
