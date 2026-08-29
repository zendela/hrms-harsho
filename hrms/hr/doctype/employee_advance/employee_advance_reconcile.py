import frappe
from frappe import _
from frappe.utils import flt


def _reconcile_doc(ea):
	"""Recalculate payment values from the accounting advance ledger."""
	ea.set_total_advance_paid()
	ea.reload()
	return {
		"paid": flt(ea.paid_amount),
		"outstanding": flt(ea.advance_amount) - flt(ea.paid_amount),
		"status": ea.status,
	}


def update_payment_status(doc, method=None):
	"""Keep linked Employee Advances synchronized with Payment Entry lifecycle events."""
	advance_names = {
		reference.reference_name
		for reference in doc.get("references", [])
		if reference.reference_doctype == "Employee Advance" and reference.reference_name
	}

	for advance_name in advance_names:
		advance = frappe.get_doc("Employee Advance", advance_name)
		if advance.docstatus == 1:
			_reconcile_doc(advance)


@frappe.whitelist()
def refresh_payments(advance: str):
	frappe.only_for(("Accounts User", "Accounts Manager", "System Manager"))

	if not advance:
		frappe.throw(_("Advance name is required"))

	ea = frappe.get_doc("Employee Advance", advance)
	if ea.docstatus != 1:
		frappe.throw(_("Only submitted Employee Advances can be reconciled"))

	result = _reconcile_doc(ea)

	return {
		"name": ea.name,
		"status": ea.status,
		"paid_amount": result["paid"],
		"outstanding_amount": result["outstanding"],
	}
