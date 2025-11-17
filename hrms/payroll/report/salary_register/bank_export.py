import frappe, csv, io

@frappe.whitelist()
def export_bank_csv(filters: dict=None):
    filters = frappe._dict(filters or {})
    cols, rows = frappe.get_attr(
        "hrms_ext.payroll.report.payroll_bank_disbursement.payroll_bank_disbursement.execute"
    )(filters)

    buf = io.StringIO()
    w = csv.writer(buf)
    # Adjust headers to your bank’s template if needed
    w.writerow(["Employee", "Name", "Bank", "Branch", "Account", "Amount", "Reference"])
    for r in rows:
        ref = f"{filters.get('payroll_entry','')}-{r.get('employee') or ''}"
        w.writerow([
            r.get("employee"), r.get("employee_name"), r.get("bank_name"),
            r.get("bank_branch"), r.get("bank_account_no"), r.get("net_pay"), ref
        ])

    fname = f"bank-disbursement-{filters.get('payroll_entry','all')}.csv"
    filedoc = frappe.get_doc({
        "doctype":"File",
        "file_name": fname,
        "content": buf.getvalue(),
        "is_private": 1
    }).insert()
    return {"file_url": filedoc.file_url}
