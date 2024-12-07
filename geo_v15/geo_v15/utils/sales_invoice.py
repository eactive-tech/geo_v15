import frappe
from frappe.utils import today

def validate_batch_stock(doc, method):
    if doc.update_stock:
        if doc.items:
            for item in doc.items:
                if item.batch_no:
                    x = frappe.call(
                        "frappe.desk.query_report.run",
                        report_name="Batch-Wise Balance History",
                        filters={
                            "company": doc.company,
                            "from_date": today(),
                            "to_date": today(),
                            "item_code":item.item_code,
                            "warehouse": item.warehouse,
                            "batch_no": item.batch_no
                            },
                        ignore_prepared_report=True
                        )
                    if x.get("result"):
                        x["result"].pop()                    

                        if item.qty > x["result"][0].get("balance_qty"):
                            frappe.throw(f'Stock Insufficient{x["result"][0].get("balance_qty")}')
