# reports/ui.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTextEdit, QApplication, QDateEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from database.reports import generate_report_text, get_daily_report, get_stock_changes_for_date, export_daily_csv
from datetime import datetime

class ReportsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sales Reports")
        self.setGeometry(100, 100, 1000, 600)
        
        self.init_ui()
        self.load_today_report()
    
    def init_ui(self):
        """Initialize the reports UI."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Daily Sales Reports")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title)
        
        # Date selection
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Select Date:"))
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_edit)
        
        load_btn = QPushButton("Load Report")
        load_btn.clicked.connect(self.load_report_by_date)
        date_layout.addWidget(load_btn)
        
        today_btn = QPushButton("Today")
        today_btn.clicked.connect(self.load_today_report)
        date_layout.addWidget(today_btn)
        
        date_layout.addStretch()
        main_layout.addLayout(date_layout)
        
        # Report display
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet("font-family: Courier; font-size: 10px;")
        main_layout.addWidget(self.report_text)
        
        # Stock changes section
        stock_title = QLabel("Stock Changes Summary")
        stock_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        main_layout.addWidget(stock_title)
        
        self.stock_text = QTextEdit()
        self.stock_text.setReadOnly(True)
        self.stock_text.setStyleSheet("font-family: Courier; font-size: 10px;")
        self.stock_text.setMaximumHeight(200)
        main_layout.addWidget(self.stock_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_today_report)
        
        print_btn = QPushButton("Print/Save Report")
        print_btn.clicked.connect(self.save_report)

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(print_btn)
        button_layout.addWidget(export_csv_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        main_widget.setLayout(main_layout)
    
    def load_today_report(self):
        """Load today's report."""
        self.date_edit.setDate(QDate.currentDate())
        self.load_report_by_date()
    
    def load_report_by_date(self):
        """Load report for selected date."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        
        # Load full report
        report_text = generate_report_text(date_str)
        self.report_text.setText(report_text)
        
        # Load stock changes
        result = get_stock_changes_for_date(date_str)
        if result["success"]:
            changes = result["stock_changes"]
            if not changes:
                stock_text = f"No sales recorded for {date_str}"
            else:
                stock_text = f"Stock Changes for {date_str}:\n" + "=" * 60 + "\n\n"
                for product_id, data in sorted(changes.items()):
                    stock_text += f"Product ID {product_id}: {data['product_name']}\n"
                    stock_text += f"  Units Sold: {data['quantity_sold']}\n"
                    stock_text += f"  Revenue: ${data['revenue']:.2f}\n\n"
        else:
            stock_text = f"No data available for {date_str}\n{result['error']}"
        
        self.stock_text.setText(stock_text)
    
    def save_report(self):
        """Save/print the report."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        report_text = self.report_text.toPlainText()
        
        try:
            # Save to file
            from pathlib import Path
            exports_folder = Path(__file__).parent.parent / "exports"
            exports_folder.mkdir(exist_ok=True)
            
            filename = exports_folder / f"report_{date_str}.txt"
            with open(filename, 'w') as f:
                f.write(report_text)
            
            QMessageBox.information(self, "Success", f"Report saved to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save report:\n{str(e)}")

    def export_csv(self):
        """Export the selected day's report to CSV."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        result = export_daily_csv(date_str)
        if result.get("success"):
            QMessageBox.information(self, "Exported", f"CSV exported to:\n{result['csv_path']}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to export CSV:\n{result.get('error')}")

# Optional: for standalone testing
if __name__ == "__main__":
    app = QApplication([])
    window = ReportsWindow()
    window.show()
    app.exec()
