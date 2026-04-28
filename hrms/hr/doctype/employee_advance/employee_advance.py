# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Abs, Sum
from frappe.utils import flt, get_first_day, get_last_day, get_link_to_form, getdate, nowdate

import erpnext
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

import hrms
from hrms.hr.utils import validate_active_employee


class EmployeeAdvanceOverPayment(frappe.ValidationError):
	pass


class EmployeeAdvance(Document):
	def onload(self):
		self.get("__onload").make_payment_via_journal_entry = frappe.db.get_single_value(
			"Accounts Settings", "make_payment_via_journal_entry"
		)

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_exchange_rate()
		self.validate_advance_account_type()
		self.validate_one_advance_per_month()
		self.set_status()
		self.set_pending_amount()

	def validate_one_advance_per_month(self):
		if not self.payroll_month:
			return

		month_start = get_first_day(getdate(self.payroll_month))
		month_end = get_last_day(getdate(self.payroll_month))

		filters = {
			"employee": self.employee,
			"payroll_month": ["between", [month_start, month_end]],
			"docstatus": ["!=", 2],
		}
		if not self.is_new():
			filters["name"] = ["!=", self.name]

		existing = frappe.db.get_value("Employee Advance", filters, "name")
		if existing:
			frappe.throw(
				_("An advance already exists for employee {0} for the payroll month {1}: {2}").format(
					frappe.bold(self.employee),
					frappe.bold(month_start.strftime("%B %Y")),
					get_link_to_form("Employee Advance", existing),
				),
				title=_("Duplicate Advance"),
			)

	def before_submit(self):
		if not self.get("advance_account"):
			default_advance_account = frappe.db.get_value(
				"Company", self.company, "default_employee_advance_account"
			)
			if default_advance_account:
				self.advance_account = default_advance_account
			else:
				frappe.throw(
					_(
						'Advance Account is mandatory. Please set the <a href="/app/company/{0}#default_employee_advance_account" target="_blank">Default Employee Advance Account</a> in the Company record {0} and submit this document.'
					).format(self.company),
					title=_("Missing Advance Account"),
				)

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry", "Advance Payment Ledger Entry")
		self.check_linked_payment_entry()
		self.set_status(update=True)

	def on_update(self):
		self.publish_update()

	def after_delete(self):
		self.publish_update()

	def publish_update(self):
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
		hrms.refetch_resource("hrms:employee_advance_balance", employee_user)

	def validate_exchange_rate(self):
		if not self.exchange_rate:
			frappe.throw(_("Exchange Rate cannot be zero."))

	def validate_advance_account_type(self):
		account_type = frappe.db.get_value("Account", self.advance_account, "account_type")
		if account_type != "Receivable":
			frappe.throw(
				_("Employee advance account {0} should be of type {1}.").format(
					get_link_to_form("Account", self.advance_account), frappe.bold(_("Receivable"))
				)
			)

	def set_status(self, update=False):
		precision = self.precision("paid_amount")
		total_amount = flt(flt(self.claimed_amount) + flt(self.return_amount), precision)
		status = None

		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			if flt(self.claimed_amount) > 0 and flt(self.claimed_amount, precision) == flt(
				self.paid_amount, precision
			):
				status = "Claimed"
			elif flt(self.return_amount) > 0 and flt(self.return_amount, precision) == flt(
				self.paid_amount, precision
			):
				status = "Returned"
			elif (
				flt(self.claimed_amount) > 0
				and (flt(self.return_amount) > 0)
				and total_amount == flt(self.paid_amount, precision)
			):
				status = "Partly Claimed and Returned"
			elif flt(self.paid_amount) > 0 and flt(self.advance_amount, precision) == flt(
				self.paid_amount, precision
			):
				status = "Paid"
			else:
				status = "Unpaid"
		elif self.docstatus == 2:
			status = "Cancelled"

		if update:
			self.db_set("status", status)
			self.publish_update()
			self.notify_update()
		else:
			self.status = status

	def set_total_advance_paid(self):
		aple = frappe.qb.DocType("Advance Payment Ledger Entry")

		account_type, account_curreny = frappe.get_value(
			"Account", self.advance_account, ["account_type", "account_currency"]
		)

		company_currency = frappe.get_value("Company", self.company, "default_currency")

		if account_type == "Receivable":
			paid_amount_condition = aple.amount > 0
			returned_amount_condition = aple.amount < 0
		elif account_type == "Payable":
			paid_amount_condition = aple.amount < 0
			returned_amount_condition = aple.amount > 0
		else:
			frappe.throw(
				_("Employee advance account {0} should be of type {1}.").format(
					get_link_to_form("Account", self.advance_account),
					frappe.bold(_("Receivable")),
				)
			)

		paid_amount = (
			frappe.qb.from_(aple)
			.select(Abs(Sum(aple.amount)).as_("paid_amount"))
			.where(
				(aple.company == self.company)
				& (aple.delinked == 0)
				& (aple.against_voucher_type == self.doctype)
				& (aple.against_voucher_no == self.name)
				& (paid_amount_condition)
			)
		).run(as_dict=True)[0].paid_amount or 0
		return_amount = (
			frappe.qb.from_(aple)
			.select(Abs(Sum(aple.amount)).as_("return_amount"))
			.where(
				(aple.company == self.company)
				& (aple.delinked == 0)
				& (aple.against_voucher_type == self.doctype)
				& (aple.against_voucher_no == self.name)
				& (returned_amount_condition)
			)
		).run(as_dict=True)[0].return_amount or 0

		if company_currency != self.currency and account_curreny == company_currency:
			paid_amount = flt(paid_amount) / flt(self.exchange_rate)
			return_amount = flt(return_amount) / flt(self.exchange_rate)

		precision = self.precision("paid_amount")
		paid_amount = flt(paid_amount, precision)
		if paid_amount > flt(self.advance_amount, precision):
			frappe.throw(
				_("Row {0}# Paid Amount cannot be greater than requested advance amount"),
				EmployeeAdvanceOverPayment,
			)

		precision = self.precision("return_amount")
		return_amount = flt(return_amount, precision)

		if return_amount > 0 and return_amount > flt(paid_amount - self.claimed_amount, precision):
			frappe.throw(_("Return amount cannot be greater than unclaimed amount"))

		self.db_set("paid_amount", paid_amount)
		self.db_set("return_amount", return_amount)
		self.set_status(update=True)

		# Auto-create payroll deduction entry when advance becomes fully paid
		self.reload()
		if self.status == "Paid":
			self.create_advance_deduction_entry()

	def create_advance_deduction_entry(self):
		"""
		Create a submitted Additional Salary (Deduction) so the advance amount
		is recovered from the employee's payroll for the configured payroll_month.
		Skips silently if:
		  - advance_deduction_component is not set in HR Settings
		  - payroll_month is not set on this advance
		  - an Additional Salary already exists for this advance
		"""
		salary_component = frappe.db.get_single_value(
			"HR Settings", "advance_deduction_component"
		)
		if not salary_component:
			return

		if not self.get("payroll_month"):
			return

		# Idempotency: skip if already created
		existing = frappe.db.exists(
			"Additional Salary",
			{
				"ref_doctype": "Employee Advance",
				"ref_docname": self.name,
				"docstatus": ["!=", 2],
			},
		)
		if existing:
			return

		additional_salary = frappe.new_doc("Additional Salary")
		additional_salary.employee         = self.employee
		additional_salary.company          = self.company
		additional_salary.currency         = self.currency
		additional_salary.salary_component = salary_component
		additional_salary.amount           = flt(self.advance_amount)
		additional_salary.payroll_date     = getdate(self.payroll_month)
		additional_salary.ref_doctype      = "Employee Advance"
		additional_salary.ref_docname      = self.name
		additional_salary.overwrite_salary_structure_amount = 0

		additional_salary.insert(ignore_permissions=True)
		additional_salary.submit()

	def update_claimed_amount(self):
		claimed_amount = (
			frappe.db.sql(
				"""
			SELECT sum(ifnull(allocated_amount, 0))
			FROM `tabExpense Claim Advance` eca, `tabExpense Claim` ec
			WHERE
				eca.employee_advance = %s
				AND ec.approval_status="Approved"
				AND ec.name = eca.parent
				AND ec.docstatus=1
				AND eca.allocated_amount > 0
		""",
				self.name,
			)[0][0]
			or 0
		)

		frappe.db.set_value("Employee Advance", self.name, "claimed_amount", flt(claimed_amount))
		self.reload()
		self.set_status(update=True)

	def set_pending_amount(self):
		Advance = frappe.qb.DocType("Employee Advance")
		self.pending_amount = (
			frappe.qb.from_(Advance)
			.select(Sum(Advance.advance_amount - Advance.paid_amount))
			.where(
				(Advance.employee == self.employee)
				& (Advance.docstatus == 1)
				& (Advance.posting_date <= self.posting_date)
				& (Advance.status == "Unpaid")
			)
		).run()[0][0] or 0.0

	def check_linked_payment_entry(self):
		from erpnext.accounts.utils import (
			remove_ref_doc_link_from_pe,
			update_accounting_ledgers_after_reference_removal,
		)

		if frappe.db.get_single_value("HR Settings", "unlink_payment_on_cancellation_of_employee_advance"):
			remove_ref_doc_link_from_pe(self.doctype, self.name)
			update_accounting_ledgers_after_reference_removal(self.doctype, self.name)


@frappe.whitelist()
def make_bank_entry(dt, dn):
	doc = frappe.get_doc(dt, dn)
	payment_account = get_default_bank_cash_account(
		doc.company, account_type="Cash", mode_of_payment=doc.mode_of_payment
	)
	if not payment_account:
		frappe.throw(_("Please set a Default Cash Account in Company defaults"))

	advance_account_currency = frappe.db.get_value("Account", doc.advance_account, "account_currency")

	advance_amount, advance_exchange_rate = get_advance_amount_advance_exchange_rate(
		advance_account_currency, doc
	)

	paying_amount, paying_exchange_rate = get_paying_amount_paying_exchange_rate(payment_account, doc)

	je = frappe.new_doc("Journal Entry")
	je.posting_date = nowdate()
	je.voucher_type = "Bank Entry"
	je.company = doc.company
	je.remark = "Payment against Employee Advance: " + dn
	je.multi_currency = 1 if advance_account_currency != payment_account.account_currency else 0

	je.append(
		"accounts",
		{
			"account": doc.advance_account,
			"account_currency": advance_account_currency,
			"exchange_rate": flt(advance_exchange_rate),
			"debit_in_account_currency": flt(advance_amount),
			"reference_type": "Employee Advance",
			"reference_name": doc.name,
			"party_type": "Employee",
			"cost_center": erpnext.get_default_cost_center(doc.company),
			"party": doc.employee,
			"is_advance": "Yes",
		},
	)

	je.append(
		"accounts",
		{
			"account": payment_account.account,
			"cost_center": erpnext.get_default_cost_center(doc.company),
			"credit_in_account_currency": flt(paying_amount),
			"account_currency": payment_account.account_currency,
			"account_type": payment_account.account_type,
			"exchange_rate": flt(paying_exchange_rate),
		},
	)

	return je.as_dict()


def get_advance_amount_advance_exchange_rate(advance_account_currency, doc):
	if advance_account_currency != doc.currency:
		advance_amount = flt(doc.advance_amount) * flt(doc.exchange_rate)
		advance_exchange_rate = 1
	else:
		advance_amount = doc.advance_amount
		advance_exchange_rate = doc.exchange_rate

	return advance_amount, advance_exchange_rate


def get_paying_amount_paying_exchange_rate(payment_account, doc):
	if payment_account.account_currency != doc.currency:
		paying_amount = flt(doc.advance_amount) * flt(doc.exchange_rate)
		paying_exchange_rate = 1
	else:
		paying_amount = doc.advance_amount
		paying_exchange_rate = doc.exchange_rate

	return paying_amount, paying_exchange_rate


@frappe.whitelist()
def create_return_through_additional_salary(doc):
	import json

	if isinstance(doc, str):
		doc = frappe._dict(json.loads(doc))

	additional_salary = frappe.new_doc("Additional Salary")
	additional_salary.employee = doc.employee
	additional_salary.currency = doc.currency
	additional_salary.overwrite_salary_structure_amount = 0
	additional_salary.amount = doc.paid_amount - doc.claimed_amount
	additional_salary.company = doc.company
	additional_salary.ref_doctype = doc.doctype
	additional_salary.ref_docname = doc.name

	return additional_salary


@frappe.whitelist()
def make_return_entry(
	employee,
	company,
	employee_advance_name,
	return_amount,
	advance_account,
	currency,
	exchange_rate,
	mode_of_payment=None,
):
	bank_cash_account = get_default_bank_cash_account(
		company, account_type="Cash", mode_of_payment=mode_of_payment
	)
	if not bank_cash_account:
		frappe.throw(_("Please set a Default Cash Account in Company defaults"))

	advance_account_currency = frappe.db.get_value("Account", advance_account, "account_currency")

	je = frappe.new_doc("Journal Entry")
	je.posting_date = nowdate()
	je.voucher_type = get_voucher_type(mode_of_payment)
	je.company = company
	je.remark = "Return against Employee Advance: " + employee_advance_name
	je.multi_currency = 1 if advance_account_currency != bank_cash_account.account_currency else 0

	advance_account_amount = (
		flt(return_amount)
		if advance_account_currency == currency
		else flt(return_amount) * flt(exchange_rate)
	)

	je.append(
		"accounts",
		{
			"account": advance_account,
			"credit_in_account_currency": advance_account_amount,
			"account_currency": advance_account_currency,
			"exchange_rate": flt(exchange_rate) if advance_account_currency == currency else 1,
			"reference_type": "Employee Advance",
			"reference_name": employee_advance_name,
			"party_type": "Employee",
			"party": employee,
			"is_advance": "Yes",
			"cost_center": erpnext.get_default_cost_center(company),
		},
	)

	bank_amount = (
		flt(return_amount)
		if bank_cash_account.account_currency == currency
		else flt(return_amount) * flt(exchange_rate)
	)

	je.append(
		"accounts",
		{
			"account": bank_cash_account.account,
			"debit_in_account_currency": bank_amount,
			"account_currency": bank_cash_account.account_currency,
			"account_type": bank_cash_account.account_type,
			"exchange_rate": flt(exchange_rate) if bank_cash_account.account_currency == currency else 1,
			"cost_center": erpnext.get_default_cost_center(company),
		},
	)

	return je.as_dict()


def get_voucher_type(mode_of_payment=None):
	voucher_type = "Cash Entry"

	if mode_of_payment:
		mode_of_payment_type = frappe.get_cached_value("Mode of Payment", mode_of_payment, "type")
		if mode_of_payment_type == "Bank":
			voucher_type = "Bank Entry"

	return voucher_type


@frappe.whitelist()
def bulk_mark_as_paid(advance_names, bank_account=None, mode_of_payment=None):
	"""
	Create a single Payment Entry covering all selected Unpaid advances.
	All advances must belong to the same company and use the same currency.
	Returns the submitted Payment Entry name.
	"""
	import json

	if isinstance(advance_names, str):
		advance_names = json.loads(advance_names)

	if not advance_names:
		frappe.throw(_("No advances selected."))

	advances = frappe.get_all(
		"Employee Advance",
		filters={"name": ["in", advance_names], "docstatus": 1, "status": "Unpaid"},
		fields=[
			"name", "employee", "employee_name", "company", "currency",
			"advance_amount", "paid_amount", "exchange_rate", "advance_account",
		],
	)

	if not advances:
		frappe.throw(_("No submitted Unpaid advances found in the selection."))

	# All advances must share the same company and currency
	companies  = {a.company for a in advances}
	currencies = {a.currency for a in advances}
	if len(companies) > 1:
		frappe.throw(
			_("All selected advances must belong to the same company. Found: {0}").format(
				", ".join(companies)
			)
		)
	if len(currencies) > 1:
		frappe.throw(
			_("All selected advances must use the same currency. Found: {0}").format(
				", ".join(currencies)
			)
		)

	company  = companies.pop()
	currency = currencies.pop()

	# Resolve payment account
	payment_account = get_default_bank_cash_account(
		company, account_type="Cash", mode_of_payment=mode_of_payment
	)
	if bank_account:
		payment_account = frappe._dict(
			frappe.db.get_value(
				"Bank Account", bank_account,
				["account", "account_currency"],
				as_dict=True,
			) or {}
		)
	if not payment_account or not payment_account.get("account"):
		frappe.throw(
			_("Please set a Default Cash Account in Company defaults or pass a bank_account.")
		)

	company_currency = erpnext.get_company_currency(company)
	advance_account  = advances[0].advance_account or frappe.db.get_value(
		"Company", company, "default_employee_advance_account"
	)
	if not advance_account:
		frappe.throw(
			_("No Advance Account found. Set the Default Employee Advance Account on the Company.")
		)

	from erpnext.accounts.utils import get_account_currency
	advance_account_currency = get_account_currency(advance_account)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type               = "Pay"
	pe.company                    = company
	pe.posting_date               = nowdate()
	pe.mode_of_payment            = mode_of_payment
	pe.party_type                 = "Employee"
	pe.paid_from                  = payment_account.account
	pe.paid_to                    = advance_account
	pe.paid_from_account_currency = payment_account.get("account_currency") or company_currency
	pe.paid_to_account_currency   = advance_account_currency

	total_outstanding = 0.0

	for adv in advances:
		outstanding = flt(adv.advance_amount) - flt(adv.paid_amount)
		if advance_account_currency != adv.currency:
			outstanding = outstanding * flt(adv.exchange_rate)

		pe.append(
			"references",
			{
				"reference_doctype": "Employee Advance",
				"reference_name":    adv.name,
				"total_amount":      flt(adv.advance_amount),
				"outstanding_amount": outstanding,
				"allocated_amount":  outstanding,
			},
		)
		total_outstanding += outstanding

	pe.paid_amount     = total_outstanding
	pe.received_amount = total_outstanding

	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.set_missing_ref_details()
	pe.set_amounts()

	pe.insert(ignore_permissions=True)
	pe.submit()

	return pe.name
