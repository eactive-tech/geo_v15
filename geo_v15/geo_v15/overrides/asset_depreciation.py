import frappe
from frappe import _
from frappe.utils import (
	cint,
	getdate,
)

def _make_journal_entry_for_depreciation(
	asset_depr_schedule_doc,
	asset,
	date,
	depr_schedule,
	sch_start_idx,
	sch_end_idx,
	depreciation_cost_center,
	depreciation_series,
	credit_account,
	debit_account,
	accounting_dimensions,
):
	if not (sch_start_idx and sch_end_idx) and not (
		not depr_schedule.journal_entry and getdate(depr_schedule.schedule_date) <= getdate(date)
	):
		return

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Depreciation Entry"
	je.naming_series = depreciation_series
	je.posting_date = depr_schedule.schedule_date
	je.company = asset.company
	je.finance_book = asset_depr_schedule_doc.finance_book
	je.remark = f"Depreciation Entry against {asset.name} worth {depr_schedule.depreciation_amount}"
	
    # Calculate values for user_remark
	asset_amount = asset.gross_purchase_amount
	asset_date = asset.available_for_use_date
	depreciation_amount = depr_schedule.depreciation_amount

	# Set user_remark with formatted information
	je.user_remark = (
		f"Asset Amount: {asset_amount}, <br>"
		f"Asset Date: {asset_date}, <br>"
		f"Depreciation Amount: {depreciation_amount}"
	)
	je.voucher_entry_type = "Journal Entry"
	je.branch = asset.branch

	credit_entry = {
		"account": credit_account,
		"credit_in_account_currency": depr_schedule.depreciation_amount,
		"reference_type": "Asset",
		"reference_name": asset.name,
		"cost_center": depreciation_cost_center,
	}

	debit_entry = {
		"account": debit_account,
		"debit_in_account_currency": depr_schedule.depreciation_amount,
		"reference_type": "Asset",
		"reference_name": asset.name,
		"cost_center": depreciation_cost_center,
	}

	for dimension in accounting_dimensions:
		if asset.get(dimension["fieldname"]) or dimension.get("mandatory_for_bs"):
			credit_entry.update(
				{
					dimension["fieldname"]: asset.get(dimension["fieldname"])
					or dimension.get("default_dimension")
				}
			)

		if asset.get(dimension["fieldname"]) or dimension.get("mandatory_for_pl"):
			debit_entry.update(
				{
					dimension["fieldname"]: asset.get(dimension["fieldname"])
					or dimension.get("default_dimension")
				}
			)

	je.append("accounts", credit_entry)
	je.append("accounts", debit_entry)

	je.flags.ignore_permissions = True
	je.flags.planned_depr_entry = True
	je.save()

	depr_schedule.db_set("journal_entry", je.name)

	if not je.meta.get_workflow():
		je.submit()
		asset.reload()
		idx = cint(asset_depr_schedule_doc.finance_book_id)
		row = asset.get("finance_books")[idx - 1]
		row.value_after_depreciation -= depr_schedule.depreciation_amount
		row.db_update()