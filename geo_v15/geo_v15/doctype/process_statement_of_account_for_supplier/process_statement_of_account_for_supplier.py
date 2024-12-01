# Copyright (c) 2024, eactive and contributors
# For license information, please see license.txt

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



class ProcessStatementofaccountforsupplier(Document):
	def validate(self):
		if not self.subject:
			self.subject = "Statement Of Accounts for {{ supplier.name }}"
		if not self.body:
			self.body = "Hello {{ supplier.name }},<br>PFA your Statement Of Accounts from {{ doc.from_date }} to {{ doc.to_date }}."

		validate_template(self.subject)
		validate_template(self.body)

		if not self.suppliers:
			frappe.throw(_("Suppliers not selected."))

		if self.enable_auto_email:
			if self.start_date and getdate(self.start_date) >= getdate(today()):
				self.to_date = self.start_date
				self.from_date = add_months(self.to_date, -1 * self.filter_duration)


def get_report_pdf(doc, consolidated=True):
	statement_dict = {}
	ageing = ""
	base_template_path = "frappe/www/printview.html"
	template_path = (
		# "erpnext/accounts/doctype/process_statement_of_account_for_supplier/confirmation_of_accounts.html"
		"geo_v15/templates/general_ledger.html"
		)

	if doc.geo_is_confirmation_account == 1:
		template_path = (
		# "erpnext/accounts/doctype/process_statement_of_account_for_supplier/confirmation_of_accounts.html"
		"geo_v15/doctype/process_statement_of_account_for_supplier/confirmation_of_accounts.html"
		)


	for entry in doc.suppliers:
		if doc.include_ageing:
			ageing_filters = frappe._dict(
				{
					"company": doc.company,
					"report_date": doc.to_date,
					"ageing_based_on": doc.ageing_based_on,
					"range1": 30,
					"range2": 60,
					"range3": 90,
					"range4": 120,
					"supplier": entry.supplier,
				}
			)
			col1, ageing = get_ageing(ageing_filters)

			if ageing:
				ageing[0]["ageing_based_on"] = doc.ageing_based_on

		tax_id = frappe.get_doc("Supplier", entry.supplier).tax_id
		presentation_currency = (
			get_party_account_currency("Supplier", entry.supplier, doc.company)
			or doc.currency
			or get_company_currency(doc.company)
		)
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
				"party_type": "Supplier",
				"party": [entry.supplier],
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

		if len(res) == 3:
			continue

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

		html = frappe.render_template(
			base_template_path,
			{"body": html, "css": get_print_style(), "title": "Statement For " + entry.supplier},
		)
		statement_dict[entry.supplier] = html

	if not bool(statement_dict):
		return False
	elif consolidated:
		delimiter = '<div style="page-break-before: always;"></div>' if doc.include_break else ""
		result = delimiter.join(list(statement_dict.values()))
		return get_pdf(result, {"orientation": doc.orientation})
	else:
		for supplier, statement_html in statement_dict.items():
			statement_dict[supplier] = get_pdf(statement_html, {"orientation": doc.orientation})
		return statement_dict


def get_recipients_and_cc(supplier, doc):
	recipients = []
	for clist in doc.suppliers:
		if clist.supplier == supplier:
			recipients.append(clist.billing_email)
			if doc.primary_mandatory and clist.primary_email:
				recipients.append(clist.primary_email)
	cc = []
	if doc.cc_to != "":
		try:
			cc = [frappe.get_value("User", doc.cc_to, "email")]
		except Exception:
			pass

	return recipients, cc


def get_context(supplier, doc):
	template_doc = copy.deepcopy(doc)
	del template_doc.suppliers
	template_doc.from_date = format_date(template_doc.from_date)
	template_doc.to_date = format_date(template_doc.to_date)
	return {
		"doc": template_doc,
		"supplier": frappe.get_doc("Supplier", supplier),
		"frappe": frappe.utils,
	}



@frappe.whitelist()
def fetch_suppliers(supplier_group, supplier_name, primary_mandatory):
	supplier_list = []
	suppliers = []
	if supplier_name :
		suppliers = frappe.get_list(
			"Supplier",
			fields=["name", "email_id"],
			filters={"supplier_group":supplier_group,"supplier_name":supplier_name})
	else :
		suppliers = frappe.get_list(
			"Supplier",
			fields=["name", "email_id"],
			filters={"supplier_group":supplier_group})

	for supplier in suppliers:
		primary_email = supplier.get("email_id") or ""
		billing_email = ''

		if int(primary_mandatory):
			if primary_email == "":
				continue

		supplier_list.append(
			{"name": supplier.name, "primary_email": primary_email, "billing_email": billing_email}
		)
	return suppliers



# @frappe.whitelist()
# def get_customer_emails(supplier_name, primary_mandatory, billing_and_primary=True):
# 	"""Returns first email from Contact Email table as a Billing email
# 	when Is Billing Contact checked
# 	and Primary email- email with Is Primary checked"""

# 	billing_email = frappe.db.sql(
# 		"""
# 		SELECT
# 			email.email_id
# 		FROM
# 			`tabContact Email` AS email
# 		JOIN
# 			`tabDynamic Link` AS link
# 		ON
# 			email.parent=link.parent
# 		JOIN
# 			`tabContact` AS contact
# 		ON
# 			contact.name=link.parent
# 		WHERE
# 			link.link_doctype='Customer'
# 			and link.link_name=%s
# 			and contact.is_billing_contact=1
# 			{mcond}
# 		ORDER BY
# 			contact.creation desc
# 		""".format(
# 			mcond=get_match_cond("Contact")
# 		),
# 		customer_name,
# 	)

# 	if len(billing_email) == 0 or (billing_email[0][0] is None):
# 		if billing_and_primary:
# 			frappe.throw(_("No billing email found for supplier: {0}").format(customer_name))
# 		else:
# 			return ""

# 	if billing_and_primary:
# 		primary_email = frappe.get_value("Supplier", customer_name, "email_id")
# 		if primary_email is None and int(primary_mandatory):
# 			frappe.throw(_("No primary email found for customer: {0}").format(customer_name))
# 		return [primary_email or "", billing_email[0][0]]
# 	else:
# 		return billing_email[0][0] or ""


@frappe.whitelist()
def download_statements(document_name):
	doc = frappe.get_doc("Process Statement of account for supplier", document_name)
	report = get_report_pdf(doc)
	if report:
		frappe.local.response.filename = doc.name + ".pdf"
		frappe.local.response.filecontent = report
		frappe.local.response.type = "download"


@frappe.whitelist()
def send_emails(document_name, from_scheduler=False):
	doc = frappe.get_doc("Process Statement of account for supplier", document_name)
	report = get_report_pdf(doc, consolidated=False)

	if report:
		for supplier, report_pdf in report.items():
			attachments = [{"fname": supplier + ".pdf", "fcontent": report_pdf}]

			recipients, cc = get_recipients_and_cc(supplier, doc)
			if not recipients:
				continue
			context = get_context(supplier, doc)
			subject = frappe.render_template(doc.subject, context)
			message = frappe.render_template(doc.body, context)

			frappe.enqueue(
				queue="short",
				method=frappe.sendmail,
				recipients=recipients,
				sender=frappe.session.user,
				cc=cc,
				subject=subject,
				message=message,
				now=True,
				reference_doctype="Process Statement of account for supplier",
				reference_name=document_name,
				attachments=attachments,
			)

		if doc.enable_auto_email and from_scheduler:
			new_to_date = getdate(today())
			if doc.frequency == "Weekly":
				new_to_date = add_days(new_to_date, 7)
			else:
				new_to_date = add_months(new_to_date, 1 if doc.frequency == "Monthly" else 3)
			new_from_date = add_months(new_to_date, -1 * doc.filter_duration)
			doc.add_comment(
				"Comment", "Emails sent on: " + frappe.utils.format_datetime(frappe.utils.now())
			)
			doc.db_set("to_date", new_to_date, commit=True)
			doc.db_set("from_date", new_from_date, commit=True)
		return True
	else:
		return False


@frappe.whitelist()
def send_auto_email():
	selected = frappe.get_list(
		"Process Statement of account for supplier",
		filters={"to_date": format_date(today()), "enable_auto_email": 1},
	)
	for entry in selected:
		send_emails(entry.name, from_scheduler=True)
	return True
