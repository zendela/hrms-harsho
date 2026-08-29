import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import flt

from hrms.setup import get_salary_slip_loan_fields


def execute():
	if "lending" not in frappe.get_installed_apps() or not frappe.db.has_table("Loan Repayment"):
		return

	create_custom_fields(get_salary_slip_loan_fields(), ignore_validate=True)

	salary_slip_loan = frappe.qb.DocType("Salary Slip Loan")
	loan_repayment = frappe.qb.DocType("Loan Repayment")
	rows = (
		frappe.qb.from_(salary_slip_loan)
		.inner_join(loan_repayment)
		.on(loan_repayment.name == salary_slip_loan.loan_repayment_entry)
		.select(
			salary_slip_loan.name,
			loan_repayment.pending_principal_amount,
			loan_repayment.principal_amount_paid,
		)
		.where(salary_slip_loan.parenttype == "Salary Slip")
		.where(loan_repayment.docstatus == 1)
	).run(as_dict=True)

	for row in rows:
		opening_balance = flt(row.pending_principal_amount)
		frappe.db.set_value(
			"Salary Slip Loan",
			row.name,
			{
				"opening_principal_balance": opening_balance,
				"closing_principal_balance": max(
					opening_balance - flt(row.principal_amount_paid), 0
				),
			},
			update_modified=False,
		)

	if frappe.db.has_column("Salary Slip", "total_deductions_including_loan"):
		frappe.db.sql(
			"""
			UPDATE `tabSalary Slip`
			SET total_deductions_including_loan =
				COALESCE(total_deduction, 0) + COALESCE(total_loan_repayment, 0)
			"""
		)
