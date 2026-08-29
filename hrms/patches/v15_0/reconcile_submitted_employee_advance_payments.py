import frappe
from frappe.utils import flt


def execute():
	"""Reconcile stale Employee Advances that already have submitted payments."""
	advances = frappe.db.sql(
		"""
		SELECT DISTINCT ea.name
		FROM `tabEmployee Advance` ea
		INNER JOIN `tabPayment Entry Reference` per
			ON per.reference_doctype = 'Employee Advance'
			AND per.reference_name = ea.name
		INNER JOIN `tabPayment Entry` pe
			ON pe.name = per.parent
			AND pe.docstatus = 1
		WHERE ea.docstatus = 1
			AND (
				COALESCE(ea.paid_amount, 0) != COALESCE(ea.advance_amount, 0)
				OR ea.status = 'Unpaid'
			)
		""",
		pluck=True,
	)

	for advance_name in advances:
		try:
			advance = frappe.get_doc("Employee Advance", advance_name)
			advance.set_total_advance_paid()
			advance.reload()

			precision = advance.precision("paid_amount")
			if flt(advance.paid_amount, precision) != flt(advance.advance_amount, precision):
				frappe.log_error(
					message=(
						f"Employee Advance {advance.name} has a submitted Payment Entry, but its "
						"Advance Payment Ledger does not contain the full amount. Repost the "
						"Accounting Ledger for its submitted Payment Entry."
					),
					title="Employee Advance payment needs ledger repost",
				)
		except Exception:
			frappe.log_error(
				title=f"Failed to reconcile Employee Advance {advance_name}"
			)
