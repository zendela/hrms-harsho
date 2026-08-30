import csv
import io

import frappe
from frappe import _
from frappe.utils import now_datetime


BANK_FILE_HEADERS = ["Employee", "Name", "Bank", "Branch", "Account", "Amount", "Reference"]


def execute(filters=None):
	filters = validate_filters(filters)
	return get_columns(), get_data(filters)


def validate_filters(filters=None):
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)

	filters = frappe._dict(filters or {})
	if not filters.payroll_entry:
		frappe.throw(_("Payroll Entry is required."))

	payroll_entry = frappe.get_doc("Payroll Entry", filters.payroll_entry)
	payroll_entry.check_permission("read")
	if not frappe.has_permission("Salary Slip", "read"):
		frappe.throw(_("You are not permitted to export Salary Slip bank details."), frappe.PermissionError)

	if payroll_entry.docstatus != 1 or not payroll_entry.salary_slips_submitted:
		frappe.throw(
			_("Submit all Salary Slips for Payroll Entry {0} before generating the bank file.").format(
				frappe.bold(payroll_entry.name)
			)
		)

	if filters.company and filters.company != payroll_entry.company:
		frappe.throw(
			_("Payroll Entry {0} does not belong to company {1}.").format(
				frappe.bold(payroll_entry.name), frappe.bold(filters.company)
			)
		)

	filters.company = payroll_entry.company
	return filters


def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
		{"label": _("Bank"), "fieldname": "bank_name", "fieldtype": "Data", "width": 160},
		{"label": _("Branch Name"), "fieldname": "branch_name", "fieldtype": "Data", "width": 160},
		{"label": _("Branch Code"), "fieldname": "branch_code", "fieldtype": "Data", "width": 120},
		{"label": _("Account No"), "fieldname": "bank_account_no", "fieldtype": "Data", "width": 160},
		{
			"label": _("Amount"),
			"fieldname": "net_pay",
			"fieldtype": "Currency",
			"width": 130,
			"options": "currency",
		},
		{
			"label": _("Payroll Entry"),
			"fieldname": "payroll_entry",
			"fieldtype": "Link",
			"options": "Payroll Entry",
			"width": 160,
		},
		{"label": _("Mode"), "fieldname": "mode_of_payment", "fieldtype": "Data", "width": 90},
	]


def get_data(filters):
	conditions = [
		"ss.docstatus = 1",
		"ss.net_pay > 0",
		"ss.mode_of_payment in ('Bank', 'Cheque')",
		"ss.payroll_entry = %s",
		"ss.company = %s",
	]
	values = [filters.payroll_entry, filters.company]

	if filters.bank_name:
		conditions.append("emp.bank_name = %s")
		values.append(filters.bank_name)
	if filters.branch_code:
		conditions.append("emp.bank_code = %s")
		values.append(filters.branch_code)

	data = frappe.db.sql(
		f"""
		SELECT
			ss.employee,
			ss.employee_name,
			emp.bank_name,
			emp.branch_name,
			emp.bank_code AS branch_code,
			emp.bank_ac_no AS bank_account_no,
			ss.net_pay,
			ss.payroll_entry,
			ss.currency,
			ss.mode_of_payment
		FROM `tabSalary Slip` ss
		LEFT JOIN `tabEmployee` emp ON emp.name = ss.employee
		WHERE {" AND ".join(conditions)}
		ORDER BY ss.employee
		""",
		values,
		as_dict=True,
	)

	default_currency = frappe.get_cached_value("Company", filters.company, "default_currency") or "TZS"
	for row in data:
		row.currency = row.currency or default_currency

	return data


def validate_bank_details(rows):
	missing_details = []
	for row in rows:
		missing = []
		if not row.get("bank_name"):
			missing.append(_("Bank"))
		if not row.get("bank_account_no"):
			missing.append(_("Account No"))

		if missing:
			missing_details.append(
				_("{0} ({1}): {2}").format(
					row.get("employee_name") or row.get("employee"),
					row.get("employee"),
					", ".join(missing),
				)
			)

	if missing_details:
		frappe.throw(
			_("Complete the following Employee bank details before downloading the bank file:<br>{0}").format(
				"<br>".join(missing_details)
			),
			title=_("Missing Bank Details"),
		)


def build_bank_csv(rows, payroll_entry):
	buffer = io.StringIO()
	writer = csv.writer(buffer, lineterminator="\n")
	writer.writerow(BANK_FILE_HEADERS)

	for row in rows:
		writer.writerow(
			[
				row.get("employee"),
				row.get("employee_name"),
				row.get("bank_name"),
				row.get("branch_name"),
				row.get("bank_account_no"),
				row.get("net_pay"),
				f"{payroll_entry}-{row.get('employee') or ''}",
			]
		)

	return buffer.getvalue()


@frappe.whitelist()
def export_bank_csv(filters=None):
	filters = validate_filters(filters)
	rows = get_data(filters)
	if not rows:
		frappe.throw(
			_("No submitted Bank or Cheque Salary Slips were found for Payroll Entry {0}.").format(
				frappe.bold(filters.payroll_entry)
			)
		)

	validate_bank_details(rows)
	content = build_bank_csv(rows, filters.payroll_entry)
	timestamp = now_datetime().strftime("%Y%m%d-%H%M%S")
	file_name = f"bank-disbursement-{filters.payroll_entry}-{timestamp}.csv"
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"content": content,
			"is_private": 1,
			"attached_to_doctype": "Payroll Entry",
			"attached_to_name": filters.payroll_entry,
		}
	).insert(ignore_permissions=True)

	return {"file_url": file_doc.file_url, "file_name": file_doc.file_name, "row_count": len(rows)}
