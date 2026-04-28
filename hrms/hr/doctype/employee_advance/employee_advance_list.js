// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings["Employee Advance"] = {
	add_fields: ["status", "advance_amount", "paid_amount", "currency"],

	get_indicator: function (doc) {
		const map = {
			"Unpaid":                    "orange",
			"Paid":                      "green",
			"Claimed":                   "blue",
			"Returned":                  "gray",
			"Partly Claimed and Returned": "yellow",
			"Cancelled":                 "red",
			"Draft":                     "red",
		};
		const color = map[doc.status] || "gray";
		return [__(doc.status), color, "status,=," + doc.status];
	},

	onload: function (listview) {
		listview.page.add_action_item(__("Mark as Paid"), () => {
			const selected = listview.get_checked_items();
			if (!selected.length) {
				frappe.msgprint(__("Please select at least one Employee Advance."));
				return;
			}

			const unpaid = selected.filter((r) => r.status === "Unpaid");
			if (!unpaid.length) {
				frappe.msgprint(__("None of the selected advances are in Unpaid status."));
				return;
			}

			const dialog = new frappe.ui.Dialog({
				title: __("Bulk Mark as Paid"),
				fields: [
					{
						fieldname: "info",
						fieldtype: "HTML",
						options: `<p class="text-muted">${__("{0} Unpaid advance(s) selected.", [unpaid.length])}</p>`,
					},
					{
						fieldname: "mode_of_payment",
						label: __("Mode of Payment"),
						fieldtype: "Link",
						options: "Mode of Payment",
					},
					{
						fieldname: "bank_account",
						label: __("Bank Account"),
						fieldtype: "Link",
						options: "Bank Account",
						description: __("Leave blank to use the Company default cash account."),
					},
				],
				primary_action_label: __("Create Payment Entry"),
				primary_action(values) {
					dialog.hide();
					frappe.call({
						method: "hrms.hr.doctype.employee_advance.employee_advance.bulk_mark_as_paid",
						freeze: true,
						freeze_message: __("Creating Payment Entry..."),
						args: {
							advance_names: unpaid.map((r) => r.name),
							mode_of_payment: values.mode_of_payment || null,
							bank_account: values.bank_account || null,
						},
						callback(r) {
							if (r.message) {
								frappe.show_alert({
									message: __(
										"Payment Entry {0} created and submitted.",
										[`<a href="/app/payment-entry/${r.message}">${r.message}</a>`]
									),
									indicator: "green",
								});
								listview.refresh();
							}
						},
					});
				},
			});
			dialog.show();
		});
	},
};
