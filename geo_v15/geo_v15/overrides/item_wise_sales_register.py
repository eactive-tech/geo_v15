import frappe
from frappe import _
from pypika import Order

from erpnext.accounts.report.item_wise_sales_register.item_wise_sales_register import apply_group_by_conditions

def get_columns(additional_table_columns, filters):
	columns = []

	if filters.get("group_by") != ("Item"):
		columns.extend(
			[
				{
					"label": _("Item Code"),
					"fieldname": "item_code",
					"fieldtype": "Link",
					"options": "Item",
					"width": 120,
				},
				{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 120},
			]
		)

	if filters.get("group_by") not in ("Item", "Item Group"):
		columns.extend(
			[
				{
					"label": _("Item Group"),
					"fieldname": "item_group",
					"fieldtype": "Link",
					"options": "Item Group",
					"width": 120,
				}
			]
		)

	columns.extend(
		[
			{"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 150},
			{
				"label": _("Invoice"),
				"fieldname": "invoice",
				"fieldtype": "Link",
				"options": "Sales Invoice",
				"width": 120,
			},
			{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		]
	)

	if filters.get("group_by") != "Customer":
		columns.extend(
			[
				{
					"label": _("Customer Group"),
					"fieldname": "customer_group",
					"fieldtype": "Link",
					"options": "Customer Group",
					"width": 120,
				}
			]
		)

	if filters.get("group_by") not in ("Customer", "Customer Group"):
		columns.extend(
			[
				{
					"label": _("Customer"),
					"fieldname": "customer",
					"fieldtype": "Link",
					"options": "Customer",
					"width": 120,
				},
				{
					"label": _("Customer Name"),
					"fieldname": "customer_name",
					"fieldtype": "Data",
					"width": 120,
				},
			]
		)

    # branch filter added
	if filters.get("branch"):
		columns.append(
			{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "width": 80, "options": "Branch"}
		)


	if additional_table_columns:
		columns += additional_table_columns

	columns += [
		{
			"label": _("Receivable Account"),
			"fieldname": "debit_to",
			"fieldtype": "Link",
			"options": "Account",
			"width": 80,
		},
		{
			"label": _("Mode Of Payment"),
			"fieldname": "mode_of_payment",
			"fieldtype": "Data",
			"width": 120,
		},
	]

	if filters.get("group_by") != "Territory":
		columns.extend(
			[
				{
					"label": _("Territory"),
					"fieldname": "territory",
					"fieldtype": "Link",
					"options": "Territory",
					"width": 80,
				}
			]
		)

	columns += [
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 80,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 80,
		},
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 100,
		},
		{
			"label": _("Delivery Note"),
			"fieldname": "delivery_note",
			"fieldtype": "Link",
			"options": "Delivery Note",
			"width": 100,
		},
		{
			"label": _("Income Account"),
			"fieldname": "income_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 100,
		},
		{
			"label": _("Cost Center"),
			"fieldname": "cost_center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 100,
		},
		{"label": _("Stock Qty"), "fieldname": "stock_qty", "fieldtype": "Float", "width": 100},
		{
			"label": _("Stock UOM"),
			"fieldname": "stock_uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 100,
		},
		{
			"label": _("Rate"),
			"fieldname": "rate",
			"fieldtype": "Float",
			"options": "currency",
			"width": 100,
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 100,
		},
	]

	if filters.get("group_by"):
		columns.append(
			{"label": _("% Of Grand Total"), "fieldname": "percent_gt", "fieldtype": "Float", "width": 80}
		)

	return columns


def apply_conditions(query, si, sii, filters, additional_conditions=None):
	for opts in ("company", "customer"):
		if filters.get(opts):
			query = query.where(si[opts] == filters[opts])

	if filters.get("from_date"):
		query = query.where(si.posting_date >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(si.posting_date <= filters.get("to_date"))

	if filters.get("mode_of_payment"):
		sales_invoice = frappe.db.get_all(
			"Sales Invoice Payment", {"mode_of_payment": filters.get("mode_of_payment")}, pluck="parent"
		)
		query = query.where(si.name.isin(sales_invoice))

	if filters.get("warehouse"):
		if frappe.db.get_value("Warehouse", filters.get("warehouse"), "is_group"):
			lft, rgt = frappe.db.get_all(
				"Warehouse", filters={"name": filters.get("warehouse")}, fields=["lft", "rgt"], as_list=True
			)[0]
			warehouses = frappe.db.get_all("Warehouse", {"lft": (">", lft), "rgt": ("<", rgt)}, pluck="name")
			query = query.where(sii.warehouse.isin(warehouses))
		else:
			query = query.where(sii.warehouse == filters.get("warehouse"))

	if filters.get("brand"):
		query = query.where(sii.brand == filters.get("brand"))

	if filters.get("item_code"):
		query = query.where(sii.item_code == filters.get("item_code"))

	if filters.get("item_group"):
		query = query.where(sii.item_group == filters.get("item_group"))

	if filters.get("income_account"):
		query = query.where(
			(sii.income_account == filters.get("income_account"))
			| (sii.deferred_revenue_account == filters.get("income_account"))
			| (si.unrealized_profit_loss_account == filters.get("income_account"))
		)

    # branch filter added
	if filters.get("branch"):
		query = query.where(si.branch == filters.get("branch"))

	if not filters.get("group_by"):
		query = query.orderby(si.posting_date, order=Order.desc)
		query = query.orderby(sii.item_group, order=Order.desc)
	else:
		query = apply_group_by_conditions(query, si, sii, filters)

	for key, value in (additional_conditions or {}).items():
		query = query.where(si[key] == value)

	return query


def get_items(filters, additional_query_columns, additional_conditions=None):
	doctype = "Sales Invoice"
	si = frappe.qb.DocType(doctype)
	sii = frappe.qb.DocType(f"{doctype} Item")
	item = frappe.qb.DocType("Item")

	query = (
		frappe.qb.from_(si)
		.join(sii)
		.on(si.name == sii.parent)
		.left_join(item)
		.on(sii.item_code == item.name)
		.select(
			sii.name,
			sii.parent,
			si.posting_date,
			si.debit_to,
			si.branch,
			si.unrealized_profit_loss_account,
			si.is_internal_customer,
			si.customer,
			si.remarks,
			si.territory,
			si.company,
			si.base_net_total,
			sii.project,
			sii.item_code,
			sii.description,
			sii.item_name,
			sii.item_group,
			sii.item_name.as_("si_item_name"),
			sii.item_group.as_("si_item_group"),
			item.item_name.as_("i_item_name"),
			item.item_group.as_("i_item_group"),
			sii.sales_order,
			sii.delivery_note,
			sii.income_account,
			sii.cost_center,
			sii.enable_deferred_revenue,
			sii.deferred_revenue_account,
			sii.stock_qty,
			sii.stock_uom,
			sii.base_net_rate,
			sii.base_net_amount,
			si.customer_name,
			si.customer_group,
			sii.so_detail,
			si.update_stock,
			sii.uom,
			sii.qty,
		)
		.where(si.docstatus == 1)
		.where(sii.parenttype == doctype)
	)

	if additional_query_columns:
		for column in additional_query_columns:
			if column.get("_doctype"):
				table = frappe.qb.DocType(column.get("_doctype"))
				query = query.select(table[column.get("fieldname")])
			else:
				query = query.select(si[column.get("fieldname")])

	if filters.get("customer"):
		query = query.where(si.customer == filters["customer"])

	if filters.get("customer_group"):
		query = query.where(si.customer_group == filters["customer_group"])

	query = apply_conditions(query, si, sii, filters, additional_conditions)

	return query.run(as_dict=True)
