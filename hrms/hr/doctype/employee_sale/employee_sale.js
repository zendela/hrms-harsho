// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Sale", {
	refresh(frm) {
		if (frm.doc.__islocal) {
			// Default payroll_month to first day of current month
			if (!frm.doc.payroll_month) {
				frm.set_value("payroll_month", frappe.datetime.month_start());
			}
			// Default currency to company currency
			if (!frm.doc.currency && frm.doc.company) {
				frm.trigger("company");
			}
		}
	},

	company(frm) {
		if (frm.doc.company) {
			frappe.db.get_value("Company", frm.doc.company, "default_currency", (r) => {
				if (r && r.default_currency) {
					frm.set_value("currency", r.default_currency);
				}
			});
		}
	},
});

frappe.ui.form.on("Employee Sale Item", {
	qty(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},

	unit_price(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},

	items_remove(frm) {
		calculate_total(frm);
	},
});

function calculate_row_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const amount = flt(row.qty) * flt(row.unit_price);
	frappe.model.set_value(cdt, cdn, "amount", amount);
	calculate_total(frm);
}

function calculate_total(frm) {
	let total = 0;
	(frm.doc.items || []).forEach((row) => {
		total += flt(row.amount);
	});
	frm.set_value("total_amount", total);
}
