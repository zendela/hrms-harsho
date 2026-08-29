import frappe


def execute():
	"""Refresh advances using submitted Payment Entry references as a ledger fallback."""
	advance_names = frappe.db.sql(
		"""
		SELECT DISTINCT per.reference_name
		FROM `tabPayment Entry` pe
		INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
		INNER JOIN `tabEmployee Advance` ea ON ea.name = per.reference_name
		WHERE pe.docstatus = 1
			AND ea.docstatus = 1
			AND per.reference_doctype = 'Employee Advance'
		""",
		pluck=True,
	)

	for advance_name in advance_names:
		try:
			frappe.get_doc("Employee Advance", advance_name).set_total_advance_paid()
		except Exception:
			frappe.log_error(title=f"Failed to reconcile Employee Advance {advance_name}")
