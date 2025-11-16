import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate
from hrms.hr.doctype.shift_assignment.shift_assignment import MultipleShiftError
# ---------- helpers ----------

def _get_settings():
    """Read defaults from Shift Swap Auto Scheduler (Single)."""
    try:
        s = frappe.get_single("Shift Swap Auto Scheduler")
        return {
            "default_respect_stay_flag": int(s.default_respect_stay_flag or 0),
            "default_cancel_existing": int(s.default_cancel_existing or 0),
        }
    except Exception:
        # safe fallback if single not present
        return {"default_respect_stay_flag": 0, "default_cancel_existing": 0}

def _assigned_in_window(shift_name, fd, td):
    if not shift_name:
        return []
    return frappe.db.sql(
        """
        SELECT sa.name, sa.employee, sa.employee_name, sa.start_date, sa.end_date, sa.shift_type
        FROM `tabShift Assignment` sa
        WHERE sa.docstatus = 1
          AND sa.shift_type = %s
          AND sa.start_date <= %s
          AND sa.end_date   >= %s
        """,
        (shift_name, td, fd),
        as_dict=True,
    )
def _hr_allow_multiple_assignments():
    """HR Settings: Allow Multiple Shift Assignments for Same Date (bool)."""
    try:
        val = frappe.db.get_single_value("HR Settings", "allow_multiple_shift_assignments")
        return int(val or 0)
    except Exception:
        return 0

def _employee_names(emp_list):
    if not emp_list:
        return {}
    rows = frappe.get_all(
        "Employee",
        filters={"name": ["in", emp_list]},
        fields=["name", "employee_name", "stay_in_current_shift"],
    )
    return {r.name: {"employee_name": r.employee_name, "stay": int(r.stay_in_current_shift or 0)} for r in rows}

def _cancel_overlaps(employees, fd, td):
    if not employees:
        return []
    rows = frappe.db.sql(
        """
        SELECT name
        FROM `tabShift Assignment`
        WHERE docstatus = 1
          AND employee IN ({})
          AND start_date <= %s
          AND end_date   >= %s
        """.format(", ".join(["%s"] * len(employees))),
        tuple(employees) + (td, fd),
        as_dict=True,
    )
    cancelled = []
    for r in rows:
        doc = frappe.get_doc("Shift Assignment", r["name"])
        doc.cancel()
        cancelled.append(r["name"])
    return cancelled

def _collect_child_stay_flags(doc: Document):
    """
    Users can mark 'Stay In Current Shift' in the child rows.
    Return a set of employee ids that should stay (override).
    """
    stayed = set()
    for table_field in ("shift_a_table", "shift_b_table"):
        for row in (doc.get(table_field) or []):
            # support both 1/0 and True/False
            if int(row.get("stay_in_current_shift") or 0) == 1 and row.get("employee"):
                stayed.add(row.get("employee"))
    return stayed

def _find_overlaps_for_employees(employees, fd, td):
    if not employees:
        return []
    return frappe.db.sql(
        """
        SELECT name, employee, shift_type, start_date, end_date
        FROM `tabShift Assignment`
        WHERE docstatus = 1
          AND employee IN ({})
          AND start_date <= %s
          AND end_date   >= %s
        """.format(", ".join(["%s"] * len(employees))),
        tuple(employees) + (td, fd),
        as_dict=True,
    )

def _cancel_overlaps_for_emp(employee, fd, td):
    rows = frappe.db.sql(
        """
        SELECT name
        FROM `tabShift Assignment`
        WHERE docstatus = 1
          AND employee = %s
          AND start_date <= %s
          AND end_date   >= %s
        """,
        (employee, td, fd),
        as_dict=True,
    )
    cancelled = []
    for r in rows:
        doc = frappe.get_doc("Shift Assignment", r["name"])
        doc.cancel()
        cancelled.append(r["name"])
    return cancelled



def _preview_swap(from_shift, to_shift, fetch_fd, fetch_td, respect_stay_flag: int, stayed_overrides: set | None = None):
    A = _assigned_in_window(from_shift, fetch_fd, fetch_td)
    B = _assigned_in_window(to_shift, fetch_fd, fetch_td)

    A_emp = {r.employee for r in A}
    B_emp = {r.employee for r in B}
    info  = _employee_names(list(A_emp | B_emp))
    stayed_overrides = stayed_overrides or set()

    def must_stay(emp):
        # If user marked stay in child, it wins; else use Employee.stay_in_current_shift
        return (emp in stayed_overrides) or (info.get(emp, {}).get("stay") == 1)

    def filter_swap(emp_set):
        out = []
        for e in sorted(emp_set):
            if respect_stay_flag and must_stay(e):
                continue
            out.append(e)
        return out

    A_swap = filter_swap(A_emp)
    B_swap = filter_swap(B_emp)

    stayed = [e for e in sorted(A_emp | B_emp) if must_stay(e)] if respect_stay_flag else []

    a_to_b = [{"employee": e, "employee_name": info.get(e, {}).get("employee_name")} for e in A_swap]
    b_to_a = [{"employee": e, "employee_name": info.get(e, {}).get("employee_name")} for e in B_swap]

    return {
        "fetch_window": [str(fetch_fd), str(fetch_td)],
        "from_shift": from_shift,
        "to_shift": to_shift,
        "a_to_b": a_to_b,
        "b_to_a": b_to_a,
        "stayed": stayed,
    }

def _execute_swap(from_shift, to_shift,
                  fetch_fd, fetch_td,
                  create_fd, create_td,
                  respect_stay_flag: int, cancel_existing: int,
                  stayed_overrides: set | None = None):
    prev = _preview_swap(from_shift, to_shift, fetch_fd, fetch_td, respect_stay_flag, stayed_overrides)
    A_swap = [x["employee"] for x in prev["a_to_b"]]
    B_swap = [x["employee"] for x in prev["b_to_a"]]
    all_emps = list(set(A_swap) | set(B_swap))

    allow_multi = _hr_allow_multiple_assignments()

    # Hard fail if not allowed and user didn't choose cancel, with a helpful message.
    if not allow_multi and not cancel_existing:
        overlaps = _find_overlaps_for_employees(all_emps, create_fd, create_td)
        if overlaps:
            sample = overlaps[:10]
            lines = [
                _("{0}: {1} ({2} → {3})").format(
                    r.get("employee"),
                    r.get("shift_type"),
                    frappe.format(r.get("start_date"), {"fieldtype": "Date"}),
                    frappe.format(r.get("end_date"), {"fieldtype": "Date"}),
                )
            for r in sample]
            more = "" if len(overlaps) <= 10 else _("\n... and {0} more").format(len(overlaps) - 10)
            frappe.throw(
                _("Cannot create overlapping Shift Assignments because HR Settings disallow multiple assignments on the same date.\n"
                  "Either enable 'Cancel Existing' on this Swap, or allow multiple assignments in HR Settings.\n"
                  "Overlaps found:\n{0}{1}").format("\n".join(lines), more)
            )

    cancelled = []
    created = []

    def _create(emp, target_shift):
        d = frappe.new_doc("Shift Assignment")
        d.update({
            "employee": emp,
            "start_date": create_fd,
            "end_date": create_td,
            "shift_type": target_shift,
            "company": frappe.db.get_value("Employee", emp, "company"),
        })
        try:
            d.insert(ignore_permissions=True)
            d.submit()
            created.append(d.name)
        except MultipleShiftError:
            # If policy disallows multiple and cancel_existing=1, cancel then retry once
            if not allow_multi and cancel_existing:
                cancelled.extend(_cancel_overlaps_for_emp(emp, create_fd, create_td))
                d = frappe.new_doc("Shift Assignment")
                d.update({
                    "employee": emp,
                    "start_date": create_fd,
                    "end_date": create_td,
                    "shift_type": target_shift,
                    "company": frappe.db.get_value("Employee", emp, "company"),
                })
                d.insert(ignore_permissions=True)
                d.submit()
                created.append(d.name)
            else:
                # re-raise so the user gets the native error if neither condition is met
                raise

    for e in A_swap:
        _create(e, to_shift)
    for e in B_swap:
        _create(e, from_shift)

    return {
        "meta": {
            "fetch_window": [str(fetch_fd), str(fetch_td)],
            "create_window": [str(create_fd), str(create_td)],
            "from_shift": from_shift,
            "to_shift": to_shift,
            "allow_multiple_assignments": int(allow_multi),
        },
        "created": created,
        "cancelled": cancelled,
        "a_to_b": prev["a_to_b"],
        "b_to_a": prev["b_to_a"],
        "stayed": prev["stayed"],
    }

# ---------- DocType controller ----------

class SwapShift(Document):
    def validate(self):
        settings = _get_settings()
        # If fields are unset (None), apply defaults. If explicitly 0/1, keep them.
        if self.respect_stay_flag is None:
            self.respect_stay_flag = settings["default_respect_stay_flag"]
        if self.cancel_existing is None:
            self.cancel_existing = settings["default_cancel_existing"]

        if not self.shift_a or not self.shift_b:
            frappe.throw(_("Shift A and Shift B are required."))
        if self.shift_a == self.shift_b:
            frappe.throw(_("Shift A and Shift B must be different."))

        if self.to_date and self.from_date and getdate(self.to_date) < getdate(self.from_date):
            frappe.throw(_("To Date must be on or after From Date"))

        if self.get("new_from_date") and self.get("new_to_date"):
            nfd, ntd = getdate(self.new_from_date), getdate(self.new_to_date)
            if ntd < nfd:
                frappe.throw(_("New To Date must be on or after New From Date"))

    def on_submit(self):
        fetch_fd, fetch_td = getdate(self.from_date), getdate(self.to_date)
        create_fd = getdate(self.new_from_date) if self.get("new_from_date") else fetch_fd
        create_td = getdate(self.new_to_date) if self.get("new_to_date") else fetch_td

        stayed_overrides = _collect_child_stay_flags(self)

        _execute_swap(
            self.shift_a,
            self.shift_b,
            fetch_fd, fetch_td,
            create_fd, create_td,
            int(self.respect_stay_flag or 0),
            int(self.cancel_existing or 0),
            stayed_overrides=stayed_overrides,
        )
        self.db_set("status", "Executed")

    @frappe.whitelist()
    def preview(self):
        fetch_fd, fetch_td = getdate(self.from_date), getdate(self.to_date)
        stayed_overrides = _collect_child_stay_flags(self)
        data = _preview_swap(
            self.shift_a, self.shift_b, fetch_fd, fetch_td, int(self.respect_stay_flag or 0),
            stayed_overrides=stayed_overrides
        )

        # Add overlap summary for the CREATION window preview convenience
        create_fd = getdate(self.new_from_date) if self.get("new_from_date") else fetch_fd
        create_td = getdate(self.new_to_date) if self.get("new_to_date") else fetch_td
        all_emps = [x["employee"] for x in (data.get("a_to_b") or [])] + [x["employee"] for x in (data.get("b_to_a") or [])]
        overlaps = _find_overlaps_for_employees(list(set(all_emps)), create_fd, create_td)
        data["creation_window"] = [str(create_fd), str(create_td)]
        data["overlaps_in_creation_window"] = len(overlaps)
        data["allow_multiple_assignments"] = _hr_allow_multiple_assignments()
        return data


    @frappe.whitelist()
    def get_employees_for_window(self):
        """Return rows for both child tables based on the FETCH window (do NOT save)."""
        fetch_fd, fetch_td = getdate(self.from_date), getdate(self.to_date)
        A = _assigned_in_window(self.shift_a, fetch_fd, fetch_td)
        B = _assigned_in_window(self.shift_b, fetch_fd, fetch_td)
        info = _employee_names([*{x.employee for x in A}, *{x.employee for x in B}])

        a_rows = [{
            "employee": r.employee,
            "employee_name": r.employee_name,
            "stay_in_current_shift": info.get(r.employee, {}).get("stay", 0),
            "assigned_to": r.name,
            "from_date": r.start_date,
            "to_date": r.end_date
        } for r in A]

        b_rows = [{
            "employee": r.employee,
            "employee_name": r.employee_name,
            "stay_in_current_shift": info.get(r.employee, {}).get("stay", 0),
            "assigned_to": r.name,
            "from_date": r.start_date,
            "to_date": r.end_date
        } for r in B]

        return {"a_rows": a_rows, "b_rows": b_rows, "a_count": len(a_rows), "b_count": len(b_rows)}
