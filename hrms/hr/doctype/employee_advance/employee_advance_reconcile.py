import frappe
from frappe.utils import flt
from frappe import _

def _reconcile_doc(ea):
    """Recalculate paid/outstanding/status for a single Employee Advance doc."""
    # Sum allocated amount from submitted Payment Entries that reference this advance
    paid = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(per.allocated_amount), 0)
        FROM `tabPayment Entry Reference` per
        JOIN `tabPayment Entry` pe ON pe.name = per.parent
        WHERE pe.docstatus = 1
          AND per.reference_doctype = 'Employee Advance'
          AND per.reference_name = %s
    """, (ea.name,))[0][0] or 0)

    total = flt(ea.advance_amount or 0)
    outstanding = total - paid

    # Update numeric fields if they exist (depends on ERPNext version)
    if hasattr(ea, "paid_amount"):
        ea.db_set("paid_amount", paid)
    if hasattr(ea, "outstanding_amount"):
        ea.db_set("outstanding_amount", outstanding)

    # Flip status
    new_status = "Paid" if outstanding <= 0.0001 else "Unpaid"
    ea.db_set("status", new_status)

    return {"paid": paid, "outstanding": outstanding, "status": new_status}


@frappe.whitelist()
def refresh_payments(advance: str):
    if not advance:
        frappe.throw(_("Advance name is required"))

    ea = frappe.get_doc("Employee Advance", advance)
    if ea.docstatus != 1:
        frappe.throw(_("Only submitted Employee Advances can be reconciled"))

    # Sum allocated from submitted Payment Entries that reference this advance
    paid = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(per.allocated_amount), 0)
        FROM `tabPayment Entry Reference` per
        JOIN `tabPayment Entry` pe ON pe.name = per.parent
        WHERE pe.docstatus = 1
          AND per.reference_doctype = 'Employee Advance'
          AND per.reference_name = %s
    """, (ea.name,))[0][0] or 0)

    total = flt(ea.advance_amount or 0)
    outstanding = total - paid
    new_status = "Paid" if outstanding <= 0.0001 else "Unpaid"

    meta = frappe.get_meta("Employee Advance")
    updates = {"status": new_status}

    # Set optional fields only if they exist in this version
    if meta.has_field("paid_amount"):
        updates["paid_amount"] = paid
    if meta.has_field("outstanding_amount"):
        updates["outstanding_amount"] = outstanding

    # Persist (and bump modified so list view refreshes)
    frappe.db.set_value("Employee Advance", ea.name, updates, update_modified=True)

    # OPTIONAL: also move workflow badge if you use a "Paid" state in your workflow
    try:
        if meta.has_field("workflow_state"):
            states = {s.state for s in frappe.get_all("Workflow State", pluck="state")}
            if "Paid" in states:
                frappe.db.set_value("Employee Advance", ea.name, "workflow_state", "Paid", update_modified=True)
    except Exception:
        pass  # ignore if no workflow / permissions

    frappe.clear_document_cache("Employee Advance", ea.name)
    ea.reload()

    return {
        "name": ea.name,
        "status": ea.status,
        "paid_amount": getattr(ea, "paid_amount", paid),
        "outstanding_amount": getattr(ea, "outstanding_amount", outstanding),
    }