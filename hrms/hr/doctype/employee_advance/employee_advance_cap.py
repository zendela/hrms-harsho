import frappe
from frappe.utils import getdate
from frappe import _

def _policy():
    basis = frappe.db.get_single_value("HR Settings", "advance_cap_basis") or "Base"
    percent = float(frappe.db.get_single_value("HR Settings", "advance_cap_percent") or 30)
    return basis, percent

def _active_base_from_ssa(employee, on_date):
    # Prefer active Salary Structure Assignment (docstatus=1 & date window)
    row = frappe.db.get_value(
        "Salary Structure Assignment",
        {
            "employee": employee,
            "docstatus": 1,
            "from_date": ["<=", on_date],
        },
        ["base", "from_date"],
        order_by="from_date desc",
        as_dict=True,
    )
    if row and row.base:
        return float(row.base), f"Base from SSA (from {frappe.format(row.from_date, {'fieldtype':'Date'})})"
    # fallback to Employee.base (if you store it) or 0
    base = frappe.db.get_value("Employee", employee, "base") or 0
    return float(base), "Base from Employee.base"

def _last_gross(employee, on_date):
    # Last approved Salary Slip up to on_date
    row = frappe.db.get_value(
        "Salary Slip",
        {
            "employee": employee,
            "docstatus": 1,
            "start_date": ["<=", on_date],
        },
        ["gross_pay", "start_date", "end_date", "name"],
        order_by="end_date desc, modified desc",
        as_dict=True,
    )
    if row and row.gross_pay:
        note = f"Gross from Salary Slip {row.name} ({frappe.format(row.start_date, {'fieldtype':'Date'})}–{frappe.format(row.end_date, {'fieldtype':'Date'})})"
        return float(row.gross_pay), note
    return 0.0, "No prior Salary Slip found"

@frappe.whitelist()
def compute_advance_cap(employee: str, posting_date: str = None):
    if not employee:
        return {"cap_amount": 0, "basis": "Base", "percent": 30, "note": "Missing employee"}
    on_date = getdate(posting_date) if posting_date else getdate()

    basis, percent = _policy()
    if basis == "Gross":
        gross, note = _last_gross(employee, on_date)
        cap_base = gross
    else:
        base, note = _active_base_from_ssa(employee, on_date)
        cap_base = base

    cap_amount = round((percent/100.0) * float(cap_base), 2)
    return {
        "cap_amount": cap_amount,
        "basis": basis,
        "percent": percent,
        "note": note
    }

def _enforce(doc):
    if not doc.employee:
        return
    res = compute_advance_cap(doc.employee, str(doc.posting_date))
    cap = float(res["cap_amount"] or 0)
    doc.eligible_amount = cap
    doc.cap_basis = res["basis"]
    doc.cap_percent = res["percent"]
    doc.cap_source_note = res["note"]

    # hard rule: cannot exceed cap
    req = float(doc.advance_amount or 0)
    if req > cap:
        frappe.throw(
            _("Requested amount {0} exceeds Eligible Amount {1} ({2}% of {3}).")
            .format(frappe.utils.fmt_money(req, currency=doc.currency or ""),
                    frappe.utils.fmt_money(cap, currency=doc.currency or ""),
                    res["percent"], res["basis"])
        )

# Hook from doc_events
def validate(doc, method=None):
    _enforce(doc)

def before_submit(doc, method=None):
    _enforce(doc)
