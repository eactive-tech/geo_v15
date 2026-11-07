# Copyright (c) 2026, eactive and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

CRITERIA_PAPER = "Dealer Category Criteria Paper"
CUSTOMER_CATEGORY_FIELD = "custom_customer_category_as_per_balance_sheet"

# (point field, ratio attribute, child doctype, parentfield on Criteria Paper, table label)
POINT_TABLES = [
	("st_point", "sales_turnover", "DCCP Sales Turnover", "sales_turnover", "Sales Turnover"),
	("gpr_point", "gp_ratio", "DCCP Gross Profit Ratio", "gross_profit_ratio", "Gross Profit Ratio"),
	("npr_point", "np_ratio", "DCCP Net Profit Ratio", "net_profit_ratio", "Net Profit Ratio"),
	("wc_point", "working_capital_ratio", "DCCP Working Capital", "working_capital", "Working Capital"),
	("net_worth_point", "net_worth_ratio", "DCCP Net Worth", "net_worth", "Net Worth"),
	("dso_point", "dso", "DCCP DSO", "dso", "DSO"),
]


class DealerCategoryCalculation(Document):
	def validate(self):
		self.calculate_ratios()
		self.calculate_points()

	def on_submit(self):
		self.update_customer_category()

	def on_cancel(self):
		self.update_customer_category()

	def calculate_ratios(self):
		sales = flt(self.sales_turnover)
		purchase = flt(self.purchase_turnover)
		debtors = flt(self.sundry_debtors)
		creditors = flt(self.sundry_creditors)

		current_assets = (
			debtors
			+ flt(self.inventory_stock)
			+ flt(self.other_current_assets)
			+ flt(self.cash_bank_balances)
		)
		current_liabilities = flt(self.other_current_liabilities) + creditors
		total_assets = flt(self.fixed_asset) + flt(self.investment) + current_assets

		self.working_capital = current_assets - current_liabilities
		self.net_worth = (
			total_assets
			- flt(self.secured_loans_long_term)
			- flt(self.unsecured_loans_short_term)
			- current_liabilities
		)

		self.gp_ratio = 0 if sales == 0 else flt(self.gross_profit) / sales * 100
		self.np_ratio = 0 if sales == 0 else flt(self.net_profit_before_tax) / sales * 100

		# Excel guards these on debtors / creditors; #DIV/0! is treated as 0
		if debtors == 0 or current_liabilities == 0:
			self.working_capital_ratio = 0
		else:
			self.working_capital_ratio = current_assets / current_liabilities

		if debtors == 0 or total_assets == 0:
			self.net_worth_ratio = 0
		else:
			self.net_worth_ratio = self.net_worth / total_assets * 100

		if creditors == 0 or purchase == 0:
			self.dso = 0
		else:
			self.dso = creditors / purchase * 365

	def calculate_points(self):
		paper = frappe.db.get_value(CRITERIA_PAPER, {"is_active": 1}, "name")
		missing = []

		for point_field, value_field, child_doctype, parentfield, label in POINT_TABLES:
			rows = get_ranges(paper, child_doctype, parentfield, "points")
			if not rows:
				missing.append(label)
			self.set(point_field, flt(match_range(rows, flt(self.get(value_field)), "points")))

		self.total_points = sum(flt(self.get(point_field)) for point_field, *_rest in POINT_TABLES)

		category_rows = get_ranges(paper, "DCCP Category Points", "category_points", "category")
		if not category_rows:
			missing.append("Point Table for Category")
		self.new_dealer_category = match_range(category_rows, self.total_points, "category") or ""

		if not paper:
			frappe.msgprint(
				_(
					"No active Dealer Category Criteria Paper found. Points were set to 0 and New Dealer Category was left blank."
				)
			)
		elif missing:
			frappe.msgprint(
				_(
					"Active Dealer Category Criteria Paper {0} has no rows in: {1}. Those values were set to 0 / blank."
				).format(paper, ", ".join(missing))
			)

	def update_customer_category(self):
		"""Set the Customer's category from its latest-Fiscal-Year submitted calculation."""
		customer = self.customer

		if self.docstatus == 1 and not (self.new_dealer_category or "").strip():
			frappe.msgprint(
				_("New Dealer Category is blank, so it was not used to update Customer {0}.").format(customer),
				indicator="orange",
			)

		latest = get_latest_calculation(customer)
		if latest:
			category = latest.new_dealer_category.strip()
		elif self.docstatus == 2:
			# no submitted calculation left after this cancel: default to D
			category = "D"
		else:
			category = ""

		options = (frappe.get_meta("Customer").get_options(CUSTOMER_CATEGORY_FIELD) or "").split("\n")
		if category not in options:
			frappe.throw(
				_("Dealer Category {0} is not a valid Customer Category. Allowed values: {1}").format(
					category, ", ".join(o for o in options if o)
				)
			)

		if (frappe.db.get_value("Customer", customer, CUSTOMER_CATEGORY_FIELD) or "") != category:
			frappe.db.set_value("Customer", customer, CUSTOMER_CATEGORY_FIELD, category)
			source = latest.name if latest else "default (no submitted Dealer Category Calculation)"
			frappe.get_doc("Customer", customer).add_comment(
				"Info", _("Customer Category set to {0} from {1}").format(category or "blank", source)
			)


def get_ranges(paper, child_doctype, parentfield, result_field):
	if not paper:
		return []
	return frappe.get_all(
		child_doctype,
		filters={"parent": paper, "parenttype": CRITERIA_PAPER, "parentfield": parentfield},
		fields=["from_value", "to_value", result_field],
		order_by="from_value desc",
	)


def match_range(rows, value, result_field):
	"""Return the result of the row whose range holds the value.

	Rows are checked from the highest From down, so a value matches only one row.
	A row whose To is not above its From (e.g. 80 -> 0) has no upper limit.
	A value in a gap between ranges takes the nearest row below it,
	and a value below every range takes the lowest row.
	"""
	for r in rows:
		value_from = flt(r.from_value)
		value_to = flt(r.to_value)
		if value >= value_from and (value_to <= value_from or value <= value_to):
			return r.get(result_field)
	for r in rows:
		if value >= flt(r.from_value):
			return r.get(result_field)
	if rows:
		return rows[-1].get(result_field)
	return None


def get_latest_calculation(customer):
	"""Latest submitted calculation with a category, by Fiscal Year start date."""
	calculations = frappe.get_all(
		"Dealer Category Calculation",
		filters={"customer": customer, "docstatus": 1, "new_dealer_category": ["is", "set"]},
		fields=["name", "fiscal_year", "new_dealer_category"],
	)
	if not calculations:
		return None

	start_date = {
		fy.name: str(fy.year_start_date)
		for fy in frappe.get_all(
			"Fiscal Year",
			filters={"name": ["in", [d.fiscal_year for d in calculations]]},
			fields=["name", "year_start_date"],
		)
	}

	latest = None
	for d in calculations:
		if not latest or start_date.get(d.fiscal_year, "") > start_date.get(latest.fiscal_year, ""):
			latest = d
	return latest
