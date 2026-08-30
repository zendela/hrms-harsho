import csv
import io

import frappe
from frappe.tests import UnitTestCase

from hrms.payroll.report.payroll_bank_disbursement.payroll_bank_disbursement import (
	BANK_FILE_HEADERS,
	build_bank_csv,
	validate_bank_details,
)


class TestPayrollBankDisbursement(UnitTestCase):
	def test_bank_csv_uses_branch_name_and_net_pay(self):
		rows = [
			frappe._dict(
				{
					"employee": "EMP-0001",
					"employee_name": "Jane Employee",
					"bank_name": "Example Bank",
					"branch_name": "Main Branch",
					"bank_account_no": "0012345678",
					"net_pay": 1250000,
				}
			)
		]

		content = build_bank_csv(rows, "HR-PRUN-2026-00009")
		csv_rows = list(csv.reader(io.StringIO(content)))

		self.assertEqual(csv_rows[0], BANK_FILE_HEADERS)
		self.assertEqual(csv_rows[1][3], "Main Branch")
		self.assertEqual(csv_rows[1][4], "0012345678")
		self.assertEqual(csv_rows[1][5], "1250000")
		self.assertEqual(csv_rows[1][6], "HR-PRUN-2026-00009-EMP-0001")

	def test_bank_details_are_required(self):
		rows = [
			frappe._dict(
				{
					"employee": "EMP-0001",
					"employee_name": "Jane Employee",
					"bank_name": None,
					"bank_account_no": None,
				}
			)
		]

		with self.assertRaises(frappe.ValidationError):
			validate_bank_details(rows)
