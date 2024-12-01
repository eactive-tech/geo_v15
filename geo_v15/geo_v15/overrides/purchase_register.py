import frappe
from frappe import _, msgprint
from frappe.query_builder.custom import ConstantColumn
from frappe.utils import flt, getdate
from pypika import Order

from erpnext.accounts.party import get_party_account
from erpnext.accounts.report.utils import (
	apply_common_conditions,
	get_opening_row,
	get_party_details,
	get_query_columns,
	get_values_for_columns,
)

from erpnext.accounts.report.purchase_register.purchase_register import get_conditions, get_account_columns, get_invoice_po_pr_map, get_payments, get_invoice_tax_map, get_internal_invoice_map, get_invoice_expense_map


def execute(filters=None):
	return _execute(filters)

def _execute(filters=None, additional_table_columns=None):
	if not filters:
		filters = {}

	include_payments = filters.get("include_payments")
	if filters.get("include_payments") and not filters.get("supplier"):
		frappe.throw(_("Please select a supplier for fetching payments."))
	if filters.get("include_payments"):
		invoice_list += get_payments(filters)
	if filters.get("branch"):
		invoice_list = get_invoices(filters, get_query_columns(additional_table_columns), filter.get("branch"))
	else:
		invoice_list = get_invoices(filters, get_query_columns(additional_table_columns))

	columns, expense_accounts, tax_accounts, unrealized_profit_loss_accounts = get_columns(
		invoice_list, additional_table_columns, include_payments
	)

	if not invoice_list:
		msgprint(_("No record found"))
		return columns, invoice_list

	invoice_expense_map = get_invoice_expense_map(invoice_list)
	internal_invoice_map = get_internal_invoice_map(invoice_list)
	invoice_expense_map, invoice_tax_map = get_invoice_tax_map(
		invoice_list, invoice_expense_map, expense_accounts, include_payments
	)
	invoice_po_pr_map = get_invoice_po_pr_map(invoice_list)
	suppliers = list(set(d.supplier for d in invoice_list))
	supplier_details = get_party_details("Supplier", suppliers)

	company_currency = frappe.get_cached_value("Company", filters.company, "default_currency")

	res = []
	if include_payments:
		opening_row = get_opening_row(
			"Supplier", filters.supplier, getdate(filters.from_date), filters.company
		)[0]
		res.append(
			{
				"payable_account": opening_row.account,
				"debit": flt(opening_row.debit),
				"credit": flt(opening_row.credit),
				"balance": flt(opening_row.balance),
			}
		)

	data = []
	for inv in invoice_list:
		# invoice details
		purchase_order = list(set(invoice_po_pr_map.get(inv.name, {}).get("purchase_order", [])))
		purchase_receipt = list(set(invoice_po_pr_map.get(inv.name, {}).get("purchase_receipt", [])))
		project = list(set(invoice_po_pr_map.get(inv.name, {}).get("project", [])))

		row = {
			"voucher_type": inv.doctype,
			"voucher_no": inv.name,
			"posting_date": inv.posting_date,
			"supplier_id": inv.supplier,
			"supplier_name": inv.supplier_name,
			"branch": inv.branch,
			**get_values_for_columns(additional_table_columns, inv),
			"supplier_group": supplier_details.get(inv.supplier).get("supplier_group"),
			"tax_id": supplier_details.get(inv.supplier).get("tax_id"),
			"payable_account": inv.credit_to,
			"mode_of_payment": inv.mode_of_payment,
			"project": ", ".join(project) if inv.doctype == "Purchase Invoice" else inv.project,
			"bill_no": inv.bill_no,
			"bill_date": inv.bill_date,
			"remarks": inv.remarks,
			"purchase_order": ", ".join(purchase_order),
			"purchase_receipt": ", ".join(purchase_receipt),
			"currency": company_currency,
		}

		# map expense values
		base_net_total = 0
		for expense_acc in expense_accounts:
			if inv.is_internal_supplier and inv.company == inv.represents_company:
				expense_amount = 0
			else:
				expense_amount = flt(invoice_expense_map.get(inv.name, {}).get(expense_acc))
			base_net_total += expense_amount
			row.update({frappe.scrub(expense_acc): expense_amount})

		# Add amount in unrealized account
		for account in unrealized_profit_loss_accounts:
			row.update(
				{frappe.scrub(account + "_unrealized"): flt(internal_invoice_map.get((inv.name, account)))}
			)

		# net total
		row.update({"net_total": base_net_total or inv.base_net_total})

		# tax account
		total_tax = 0
		for tax_acc in tax_accounts:
			if tax_acc not in expense_accounts:
				tax_amount = flt(invoice_tax_map.get(inv.name, {}).get(tax_acc))
				total_tax += tax_amount
				row.update({frappe.scrub(tax_acc): tax_amount})

		# total tax, grand total, rounded total & outstanding amount
		row.update(
			{
				"total_tax": total_tax,
				"grand_total": inv.base_grand_total,
				"rounded_total": inv.base_rounded_total,
				"outstanding_amount": inv.outstanding_amount,
			}
		)

		if inv.doctype == "Purchase Invoice":
			row.update({"debit": inv.base_grand_total, "credit": 0.0})
		else:
			row.update({"debit": 0.0, "credit": inv.base_grand_total})
		data.append(row)

	res += sorted(data, key=lambda x: x["posting_date"])

	if include_payments:
		running_balance = flt(opening_row.balance)
		for row in range(1, len(res)):
			running_balance += res[row]["debit"] - res[row]["credit"]
			res[row].update({"balance": running_balance})

	return columns, res, None, None, None, include_payments

def get_columns(invoice_list, additional_table_columns, include_payments=False):
	"""return columns based on filters"""
	columns = [
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"width": 120,
		},
		{
			"label": _("Voucher"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 120,
		},
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 120,
		},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 80},
		{
			"label": _("Supplier"),
			"fieldname": "supplier_id",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 120,
		},
		{"label": _("Supplier Name"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 120},
	]

	if additional_table_columns and not include_payments:
		columns += additional_table_columns

	if not include_payments:
		columns += [
			{
				"label": _("Supplier Group"),
				"fieldname": "supplier_group",
				"fieldtype": "Link",
				"options": "Supplier Group",
				"width": 120,
			},
			{"label": _("Tax Id"), "fieldname": "tax_id", "fieldtype": "Data", "width": 80},
			{
				"label": _("Payable Account"),
				"fieldname": "payable_account",
				"fieldtype": "Link",
				"options": "Account",
				"width": 100,
			},
			{
				"label": _("Mode Of Payment"),
				"fieldname": "mode_of_payment",
				"fieldtype": "Data",
				"width": 120,
			},
			{
				"label": _("Project"),
				"fieldname": "project",
				"fieldtype": "Link",
				"options": "Project",
				"width": 80,
			},
			{"label": _("Bill No"), "fieldname": "bill_no", "fieldtype": "Data", "width": 120},
			{"label": _("Bill Date"), "fieldname": "bill_date", "fieldtype": "Date", "width": 80},
			{
				"label": _("Purchase Order"),
				"fieldname": "purchase_order",
				"fieldtype": "Link",
				"options": "Purchase Order",
				"width": 100,
			},
			{
				"label": _("Purchase Receipt"),
				"fieldname": "purchase_receipt",
				"fieldtype": "Link",
				"options": "Purchase Receipt",
				"width": 100,
			},
			{"fieldname": "currency", "label": _("Currency"), "fieldtype": "Data", "width": 80},
		]
	else:
		columns += [
			{
				"fieldname": "payable_account",
				"label": _("Payable Account"),
				"fieldtype": "Link",
				"options": "Account",
				"width": 120,
			},
			{"fieldname": "debit", "label": _("Debit"), "fieldtype": "Currency", "width": 120},
			{"fieldname": "credit", "label": _("Credit"), "fieldtype": "Currency", "width": 120},
			{"fieldname": "balance", "label": _("Balance"), "fieldtype": "Currency", "width": 120},
		]

	account_columns, accounts = get_account_columns(invoice_list, include_payments)

	columns = (
		columns
		+ account_columns[0]
		+ account_columns[1]
		+ [
			{
				"label": _("Net Total"),
				"fieldname": "net_total",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		]
		+ account_columns[2]
		+ [
			{
				"label": _("Total Tax"),
				"fieldname": "total_tax",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		]
	)

	if not include_payments:
		columns += [
			{
				"label": _("Grand Total"),
				"fieldname": "grand_total",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Rounded Total"),
				"fieldname": "rounded_total",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Outstanding Amount"),
				"fieldname": "outstanding_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
		]
	columns += [{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 120}]
	return columns, accounts[0], accounts[2], accounts[1]

def get_invoices(filters, additional_query_columns, branch = None):
	user_branch = frappe.db.get_list("User Permission", filters={"user": frappe.session.user, "allow": "Branch"}, pluck="for_value")
	pi = frappe.qb.DocType("Purchase Invoice")
	query = (
		frappe.qb.from_(pi)
		.select(
			ConstantColumn("Purchase Invoice").as_("doctype"),
			pi.name,
			pi.posting_date,
			pi.credit_to,
			pi.supplier,
			pi.supplier_name,
			pi.branch,
			pi.tax_id,
			pi.bill_no,
			pi.bill_date,
			pi.remarks,
			pi.base_net_total,
			pi.base_grand_total,
			pi.base_rounded_total,
			pi.outstanding_amount,
			pi.mode_of_payment,
		)
		.where(pi.docstatus == 1)
		.orderby(pi.posting_date, pi.name, order=Order.desc)
	)
	if user_branch:
		if branch:
			if branch in user_branch:
				query = query.where(pi.branch == branch)
			else:
				return []
		else:
			query = query.where(pi.branch.isin(user_branch))
	elif branch:
		query = query.where(pi.branch == branch)

	if additional_query_columns:
		for col in additional_query_columns:
			query = query.select(col)

	if filters.get("supplier"):
		query = query.where(pi.supplier == filters.supplier)
	if filters.get("supplier_group"):
		query = query.where(pi.supplier_group == filters.supplier_group)

	query = get_conditions(filters, query, "Purchase Invoice")

	query = apply_common_conditions(
		filters, query, doctype="Purchase Invoice", child_doctype="Purchase Invoice Item"
	)

	if filters.get("include_payments"):
		party_account = get_party_account(
			"Supplier", filters.get("supplier"), filters.get("company"), include_advance=True
		)
		query = query.where(pi.credit_to.isin(party_account))

	invoices = query.run(as_dict=True)
	return invoices
