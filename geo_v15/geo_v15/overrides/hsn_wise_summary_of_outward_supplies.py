import frappe
from frappe import _
from india_compliance.gst_india.report.hsn_wise_summary_of_outward_supplies.hsn_wise_summary_of_outward_supplies import get_conditions


def get_items(filters):
    conditions = get_conditions(filters)
    match_conditions = frappe.build_match_conditions("Sales Invoice")
    if match_conditions:
        conditions += f" and {match_conditions} "

    if filters.get("branch"):
        conditions += f" and `tabSales Invoice`.branch = %(branch)s"

    items = frappe.db.sql(
        f"""
        SELECT
            COALESCE(`tabSales Invoice Item`.gst_hsn_code, '') AS gst_hsn_code,
            `tabSales Invoice Item`.stock_uom as uqc,
            sum(`tabSales Invoice Item`.stock_qty) AS stock_qty,
            sum(`tabSales Invoice Item`.taxable_value) AS taxable_value,
            `tabSales Invoice Item`.parent,
            `tabSales Invoice Item`.item_code,
            `tabSales Invoice Item`.item_name,
            COALESCE(`tabGST HSN Code`.description, 'NA') AS description
        FROM
            `tabSales Invoice`
            INNER JOIN `tabSales Invoice Item` ON `tabSales Invoice`.name = `tabSales Invoice Item`.parent
            LEFT JOIN `tabGST HSN Code` ON `tabSales Invoice Item`.gst_hsn_code = `tabGST HSN Code`.name
        WHERE
            `tabSales Invoice`.docstatus = 1
            AND `tabSales Invoice`.is_opening != 'Yes'
            AND `tabSales Invoice`.company_gstin != IFNULL(`tabSales Invoice`.billing_address_gstin, '') {conditions}
        GROUP BY
            `tabSales Invoice Item`.parent,
            `tabSales Invoice Item`.item_code
        """,
        filters,
        as_dict=1,
    )

    return items