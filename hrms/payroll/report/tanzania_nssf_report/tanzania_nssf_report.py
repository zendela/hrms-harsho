# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, get_last_day, getdate

from hrms.payroll.report.tanzania_statutory_utils import get_component_amounts_bulk


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
		{"label": _("Rate / Fixed"), "fieldname": "contribution_basis", "fieldtype": "Data", "width": 110},
		{"label": _("Employee NSSF"), "fieldname": "nssf_employee", "fieldtype": "Currency", "width": 140},
		{"label": _("Employer NSSF"), "fieldname": "nssf_employer", "fieldtype": "Currency", "width": 140},
		{"label": _("Total NSSF"), "fieldname": "nssf_total", "fieldtype": "Currency", "width": 130},
		{"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 160},
	]


def get_data(filters):
	month_start = get_first_day(getdate(filters["payroll_month"]))
	month_end = get_last_day(getdate(filters["payroll_month"]))

	# Only employees enrolled in NSSF
	slips = frappe.db.sql(
		"""
		SELECT
			ss.name, ss.employee, ss.employee_name, ss.department, ss.gross_pay,
			ss.contribution_in_percent, ss.has_fixed_contribution,
			ss.contribution_fixed_amount
		FROM `tabSalary Slip` ss
		WHERE
			ss.docstatus = 1
			AND ss.company = %(company)s
			AND ss.start_date >= %(month_start)s
			AND ss.end_date <= %(month_end)s
			AND ss.has_nssf = 1
		ORDER BY ss.employee_name ASC
		""",
		{"company": filters["company"], "month_start": month_start, "month_end": month_end},
		as_dict=True,
	)

	if not slips:
		return []

	# Pull actual deducted amounts from salary detail rows
	slip_names = [s.name for s in slips]
	deducted_map = get_component_amounts_bulk(slip_names, filters["nssf_employee_component"])

	data = []
	for slip in slips:
		gross = flt(slip.gross_pay)

		# Prefer the actual deducted amount; fall back to computing from employee settings
		emp_nssf = deducted_map.get(slip.name, 0.0)
		if not emp_nssf:
			if slip.has_fixed_contribution and flt(slip.contribution_fixed_amount) > 0:
				emp_nssf = flt(slip.contribution_fixed_amount)
			else:
				rate = flt(slip.contribution_in_percent) or 10.0
				emp_nssf = gross * (rate / 100.0)

		# Employer mirrors employee contribution (equal-share NSSF)
		er_nssf = emp_nssf

		if slip.has_fixed_contribution and flt(slip.contribution_fixed_amount) > 0:
			basis = _("Fixed")
		else:
			rate = flt(slip.contribution_in_percent) or 10
			basis = "{}%".format(int(rate))

		data.append({
			"employee":           slip.employee,
			"employee_name":      slip.employee_name,
			"department":         slip.department,
			"gross_pay":          gross,
			"contribution_basis": basis,
			"nssf_employee":      emp_nssf,
			"nssf_employer":      er_nssf,
			"nssf_total":         emp_nssf + er_nssf,
			"salary_slip":        slip.name,
		})

	# Totals row
	data.append({
		"employee":           "",
		"employee_name":      frappe.bold(_("Total")),
		"department":         "",
		"gross_pay":          sum(r["gross_pay"] for r in data),
		"contribution_basis": "",
		"nssf_employee":      sum(r["nssf_employee"] for r in data),
		"nssf_employer":      sum(r["nssf_employer"] for r in data),
		"nssf_total":         sum(r["nssf_total"] for r in data),
		"salary_slip":        "",
	})

	return data


def get_summary(data):
	if not data:
		return []
	rows = [r for r in data if r.get("employee")]
	return [
		{"label": _("NSSF Members"), "value": len(rows), "datatype": "Int", "indicator": "green"},
		{"label": _("Total Employee NSSF"), "value": sum(r["nssf_employee"] for r in rows), "datatype": "Currency", "indicator": "orange"},
		{"label": _("Total Employer NSSF"), "value": sum(r["nssf_employer"] for r in rows), "datatype": "Currency", "indicator": "orange"},
		{"label": _("Total NSSF Payable"), "value": sum(r["nssf_total"] for r in rows), "datatype": "Currency", "indicator": "red"},
	]
