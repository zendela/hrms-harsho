// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Tanzania NSSF Report"] = {
	filters: [
		{
			fieldname: "payroll_month",
			label: __("Payroll Month"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "nssf_employee_component",
			label: __("NSSF Employee Component"),
			fieldtype: "Link",
			options: "Salary Component",
			reqd: 1,
			default: "NSSF Employee",
		},
		{
			fieldname: "nssf_employer_rate",
			label: __("Employer Contribution Rate (%)"),
			fieldtype: "Float",
			default: 10,
			description: __("Employer NSSF rate — computed as % of gross pay"),
		},
	],
};
