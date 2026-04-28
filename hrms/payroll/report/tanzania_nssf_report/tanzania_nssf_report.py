# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

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
	for f in ("payroll_month", "company", "nssf_employee_component"):
		if not filters.get(f):
			frappe.throw(_("{0} is required").format(f.replace("_", " ").title()))


def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": _("Gross Pay"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 140},
		{"label": _("Employee NSSF (10%)"), "fieldname": "nssf_employee", "fieldtype": "Currency", "width": 150},
		{"label": _("Employer NSSF (10%)"), "fieldname": "nssf_employer", "fieldtype": "Currency", "width": 150},
		{"label": _("Total NSSF"), "fieldname": "nssf_total", "fieldtype": "Currency", "width": 130},
		{"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 160},
	]


def get_data(filters):
	slips = get_salary_slips(filters["company"], filters["payroll_month"])
	if not slips:
		return []

	slip_names = [s.name for s in slips]
	employee_map = get_component_amounts_bulk(slip_names, filters["nssf_employee_component"])
	employer_rate = flt(filters.get("nssf_employer_rate") or 10) / 100.0

	data = []
	for slip in slips:
		emp_nssf = employee_map.get(slip.name, 0.0)
		er_nssf  = flt(slip.gross_pay) * employer_rate
		data.append({
			"employee":      slip.employee,
			"employee_name": slip.employee_name,
			"department":    slip.department,
			"gross_pay":     flt(slip.gross_pay),
			"nssf_employee": emp_nssf,
			"nssf_employer": er_nssf,
			"nssf_total":    emp_nssf + er_nssf,
			"salary_slip":   slip.name,
		})

	# Totals row
	data.append({
		"employee":      "",
		"employee_name": frappe.bold(_("Total")),
		"department":    "",
		"gross_pay":     sum(r["gross_pay"] for r in data),
		"nssf_employee": sum(r["nssf_employee"] for r in data),
		"nssf_employer": sum(r["nssf_employer"] for r in data),
		"nssf_total":    sum(r["nssf_total"] for r in data),
		"salary_slip":   "",
	})

	return data


def get_summary(data):
	if not data:
		return []
	rows = [r for r in data if r.get("employee")]
	return [
		{"label": _("Total Employee NSSF"), "value": sum(r["nssf_employee"] for r in rows), "datatype": "Currency", "indicator": "orange"},
		{"label": _("Total Employer NSSF"), "value": sum(r["nssf_employer"] for r in rows), "datatype": "Currency", "indicator": "orange"},
		{"label": _("Total NSSF Payable"), "value": sum(r["nssf_total"] for r in rows), "datatype": "Currency", "indicator": "red"},
		{"label": _("Employees"), "value": len(rows), "datatype": "Int", "indicator": "green"},
	]
