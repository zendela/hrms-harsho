import frappe

from hrms.payroll.report.payroll_bank_disbursement.payroll_bank_disbursement import (
	export_bank_csv as export_payroll_bank_csv,
)


@frappe.whitelist()
def export_bank_csv(filters=None):
	"""Backward-compatible endpoint for existing integrations."""
	return export_payroll_bank_csv(filters)
