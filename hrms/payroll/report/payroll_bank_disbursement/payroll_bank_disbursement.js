frappe.query_reports["Payroll Bank Disbursement"] = {
	onload(report) {
		report.page.add_inner_button(__("Download CSV"), () => {
			const filters = report.get_values() || {};
			frappe.call({
				method:
					"hrms.payroll.report.payroll_bank_disbursement.payroll_bank_disbursement.export_bank_csv",
				args: { filters },
				freeze: true,
				freeze_message: __("Preparing bank file..."),
			}).then((response) => {
				if (response.message?.file_url) {
					window.open(response.message.file_url, "_blank");
				}
			});
		});
	},
	filters: [
		{
			fieldname: "payroll_entry",
			label: __("Payroll Entry"),
			fieldtype: "Link",
			options: "Payroll Entry",
			reqd: 1,
			get_query: () => ({ filters: { docstatus: 1, salary_slips_submitted: 1 } }),
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{ fieldname: "bank_name", label: __("Bank"), fieldtype: "Data" },
		{ fieldname: "branch_code", label: __("Branch Code"), fieldtype: "Data" },
	],
};
