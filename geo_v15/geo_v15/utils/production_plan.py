import frappe
import json
from frappe.utils.csvutils import build_csv_response


@frappe.whitelist()
def download_raw_items(doc):
	if isinstance(doc, str):
		doc = frappe._dict(json.loads(doc))

	item_list = [
		[
			"Item Code",
			"Warehouse",
			"Type",
			"Available Qty",
			"Qty As Per BOM",
			"Plan to request Qty",
		]
	]

	items = doc.mr_items

	for d in items:
		item_list.append(
			[
				d.get("item_code"),
				d.get("warehouse"),
				d.get("material_request_type"),
				d.get("actual_qty"),
				d.get("required_bom_qty"),
				d.get("quantity")
			]
		)

	build_csv_response(item_list, doc.name)
