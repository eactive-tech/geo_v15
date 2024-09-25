import frappe
from india_compliance.gst_india.report.hsn_wise_summary_of_outward_supplies.hsn_wise_summary_of_outward_supplies import validate_filters, get_columns, get_hsn_data



def execute(filters=None):
    if not filters:
        filters = {}

    validate_filters(filters)

    columns = get_columns(filters)

    columns.append({
        "fieldtype": "Link",
        "fieldname": "branch",
        "label": "Branch"
    })


    data = get_hsn_data(filters, columns)

    return columns, data
