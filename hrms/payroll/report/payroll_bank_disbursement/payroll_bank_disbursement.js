/* eslint-disable */
frappe.query_reports["Payroll Bank Disbursement"] = {
  onload(report) {
    report.page.add_inner_button(__("Download CSV"), () => {
      const f = report.get_values() || {};
      frappe.call({
        method: "hrms_ext.payroll.bank_export.export_bank_csv",
        args: { filters: f },
        freeze: true
      }).then(r => {
        if (r.message && r.message.file_url) {
          window.open(r.message.file_url, "_blank");
        }
      });
    });
  },
  filters: [
    { fieldname:"payroll_entry", label: __("Payroll Entry"), fieldtype:"Link", options:"Payroll Entry" },
    { fieldname:"company", label: __("Company"), fieldtype:"Link", options:"Company" },
    { fieldname:"bank_name", label: __("Bank"), fieldtype:"Data" }
  ]
};
