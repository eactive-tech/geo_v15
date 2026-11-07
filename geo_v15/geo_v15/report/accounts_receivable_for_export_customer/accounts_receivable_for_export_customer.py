# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	final_filters = {
		"company": filters.get("company"),
		"report_date": filters.get("as_on_date"),
		"party": filters.get("party", []),
		"ageing_based_on": filters.get("ageing_based_on"),
		"calculate_ageing_with": filters.get("calculate_ageing_with"),
		"branch": filters.get("branch", []),
		"range": filters.get("range", "30, 60, 90, 120, 150"),
		"customer_group": filters.get("customer_group", [])
	}

	# optional/dynamic fields (only added if present)
	optional_keys = [
		"finance_book",
		"cost_center",
		"party_type",
		"party_account",
		"payment_terms_template",
		"sales_person",
		"territory",
		"group_by_party",
		"based_on_payment_terms",
		"show_future_payments",
		"show_delivery_notes",
		"show_sales_person",
		"show_remarks",
		"for_revaluation_journals",
		"ignore_accounts",
		"in_party_currency"
	]

	# add only available dynamic keys
	for key in optional_keys:
		if filters.get(key) not in [None, "", []]:
			final_filters[key] = filters.get(key)

	# finally run the report
	x = frappe.call(
		"frappe.desk.query_report.run",
		report_name="Accounts Receivable",
		filters=final_filters,
		ignore_prepared_report=True
	)

	if x.get("result"):
		x.get("result").pop()

	results = x.get("result")
	columns = x.get("columns")
	
	new_columns = [
		{
			"label": "Exchange Currency",
			"fieldname": "exchange_currency",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": "Exchange Rate",
			"fieldname": "exchange_rate",
			"fieldtype": "Float",
			"width": 120
		}
	]

	# Append new columns in output
	# Find index of voucher_no column
	insert_index = next(
		(i for i, col in enumerate(columns) if col.get("fieldname") == "voucher_no"),
		None
	)

	# If voucher_no exists, insert after it
	if insert_index is not None:
		for col in reversed(new_columns):   # reverse to maintain order
			columns.insert(insert_index + 1, col)
	else:
		# fallback: append to end
		columns.extend(new_columns)

	amount_fields = [
		"invoiced", "paid", "credit_note", "outstanding",
		"invoiced_in_account_currency", "paid_in_account_currency",
		"credit_note_in_account_currency", "outstanding_in_account_currency",
		"invoice_grand_total",
		"range1", "range2", "range3", "range4", "range5",
		"invoice_grand_total", "total_due"
	]

	for row in results:
		voucher_type = row.get("voucher_type")
		voucher_no = row.get("voucher_no")

		# fetch custom currency & rate from document
		extra = frappe.db.get_value(
			voucher_type,
			voucher_no,
			["custom_exchange_currency", "custom_exchange_rate"],
			as_dict=True
		)

		exchange_currency = extra.custom_exchange_currency if extra else None
		exchange_rate = extra.custom_exchange_rate if extra else None

		row["exchange_currency"] = exchange_currency
		row["exchange_rate"] = exchange_rate

		if not exchange_rate:
			continue

		for field in amount_fields:
			if row.get(field) not in [None, 0]:
				row[field] = row[field] / float(exchange_rate)

		row["currency"] = exchange_currency

	return x.get("columns"), x.get("result")
