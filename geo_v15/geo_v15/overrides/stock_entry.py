from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import (
	cint,
	flt,
)

def add_transfered_raw_materials_in_items(stock_entry, items) -> None:
    wo_data = frappe.db.get_value(
        "Work Order",
        stock_entry.work_order,
        ["qty", "produced_qty", "material_transferred_for_manufacturing as trans_qty"],
        as_dict=1,
    )

    precision = frappe.get_precision("Stock Entry Detail", "qty")
    for row in items:
        frappe.log_error("row", row)
        remaining_qty_to_produce = flt(wo_data.trans_qty) - flt(wo_data.produced_qty)
        if remaining_qty_to_produce <= 0 and not stock_entry.is_return:
            continue

        qty = flt(row.qty)
        if not stock_entry.is_return:
            qty = (flt(row.qty) * flt(stock_entry.fg_completed_qty)) / remaining_qty_to_produce

        item = row.item_details
        if cint(frappe.get_cached_value("UOM", item.stock_uom, "must_be_whole_number")):
            qty = frappe.utils.ceil(qty)

        if row.batch_details:
            row.batches_to_be_consume = defaultdict(float)
            batches = row.batch_details
            stock_entry.update_batches_to_be_consume(batches, row, qty)

        elif row.serial_nos:
            serial_nos = row.serial_nos[0 : cint(qty)]
            row.serial_nos = serial_nos

        if flt(qty, precision) != 0.0:
            stock_entry.update_item_in_stock_entry_detail(row, item, qty)