import frappe
from frappe import _

from erpnext.accounts.report.trial_balance.trial_balance import validate_filters, get_data, get_columns

def execute(filters=None):
	validate_filters(filters)
	data = get_data(filters)
	columns = get_columns()
	
	new_result = []
	if filters.get("account_group"):
		lft = frappe.db.get_value("Account", filters.get("account_group"), "lft")
		rgt = frappe.db.get_value("Account", filters.get("account_group"), "rgt")
		new_data = frappe.db.sql("""
			select name, account_number, parent_account, account_name, root_type, report_type, lft, rgt,is_group
			from `tabAccount` where is_group = 0 and company=%s and lft >= %s and rgt <= %s order by lft
		""", (filters.get("company"), lft, rgt), as_dict=1)

		for d in new_data:
			for x in data:
				if x.get("account") == d["name"]:
					if d["is_group"] == 0 :
						x["lft"]=''
						x["rgt"]=''
						new_result.append(x)					
		new_result.append({})
		new_result.append({
                "account": "'Total'",
                "account_name": "'Total'",
                "closing_credit": new_result[0].get('closing_credit'),
                "closing_debit": new_result[0].get('closing_debit'),
                "credit": new_result[0].get('credit'),
                "currency": "INR",
                "debit": new_result[0].get('debit'),
                "has_value": True,
                "indent": 0,
                "opening_credit": new_result[0].get('opening_credit'),
                "opening_debit": new_result[0].get('opening_debit'),
                "parent_account": '',
                "warn_if_negative": True
            })

	else:
		new_result  = data

	return columns, new_result
