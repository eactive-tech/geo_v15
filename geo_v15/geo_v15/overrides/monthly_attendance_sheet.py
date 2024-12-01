import frappe
from frappe import _
from frappe.query_builder.functions import Extract

Filters = frappe._dict

status_map = {
	"Present": "P",
	"Absent": "A",
	"Half Day": "HD",
	"Work From Home": "WFH",
	"On Leave": "L",
	"Holiday": "H",
	"Weekly Off": "WO",
}

day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_attendance_records(filters: Filters) -> list[dict]:
	up = frappe.db.get_all("User Permission", filters = [["User Permission","user","=",frappe.session.user], ["User Permission","allow","=","Branch"]], fields= ["for_value"])
	allowed_branch = [rec.for_value for rec in up]

	Attendance = frappe.qb.DocType("Attendance")
	query = (
		frappe.qb.from_(Attendance)
		.select(
			Attendance.employee,
			Extract("day", Attendance.attendance_date).as_("day_of_month"),
			Attendance.status,
			Attendance.shift,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.company.isin(filters.companies))
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
	)

	if filters.employee:
		query = query.where(Attendance.employee == filters.employee)
	query = query.orderby(Attendance.employee, Attendance.attendance_date)
	
	if len(allowed_branch) > 0:
		query = query.where((Attendance.branch.isin(allowed_branch) ))

	return query.run(as_dict=1)