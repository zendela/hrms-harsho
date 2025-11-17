import frappe

def execute(filters=None):
    filters = frappe._dict(filters or {})
    cols = [
        {"label":"Employee","fieldname":"employee","fieldtype":"Link","options":"Employee","width":120},
        {"label":"Employee Name","fieldname":"employee_name","fieldtype":"Data","width":220},
        {"label":"Department","fieldname":"department","fieldtype":"Link","options":"Department","width":160},
        {"label":"Net Pay","fieldname":"net_pay","fieldtype":"Currency","width":130,"options":"currency"},
        {"label":"Signature","fieldname":"signature","fieldtype":"Data","width":180}
    ]

    conds = ["ss.docstatus = 1", "ss.net_pay > 0", "ss.mode_of_payment = 'Cash'"]
    vals = []
    if filters.get("payroll_entry"):
        conds.append("ss.payroll_entry = %s"); vals.append(filters["payroll_entry"])
    if filters.get("company"):
        conds.append("ss.company = %s"); vals.append(filters["company"])

    data = frappe.db.sql(f"""
        SELECT ss.employee, ss.employee_name, ss.department, ss.net_pay, ss.currency
        FROM `tabSalary Slip` ss
        WHERE {" AND ".join(conds)}
        ORDER BY ss.department, ss.employee
    """, vals, as_dict=True)

    total = sum((x.get("net_pay") or 0) for x in data)
    cur = data[0].get("currency") if data else (frappe.defaults.get_global_default("currency") or "TZS")
    message = f"Grand Total: {frappe.utils.fmt_money(total, currency=cur)}"

    # Add a blank 'signature' column for the table view (purely visual)
    for row in data:
        row["signature"] = ""

    return cols, data, None, None, None, message
