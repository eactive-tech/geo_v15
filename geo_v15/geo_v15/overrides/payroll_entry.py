import frappe
from dateutil.relativedelta import relativedelta
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	DATE_FORMAT,
	add_days,
	add_to_date,
	cint,
	comma_and,
	date_diff,
	flt,
	get_link_to_form,
	getdate,
)
import erpnext
from hrms.payroll.doctype.payroll_entry.payroll_entry import log_payroll_failure
from hrms.payroll.doctype.payroll_entry.payroll_entry import show_payroll_submission_status
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
# class CustomPayrollEntry(Document):
def submit_salary_slips_for_employees(payroll_entry, salary_slips, publish_progress=True):
    # frappe.throw("monkey patching")
    try:
        submitted = []
        unsubmitted = []
        frappe.flags.via_payroll_entry = True
        count = 0

        for entry in salary_slips:
            salary_slip = frappe.get_doc("Salary Slip", entry[0])
            if salary_slip.net_pay < 0:
                unsubmitted.append(entry[0])
            else:
                try:
                    salary_slip.submit()
                    submitted.append(salary_slip)
                except frappe.ValidationError:
                    unsubmitted.append(entry[0])

            count += 1
            if publish_progress:
                frappe.publish_progress(
                    count * 100 / len(salary_slips), title=_("Submitting Salary Slips...")
                )

        if submitted:
            # payroll_entry.make_accrual_jv_entry(submitted)
            for ss in salary_slips:
                salary_slip = frappe.get_doc("Salary Slip", ss[0])
                multiple_make_accrual_jv_entry(payroll_entry,salary_slip)
            payroll_entry.email_salary_slip(submitted)
            payroll_entry.db_set({"salary_slips_submitted": 1, "status": "Submitted", "error_message": ""})

        show_payroll_submission_status(submitted, unsubmitted, payroll_entry)

    except Exception as e:
        frappe.db.rollback()
        log_payroll_failure("submission", payroll_entry, e)

    finally:
        frappe.db.commit()  # nosemgrep
        frappe.publish_realtime("completed_salary_slip_submission", user=frappe.session.user)

    frappe.flags.via_payroll_entry = False

def multiple_make_accrual_jv_entry(payroll_entry,salary_slip):
	payroll_entry.check_permission("write")
	earnings = salary_slip.earnings
	deductions = salary_slip.deductions
	payroll_payable_account = payroll_entry.payroll_payable_account
	jv_name = ""
	precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")
	mfiscal_year=''
	fiscal_year = frappe.db.sql(f""" SELECT * FROM `tabFiscal Year` WHERE %s BETWEEN year_start_date AND year_end_date """,(payroll_entry.posting_date),as_dict=True)
	if fiscal_year:
		mfiscal_year=fiscal_year[0].name

	if earnings or deductions:
		journal_entry = frappe.new_doc("Journal Entry")
		journal_entry.voucher_type = "Journal Entry"
		journal_entry.voucher_entry_type = "Salary Process"
		journal_entry.branch = payroll_entry.branch
		journal_entry.fiscal_year = mfiscal_year
		journal_entry.user_remark = _("Accrual Journal Entry for salaries from {0} to {1}").format(
			payroll_entry.start_date, payroll_entry.end_date
		)
		journal_entry.company = payroll_entry.company
		journal_entry.posting_date = payroll_entry.posting_date
		accounting_dimensions = get_accounting_dimensions() or []

		accounts = []
		currencies = []
		payable_amount = 0
		multi_currency = 0
		company_currency = erpnext.get_company_currency(payroll_entry.company)

		# Earnings
		for acc_cc in earnings:
			# frappe.log_error(acc_cc,'salary slip33')
			
			payable_amount += flt(acc_cc.amount, precision)
			sc = frappe.get_doc("Salary Component", acc_cc.salary_component)
			
			accounts.append(
				payroll_entry.update_accounting_dimensions(
					{
						"account": sc.accounts[0].account,
						"party":salary_slip.employee,
						"party_type":'Employee',
						"exchange_rate": 1,
						"debit_in_account_currency": acc_cc.amount,
						"cost_center": salary_slip.payroll_cost_center or payroll_entry.cost_center,
						"project": payroll_entry.project,
					},
					accounting_dimensions,
				)
			)

		# Deductions
		for acc_cc in deductions:
			payable_amount -= flt(acc_cc.amount, precision)
			sc = frappe.get_doc("Salary Component", acc_cc.salary_component)
			
			accounts.append(
				payroll_entry.update_accounting_dimensions(
					{
						"account": sc.accounts[0].account,
						"party":salary_slip.employee,
						"party_type":'Employee',
						"exchange_rate": 1,
						"credit_in_account_currency": acc_cc.amount,
						"cost_center": salary_slip.payroll_cost_center or payroll_entry.cost_center,
						"project": payroll_entry.project,
					},
					accounting_dimensions,
				)
			)

		# Payable amount
		exchange_rate, payable_amt = payroll_entry.get_amount_and_exchange_rate_for_journal_entry(
			payroll_payable_account, payable_amount, company_currency, currencies
		)
		accounts.append(
			payroll_entry.update_accounting_dimensions(
				{
					"party":salary_slip.employee,
					"party_type":'Employee',
					"account": payroll_payable_account,
					"credit_in_account_currency": flt(payable_amt, precision),
					"exchange_rate": flt(exchange_rate),
					"cost_center": salary_slip.payroll_cost_center,
					"reference_type": payroll_entry.doctype,
					"reference_name": payroll_entry.name,
				},
				accounting_dimensions,
			)
		)

		journal_entry.set("accounts", accounts)
		if len(currencies) > 1:
			multi_currency = 1
		journal_entry.multi_currency = multi_currency
		journal_entry.title = payroll_payable_account
		journal_entry.save()

		try:
			# journal_entry.submit()
			jv_name = journal_entry.name
			# payroll_entry.update_salary_slip_status(jv_name=jv_name)
			set_journal_entry_in_salary_slips(salary_slip, jv_name=jv_name)
				
		except Exception as e:
			if type(e) in (str, list, tuple):
				frappe.msgprint(e)
			raise

	return jv_name


def set_journal_entry_in_salary_slips( salary_slip, jv_name=None):
	# SalarySlip = frappe.qb.DocType("Salary Slip")
	# (
	# 	frappe.qb.update(SalarySlip)
	# 	.set(SalarySlip.journal_entry, jv_name)
	# 	.where(SalarySlip.name.isin([salary_slip.name for salary_slip in submitted_salary_slips]))
	# ).run()
	ss_obj = frappe.get_doc("Salary Slip", salary_slip.name)
	frappe.db.set_value("Salary Slip", ss_obj.name, "journal_entry", jv_name)