# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Shared utilities for Tanzania statutory payroll reports.
"""

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, getdate


def get_statutory_filters():
	"""Standard filters shared by all Tanzania statutory reports."""
	return [
		{
			"fieldname": "payroll_month",
			"label": __("Payroll Month"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.utils.get_first_day(frappe.utils.nowdate()),
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
		},
	]


def get_salary_slips(company, payroll_month):
	"""Return submitted salary slips for the given company and payroll month."""
	month_start = get_first_day(getdate(payroll_month))
	month_end = get_last_day(getdate(payroll_month))

	return frappe.db.sql(
		"""
		SELECT
			ss.name,
			ss.employee,
			ss.employee_name,
			ss.department,
			ss.gross_pay,
			ss.net_pay,
			ss.total_deduction
		FROM `tabSalary Slip` ss
		WHERE
			ss.docstatus = 1
			AND ss.company = %(company)s
			AND ss.start_date >= %(month_start)s
			AND ss.end_date <= %(month_end)s
		ORDER BY ss.employee_name ASC
		""",
		{"company": company, "month_start": month_start, "month_end": month_end},
		as_dict=True,
	)


def get_component_amount(slip_name, component_name):
	"""Return the deduction amount for a specific salary component on a slip."""
	result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(sd.amount), 0)
		FROM `tabSalary Detail` sd
		WHERE
			sd.parent = %(slip)s
			AND sd.parentfield = 'deductions'
			AND sd.salary_component = %(component)s
		""",
		{"slip": slip_name, "component": component_name},
	)
	return flt(result[0][0]) if result else 0.0


def get_component_amounts_bulk(slip_names, component_name):
	"""Return {slip_name: amount} for a component across multiple slips."""
	if not slip_names:
		return {}
	result = frappe.db.sql(
		"""
		SELECT sd.parent, COALESCE(SUM(sd.amount), 0) AS amount
		FROM `tabSalary Detail` sd
		WHERE
			sd.parent IN ({placeholders})
			AND sd.parentfield = 'deductions'
			AND sd.salary_component = %(component)s
		GROUP BY sd.parent
		""".format(placeholders=", ".join(["%s"] * len(slip_names))),
		tuple(slip_names) + (component_name,),
		as_dict=True,
	)
	return {r.parent: flt(r.amount) for r in result}
