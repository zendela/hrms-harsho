// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Advance Disbursement"] = {
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
			fieldname: "reference",
			label: __("Reference"),
			fieldtype: "Data",
			description: __("Payment batch label printed in the Reference column (e.g. HMC SALARY MARCH 2026)"),
		},
	],
};
