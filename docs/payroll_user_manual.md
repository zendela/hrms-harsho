# Payroll User Manual
## Tanzania Payroll — End-to-End Setup & Monthly Operations

---

## Table of Contents

1. [One-Time System Setup](#1-one-time-system-setup)
2. [Employee Master Setup](#2-employee-master-setup)
3. [Salary Structure Setup](#3-salary-structure-setup)
4. [Tanzania Statutory Deductions](#4-tanzania-statutory-deductions)
5. [Employee Sales Deductions (Mango, Eggs, Chicken)](#5-employee-sales-deductions)
6. [Salary Advance Setup](#6-salary-advance-setup)
7. [Monthly Payroll Workflow](#7-monthly-payroll-workflow)
8. [Salary Advance Monthly Workflow](#8-salary-advance-monthly-workflow)
9. [Shift Management](#9-shift-management)
10. [Suggested Improvements](#10-suggested-improvements)

---

## 1. One-Time System Setup

### 1.1 Company Settings

**Path:** Accounting → Company → *your company*

| Field | Value |
|---|---|
| Default Currency | TZS |
| Default Employee Advance Account | e.g. `1310 - Employee Advances - HMC` (Receivable type) |
| Default Cash / Bank Account | The account used to disburse advances |

### 1.2 HR Settings

**Path:** HR → Settings → HR Settings

| Field | Value | Purpose |
|---|---|---|
| **Calculate Salary Advance Based On** | `Basic Pay` or `Gross Pay` | Basis for computing eligible advance amount |
| **Salary Advance Eligible Percent** | e.g. `30` | % of basis an employee may request |
| **Advance Deduction Salary Component** | e.g. `Salary Advance Recovery` | Deduction component auto-created when advance is paid |
| **Salary Advance Require Approval** | Checked | Advances require HR/Finance approval before submission |
| **Unlink Payment on Cancellation of Employee Advance** | As required | Whether to unlink payment entries on advance cancellation |

### 1.3 Payroll Period

**Path:** Payroll → Payroll Period

Create a Payroll Period covering the fiscal year (e.g. 1 Jan 2026 – 31 Dec 2026). This is required for income tax slab calculations.

### 1.4 Income Tax Slab (PAYE)

**Path:** Payroll → Income Tax Slab

Create a slab for Tanzania PAYE using the current TRA bands. Example (2025/2026):

| From (TZS) | To (TZS) | Rate % |
|---|---|---|
| 0 | 270,000 | 0 |
| 270,001 | 520,000 | 8 |
| 520,001 | 760,000 | 20 |
| 760,001 | 1,000,000 | 25 |
| 1,000,001 | and above | 30 |

> ⚠️ Always verify current TRA bands before each fiscal year.

### 1.5 Chart of Accounts

Ensure the following accounts exist:

| Account | Type | Purpose |
|---|---|---|
| Employee Advances | Receivable | Tracks advance balances |
| PAYE Payable | Payable | PAYE withheld from employees |
| NSSF Payable | Payable | NSSF contributions |
| WCF Payable | Payable | Workers Compensation Fund |
| SDL Payable | Payable | Skills Development Levy |
| Employee Sales Deductions | Payable | Goods sold to employees |
| Salary Payable | Payable | Net salary payable |

---

## 2. Employee Master Setup

**Path:** HR → Employee → *New Employee*

### 2.1 Required Fields

| Tab | Field | Notes |
|---|---|---|
| Personal | Employee Name, Date of Birth, Gender | |
| Job | Date of Joining, Department, Designation | |
| Salary | **Salary Mode** | Set to `Bank` for bank transfer employees |
| Salary | **Bank Name** | Enter the bank code (e.g. `017010` for CRDB) |
| Salary | **Bank A/C No.** | Employee's bank account number |
| Shift | **Stay In Current Shift** | Check if this employee should never be swapped out of their shift |

> **Bank Name field note:** This field is used as "Bank Code" in the Advance Disbursement report. Enter the numeric bank code (e.g. `017010`) rather than the full bank name so the report matches the bank's expected format.

### 2.2 Salary Structure Assignment

**Path:** Payroll → Salary Structure Assignment → New

After creating the employee, assign a salary structure:

| Field | Value |
|---|---|
| Employee | Select employee |
| Salary Structure | Select applicable structure |
| From Date | Date of joining or effective date |
| Base | Monthly basic pay in TZS |
| Currency | TZS |

> The **Base** amount here is what the advance cap calculation uses when **Calculate Salary Advance Based On** is set to `Basic Pay`.

---

## 3. Salary Structure Setup

**Path:** Payroll → Salary Structure → New

### 3.1 Recommended Structure for Tanzania

**Earnings:**

| Component | Type | Notes |
|---|---|---|
| Basic Pay | Earning | Formula or fixed — base of all calculations |
| Housing Allowance | Earning | Typically % of basic |
| Transport Allowance | Earning | Fixed or % |
| Other Allowances | Earning | As applicable |

**Deductions:**

| Component | Type | Notes |
|---|---|---|
| PAYE | Deduction | `variable_based_on_taxable_salary = 1` — computed from Income Tax Slab |
| NSSF Employee | Deduction | 10% of gross (employee share) |
| WCF | Deduction | 0.5% of gross |
| Salary Advance Recovery | Deduction | Used for advance deductions — **do not add formula here**; it is injected via Additional Salary |
| Employee Sales Deduction | Deduction | Used for goods sold to employees |

### 3.2 Salary Component Configuration

**Path:** Payroll → Salary Component

For each component, set:

| Field | Notes |
|---|---|
| Type | Earning or Deduction |
| Is Tax Applicable | Check for earnings that are taxable |
| Variable Based on Taxable Salary | Check **only** for PAYE |
| Salary Component Account | Map to the correct GL account |

---

## 4. Tanzania Statutory Deductions

These are configured as Salary Components and included in the Salary Structure. They are calculated automatically when Salary Slips are generated.

### 4.1 PAYE (Pay As You Earn)

- Salary Component type: **Deduction**
- Enable **Variable Based on Taxable Salary**
- Link to the Income Tax Slab created in step 1.4
- Computed automatically by the system based on taxable gross

### 4.2 NSSF (National Social Security Fund)

- Employee contribution: **10% of gross pay**
- Employer contribution: **10% of gross pay** (recorded separately via Journal Entry or a separate payroll component)
- Configure as a formula-based Deduction component:
  ```
  gross_pay * 0.10
  ```

### 4.3 WCF (Workers Compensation Fund)

- **0.5% of gross pay**, employer-only contribution
- Typically handled via a separate Journal Entry at month-end rather than on the salary slip
- If included on the slip, configure as a Deduction with formula:
  ```
  gross_pay * 0.005
  ```

### 4.4 SDL (Skills Development Levy)

- **4.5% of gross payroll**, employer-only
- Typically posted as a Journal Entry after payroll is finalised, not on individual salary slips

> **Suggested improvement:** Create a Payroll Summary report that totals NSSF employer, WCF, and SDL across all employees for the month to simplify statutory filing.

---

## 5. Employee Sales Deductions (Mango, Eggs, Chicken)

Goods sold to employees (mango, eggs, chicken) are deducted from salary. The recommended approach is **Additional Salary** (Deduction type) created per employee per month.

### 5.1 One-Time Setup

1. Create a Salary Component: **Employee Sales Deduction**
   - Type: Deduction
   - Not tax-applicable
   - Map to account: `Employee Sales Deductions - HMC` (Payable)

2. Ensure this component is in the Salary Structure (with amount 0 or no formula — the actual amount comes from Additional Salary each month).

### 5.2 Monthly Process

For each employee who purchased goods:

**Path:** Payroll → Additional Salary → New

| Field | Value |
|---|---|
| Employee | Select employee |
| Salary Component | `Employee Sales Deduction` |
| Amount | Total value of goods purchased (TZS) |
| Payroll Date | First day of the payroll month (e.g. 2026-04-01) |
| Type | Deduction |

Save and Submit. The deduction will appear automatically on the employee's Salary Slip when it is generated.

> **Suggested improvement:** Build a simple Sales Invoice or internal sales form where the store records each sale against an employee. On save, it auto-creates the Additional Salary entry. This eliminates manual data entry and creates an audit trail of what was sold.

---

## 6. Salary Advance Setup

### 6.1 One-Time Setup Checklist

- [ ] Set **Advance Deduction Salary Component** in HR Settings (e.g. `Salary Advance Recovery`)
- [ ] Create the `Salary Advance Recovery` Salary Component (Deduction type, not tax-applicable)
- [ ] Set **Default Employee Advance Account** on the Company
- [ ] Set **Default Cash Account** on the Company (used for bulk payment)
- [ ] Set **Calculate Salary Advance Based On** and **Salary Advance Eligible Percent** in HR Settings
- [ ] Ensure each employee has **Bank Name** (bank code) and **Bank A/C No.** filled in

---

## 7. Monthly Payroll Workflow

### Step 1 — Process Employee Sales Deductions

Before generating payroll, create Additional Salary entries for all goods sold to employees that month (see Section 5.2).

### Step 2 — Process Salary Advances

Complete the full advance workflow (see Section 8) before generating payroll so that advance deductions are already in place as Additional Salary entries.

### Step 3 — Create Payroll Entry

**Path:** Payroll → Payroll Entry → New

| Field | Value |
|---|---|
| Company | Your company |
| Payroll Frequency | Monthly |
| Start Date | First day of month (e.g. 2026-04-01) |
| End Date | Last day of month (e.g. 2026-04-30) |
| Department | Leave blank for all departments, or filter |
| Branch | As applicable |
| Payroll Account | Salary Payable account |

Click **Get Employees** → verify the list → Click **Create Salary Slips**.

### Step 4 — Review Salary Slips

**Path:** Payroll → Salary Slip

Open a sample slip and verify:
- Earnings are correct (Basic, Housing, Transport, etc.)
- PAYE is computed correctly against the tax slab
- NSSF deduction is 10% of gross
- **Salary Advance Recovery** deduction appears for employees who received a paid advance this month
- **Employee Sales Deduction** appears for employees who purchased goods
- Net pay is correct

### Step 5 — Submit Salary Slips

Back in Payroll Entry, click **Submit Salary Slips**. This locks all slips.

### Step 6 — Post Journal Entry (Bank Transfer)

In Payroll Entry, click **Make Bank Entry**. This creates a Journal Entry that:
- Debits Salary Payable
- Credits the bank account for net pay per employee
- Credits PAYE Payable, NSSF Payable, etc.
- Credits Employee Advance account for advance recovery amounts (closing the advance)

### Step 7 — Statutory Payments

After payroll JE is posted:

| Obligation | Deadline | Action |
|---|---|---|
| PAYE | 7th of following month | Pay TRA; post JE: Dr PAYE Payable / Cr Bank |
| NSSF (employee + employer) | 7th of following month | Pay NSSF; post JE |
| WCF | Monthly | Pay WCF; post JE |
| SDL | Monthly | Pay SDL; post JE |

---

## 8. Salary Advance Monthly Workflow

### Step 1 — Employee Submits Advance Request

**Path:** HR → Employee Advance → New

When the employee selects their name:
- **Eligible Amount** is auto-calculated (e.g. 30% of Basic Pay from their Salary Structure Assignment)
- **Advance Amount** is auto-filled from Eligible Amount (editable)
- **Payroll Month** is auto-set to the first day of the current month (editable)

The system enforces:
- Only one advance per employee per month
- Advance amount cannot exceed Eligible Amount
- Employee must be active

Save and submit (or route through approval if **Salary Advance Require Approval** is enabled).

### Step 2 — Generate Disbursement Report

**Path:** HR → Reports → Employee Advance Disbursement

| Filter | Value |
|---|---|
| Payroll Month | First day of the month (e.g. 2026-04-01) |
| Company | Your company |
| Reference | Auto-generated as `HMC SALARY ADVANCE APRIL 2026` — edit if needed |

The report shows:

| Column | Source |
|---|---|
| Employee Name | Employee Advance |
| Reference | Auto-generated label |
| Bank Code | Employee → Bank Name field |
| Bank Account | Employee → Bank A/C No. field |
| Amount | Advance Amount |
| **Total** | Sum row at bottom |

Export to Excel/CSV and send to the bank for bulk transfer.

### Step 3 — Mark Advances as Paid (Bulk)

After the bank confirms transfers:

**Path:** HR → Employee Advance (List View)

1. Filter by **Status = Unpaid** and **Payroll Month = current month**
2. Select all relevant rows using the checkboxes
3. Click **Actions → Mark as Paid**
4. In the dialog, select **Mode of Payment** and optionally a **Bank Account**
5. Click **Create Payment Entry**

The system:
- Creates and submits a single Payment Entry with one reference row per advance
- Each advance status flips to **Paid**
- An **Additional Salary** (Deduction: Salary Advance Recovery) is automatically created and submitted for each advance, dated to the advance's Payroll Month

### Step 4 — Verify Deduction Entries

**Path:** Payroll → Additional Salary

Filter by:
- Type: Deduction
- Salary Component: Salary Advance Recovery
- Payroll Date: current month

Confirm one entry exists per paid advance. These will be picked up automatically when Salary Slips are generated in Step 3 of the payroll workflow.

### Step 5 — Advance Appears on Salary Slip

When the Salary Slip is generated for the month, the **Salary Advance Recovery** deduction line appears automatically. The Payroll Entry JE credits the Employee Advance account, closing the advance balance.

---

## 9. Shift Management

### 9.1 Swap Shift

**Path:** HR → Swap Shift → New

Used to swap employees between two shifts for a date range.

| Field | Notes |
|---|---|
| Shift A | First shift type |
| From Date / To Date | Date range to **fetch** employees from (who is currently assigned) |
| Shift B | Second shift type |
| New Assignment From Date / To Date | Date range for the **new** assignments (can differ from fetch window) |
| Respect Stay | If checked, employees with **Stay In Current Shift** ticked will not be swapped — but will still receive a new assignment in their original shift for the new date range |
| Cancel Existing | If checked, existing overlapping assignments are cancelled before new ones are created |

Click **Preview** to see which employees will be swapped and which will stay, before submitting.

On Submit, the system:
- Creates new Shift Assignments for swapped employees in the new date range
- Creates new Shift Assignments for stayed employees in their **original** shift for the new date range (so they are not left unscheduled)

### 9.2 Stay In Current Shift Flag

Set on the **Employee** record. Employees with this flag will never be moved out of their shift during a swap operation (when Respect Stay is enabled). The flag is also shown in the Shift A / Shift B child tables on the Swap Shift form and can be overridden per-swap.

---

## 10. Suggested Improvements

| Area | Suggestion | Benefit |
|---|---|---|
| Employee Sales | Build an internal Sales form that auto-creates Additional Salary on save | Eliminates manual entry, creates item-level audit trail |
| Statutory Reports | Add PAYE, NSSF, WCF, SDL summary reports | Simplifies monthly statutory filing |
| Bank Code | Add a dedicated `Bank Code` field on Employee (separate from Bank Name) | Ensures disbursement report always has the correct numeric code |
| Advance Approval | Configure a Workflow on Employee Advance for multi-level approval (Employee → HR → Finance) | Enforces authorisation before disbursement |
| Payroll Checklist | Add a monthly payroll checklist doctype | Ensures no step is missed each month |
| SDL / WCF JE | Add a button on Payroll Entry to auto-post SDL and WCF employer JEs | Reduces manual journal entries |
| Employee Sales Reconciliation | Monthly report showing goods sold vs. deductions processed | Confirms all sales are recovered |
