import frappe
from frappe.utils import today

def validate_batch_stock(doc, method):
    if doc.update_stock:
        if doc.items:
            for item in doc.items:
                x = frappe.call(
                    "frappe.desk.query_report.run",
                    report_name="Batch-Wise Balance History",
                    filters={
                        "company": doc.company,
                        "from_date": today(),
                        "to_date": today(),
                        "item_code":item.item_code,
                        "warehouose": item.warehouse,
                        "batch_no": item.batch_no
                        },
                    ignore_prepared_report=True
                    )
                x["result"].pop()
                
                # if x and x.get("result"):
                #     balance_qty = x["result"][0].get("balance_qty")
                
                #     if balance_qty is not None and item.qty > balance_qty:
                #         frappe.throw(f'Insufficient stock for batch {item.batch_no}. Available: {balance_qty}, Required: {item.qty}')
                if len(x["result"]) > 0:
                    if item.qty > x["result"][0].get("balance_qty"):
                        frappe.throw(f'Stock Insufficient{x["result"][0].get("balance_qty")}')
