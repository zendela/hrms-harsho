import frappe
from frappe.tests.utils import FrappeTestCase

from hrms.payroll.doctype.payroll_entry.payroll_entry import (
	PayrollEntry,
	get_start_end_dates,
	validate_payment_status_transition,
)


class TestPayrollPaymentControls(FrappeTestCase):
	def test_fortnightly_period_is_fourteen_days(self):
		dates = get_start_end_dates("Fortnightly", "2026-07-01")
		self.assertEqual(str(dates.start_date), "2026-07-01")
		self.assertEqual(str(dates.end_date), "2026-07-14")

	def test_pending_automated_payroll_cannot_be_submitted(self):
		payroll_entry = PayrollEntry(
			{
				"doctype": "Payroll Entry",
				"requires_payroll_approval": 1,
				"payroll_approval_status": "Pending",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			payroll_entry.before_submit()

	def test_payment_status_transitions(self):
		validate_payment_status_transition("Pending", "Ready")
		validate_payment_status_transition("Ready", "Sent")
		validate_payment_status_transition("Sent", "Paid", reference="TXN-001")
		validate_payment_status_transition("Paid", "Reconciled", reference="TXN-001")

	def test_invalid_payment_status_transitions(self):
		with self.assertRaises(frappe.ValidationError):
			validate_payment_status_transition("Pending", "Paid", reference="TXN-001")
		with self.assertRaises(frappe.ValidationError):
			validate_payment_status_transition("Sent", "Paid")
		with self.assertRaises(frappe.ValidationError):
			validate_payment_status_transition("Ready", "Failed")
