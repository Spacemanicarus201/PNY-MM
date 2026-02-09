# database/reports.py
import json
from pathlib import Path
from datetime import datetime
from config import STORE_NAME, STORE_ADDRESS, CONTACT_NUMBER, TAX_RATE, TAX_INCLUSIVE
import csv

# Reports folder path
REPORTS_FOLDER = Path(__file__).parent.parent / "reports"
REPORTS_FOLDER.mkdir(exist_ok=True)

def get_today_report_path():
    """Get the file path for today's sales report."""
    today = datetime.now().strftime("%Y-%m-%d")
    return REPORTS_FOLDER / f"sales_{today}.json"

def log_sale(receipt_data, metadata=None):
    """Log a sale to today's daily report.

    `metadata` may include: cashier_name, payment_method, amount_paid, change, invoice_number
    If `invoice_number` is not provided, one is generated: INV/YYYYMMDD/NNN
    """
    try:
        report_path = get_today_report_path()

        # Create or load existing report
        if report_path.exists():
            with open(report_path, 'r') as f:
                report = json.load(f)
        else:
            report = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "store": {
                    "name": STORE_NAME,
                    "address": STORE_ADDRESS,
                    "contact": CONTACT_NUMBER,
                    "tax_rate": TAX_RATE,
                    "tax_inclusive": TAX_INCLUSIVE
                },
                "sales": [],
                "summary": {
                    "total_sales": 0,
                    "total_tax": 0,
                    "total_revenue": 0,
                    "total_units_sold": 0,
                    "transaction_count": 0
                }
            }

        # Transaction sequence id
        txn_id = len(report["sales"]) + 1

        # Generate invoice number if not provided
        today_code = datetime.now().strftime("%Y%m%d")
        invoice_number = None
        if metadata and metadata.get("invoice_number"):
            invoice_number = metadata.get("invoice_number")
        else:
            invoice_number = f"INV/{today_code}/{str(txn_id).zfill(3)}"

        # Build sale entry
        sale_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "transaction_id": txn_id,
            "invoice_number": invoice_number,
            "cashier": (metadata.get("cashier_name") if metadata else None),
            "payment_method": (metadata.get("payment_method") if metadata else None),
            "amount_paid": (metadata.get("amount_paid") if metadata else None),
            "change": (metadata.get("change") if metadata else None),
            "items": [],
            "subtotal": receipt_data["totals"]["subtotal"],
            "tax": receipt_data["totals"]["tax"],
            "total": receipt_data["totals"]["total"]
        }

        # Extract items from receipt
        for product_id, item in receipt_data["items"].items():
            product = item["product"]
            sale_entry["items"].append({
                "product_id": product_id,
                "product_name": product["name"],
                "code": product.get("code"),
                "color": product.get("color"),
                "size": product.get("size"),
                "quantity": item["quantity"],
                "unit_price": item["price"],
                "line_total": item["quantity"] * item["price"]
            })

        # Add to report
        report["sales"].append(sale_entry)

        # Update summary
        report["summary"]["total_sales"] += receipt_data["totals"]["subtotal"]
        report["summary"]["total_tax"] += receipt_data["totals"]["tax"]
        report["summary"]["total_revenue"] += receipt_data["totals"]["total"]
        report["summary"]["total_units_sold"] += receipt_data["totals"]["unit_count"]
        report["summary"]["transaction_count"] += 1

        # Save report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Also export CSV for today's report
        try:
            export_daily_csv()
        except Exception:
            # Non-fatal: continue even if CSV export fails
            pass

        return {"success": True, "report_path": str(report_path), "invoice_number": invoice_number}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_daily_report(date=None):
    """Retrieve a daily sales report."""
    try:
        if date is None:
            report_path = get_today_report_path()
        else:
            report_path = REPORTS_FOLDER / f"sales_{date}.json"
        
        if not report_path.exists():
            return {"success": False, "error": f"No report found for {date or 'today'}"}
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        return {"success": True, "report": report}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_stock_changes_for_date(date=None):
    """Get a summary of stock changes from sales on a given date."""
    try:
        result = get_daily_report(date)
        if not result["success"]:
            return result
        
        report = result["report"]
        stock_changes = {}
        
        for sale in report["sales"]:
            for item in sale["items"]:
                product_id = item["product_id"]
                if product_id not in stock_changes:
                    stock_changes[product_id] = {
                        "product_name": item["product_name"],
                        "quantity_sold": 0,
                        "revenue": 0.0
                    }
                
                stock_changes[product_id]["quantity_sold"] += item["quantity"]
                stock_changes[product_id]["revenue"] += item["line_total"]
        
        return {"success": True, "stock_changes": stock_changes, "date": report["date"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def export_daily_csv(date=None):
    """Export the daily JSON report to a CSV file.

    Each CSV row corresponds to one sold item with transaction metadata.
    """
    try:
        # Load report
        if date is None:
            report_path = get_today_report_path()
            csv_name = report_path.with_suffix('.csv')
        else:
            report_path = REPORTS_FOLDER / f"sales_{date}.json"
            csv_name = REPORTS_FOLDER / f"sales_{date}.csv"

        if not report_path.exists():
            return {"success": False, "error": f"No report found for {date or 'today'}"}

        with open(report_path, 'r') as f:
            report = json.load(f)

        # CSV header
        header = [
            'invoice_number', 'timestamp', 'transaction_id', 'cashier', 'payment_method',
            'product_id', 'product_name', 'code', 'color', 'size', 'quantity', 'unit_price', 'line_total',
            'subtotal', 'tax', 'total', 'amount_paid', 'change'
        ]

        with open(csv_name, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()

            for sale in report.get('sales', []):
                for item in sale.get('items', []):
                    row = {
                        'invoice_number': sale.get('invoice_number'),
                        'timestamp': sale.get('timestamp'),
                        'transaction_id': sale.get('transaction_id'),
                        'cashier': sale.get('cashier'),
                        'payment_method': sale.get('payment_method'),
                        'product_id': item.get('product_id'),
                        'product_name': item.get('product_name'),
                        'code': item.get('code'),
                        'color': item.get('color'),
                        'size': item.get('size'),
                        'quantity': item.get('quantity'),
                        'unit_price': item.get('unit_price'),
                        'line_total': item.get('line_total'),
                        'subtotal': sale.get('subtotal'),
                        'tax': sale.get('tax'),
                        'total': sale.get('total'),
                        'amount_paid': sale.get('amount_paid'),
                        'change': sale.get('change')
                    }
                    writer.writerow(row)

        return {"success": True, "csv_path": str(csv_name)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_report_text(date=None):
    """Generate a formatted text report for printing or viewing."""
    try:
        result = get_daily_report(date)
        if not result["success"]:
            return result["error"]
        
        report = result["report"]
        summary = report["summary"]
        store = report.get("store", {})
        store_block = ""
        if store:
            store_block = f"{store.get('name','')}\n{store.get('address','')}\nTel: {store.get('contact','')}\nTax: {int(store.get('tax_rate',0)*100)}% {'(Included)' if store.get('tax_inclusive') else ''}\n\n"

        text = f"""
{'=' * 60}
DAILY SALES REPORT
Date: {report['date']}
{'=' * 60}

{store_block}
TRANSACTION DETAILS:
"""
        
        for idx, sale in enumerate(report["sales"], 1):
            text += f"\nTransaction #{sale['transaction_id']} - {sale['timestamp']}\n"
            text += f"Invoice: {sale.get('invoice_number','-')}\n"
            text += f"Cashier: {sale.get('cashier','-')}    Payment: {sale.get('payment_method','-')}\n"
            text += "-" * 60 + "\n"
            
            for item in sale["items"]:
                text += f"  {item['product_name']} ({item.get('code','-')})\n"
                text += f"    Color: {item.get('color','')}, Size: {item.get('size','')}\n"
                text += f"    Qty: {item['quantity']} @ ${item['unit_price']:.2f} = ${item['line_total']:.2f}\n"
            
            text += f"  Subtotal: ${sale['subtotal']:.2f}\n"
            text += f"  Tax:      ${sale['tax']:.2f}\n"
            text += f"  Total:    ${sale['total']:.2f}\n"
            text += f"  Bayar:    ${sale.get('amount_paid',0):.2f}    Kembali: ${sale.get('change',0):.2f}\n"
        
        # Summary section
        text += f"""
{'=' * 60}
DAILY SUMMARY
{'=' * 60}
Total Transactions: {summary['transaction_count']}
Total Units Sold:  {summary['total_units_sold']}
Total Sales:       ${summary['total_sales']:.2f}
Total Tax:         ${summary['total_tax']:.2f}
Total Revenue:     ${summary['total_revenue']:.2f}
{'=' * 60}
"""
        
        return text
    except Exception as e:
        return f"Error generating report: {str(e)}"
