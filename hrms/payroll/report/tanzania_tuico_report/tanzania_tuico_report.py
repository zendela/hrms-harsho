# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, getdate


def execute(filters=None):
	filters = filters or {}
	validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	summary = get_summary(data)
	return columns, data, None, None, summary


def validate_filters(filters):
	for f in ("payroll_month", "company", "tuico_component"):
		if not filters.get(f):
			frappe.throw(_("{0} is required").format(f.replace("_", " ").title()))


def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": _("Gross Pay"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 140},
		{"label": _("TUICO"), "fieldname": "tuico", "fieldtype": "Currency", "width": 130},
		{"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 160},
	]


def get_data(filters):
	month_start = get_first_day(getdate(filters["payroll_month"]))
	month_end = get_last_day(getdate(filters["payroll_month"]))

	# The TUICO component on the submitted salary slip determines membership.
	slips = frappe.db.sql(
		"""
		SELECT
			ss.name, ss.employee, ss.employee_name,
			ss.department, ss.gross_pay,
			COALESCE(SUM(sd.amount), 0) AS tuico
		FROM `tabSalary Slip` ss
		INNER JOIN `tabSalary Detail` sd
			ON sd.parent = ss.name
			AND sd.parenttype = 'Salary Slip'
			AND sd.parentfield = 'deductions'
			AND sd.salary_component = %(tuico_component)s
		WHERE
			ss.docstatus = 1
			AND ss.company = %(company)s
			AND ss.start_date >= %(month_start)s
			AND ss.end_date <= %(month_end)s
		GROUP BY
			ss.name, ss.employee, ss.employee_name,
			ss.department, ss.gross_pay
		ORDER BY ss.employee_name ASC
		""",
		{
			"company": filters["company"],
			"month_start": month_start,
			"month_end": month_end,
			"tuico_component": filters["tuico_component"],
		},
		as_dict=True,
	)

	if not slips:
		return []

	data = []
	for slip in slips:
		data.append({
			"employee":      slip.employee,
			"employee_name": slip.employee_name,
			"department":    slip.department,
			"gross_pay":     flt(slip.gross_pay),
			"tuico":         flt(slip.tuico),
			"salary_slip":   slip.name,
		})

	# Totals row
	data.append({
		"employee":      "",
		"employee_name": frappe.bold(_("Total")),
		"department":    "",
		"gross_pay":     sum(r["gross_pay"] for r in data),
		"tuico":         sum(r["tuico"] for r in data),
		"salary_slip":   "",
	})

	return data


def get_summary(data):
	if not data:
		return []
	rows = [r for r in data if r.get("employee")]
	return [
		{"label": _("TUICO Members"), "value": len(rows), "datatype": "Int", "indicator": "green"},
		{"label": _("Total TUICO"), "value": sum(r["tuico"] for r in rows), "datatype": "Currency", "indicator": "orange"},
	]
