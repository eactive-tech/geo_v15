import copy

import frappe
from frappe import _
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.utils import add_days, add_months, format_date, getdate, today
from frappe.utils.jinja import validate_template
from frappe.utils.pdf import get_pdf
from frappe.www.printview import get_print_style

from erpnext import get_company_currency
from erpnext.accounts.party import get_party_account_currency
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
	execute as get_ageing,
)
from erpnext.accounts.report.general_ledger.general_ledger import execute as get_soa
import json


def get_report_pdf(doc, mcustomer=[], consolidated=True):

	statement_dict = {}
	ageing = ""
	base_template_path = "frappe/www/printview.html"
	template_path = (
		"geo_v15/templates/process_statement_of_accounts.html"
		)

	if doc.geo_is_confirmation_account == 1:
		template_path = (
		"geo_v15/templates/confirmation_of_accounts.html"
		)
	customers=[]
	if mcustomer:
		customers=json.loads(mcustomer)
		# frappe.log_error(type(customers),"Error 00001")

	else:
		customers=doc.customers

	# frappe.log_error(customers,"Error 00001")

	for entry in customers:
		# if entry:
			# frappe.log_error(entry.get('customer'),"Error 00002")
			# frappe.log_error(type(entry),"Error type")

		
		if doc.include_ageing:
			# frappe.log_error(entry,"Error 00")

			ageing_filters = frappe._dict(
				{
					"company": doc.company,
					"report_date": doc.to_date,
					"ageing_based_on": doc.ageing_based_on,
					"range1": 30,
					"range2": 60,
					"range3": 90,
					"range4": 120,
					"customer": entry.get('customer'),
				}
			)
			col1, ageing = get_ageing(ageing_filters)

			if ageing:
				ageing[0]["ageing_based_on"] = doc.ageing_based_on
		# frappe.log_error(entry.get('customer'),"Error 01")
		tax_id = frappe.get_doc("Customer", entry.get('customer')).tax_id
		presentation_currency = (
			get_party_account_currency("Customer", entry.get('customer'), doc.company)
			or doc.currency
			or get_company_currency(doc.company)
		)
		# frappe.log_error(entry.get('customer'),"Error 02")

		if doc.letter_head:
			from frappe.www.printview import get_letter_head

			letter_head = get_letter_head(doc, 0)

		filters = frappe._dict(
			{
				"from_date": doc.from_date,
				"to_date": doc.to_date,
				"geo_show_remarks": doc.geo_show_remarks,
				"geo_show_inventory": doc.geo_show_inventory,
				"geo_show_taxes": doc.geo_show_taxes,
				"company": doc.company,
				"finance_book": doc.finance_book if doc.finance_book else None,
				"account": [doc.account] if doc.account else None,
				"party_type": "Customer",
				"party": [entry.get('customer')],
				"presentation_currency": presentation_currency,
				"group_by": doc.group_by,
				"currency": doc.currency,
				"cost_center": [cc.cost_center_name for cc in doc.cost_center],
				"project": [p.project_name for p in doc.project],
				"show_opening_entries": 0,
				"include_default_book_entries": 0,
				"tax_id": tax_id if tax_id else None,
			}
		)

		col, res = get_soa(filters)

		for x in [0, -2, -1]:
			res[x]["account"] = res[x]["account"].replace("'", "")

		# if len(res) == 3:
		# 	continue
		# frappe.log_error(entry.get('customer'),"Error 03")
		frappe.log_error(message=res,title=f"Error gl {entry.get('customer')}")

		html = frappe.render_template(
			template_path,
			{
				"filters": filters,
				"data": res,
				"ageing": ageing[0] if (doc.include_ageing and ageing) else None,
				"letter_head": letter_head if doc.letter_head else None,
				"terms_and_conditions": frappe.db.get_value(
					"Terms and Conditions", doc.terms_and_conditions, "terms"
				)
				if doc.terms_and_conditions
				else None,
			},
		)
		frappe.log_error(message=statement_dict,title=f"Error html1 {entry.get('customer')}")

		html = frappe.render_template(
			base_template_path,
			{"body": html, "css": get_print_style(), "title": "Statement For " + entry.get('customer')},
		)
		statement_dict[entry.get('customer')] = html
		frappe.log_error(message=statement_dict,title=f"Error html {entry.get('customer')}")

	if not bool(statement_dict):
		return False
	elif consolidated:
		delimiter = '<div style="page-break-before: always;"></div>' if doc.include_break else ""
		result = delimiter.join(list(statement_dict.values()))
		return get_pdf(result, {"orientation": doc.orientation})
	else:
		frappe.log_error(message=entry.get('customer'),title="Error 05")

		for customer, statement_html in statement_dict.items():
			statement_dict[customer] = get_pdf(statement_html, {"orientation": doc.orientation})
		return statement_dict


@frappe.whitelist()
def download_statements(document_name, mcustomer):
	doc = frappe.get_doc("Process Statement Of Accounts", document_name)
	report = get_report_pdf(doc, mcustomer)
	doc_name_pdf=document_name
	if mcustomer:
		md = json.loads(mcustomer)
		doc_name_pdf=f"{md[0].get('customer_name')}-{md[0].get('customer')}"
	if report:
		frappe.local.response.filename = doc_name_pdf + ".pdf"
		frappe.local.response.filecontent = report
		frappe.local.response.type = "download"
		return

@frappe.whitelist()
def download_statements_pdf(args):
	doc = frappe.get_doc("Process Statement Of Accounts", args.document_name)
	report = get_report_pdf(doc, args.customer)
	if report:
		frappe.local.response.filename = doc.name + ".pdf"
		frappe.local.response.filecontent = report
		frappe.local.response.type = "download"

