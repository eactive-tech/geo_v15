app_name = "geo_v15"
app_title = "geo_v15"
app_publisher = "eactive"
app_description = "geo_v15"
app_email = "laxman@eactive.in"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/geo_v15/css/geo_v15.css"
# app_include_js = "/assets/geo_v15/js/geo_v15.js"

# include js, css files in header of web template
# web_include_css = "/assets/geo_v15/css/geo_v15.css"
# web_include_js = "/assets/geo_v15/js/geo_v15.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "geo_v15/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Process Statement Of Accounts" : "public/js/process_statement_of_accounts.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "geo_v15/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "geo_v15.utils.jinja_methods",
# 	"filters": "geo_v15.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "geo_v15.install.before_install"
# after_install = "geo_v15.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "geo_v15.uninstall.before_uninstall"
# after_uninstall = "geo_v15.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "geo_v15.utils.before_app_install"
# after_app_install = "geo_v15.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "geo_v15.utils.before_app_uninstall"
# after_app_uninstall = "geo_v15.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "geo_v15.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"geo_v15.tasks.all"
# 	],
# 	"daily": [
# 		"geo_v15.tasks.daily"
# 	],
# 	"hourly": [
# 		"geo_v15.tasks.hourly"
# 	],
# 	"weekly": [
# 		"geo_v15.tasks.weekly"
# 	],
# 	"monthly": [
# 		"geo_v15.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "geo_v15.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "geo_v15.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "geo_v15.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["geo_v15.utils.before_request"]
# after_request = ["geo_v15.utils.after_request"]

# Job Events
# ----------
# before_job = ["geo_v15.utils.before_job"]
# after_job = ["geo_v15.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"geo_v15.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

doc_events = {
	"Sales Invoice": {
		"before_save": "geo_v15.geo_v15.utils.sales_invoice.validate_batch_stock"
	}
}

override_doctype_class = {
	"PaymentReconciliation": "geo_v15.overrides.CustomPaymentReconciliation",
    "Production Plan": "geo_v15.geo_v15.overrides.production_plan.CustomProductionPlan"
    # "Work Order": "geo_v15.geo_v15.overrides.work_order.CustomWorkOrder"
}

app_include_js = [
    "/assets/geo_v15/js/gstr_1.js",
    "/assets/geo_v15/js/hsn_wise_summary_of_outward_supplies.js",
    "/assets/geo_v15/js/trial_balance.js",
    "/assets/geo_v15/js/item_wise_sales_register.js",
    "/assets/geo_v15/js/item_wise_purchase_register.js",
    "/assets/geo_v15/js/purchase_register.js",
]

# override gstr1 report 
from india_compliance.gst_india.report.gstr_1.gstr_1 import Gstr1Report
from geo_v15.geo_v15.overrides.gstr_1 import get_invoice_data, get_columns
Gstr1Report.get_invoice_data = get_invoice_data
Gstr1Report.get_columns = get_columns

# override hsnwise summary report
from india_compliance.gst_india.report.hsn_wise_summary_of_outward_supplies import hsn_wise_summary_of_outward_supplies
from geo_v15.geo_v15.overrides.hsn_wise_summary_of_outward_supplies import get_items as hsn_get_items
hsn_wise_summary_of_outward_supplies.get_items = hsn_get_items

# override process statement of accounts
from erpnext.accounts.doctype.process_statement_of_accounts import process_statement_of_accounts
from geo_v15.geo_v15.overrides.process_statement_of_accounts import get_report_pdf, download_statements_pdf
process_statement_of_accounts.get_report_pdf = get_report_pdf
process_statement_of_accounts.download_statements_pdf = download_statements_pdf

# override Trial balance report
from erpnext.accounts.report.trial_balance import trial_balance
from geo_v15.geo_v15.overrides.trial_balance import execute
trial_balance.execute = execute

# override general ledger report
from erpnext.accounts.report.item_wise_sales_register import item_wise_sales_register
from geo_v15.geo_v15.overrides.item_wise_sales_register import get_columns as sales_register_columns, apply_conditions, get_items
item_wise_sales_register.get_columns = sales_register_columns
item_wise_sales_register.apply_conditions = apply_conditions
item_wise_sales_register.get_items = get_items


#general ledger
from erpnext.accounts.report.general_ledger import general_ledger
from geo_v15.geo_v15.overrides.general_ledger import (
    execute as gl_execute,
    get_gl_entries as gl_get_gl_entries,
    get_conditions as gl_get_conditions,
    get_accountwise_gle as gl_get_accountwise_gle,
    get_result_as_list as gl_get_result_as_list,
    get_columns as gl_get_columns
    )

general_ledger.execute = gl_execute
general_ledger.get_gl_entries = gl_get_gl_entries
general_ledger.get_conditions = gl_get_conditions
general_ledger.get_accountwise_gle = gl_get_accountwise_gle
general_ledger.get_result_as_list = gl_get_result_as_list
general_ledger.get_columns = gl_get_columns


# Procurement tracker
from erpnext.buying.report.procurement_tracker import procurement_tracker
from geo_v15.geo_v15.overrides.procurement_tracker import (
    get_columns as pt_get_columns,
    get_mapped_mr_details as pt_get_mapped_mr_details,
    get_data as pt_get_data,
    get_po_entries as pt_get_po_entries
    )
procurement_tracker.get_columns = pt_get_columns
procurement_tracker.get_data = pt_get_data
procurement_tracker.get_mapped_mr_details = pt_get_mapped_mr_details
procurement_tracker.get_po_entries = pt_get_po_entries

#for Item Wise Purchase Register
from erpnext.accounts.report.item_wise_purchase_register import item_wise_purchase_register
from geo_v15.geo_v15.overrides.item_wise_purchase_registere import (
    _execute as iwpr__execute,
    get_columns as iwpr_get_columns,
    get_items as iwpr_get_items
) 
item_wise_purchase_register._execute = iwpr__execute
item_wise_purchase_register.get_columns = iwpr_get_columns
item_wise_purchase_register.get_items = iwpr_get_items


# for Purchase Register
from erpnext.accounts.report.purchase_register import purchase_register
from geo_v15.geo_v15.overrides.purchase_register import (
    _execute as pr_execute,
    get_columns as pr_get_columns,
    get_invoices as pr_get_invoices
)
purchase_register._execute = pr_execute
purchase_register.get_columns = pr_get_columns
purchase_register.get_invoices = pr_get_invoices


# For Payroll Entry
from hrms.payroll.doctype.payroll_entry import payroll_entry
from geo_v15.geo_v15.overrides.payroll_entry import submit_salary_slips_for_employees
payroll_entry.submit_salary_slips_for_employees = submit_salary_slips_for_employees


# For Asset Depreciation auto JV
from erpnext.assets.doctype.asset import depreciation
from geo_v15.geo_v15.overrides.asset_depreciation import _make_journal_entry_for_depreciation as asset_make_journal_entry_for_depreciation
depreciation._make_journal_entry_for_depreciation = asset_make_journal_entry_for_depreciation

# For stock entry
from erpnext.stock.doctype.stock_entry import stock_entry
from geo_v15.geo_v15.overrides.stock_entry import add_transfered_raw_materials_in_items
stock_entry.add_transfered_raw_materials_in_items = add_transfered_raw_materials_in_items

# For Work Order
from erpnext.manufacturing.doctype.work_order import work_order
from geo_v15.geo_v15.overrides.work_order import make_stock_return_entry
work_order.make_stock_return_entry = make_stock_return_entry


# For Monthly Attendance Sheet
from hrms.hr.report.monthly_attendance_sheet import monthly_attendance_sheet
from geo_v15.geo_v15.overrides.monthly_attendance_sheet import get_attendance_records
monthly_attendance_sheet.get_attendance_records = get_attendance_records