import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, now, nowdate
from frappe.utils.synchronization import LockTimeoutError, filelock

from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates


class PayrollAutomationSchedule(Document):
	def validate(self):
		template = frappe.get_doc("Payroll Entry", self.template_payroll_entry)
		if template.docstatus != 0:
			frappe.throw(_("Template Payroll Entry must remain in Draft status."))
		if template.salary_slips_created:
			frappe.throw(_("Template Payroll Entry cannot have Salary Slips."))

	def create_payroll_entry(self):
		template = frappe.get_doc("Payroll Entry", self.template_payroll_entry)
		dates = get_start_end_dates(self.payroll_frequency, self.next_period_start, template.company)
		existing = frappe.db.exists(
			"Payroll Entry",
			{"automation_schedule": self.name, "start_date": dates.start_date, "docstatus": ("!=", 2)},
		)
		if existing:
			return frappe.get_doc("Payroll Entry", existing)

		payroll_entry = frappe.copy_doc(template)
		payroll_entry.name = None
		payroll_entry.posting_date = dates.end_date
		payroll_entry.payroll_frequency = self.payroll_frequency
		payroll_entry.start_date = dates.start_date
		payroll_entry.end_date = dates.end_date
		payroll_entry.automation_schedule = self.name
		payroll_entry.requires_payroll_approval = self.require_approval
		payroll_entry.payroll_approval_status = "Pending" if self.require_approval else "Approved"
		payroll_entry.salary_slips_created = 0
		payroll_entry.salary_slips_submitted = 0
		payroll_entry.set("employees", [])
		if self.auto_get_employees:
			payroll_entry.fill_employee_details()
		payroll_entry.insert(ignore_permissions=True)

		self.db_set("last_payroll_entry", payroll_entry.name)
		self.db_set("next_period_start", add_days(getdate(dates.end_date), 1))
		exceptions = self.get_readiness_exceptions(payroll_entry)
		if exceptions:
			payroll_entry.db_set("error_message", "\n".join(exceptions))
			self.notify_exception(payroll_entry, "<br>".join(exceptions))
		return payroll_entry

	def get_readiness_exceptions(self, payroll_entry):
		exceptions = []
		if not payroll_entry.employees:
			exceptions.append(_("No eligible employees were found."))
		if payroll_entry.validate_attendance:
			unmarked = payroll_entry.get_employees_with_unmarked_attendance() or []
			if unmarked:
				exceptions.append(
					_("Attendance is incomplete for {0} employee(s).").format(len(unmarked))
				)
		return exceptions

	def is_due(self):
		template = frappe.get_doc("Payroll Entry", self.template_payroll_entry)
		dates = get_start_end_dates(self.payroll_frequency, self.next_period_start, template.company)
		return getdate(dates.end_date) <= getdate(nowdate())

	def notify_exception(self, payroll_entry, message):
		if not self.notification_email:
			return
		frappe.sendmail(
			recipients=[self.notification_email],
			subject=_("Payroll automation requires attention: {0}").format(self.name),
			message=_("Payroll Entry {0}: {1}").format(payroll_entry.name, message),
		)


def create_due_payroll_entries():
	for name in frappe.get_all("Payroll Automation Schedule", filters={"enabled": 1}, pluck="name"):
		try:
			with filelock(f"payroll-automation-{name}", timeout=1):
				schedule = frappe.get_doc("Payroll Automation Schedule", name)
				schedule.db_set("last_run_on", now())
				if schedule.is_due():
					schedule.create_payroll_entry()
				schedule.db_set("last_success_on", now())
				schedule.db_set("consecutive_failures", 0)
				schedule.db_set("last_error", None)
		except LockTimeoutError:
			continue
		except Exception as exc:
			frappe.db.set_value(
				"Payroll Automation Schedule",
				name,
				{
					"consecutive_failures": (frappe.db.get_value("Payroll Automation Schedule", name, "consecutive_failures") or 0) + 1,
					"last_error": str(exc)[:500],
				},
			)
			frappe.log_error(title=_("Payroll automation failed for {0}").format(name))
