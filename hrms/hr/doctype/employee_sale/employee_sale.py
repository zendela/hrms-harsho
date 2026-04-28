# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class EmployeeSale(Document):
	def validate(self):
		self._validate_salary_component()
		self._calculate_amounts()

	def on_submit(self):
		self._create_additional_salaries()
		self.db_set("status", "Submitted")

	def on_cancel(self):
		self._cancel_additional_salaries()
		self.db_set("status", "Cancelled")

	# ------------------------------------------------------------------
	# Validation
	# ------------------------------------------------------------------

	def _validate_salary_component(self):
		comp_type = frappe.db.get_value("Salary Component", self.salary_component, "type")
		if comp_type != "Deduction":
			frappe.throw(
				_("Salary Component {0} must be of type Deduction.").format(
					frappe.bold(self.salary_component)
				)
			)

	def _calculate_amounts(self):
		total = 0.0
		for row in self.items:
			row.amount = flt(row.qty) * flt(row.unit_price)
			total += row.amount
		self.total_amount = total

	# ------------------------------------------------------------------
	# Additional Salary creation / cancellation
	# ------------------------------------------------------------------

	def _create_additional_salaries(self):
		"""
		Group items by employee and create one submitted Additional Salary
		per employee for the total amount of goods they purchased.
		"""
		# Aggregate per employee
		totals = {}
		for row in self.items:
			totals[row.employee] = totals.get(row.employee, 0.0) + flt(row.amount)

		payroll_date = getdate(self.payroll_month)

		for employee, amount in totals.items():
			if amount <= 0:
				continue

			# Idempotency: skip if already created for this sale + employee
			existing = frappe.db.exists(
				"Additional Salary",
				{
					"ref_doctype": "Employee Sale",
					"ref_docname": self.name,
					"employee": employee,
					"docstatus": ["!=", 2],
				},
			)
			if existing:
				continue

			company = frappe.db.get_value("Employee", employee, "company") or self.company

			additional_salary = frappe.new_doc("Additional Salary")
			additional_salary.employee         = employee
			additional_salary.company          = company
			additional_salary.currency         = self.currency
			additional_salary.salary_component = self.salary_component
			additional_salary.amount           = amount
			additional_salary.payroll_date     = payroll_date
			additional_salary.ref_doctype      = "Employee Sale"
			additional_salary.ref_docname      = self.name
			additional_salary.overwrite_salary_structure_amount = 0

			additional_salary.insert(ignore_permissions=True)
			additional_salary.submit()

	def _cancel_additional_salaries(self):
		"""Cancel all Additional Salaries linked to this Employee Sale."""
		linked = frappe.get_all(
			"Additional Salary",
			filters={
				"ref_doctype": "Employee Sale",
				"ref_docname": self.name,
				"docstatus": 1,
			},
			pluck="name",
		)
		for name in linked:
			doc = frappe.get_doc("Additional Salary", name)
			doc.cancel()
