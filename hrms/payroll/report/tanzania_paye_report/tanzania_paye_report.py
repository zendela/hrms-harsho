# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, getdate

from hrms.payroll.report.tanzania_statutory_utils import (
	get_component_amounts_bulk,
	get_salary_slips,
)


def execute(filters=None):
	filters = filters or {}
	validate_filters(filters)
	columns = get_columns()
	data = get_data(filters)
	summary = get_summary(data)
	return columns, data, None, None, summary


def validate_filters(filters):
	if not filters.get("payroll_month"):
		frappe.throw(_("Payroll Month is required"))
	if not filters.get("company"):
		frappe.throw(_("Company is required"))
	if not filters.get("paye_component"):
		frappe.throw(_("PAYE Salary Component is required"))


def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": _("Gross Pay"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 140},
		{"label": _("PAYE"), "fieldname": "paye", "fieldtype": "Currency", "width": 130},
		{"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 160},
	]


def get_data(filters):
	slips = get_salary_slips(filters["company"], filters["payroll_month"])
	if not slips:
		return []

	slip_names = [s.name for s in slips]
	paye_map = get_component_amounts_bulk(slip_names, filters["paye_component"])

	data = []
	for slip in slips:
		paye = paye_map.get(slip.name, 0.0)
		data.append({
			"employee":      slip.employee,
			"employee_name": slip.employee_name,
			"department":    slip.department,
			"gross_pay":     flt(slip.gross_pay),
			"paye":          paye,
			"salary_slip":   slip.name,
		})

	# Totals row
	data.append({
		"employee":      "",
		"employee_name": frappe.bold(_("Total")),
		"department":    "",
		"gross_pay":     sum(r["gross_pay"] for r in data),
		"paye":          sum(r["paye"] for r in data),
		"salary_slip":   "",
	})

	return data


def get_summary(data):
	if not data:
		return []
	total_paye = sum(r.get("paye", 0) for r in data if r.get("employee"))
	total_gross = sum(r.get("gross_pay", 0) for r in data if r.get("employee"))
	return [
		{"label": _("Total Gross Pay"), "value": total_gross, "datatype": "Currency", "indicator": "blue"},
		{"label": _("Total PAYE"), "value": total_paye, "datatype": "Currency", "indicator": "orange"},
		{"label": _("Employees"), "value": len([r for r in data if r.get("employee")]), "datatype": "Int", "indicator": "green"},
	]
