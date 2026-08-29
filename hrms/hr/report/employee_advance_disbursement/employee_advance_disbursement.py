# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, getdate


def _build_reference(company, payroll_month):
	"""Generate reference label: COMPANY SALARY ADVANCE MONTH YEAR"""
	d = getdate(payroll_month)
	month_name = d.strftime("%B").upper()
	return f"{company.upper()} SALARY ADVANCE {month_name} {d.year}"


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Reference"),
			"fieldname": "reference",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Bank Code"),
			"fieldname": "bank_code",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Bank Account"),
			"fieldname": "bank_account",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


def get_data(filters):
	payroll_month = filters.get("payroll_month")
	company = filters.get("company")

	if not payroll_month:
		frappe.throw(_("Payroll Month is required"))

	reference = filters.get("reference") or _build_reference(company, payroll_month)

	month_start = get_first_day(getdate(payroll_month))
	month_end = get_last_day(getdate(payroll_month))

	# Fetch all approved/submitted advances for the payroll month. Paid advances
	# must remain visible because automatic disbursement pays them during approval.
	advances = frappe.db.sql(
		"""
		SELECT
			ea.employee_name,
			COALESCE(NULLIF(emp.bank_code, ''), emp.bank_name) AS bank_code,
			emp.bank_ac_no  AS bank_account,
			ea.advance_amount AS amount
		FROM `tabEmployee Advance` ea
		INNER JOIN `tabEmployee` emp ON emp.name = ea.employee
		WHERE
			ea.docstatus = 1
			AND ea.company = %(company)s
			AND ea.payroll_month BETWEEN %(month_start)s AND %(month_end)s
		ORDER BY ea.employee_name ASC
		""",
		{
			"company": company,
			"month_start": month_start,
			"month_end": month_end,
		},
		as_dict=True,
	)

	if not advances:
		return []

	data = []
	total = 0.0

	for row in advances:
		data.append(
			{
				"employee_name": row.employee_name,
				"reference": reference,
				"bank_code": row.bank_code or "",
				"bank_account": row.bank_account or "",
				"amount": flt(row.amount),
			}
		)
		total += flt(row.amount)

	# Totals row — blank label columns, amount in the Amount column
	data.append(
		{
			"employee_name": "",
			"reference": "",
			"bank_code": "",
			"bank_account": "",
			"amount": total,
		}
	)

	return data
