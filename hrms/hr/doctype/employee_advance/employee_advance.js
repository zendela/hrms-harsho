// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Advance", {
	setup: function (frm) {
		frm.set_query("employee", function () {
			return {
				filters: {
					status: "Active",
				},
			};
		});

		frm.set_query("advance_account", function () {
			if (!frm.doc.employee) {
				frappe.msgprint(__("Please select employee first"));
			}
			let company_currency = erpnext.get_currency(frm.doc.company);
			let currencies = [company_currency];
			if (frm.doc.currency && frm.doc.currency != company_currency) {
				currencies.push(frm.doc.currency);
			}

			return {
				filters: {
					root_type: "Asset",
					is_group: 0,
					company: frm.doc.company,
					account_currency: ["in", currencies],
					account_type: "Receivable",
				},
			};
		});

		frm.set_query("salary_component", function () {
			return {
				filters: {
					type: "Deduction",
				},
			};
		});
	},

	refresh: function (frm) {
		if (frm.doc.__islocal) {
			frm.trigger("set_payroll_month");
		}

		if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.paid_amount) < flt(frm.doc.advance_amount) &&
			frappe.model.can_create("Payment Entry")
		) {
			frm.add_custom_button(
				__("Payment"),
				function () {
					frm.events.make_payment_entry(frm);
				},
				__("Create"),
			);
		} else if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount) &&
			frappe.model.can_create("Expense Claim")
		) {
			frm.add_custom_button(
				__("Expense Claim"),
				function () {
					frm.events.make_expense_claim(frm);
				},
				__("Create"),
			);
		}

		if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount)
		) {
			if (
				frm.doc.repay_unclaimed_amount_from_salary == 0 &&
				frappe.model.can_create("Journal Entry")
			) {
				frm.add_custom_button(
					__("Return"),
					function () {
						frm.trigger("make_return_entry");
					},
					__("Create"),
				);
			} else if (
				frm.doc.repay_unclaimed_amount_from_salary == 1 &&
				frappe.model.can_create("Additional Salary")
			) {
				frm.add_custom_button(
					__("Deduction from Salary"),
					function () {
						frm.events.make_deduction_via_additional_salary(frm);
					},
					__("Create"),
				);
			}
		}
	},

	
	make_deduction_via_additional_salary: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.create_return_through_additional_salary",
			args: {
				doc: frm.doc,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_payment_entry: function (frm) {
		let method = "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee";
		if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "hrms.hr.doctype.employee_advance.employee_advance.make_bank_entry";
		}
		return frappe.call({
			method: method,
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_expense_claim: function (frm) {
		return frappe.call({
			method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim",
			args: {
				employee_name: frm.doc.employee,
				company: frm.doc.company,
				employee_advance_name: frm.doc.name,
				posting_date: frm.doc.posting_date,
				paid_amount: frm.doc.paid_amount,
				claimed_amount: frm.doc.claimed_amount,
				return_amount: frm.doc.return_amount,
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_return_entry: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.make_return_entry",
			args: {
				employee: frm.doc.employee,
				company: frm.doc.company,
				employee_advance_name: frm.doc.name,
				return_amount: flt(frm.doc.paid_amount - frm.doc.claimed_amount),
				advance_account: frm.doc.advance_account,
				mode_of_payment: frm.doc.mode_of_payment,
				currency: frm.doc.currency,
				exchange_rate: frm.doc.exchange_rate,
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	employee: function (frm) {
		if (frm.doc.employee) frm.trigger("get_employee_currency");
	},

	posting_date: function (frm) {
		frm.trigger("set_payroll_month");
	},

	set_payroll_month: function (frm) {
		if (frm.doc.posting_date) {
			// Default payroll_month to the first day of the posting_date month
			const d = frappe.datetime.str_to_obj(frm.doc.posting_date);
			const first_day = frappe.datetime.obj_to_str(
				new Date(d.getFullYear(), d.getMonth(), 1)
			);
			if (!frm.doc.payroll_month) {
				frm.set_value("payroll_month", first_day);
			}
		}
	},

	get_employee_currency: function (frm) {
		frappe.db.get_value(
			"Salary Structure Assignment",
			{ employee: frm.doc.employee, docstatus: 1 },
			"currency",
			(r) => {
				if (r.currency) frm.set_value("currency", r.currency);
				else frm.set_value("currency", erpnext.get_currency(frm.doc.company));
				frm.refresh_fields();
			},
		);
	},

	currency: function (frm) {
		if (frm.doc.currency) {
			var from_currency = frm.doc.currency;
			var company_currency;
			if (!frm.doc.company) {
				company_currency = erpnext.get_currency(frappe.defaults.get_default("Company"));
			} else {
				company_currency = erpnext.get_currency(frm.doc.company);
			}
			if (from_currency != company_currency) {
				frm.events.set_exchange_rate(frm, from_currency, company_currency);
			} else {
				frm.set_value("exchange_rate", 1.0);
				frm.set_df_property("exchange_rate", "hidden", 1);
				frm.set_df_property("exchange_rate", "description", "");
			}
			frm.refresh_fields();
		}
	},

	set_exchange_rate: function (frm, from_currency, company_currency) {
		frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				from_currency: from_currency,
				to_currency: company_currency,
			},
			callback: function (r) {
				frm.set_value("exchange_rate", flt(r.message));
				frm.set_df_property("exchange_rate", "hidden", 0);
				frm.set_df_property(
					"exchange_rate",
					"description",
					"1 " + frm.doc.currency + " = [?] " + company_currency,
				);
			},
		});
	},
});


frappe.ui.form.on('Employee Advance', {
  employee: refresh_cap,
  posting_date: refresh_cap,
  refresh(frm) { refresh_cap(frm); }
});

function refresh_cap(frm) {
  if (!frm.doc.employee) return;
  frappe.call({
    method: 'hrms.hr.doctype.employee_advance.employee_advance_cap.compute_advance_cap',
    args: { employee: frm.doc.employee, posting_date: frm.doc.posting_date },
  }).then(r => {
    const m = r.message || {};
    frm.set_value('eligible_amount', m.cap_amount || 0);
    frm.set_value('cap_basis', m.basis || '');
    frm.set_value('cap_percent', m.percent || 0);
    frm.set_value('cap_source_note', m.note || '');
    // Suggest the cap only once; never overwrite an employee's saved request.
    if (frm.is_new() && !flt(frm.doc.advance_amount)) {
      frm.set_value('advance_amount', m.cap_amount || 0);
    }
  });
}
frappe.ui.form.on('Employee Advance', {
  refresh(frm) {
    // Show only for submitted docs
    if (
      frm.doc.docstatus === 1 &&
      frappe.user_roles.some((role) =>
        ['Accounts User', 'Accounts Manager', 'System Manager'].includes(role)
      )
    ) {
      frm.add_custom_button(__('Refresh Payment Status'), () => {
        frappe.call({
          method: 'hrms.hr.doctype.employee_advance.employee_advance_reconcile.refresh_payments',
          args: { advance: frm.doc.name },
          freeze: true,
          freeze_message: __('Recalculating payment status...')
        }).then(r => {
          const m = r.message || {};
          frm.reload_doc().then(() => {
            frappe.msgprint({
              title: __('Payment Status Updated'),
              message: __(
                'Status: <b>{0}</b><br>Paid: <b>{1}</b><br>Outstanding: <b>{2}</b>',
                [
                  frm.doc.status || m.status || '-',
                  frappe.format((frm.doc.paid_amount ?? m.paid_amount ?? 0), {fieldtype:'Currency', options: frm.doc.currency}),
                  frappe.format((frm.doc.outstanding_amount ?? m.outstanding_amount ?? 0), {fieldtype:'Currency', options: frm.doc.currency})
                ]
              ),
              indicator: (frm.doc.status === 'Paid' ? 'green' : 'orange')
            });
          });
        });
      }).addClass('btn-primary');
    }
  }
});
