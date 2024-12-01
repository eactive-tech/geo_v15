import frappe
from frappe import _
from frappe.utils import flt
from erpnext.buying.report.procurement_tracker.procurement_tracker import get_mapped_pi_records, get_mapped_pr_records


def get_columns(filters):
		# frappe.throw(str(filters))
		columns = [
			{
				"label": _("Material Request Date"),
				"fieldname": "material_request_date",
				"fieldtype": "Date",
				"width": 140,
			},
			{
				"label": _("Material Request No"),
				"options": "Material Request",
				"fieldname": "material_request_no",
				"fieldtype": "Link",
				"width": 140,
			},
			{
				"label": _("Material Request By"),
				"fieldname": "material_request_by",
				"fieldtype": "Link",
				"options": "User",
				"width": 140,
			},
			{
				"label": _("Material Request Item"),
				"fieldname": "material_request_item",
				"fieldtype": "Link",
				"options": "Item",
				"width": 140,
			},
			{
				"label": _("Material Request Qty"),
				"fieldname": "material_request_qty",
				"fieldtype": "Data",
				"width": 140,
			},
			{
				"label": _("Cost Center"),
				"options": "Cost Center",
				"fieldname": "cost_center",
				"fieldtype": "Link",
				"width": 140,
			},
			{
				"label": _("Project"),
				"options": "Project",
				"fieldname": "project",
				"fieldtype": "Link",
				"width": 140,
			},
			{
				"label": _("Requesting Site"),
				"options": "Warehouse",
				"fieldname": "requesting_site",
				"fieldtype": "Link",
				"width": 140,
			},
			{
				"label": _("Purchase order creator"),
				"fieldname": "requestor",
				"fieldtype": "Data",
				"width": 140,
			},
			{
				"label": _("Item"),
				"fieldname": "item_code",
				"fieldtype": "Link",
				"options": "Item",
				"width": 150,
			},
			{"label": _("Ordered Qty"), "fieldname": "quantity", "fieldtype": "Float", "width": 140},
			{"label": _("PO Rate  (Item Wise)"), "fieldname": "rate", "fieldtype": "Currency", "width": 140},
			{
				"label": _("Unit of Measure"),
				"options": "UOM",
				"fieldname": "unit_of_measurement",
				"fieldtype": "Link",
				"width": 140,
			},
			{"label": _("Status"), "fieldname": "status", "fieldtype": "data", "width": 140},
			{
				"label": _("Purchase Order Date"),
				"fieldname": "purchase_order_date",
				"fieldtype": "Date",
				"width": 140,
			},
			{
				"label": _("Purchase Order"),
				"options": "Purchase Order",
				"fieldname": "purchase_order",
				"fieldtype": "Link",
				"width": 140,
			},
			{
				"label": _("Purchase Order By"),
				"fieldname": "purchase_order_by",
				"fieldtype": "Data",
				"width": 140,
			},
			{
				"label": _("Supplier"),
				"options": "Supplier",
				"fieldname": "supplier",
				"fieldtype": "Link",
				"width": 140,
			},
			{
				"label": _("Supplier Name"),
				"fieldname": "supplier_name",
				"fieldtype": "Data",
				"width": 140,
			},
			{
				"label": _("Estimated Cost"),
				"fieldname": "estimated_cost",
				"fieldtype": "Float",
				"width": 140,
			},
			{"label": _("Actual Cost"), "fieldname": "actual_cost", "fieldtype": "Float", "width": 140},
			{
				"label": _("Purchase Order Amount"),
				"fieldname": "purchase_order_amt",
				"fieldtype": "Float",
				"width": 140,
			},
			{"label": _("Received Qty"), "fieldname": "received_qty", "fieldtype": "Float", "width": 140},
			{"label": _("Pending Qty"), "fieldname": "pending_qty", "fieldtype": "Float", "width": 140},
			{"label": _("%Ordered"), "fieldname": "order_per", "fieldtype": "Percent", "width": 140},
			{"label": _("%Received"), "fieldname": "received_per", "fieldtype": "Percent", "width": 140},


			{
				"label": _("Purchase Order Amount(Company Currency)"),
				"fieldname": "purchase_order_amt_in_company_currency",
				"fieldtype": "Float",
				"width": 140,
			},
			{
				"label": _("Expected Delivery Date"),
				"fieldname": "expected_delivery_date",
				"fieldtype": "Date",
				"width": 140,
			},
			{
				"label": _("Actual Delivery Date"),
				"fieldname": "actual_delivery_date",
				"fieldtype": "Date",
				"width": 140,
			},
		]
		return columns

def get_data(filters):
		conditions_dict = get_conditions(filters)
		conditions = conditions_dict['conditions_string']
		values = conditions_dict['values']
		purchase_order_entry = get_po_entries(conditions, values)

		mr_conditons_dict = get_mr_details_conditions(filters)
		mr_conditions = mr_conditons_dict['conditions_string']
		mr_values = mr_conditons_dict['values']
		mr_records, procurement_record_against_mr = get_mapped_mr_details(mr_conditions, mr_values)

		pr_records = get_mapped_pr_records()
		pi_records = get_mapped_pi_records()

		procurement_record = []
		if procurement_record_against_mr:
			procurement_record += procurement_record_against_mr
		for po in purchase_order_entry:
			# fetch material records linked to the purchase order item
			mr_record = mr_records.get(po.material_request_item, [{}])[0]
			pending_qty = flt(po.qty)- flt(po.received_qty)
			if mr_record.get("qty") :
				order_per = (flt(po.qty)/flt(mr_record.get("qty")))*100
			else :
				order_per = 0.00*100
			if flt(po.received_qty) :
				received_per =  (po.received_qty/flt(po.qty))*100
			else :
				received_per = 0.00*100

			procurement_detail = {
				"material_request_date": mr_record.get("transaction_date"),
				"cost_center": po.cost_center,
				"project": po.project,
				"requesting_site": po.warehouse,
				"requestor": po.po_requestor,
				"material_request_by": mr_record.get("mr_requestor"),
				"order_per":order_per,
				"received_per":received_per,
				"material_request_item": mr_record.get("item_code"),
				"material_request_qty": mr_record.get("qty"),
				"material_request_no": po.material_request,
				"item_code": po.item_code,
				"quantity": flt(po.qty),
				"pending_qty": pending_qty,
				"received_qty": po.received_qty,
				"rate": po.rate,
				"unit_of_measurement": po.stock_uom,
				"status": po.status,
				"purchase_order_date": po.transaction_date,
				"purchase_order": po.parent,
				"supplier": po.supplier,
				"supplier_name":po.supplier_name,
				"estimated_cost": flt(mr_record.get("amount")),
				"actual_cost": flt(pi_records.get(po.name)),
				"purchase_order_amt": flt(po.amount),
				"purchase_order_amt_in_company_currency": flt(po.base_amount),
				"expected_delivery_date": po.schedule_date,
				"actual_delivery_date": pr_records.get(po.name),
			}
			procurement_record.append(procurement_detail)
		return procurement_record

def get_mapped_mr_details(conditions, values):
		mr_records = {}
		mr_details = frappe.db.sql(
			"""
			SELECT
				parent.transaction_date,
				parent.per_ordered,
				parent.owner mr_requestor,
				child.name,
				child.parent,
				child.amount,
				child.qty,
				child.item_code,
				child.uom,
				parent.status,
				child.project,
				child.cost_center
			FROM `tabMaterial Request` parent, `tabMaterial Request Item` child
			WHERE
				{conditions}
				AND parent.per_ordered>=0
				AND parent.name=child.parent
				AND parent.docstatus=1
			""".format(
				conditions=conditions
			),
			values = values,
			as_dict=1,
		)  # nosec

		procurement_record_against_mr = []
		for record in mr_details:
			if record.per_ordered:
				mr_records.setdefault(record.name, []).append(frappe._dict(record))
			else:
				procurement_record_details = dict(
					material_request_date=record.transaction_date,
					material_request_no=record.parent,
					material_request_by=record.mr_requestor,
					requestor=record.po_requestor,
					item_code=record.item_code,
					estimated_cost=flt(record.amount),
					quantity=flt(record.qty),
					material_request_qty=flt(record.qty),
					unit_of_measurement=record.uom,
					status=record.status,
					actual_cost=0,
					purchase_order_amt=0,
					purchase_order_amt_in_company_currency=0,
					project=record.project,
					cost_center=record.cost_center,
				)
				procurement_record_against_mr.append(procurement_record_details)
		return mr_records, procurement_record_against_mr

def get_po_entries(conditions, values):
		# frappe.throw(str({'conditions':conditions, 'values':values}))
		return frappe.db.sql(
			"""
			SELECT
				child.name,
				child.parent,
				child.cost_center,
				child.project,
				child.warehouse,
				child.material_request,
				child.material_request_item,
				child.item_code,
				child.stock_uom,
				child.qty,
				child.amount,
				child.base_amount,
				child.schedule_date,
				child.received_qty,
				child.rate,
				parent.transaction_date,
				parent.supplier,
				parent.supplier_name,
				parent.status,
				parent.owner po_requestor
			FROM `tabPurchase Order` parent, `tabPurchase Order Item` child
			WHERE
				{conditions}
				AND parent.docstatus = 1
				AND parent.name = child.parent
				AND parent.status not in  ("Closed","Completed","Cancelled")
			GROUP BY
				parent.name, child.item_code
			""".format(
				conditions=conditions
			),
			values = values,
			as_dict=1,
		)  # nosec

def get_conditions(filters):
	conditions = []
	values = dict()
	
	if filters.get("from_date"):
		conditions.append("parent.transaction_date >= %(from_date)s")
		values['from_date'] = filters.get('from_date')
	
	if filters.get("to_date"):
		conditions.append("parent.transaction_date <= %(to_date)s")
		values['to_date'] = filters.get('to_date')
	
	if filters.get("cost_center"):
		# filters["cost_center"] = get_cost_centers_with_children(filters.cost_center)
		# frappe.throw(str(filters["cost_center"]))
		# cc = "'%(cost_center)s', ".join(filters.get('cost_center')) if filters.get('cost_center') else ""
		# conditions.append(f"parent.cost_center IN ('{str(cc)}')")
		conditions.append("parent.cost_center = %(cost_center)s")
		values['cost_center'] = filters.get('cost_center')
	
	if filters.get("project"):
		conditions.append("parent.project = %(project)s")
		values['project'] = filters.get('project')


	conditions_string = " AND ".join(conditions) if conditions else ""
	conditions_dict = {'conditions_string':conditions_string, 'values':values}
	# frappe.throw(str(conditions_dict))

	return conditions_dict


def get_mr_details_conditions(filters):
	conditions = []
	values = dict()
	
	if filters.get("from_date"):
		conditions.append("parent.transaction_date >= %(from_date)s")
		values['from_date'] = filters.get('from_date')
	
	if filters.get("to_date"):
		conditions.append("parent.transaction_date <= %(to_date)s")
		values['to_date'] = filters.get('to_date')

	if filters.get("project"):
		conditions.append("child.project = %(project)s")
		values['project'] = filters.get('project')

	if filters.get("cost_center"):
		conditions.append("child.cost_center = %(cost_center)s")
		values['cost_center'] = filters.get('cost_center')

	conditions_string = " AND ".join(conditions) if conditions else ""
	# frappe.throw(str(conditions_string))
	conditions_dict = {'conditions_string':conditions_string, 'values':values}
	return conditions_dict