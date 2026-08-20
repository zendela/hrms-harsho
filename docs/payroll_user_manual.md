# Tanzania Payroll User Manual
## Step-by-Step Guide for HR and Finance Staff

**System:** ERPNext + Frappe HRMS | **Currency:** TZS

---

## Table of Contents

1. One-Time System Setup
2. Creating Salary Components
3. Creating a Salary Structure
4. Setting Up an Employee
5. Assigning a Salary Structure to an Employee
6. Employee Sales Setup
7. Salary Advance Setup
8. Monthly Payroll Workflow
9. Salary Advance Monthly Workflow
10. Employee Sales Monthly Workflow
11. Running Statutory Reports
12. Shift Management
13. Correcting Mistakes
14. Monthly Checklist

---
## 1. One-Time System Setup

Do these steps once when setting up the system for the first time. You will not need to repeat them every month.

---

### 1.1 Set Up the Company

1. On the top menu, click **Accounting**.
2. Click **Company**.
3. Click on your company name to open it.
4. Scroll down to the **Accounts** section and fill in:
   - **Default Currency** → type `TZS`
   - **Default Employee Advance Account** → select or type the account used to track advances (e.g. `Employee Advances - HMC`). This must be a **Receivable** type account.
   - **Default Cash Account** → select the bank or cash account used to pay advances.
5. Click **Save**.

✅ You are done when the page saves without errors.

---

### 1.2 Configure HR Settings

1. Click **HR** on the top menu.
2. Click **Settings**, then **HR Settings**.
3. Fill in the following fields:

| Field | What to enter |
|---|---|
| **Calculate Salary Advance Based On** | Choose `Basic Pay` (recommended) or `Gross Pay` |
| **Salary Advance Eligible Percent** | Type `30` (means employees can request up to 30% of their basic pay) |
| **Advance Deduction Salary Component** | Type or select `Salary Advance Recovery` |
| **Salary Advance Require Approval** | Tick this checkbox |
| **Advance Cap Basis** | Choose `Base` |

4. Click **Save**.

> ⚠️ The **Advance Deduction Salary Component** must already exist as a Salary Component before you save. If it does not exist yet, create it first (see Section 2) then come back here.

---

### 1.3 Create the Payroll Period

The payroll period tells the system which year's tax slabs to use.

1. Click **Payroll** on the top menu.
2. Click **Payroll Period**.
3. Click **New**.
4. Fill in:
   - **Period Name** → e.g. `2026`
   - **Start Date** → `01-01-2026`
   - **End Date** → `31-12-2026`
   - **Company** → select your company
5. Click **Save**.

✅ Done when saved without errors.

---

### 1.4 Create the Income Tax Slab (PAYE)

This tells the system how much PAYE to deduct at each income level.

1. Click **Payroll** → **Income Tax Slab** → **New**.
2. Fill in:
   - **Name** → `Tanzania PAYE 2026`
   - **Effective From** → `01-01-2026`
   - **Currency** → `TZS`
3. In the **Slabs** table, add one row for each band:

| From Amount | To Amount | Percent Deduction |
|---|---|---|
| 0 | 270,000 | 0 |
| 270,001 | 520,000 | 8 |
| 520,001 | 760,000 | 20 |
| 760,001 | 1,000,000 | 25 |
| 1,000,001 | 0 (leave blank = no limit) | 30 |

4. Click **Save**.

> ⚠️ Check TRA's website every year to confirm the bands have not changed.

---

### 1.5 Verify Chart of Accounts

Make sure these accounts exist. Go to **Accounting → Chart of Accounts** and search for each one. If any is missing, create it.

| Account Name | Account Type |
|---|---|
| Employee Advances | Receivable |
| PAYE Payable | Payable |
| NSSF Payable | Payable |
| NHIF Payable | Payable |
| WCF Payable | Payable |
| SDL Payable | Payable |
| TUICO Payable | Payable |
| Employee Sales Deductions | Payable |
| Salary Payable | Payable |


---

## 2. Creating Salary Components

A Salary Component is one line on a payslip — for example "Basic Pay" or "PAYE". You must create each component before you can use it in a salary structure.

**Path:** Payroll → Salary Component → New

Create each component below one at a time. For each one, follow these steps:

1. Click **Payroll** → **Salary Component** → **New**.
2. Fill in the fields shown in the table below.
3. In the **Accounts** table at the bottom, click **Add Row** and link the component to the correct GL account.
4. Click **Save**.

### 2.1 Earning Components

| Component Name | Type | Is Tax Applicable | Notes |
|---|---|---|---|
| Basic Pay | Earning | ✅ Yes | Base salary — all formulas reference this |
| Housing Allowance | Earning | ✅ Yes | Usually a % of Basic Pay |
| Transport Allowance | Earning | ❌ No | Per-employee amount set on Employee record |
| Responsibility Allowance | Earning | ✅ Yes | Per-employee amount set on Employee record |

### 2.2 Deduction Components

| Component Name | Type | Variable Based on Taxable Salary | Notes |
|---|---|---|---|
| PAYE | Deduction | ✅ Yes | Tick this — system computes from tax slab automatically |
| NSSF Employee | Deduction | ❌ No | Formula: `gross_pay * contribution_in_percent / 100` |
| NHIF | Deduction | ❌ No | Fixed amount per employee — use condition `has_nhif == 1` |
| TUICO | Deduction | ❌ No | Fixed amount; add it only to Salary Structures used by TUICO members |
| WCF | Deduction | ❌ No | Employer-only — formula: `gross_pay * 0.005` |
| Salary Advance Recovery | Deduction | ❌ No | Leave amount/formula blank — injected automatically |
| Employee Sales Deduction | Deduction | ❌ No | Leave amount/formula blank — injected via Employee Sale |

> ⚠️ **Important for NSSF and NHIF:** These do not apply to every employee. You must add a **Condition** on the salary structure row so the system skips employees who are not enrolled. For TUICO, use a Salary Structure containing the TUICO component only for union members.

> ⚠️ **For PAYE:** After ticking **Variable Based on Taxable Salary**, a new field **Income Tax Slab** will appear. Select the slab you created in step 1.4.


---

## 3. Creating a Salary Structure

A Salary Structure is the template that defines what every employee in a group earns and what is deducted. You create it once and assign it to employees.

1. Click **Payroll** → **Salary Structure** → **New**.
2. Fill in:
   - **Name** → e.g. `HMC Monthly`
   - **Company** → your company
   - **Payroll Frequency** → `Monthly`
   - **Currency** → `TZS`
3. Click **Save** (do not submit yet — add components first).

### 3.1 Adding Earning Components

In the **Earnings** table, click **Add Row** for each earning:

| Component | Amount / Formula | Notes |
|---|---|---|
| Basic Pay | `base` | The word `base` means it pulls from the Salary Structure Assignment |
| Housing Allowance | `base * 0.30` | 30% of basic — adjust as needed |
| Transport Allowance | `transport_allowance` | Pulls from Employee record field |
| Responsibility Allowance | `responsibility_allowance` | Pulls from Employee record field |

### 3.2 Adding Deduction Components

In the **Deductions** table, click **Add Row** for each deduction:

| Component | Formula | Condition | Notes |
|---|---|---|---|
| PAYE | *(leave blank — auto-computed)* | *(none)* | Tick Variable Based on Taxable Salary on the component |
| NSSF Employee | `gross_pay * (contribution_in_percent or 10) / 100` | `has_nssf == 1` | Only deducted for enrolled employees |
| NHIF | *(fixed amount per grade — enter manually)* | `has_nhif == 1` | Only deducted for enrolled employees |
| TUICO | *(fixed amount)* | *(none)* | Add only to a Salary Structure assigned to TUICO members |
| WCF | `gross_pay * 0.005` | *(none)* | Employer cost — shown on slip for reporting |
| Salary Advance Recovery | *(leave blank)* | *(none)* | Auto-injected when advance is paid |
| Employee Sales Deduction | *(leave blank)* | *(none)* | Auto-injected from Employee Sale |

> **How to enter a Condition:** Click the row, then in the **Condition** field type exactly `has_nssf == 1` (for NSSF). The system will only calculate that deduction when the employee's flag is ticked.

4. After adding all rows, click **Save**, then click **Submit**.

✅ The structure is now ready to assign to employees.


---

## 4. Setting Up an Employee

Do this for every new employee before their first payroll.

1. Click **HR** → **Employee** → **New**.
2. Fill in the tabs as described below.

### 4.1 Basic Information Tab

| Field | What to enter |
|---|---|
| **First Name / Last Name** | Employee's full name |
| **Date of Birth** | e.g. `15-03-1990` |
| **Gender** | Select Male or Female |
| **Date of Joining** | First working day |
| **Company** | Your company |
| **Status** | `Active` |
| **Employee Number** | Staff ID number |
| **Department** | Select the department |
| **Designation** | Job title |

### 4.2 Salary Tab

Scroll to the **Salary** tab and fill in:

| Field | What to enter |
|---|---|
| **Salary Mode** | Select `Bank` for bank transfer |
| **Bank Name** | Full name of the bank (e.g. `CRDB Bank`) |
| **Bank Code** | Numeric bank code (e.g. `017010` for CRDB). This is used in the advance disbursement file sent to the bank. |
| **Bank A/C No.** | Employee's bank account number |

Then scroll to **Statutory Benefits** and tick the applicable boxes:

| Field | Tick if... |
|---|---|
| **Has NSSF** | Employee is registered with NSSF |
| **Has NHIF** | Employee has NHIF health insurance |

If **Has NSSF** is ticked, also fill in:

| Field | What to enter |
|---|---|
| **Contribution in Percent** | Usually `10` (10% of gross) |
| **Has Fixed Contribution** | Tick only if this employee pays a fixed amount instead of a percentage |
| **Contribution Fixed Amount** | Enter the fixed amount if the above is ticked |

Then scroll to **Per-Employee Allowances**:

| Field | What to enter |
|---|---|
| **Transport Allowance** | Monthly transport amount in TZS. Enter `0` if not applicable. |
| **Responsibility Allowance** | Monthly responsibility amount in TZS. Enter `0` if not applicable. |

3. Click **Save**.

✅ The employee record is saved. Now assign a salary structure (Section 5).


---

## 5. Assigning a Salary Structure to an Employee

Every employee must have a Salary Structure Assignment before payroll can be run for them.

1. Click **Payroll** → **Salary Structure Assignment** → **New**.
2. Fill in:

| Field | What to enter |
|---|---|
| **Employee** | Search and select the employee |
| **Salary Structure** | Select `HMC Monthly` (or your structure name) |
| **From Date** | The date this salary takes effect (usually date of joining) |
| **Base** | The employee's monthly basic pay in TZS (e.g. `800000`) |
| **Currency** | `TZS` |

3. Click **Save**, then click **Submit**.

> ⚠️ The **Base** amount is the foundation for all formula calculations. If an employee gets a salary increment, create a **new** Salary Structure Assignment with the new base and a new From Date. Do not edit the old one.

✅ The employee will now appear in payroll runs.

---

## 6. Employee Sales Setup

This section covers the one-time setup for recording goods sold to employees (mango, eggs, chicken, etc.) and deducting the cost from their salary.

### 6.1 One-Time Setup

**Step 1 — Create the Salary Component**

Follow Section 2 to create a component named `Employee Sales Deduction` (Deduction type, not tax-applicable). Map it to the `Employee Sales Deductions` GL account.

**Step 2 — Add it to the Salary Structure**

Open your salary structure (Payroll → Salary Structure → HMC Monthly).

> ⚠️ You cannot edit a submitted salary structure directly. Click **Amend**, make the change, then **Save** and **Submit** the amended version.

In the **Deductions** table, add a row:
- **Component:** `Employee Sales Deduction`
- **Formula:** leave blank
- **Condition:** leave blank

Click **Save** and **Submit**.


---

## 7. Salary Advance Setup

### 7.1 One-Time Setup Checklist

Work through this list once before the first advance is processed:

- [ ] **Create `Salary Advance Recovery` salary component** (Section 2 — Deduction type, not tax-applicable, mapped to Employee Advances account)
- [ ] **Set Advance Deduction Salary Component in HR Settings** to `Salary Advance Recovery` (Section 1.2)
- [ ] **Set Default Employee Advance Account** on the Company (Section 1.1)
- [ ] **Set Default Cash Account** on the Company (Section 1.1)
- [ ] **Set Advance Cap Basis and Percent** in HR Settings (Section 1.2)
- [ ] **Ensure every employee has Bank Code and Bank A/C No.** filled in (Section 4.2)

### 7.2 Advance Approval Workflow — Who Does What

The system enforces a 4-stage approval before an advance is disbursed:

| Stage | Who acts | What they do |
|---|---|---|
| **Draft** | Employee / HR Officer | Creates the advance request |
| **Pending HR Review** | HR User | Reviews and clicks **Recommend** or **Reject** |
| **Recommended** | HR Manager | Approves (sends to Finance) or Rejects |
| **Pending Finance Approval** | Accounts User | Clicks **Approve & Submit** or Rejects |
| **Approved** | System | Advance is submitted and ready for payment |
| **Rejected** | Employee | Can edit and resubmit |

> ⚠️ Only the **Accounts User** role can do the final **Approve & Submit**. Make sure the Finance officer has this role assigned in their User settings.


---

## 8. Monthly Payroll Workflow

Run these steps every month in this exact order.

---

### Step 1 — Record Employee Sales (Goods Sold)

Do this before generating payroll so the deductions appear on the salary slips.

1. Click **HR** → **Employee Sale** → **New**.
2. Fill in:
   - **Company** → your company
   - **Payroll Month** → first day of the current month (e.g. `01-04-2026`)
   - **Sales Date** → today's date
   - **Deduction Salary Component** → `Employee Sales Deduction`
   - **Currency** → `TZS`
3. In the **Items Sold** table, click **Add Row** for each sale:
   - **Employee** → search and select the employee
   - **Item** → type the item name (e.g. `Mango`, `Eggs`, `Chicken`)
   - **Qty** → quantity sold
   - **Unit Price** → price per unit in TZS
   - The **Amount** column fills automatically
4. Add all sales for all employees in this one document.
5. Click **Save**, review the totals, then click **Submit**.

✅ The system automatically creates one deduction entry per employee. These will appear on their salary slips.

---

### Step 2 — Process Salary Advances

Complete the full advance workflow (Section 9) before generating payroll.

---

### Step 3 — Create the Payroll Entry

1. Click **Payroll** → **Payroll Entry** → **New**.
2. Fill in:

| Field | What to enter |
|---|---|
| **Company** | Your company |
| **Payroll Frequency** | `Monthly` |
| **Start Date** | First day of the month (e.g. `01-04-2026`) |
| **End Date** | Last day of the month (e.g. `30-04-2026`) |
| **Payroll Account** | Select `Salary Payable` |
| **Bank Account** | Select the bank account salaries are paid from |
| **Department** | Leave blank to include all departments |

3. Click **Get Employees**. A list of employees will appear at the bottom.
4. Check the list — every active employee should be there. If someone is missing, check that they have a submitted Salary Structure Assignment.
5. Click **Create Salary Slips**.
6. Wait for the system to finish. A message will confirm how many slips were created.

---

### Step 4 — Review Salary Slips

Before submitting, always check a sample of slips.

1. Click **Payroll** → **Salary Slip**.
2. Filter by the current month and open 3–5 slips at random.
3. For each slip, verify:
   - **Gross Pay** looks correct
   - **PAYE** amount is reasonable (compare against the tax slab)
   - **NSSF** appears only for employees with Has NSSF ticked
   - **NHIF** appears only for employees with Has NHIF ticked
   - **TUICO** appears only for TUICO members
   - **Salary Advance Recovery** appears for employees whose advance was paid this month
   - **Employee Sales Deduction** appears for employees who purchased goods
   - **Net Pay** = Gross Pay minus all deductions

> ⚠️ If something looks wrong, do **not** submit. Go back to the Payroll Entry and click **Delete Salary Slips**, fix the issue, then recreate them.

---

### Step 5 — Submit Salary Slips

1. Go back to the Payroll Entry.
2. Click **Submit Salary Slips**.
3. Confirm when prompted.

✅ All slips are now locked. You cannot edit them after this point.

---

### Step 6 — Make the Bank Payment Entry

1. Still in the Payroll Entry, click **Make Bank Entry**.
2. The system creates a Journal Entry that:
   - Debits Salary Payable (clears the liability)
   - Credits the bank account for each employee's net pay
   - Credits PAYE Payable, NSSF Payable, etc.
   - Credits Employee Advances account for advance recovery amounts (this closes the advance)
3. Review the Journal Entry, then click **Submit**.

---

### Step 7 — Pay Statutory Obligations

After the payroll Journal Entry is posted, pay each statutory body and record the payment:

| Obligation | Who to pay | Deadline | Journal Entry |
|---|---|---|---|
| PAYE | Tanzania Revenue Authority (TRA) | 7th of next month | Dr PAYE Payable / Cr Bank |
| NSSF (employee + employer) | NSSF | 7th of next month | Dr NSSF Payable / Cr Bank |
| NHIF | NHIF | Monthly | Dr NHIF Payable / Cr Bank |
| WCF | WCF Board | Monthly | Dr WCF Payable / Cr Bank |
| SDL | TRA | Monthly | Dr SDL Payable / Cr Bank |
| TUICO | TUICO | Monthly | Dr TUICO Payable / Cr Bank |

To record each payment: **Accounting → Journal Entry → New**, select **Bank Entry**, enter the debit and credit lines, and submit.


---

## 9. Salary Advance Monthly Workflow

Run these steps every month before generating payroll (before Step 2 of Section 8).

---

### Step 1 — Employee Creates the Advance Request

1. Click **HR** → **Employee Advance** → **New**.
2. Fill in:
   - **Employee** → search and select your name (or the employee's name if HR is entering it)
   - The system automatically fills:
     - **Eligible Amount** — the maximum the employee can request (e.g. 30% of basic pay)
     - **Advance Amount** — pre-filled from Eligible Amount (you can reduce it but not exceed it)
     - **Payroll Month** — set to the first day of the current month
3. Confirm the **Payroll Month** is correct.
4. Click **Save**.
5. Click **Submit for Review**.

> ⚠️ The system will block a second advance if one already exists for this employee in the same payroll month.

---

### Step 2 — HR User Reviews

1. The HR User opens the advance from their **Notifications** or by going to **HR → Employee Advance** and filtering by **Workflow State = Pending HR Review**.
2. Open the advance and check the amount is within policy.
3. Click **Recommend** to send it to the HR Manager, or **Reject** to send it back.

---

### Step 3 — HR Manager Approves

1. The HR Manager opens advances with **Workflow State = Recommended**.
2. Reviews and clicks **Approve** (sends to Finance) or **Reject**.

---

### Step 4 — Finance Does Final Approval

1. The Accounts User opens advances with **Workflow State = Pending Finance Approval**.
2. Confirms the amount is available.
3. Clicks **Approve & Submit**.

✅ The advance is now submitted and ready for payment.

---

### Step 5 — Generate the Disbursement Report

This report produces the file you send to the bank for bulk transfer.

1. Click **HR** → **Reports** → **Employee Advance Disbursement**.
2. Set the filters:
   - **Payroll Month** → first day of the current month (e.g. `01-04-2026`)
   - **Company** → your company
   - **Reference** → the system auto-fills this as e.g. `HMC SALARY ADVANCE APRIL 2026`. Edit if needed.
3. Click **Run**.
4. The report shows one row per employee with their name, bank code, bank account number, and amount.
5. Click the **Export** button (top right) → choose **Excel** or **CSV**.
6. Send the exported file to the bank.

---

### Step 6 — Mark Advances as Paid (After Bank Confirms)

After the bank confirms the transfers have been made:

1. Click **HR** → **Employee Advance**.
2. In the list view, use the filters to show:
   - **Status** = `Unpaid`
   - **Payroll Month** = current month
3. Tick the checkbox at the top of the list to select all rows.
4. Click **Actions** → **Mark as Paid**.
5. In the dialog that appears:
   - **Mode of Payment** → select `Bank Transfer` or your mode
   - **Bank Account** → select the account used (or leave blank to use the company default)
6. Click **Create Payment Entry**.

✅ The system:
- Creates one Payment Entry covering all selected advances
- Changes each advance status to **Paid**
- Automatically creates a **Salary Advance Recovery** deduction entry for each advance, dated to the Payroll Month

---

### Step 7 — Verify the Deduction Entries Were Created

1. Click **Payroll** → **Additional Salary**.
2. Filter by:
   - **Salary Component** = `Salary Advance Recovery`
   - **Payroll Date** = current month
3. Confirm one entry exists for each employee whose advance was paid.

✅ These entries will automatically appear as deductions on the salary slips when payroll is run.


---

## 10. Employee Sales Monthly Workflow

This is covered in Section 8 Step 1. As a reminder, the monthly process is:

1. At the end of each month, collect the sales records from the store (who bought what and how much).
2. Create one **Employee Sale** document for the whole month (HR → Employee Sale → New).
3. Add every sale as a row in the Items table.
4. Submit the document.
5. The system creates one deduction entry per employee automatically.
6. When payroll is run, the deduction appears on each employee's salary slip.

> ⚠️ Submit the Employee Sale document **before** creating salary slips. If you submit it after, the deduction will not appear on the slips for that month.

---

## 11. Running Statutory Reports

Use these reports to prepare your monthly statutory filings. Run them after salary slips are submitted.

**Path for all reports:** Payroll → Reports → *(report name)*

---

### 11.1 PAYE Report

**Report name:** Tanzania PAYE Report

1. Click **Payroll** → scroll to **Reports** → click **Tanzania PAYE Report**.
2. Set filters:
   - **Payroll Month** → first day of the month
   - **Company** → your company
   - **PAYE Salary Component** → `PAYE`
3. Click **Run**.
4. The report shows each employee's gross pay and PAYE deducted.
5. The **Total PAYE** in the summary bar is the amount to pay TRA.
6. Click **Export** → **Excel** to download for your records.

---

### 11.2 NSSF Report

**Report name:** Tanzania NSSF Report

1. Set filters: Payroll Month, Company, **NSSF Employee Component** = `NSSF Employee`.
2. Click **Run**.
3. The report shows only employees with **Has NSSF** ticked.
4. Each row shows the employee contribution, employer contribution (equal amount), and total.
5. The **Rate/Fixed** column shows whether the employee pays a percentage or a fixed amount.
6. The summary bar shows **Total NSSF Payable** (employee + employer combined) — this is what you pay to NSSF.

---

### 11.3 NHIF Report

**Report name:** Tanzania NHIF Report

1. Set filters: Payroll Month, Company, **NHIF Salary Component** = `NHIF`.
2. Click **Run**.
3. Only employees with **Has NHIF** ticked appear.
4. Export and use the total to pay NHIF.

---

### 11.4 TUICO Report

**Report name:** Tanzania TUICO Report

1. Set filters: Payroll Month, Company, **TUICO Salary Component** = `TUICO`.
2. Click **Run**.
3. Only TUICO members appear.
4. Export and use the total to pay TUICO.

---

### 11.5 WCF Report

**Report name:** Tanzania WCF Report

1. Set filters: Payroll Month, Company.
2. The **WCF Rate (%)** defaults to `0.5` — change only if the rate has changed.
3. Click **Run**.
4. The summary shows **Total WCF Payable** — employer-only contribution.

---

### 11.6 SDL Report

**Report name:** Tanzania SDL Report

1. Set filters: Payroll Month, Company.
2. The **SDL Rate (%)** defaults to `4.5` — change only if TRA has updated the rate.
3. Click **Run**.
4. The summary shows **Total SDL Payable** — employer-only contribution.


---

## 12. Shift Management

### 12.1 Setting an Employee's Shift

1. Click **HR** → **Shift Assignment** → **New**.
2. Fill in:
   - **Employee** → select the employee
   - **Shift Type** → select the shift (e.g. Morning, Night)
   - **Start Date** → when the shift starts
   - **End Date** → when the shift ends (leave blank for indefinite)
3. Click **Save** and **Submit**.

### 12.2 Marking an Employee as "Stay in Current Shift"

If an employee should never be moved during a shift swap:

1. Open the employee record (HR → Employee → search by name).
2. Go to the **Shift** tab.
3. Tick **Stay In Current Shift**.
4. Click **Save**.

> This employee will be excluded from swaps but will still receive a new shift assignment in their original shift when a swap is processed.

### 12.3 Swapping Shifts Between Two Groups

Use this when you want to rotate two groups of employees between two shifts.

1. Click **HR** → **Swap Shift** → **New**.
2. Fill in:

| Field | What to enter |
|---|---|
| **Shift A** | First shift type (e.g. Morning) |
| **From Date / To Date** | The date range to look at who is currently assigned |
| **Shift B** | Second shift type (e.g. Night) |
| **New Assignment From Date** | Start of the new assignment period |
| **New Assignment To Date** | End of the new assignment period |
| **Respect Stay** | Tick this to protect employees with "Stay In Current Shift" |
| **Cancel Existing** | Tick this to remove old overlapping assignments |

3. Click **Preview** — a table shows which employees will be swapped and which will stay. Review carefully.
4. If the preview looks correct, click **Submit**.

✅ The system creates new shift assignments for all employees in the new date range. Employees marked "Stay" keep their original shift.

---

## 13. Cancelling or Correcting a Mistake

### 13.1 Cancelling a Salary Slip

You can only cancel a salary slip if the Payroll Entry has not yet been submitted.

1. Open the salary slip (Payroll → Salary Slip → search by employee name).
2. Click **Cancel**.
3. Fix the issue (e.g. update the employee record or salary structure).
4. Go back to the Payroll Entry and recreate the slip.

### 13.2 Cancelling a Submitted Payroll Entry

1. Open the Payroll Entry.
2. Click **Cancel**.
3. This also cancels all linked salary slips and the Journal Entry.
4. Fix the issue and rerun from Step 3 of Section 8.

### 13.3 Cancelling an Employee Advance

1. Open the Employee Advance.
2. Click **Cancel**.
3. The system will also cancel the linked Payment Entry and the Salary Advance Recovery deduction entry.
4. If the advance was already deducted from payroll, you will need to manually cancel the Additional Salary entry as well.

### 13.4 Cancelling an Employee Sale

1. Open the Employee Sale document.
2. Click **Cancel**.
3. The system automatically cancels all linked Additional Salary (Employee Sales Deduction) entries.
4. If payroll has already been run, you will need to cancel and redo the salary slips.

> ⚠️ Always cancel in reverse order: cancel the latest document first. For example, cancel the Payroll Entry before cancelling a Salary Structure Assignment.

---

## 14. Quick Reference — Monthly Checklist

Use this checklist every month. Tick each item as you complete it.

### Before Running Payroll

- [ ] Collect store sales records for the month
- [ ] Create and submit **Employee Sale** document for all goods sold
- [ ] Collect advance requests from employees
- [ ] Create **Employee Advance** records and route through approval workflow
- [ ] Finance does **Approve & Submit** on all approved advances
- [ ] Run **Employee Advance Disbursement** report and send to bank
- [ ] After bank confirms, select all Unpaid advances → **Actions → Mark as Paid**
- [ ] Verify **Additional Salary** (Salary Advance Recovery) entries were auto-created

### Running Payroll

- [ ] Click **Payroll Entry → New** and fill in the month dates
- [ ] Click **Get Employees** — verify all active employees appear
- [ ] Click **Create Salary Slips**
- [ ] Open 3–5 random slips and verify earnings, deductions, and net pay
- [ ] Click **Submit Salary Slips**
- [ ] Click **Make Bank Entry** and submit the Journal Entry

### After Payroll

- [ ] Run **Tanzania PAYE Report** — note total, pay TRA by 7th
- [ ] Run **Tanzania NSSF Report** — note total (employee + employer), pay NSSF by 7th
- [ ] Run **Tanzania NHIF Report** — pay NHIF
- [ ] Run **Tanzania TUICO Report** — pay TUICO
- [ ] Run **Tanzania WCF Report** — pay WCF Board
- [ ] Run **Tanzania SDL Report** — pay TRA (SDL)
- [ ] Post Journal Entries for each statutory payment
- [ ] File returns with TRA, NSSF, NHIF as required

---

*Last updated: April 2026*
