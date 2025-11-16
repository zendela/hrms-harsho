# hrms/hr/doctype/shift_swap_auto_scheduler/shift_swap_auto_scheduler.py
import calendar
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, add_days
from frappe import _

# reuse the executor from Swap Shift
from hrms.hr.doctype.swap_shift.swap_shift import _execute_swap

WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday","Thusday"]  # include your misspelling just in case

class ShiftSwapAutoScheduler(Document):
    def validate(self):
        # Ensure row flags inherit defaults when not provided (None)
        for r in (self.rules_table or []):
            if r.respect_stay_flag is None:
                r.respect_stay_flag = self.default_respect_stay_flag
            if r.cancel_existing is None:
                r.cancel_existing = self.default_cancel_existing

    @frappe.whitelist()
    def run_now(self):
        return run_rules_once()

def scheduler_daily():
    sched = frappe.get_single("Shift Swap Auto Scheduler")
    if not int(sched.enable or 0):
        return
    run_rules_once()

def run_rules_once():
    today = getdate(nowdate())
    sched = frappe.get_single("Shift Swap Auto Scheduler")
    results = []
    for r in (sched.rules_table or []):
        if not int(r.get("active", 1)):
            results.append({"rule": r.name, "status": "skipped", "reason": "inactive"})
            continue
        try:
            due, window = _is_rule_due_today(r, today)
            if not due:
                results.append({"rule": r.name, "status": "skipped", "reason": "not_due"})
                continue
            fd, td = window
            res = _execute_swap(
                r.shift_a, r.shift_b, fd, td,
                int(r.respect_stay_flag or 0),
                int(r.cancel_existing or 0)
            )
            results.append({
                "rule": r.name, "status": "executed",
                "window": [str(fd), str(td)],
                "created": len(res.get("created", [])),
                "cancelled": len(res.get("cancelled", []))
            })
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), title=f"ShiftSwapAutoScheduler failed: {r.name}")
            results.append({"rule": r.name, "status": "error", "error": str(e)})
    return {"date": str(today), "results": results}

def _is_rule_due_today(rule, today):
    freq = (rule.frequency or "").strip().lower()
    if freq == "daily":
        return True, (today, today)

    if freq == "weekly":
        anchor = (rule.weekly_anchor_day or "Monday")
        # tolerate the “Thusday” typo
        if anchor == "Thusday":
            anchor = "Thursday"
        try:
            anchor_idx = WEEKDAYS.index(anchor)
        except ValueError:
            anchor_idx = 0  # Monday
        if today.weekday() != anchor_idx:
            return False, (None, None)
        # build next week window (Mon..Sun style)
        next_anchor = add_days(today, 7)
        start = next_anchor
        end = add_days(start, 6)
        return True, (start, end)

    if freq == "monthly":
        anchor_day = int(rule.monthly_anchor_day or 1)
        # Only run on the anchor day of this month
        last = calendar.monthrange(today.year, today.month)[1]
        if today.day != min(anchor_day, last):
            return False, (None, None)
        # Full next month window
        ny, nm = _next_month(today.year, today.month)
        nlast = calendar.monthrange(ny, nm)[1]
        start = getdate(f"{ny}-{nm:02d}-01")
        end = getdate(f"{ny}-{nm:02d}-{nlast:02d}")
        return True, (start, end)

    return False, (None, None)

def _next_month(y, m):
    return (y + (1 if m == 12 else 0), 1 if m == 12 else m + 1)
