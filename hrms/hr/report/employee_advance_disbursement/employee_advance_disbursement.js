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
			description: __("Auto-generated from company + payroll month. Edit to override."),
		},
	],

	onload: function (report) {
		// Set initial value after filters have rendered
		setTimeout(() => _set_reference(), 300);

		// Regenerate whenever company or payroll_month changes
		report.page.wrapper.on(
			"change",
			"[data-fieldname='company'] input, [data-fieldname='payroll_month'] input",
			() => _set_reference(),
		);
	},
};

function _set_reference() {
	const company = frappe.query_report.get_filter_value("company");
	const payroll_month = frappe.query_report.get_filter_value("payroll_month");

	if (!company || !payroll_month) return;

	const d = frappe.datetime.str_to_obj(payroll_month);
	const month_name = d.toLocaleString("en-US", { month: "long" }).toUpperCase();
	const year = d.getFullYear();

	frappe.query_report.set_filter_value(
		"reference",
		`${company.toUpperCase()} SALARY ADVANCE ${month_name} ${year}`,
	);
}
