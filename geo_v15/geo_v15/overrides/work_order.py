import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import get_available_materials
from collections import defaultdict
from erpnext.stock.doctype.stock_entry.stock_entry import get_available_materials

@frappe.whitelist()
def make_stock_return_entry(work_order):
	from erpnext.stock.doctype.stock_entry.stock_entry import get_available_materials

	non_consumed_items = get_available_materials(work_order)
	if not non_consumed_items:
		return

	wo_doc = frappe.get_cached_doc("Work Order", work_order)

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.from_bom = 1
	stock_entry.is_return = 1
	stock_entry.work_order = work_order
	stock_entry.purpose = "Material Transfer for Manufacture"
	stock_entry.bom_no = wo_doc.bom_no
	stock_entry.add_transfered_raw_materials_in_items()
	stock_entry.set_stock_entry_type()

	# frappe.log_error("stock_entry", stock_entry)
	return stock_entry