import frappe

def execute(filters=None):
    filters = frappe._dict(filters or {})
    cols = [
        {"label":"Employee","fieldname":"employee","fieldtype":"Link","options":"Employee","width":120},
        {"label":"Employee Name","fieldname":"employee_name","fieldtype":"Data","width":200},
        {"label":"Bank","fieldname":"bank_name","fieldtype":"Data","width":160},
        {"label":"Branch Name","fieldname":"branch_name","fieldtype":"Data","width":160},
        {"label":"Branch Code","fieldname":"branch_code","fieldtype":"Data","width":120},
        {"label":"Account No","fieldname":"bank_account_no","fieldtype":"Data","width":160},
        {"label":"Amount","fieldname":"net_pay","fieldtype":"Currency","width":130,"options":"currency"},
        {"label":"Payroll Entry","fieldname":"payroll_entry","fieldtype":"Link","options":"Payroll Entry","width":160},
        {"label":"Mode","fieldname":"mode_of_payment","fieldtype":"Data","width":90}
    ]

    conds = ["ss.docstatus = 1", "ss.net_pay > 0", "ss.mode_of_payment in ('Bank','Cheque')"]
    vals = []

    if filters.get("payroll_entry"):
        conds.append("ss.payroll_entry = %s"); vals.append(filters["payroll_entry"])
    if filters.get("company"):
        conds.append("ss.company = %s"); vals.append(filters["company"])
    if filters.get("bank_name"):
        conds.append("emp.bank_name = %s"); vals.append(filters["bank_name"])
    if filters.get("branch_code"):
        conds.append("emp.bank_code = %s"); vals.append(filters["branch_code"])

    data = frappe.db.sql(f"""
        SELECT
            ss.employee,
            ss.employee_name,
            emp.bank_name,
            emp.branch_name  AS branch_name,
            emp.bank_code    AS branch_code,
            COALESCE(emp.bank_ac_no) AS bank_account_no,
            ss.net_pay,
            ss.payroll_entry,
            ss.currency,
            ss.mode_of_payment
        FROM `tabSalary Slip` ss
        LEFT JOIN `tabEmployee` emp ON emp.name = ss.employee
        WHERE {" AND ".join(conds)}
        ORDER BY ss.employee
    """, vals, as_dict=True)

    default_cur = frappe.defaults.get_global_default("currency") or "TZS"
    for d in data:
        d["currency"] = d.get("currency") or default_cur

    return cols, data
