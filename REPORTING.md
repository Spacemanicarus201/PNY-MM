Reporting and CSV/JSON logging

Overview

- Daily sales reports are saved as JSON files in the `reports/` folder named `sales_YYYY-MM-DD.json`.
- A per-day CSV export is produced alongside the JSON as `sales_YYYY-MM-DD.csv`.
- Invoice numbering uses the format `INV/YYYYMMDD/NNN` where `NNN` is the transaction sequence for that day.

Where it's implemented

- `database/reports.py`
  - `log_sale(receipt_data, metadata=None)`: appends a sale entry to today's JSON report; accepts `metadata` with keys: `cashier_name`, `payment_method`, `amount_paid`, `change`, and optionally `invoice_number`.
  - `export_daily_csv(date=None)`: exports the day's JSON report to CSV; each CSV row is a sold item with transaction metadata.
  - `get_daily_report(date=None)`, `get_stock_changes_for_date(date=None)`, `generate_report_text(date=None)` provide retrieval and formatted text output.

- `cashier/ui.py`
  - Gathers payment metadata (cashier name, payment method, amount paid) and calls `log_sale()` after successful checkout.
  - The visible customer receipt (receipt dialog) is centered and does NOT display internal report file paths.

Formats

- JSON structure (high level):
  - `date`: "YYYY-MM-DD"
  - `store`: metadata (name, address, contact, tax settings)
  - `sales`: list of transactions; each transaction has `invoice_number`, `timestamp`, `transaction_id`, `cashier`, `payment_method`, `amount_paid`, `change`, `items` (list)
  - `summary`: aggregated totals for the day

- CSV columns produced by `export_daily_csv`:
  invoice_number, timestamp, transaction_id, cashier, payment_method,
  product_id, product_name, code, color, size, quantity, unit_price, line_total,
  subtotal, tax, total, amount_paid, change

Changing settings

- Store identity and tax settings are in `config.py`:
  - `STORE_NAME`, `STORE_ADDRESS`, `CONTACT_NUMBER`
  - `TAX_RATE` (e.g., 0.12 for 12%)
  - `TAX_INCLUSIVE` (True if prices include tax)

Notes & next steps

- The receipt dialog intentionally omits internal file paths (e.g., `Report saved: ...`).
- Print button is a placeholder; to integrate printing we can use Qt's printing APIs (QPrinter + QTextDocument.print). If you want this next, I can add a print implementation that prints the receipt HTML or exports to PDF.
- Let me know if you want different CSV columns or additional fields (e.g., SKU, category).