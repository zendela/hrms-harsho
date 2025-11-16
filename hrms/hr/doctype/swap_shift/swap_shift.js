frappe.ui.form.on('Swap Shift', {
  setup(frm) {
    // Disallow same shift in both fields
    frm.set_query('shift_b', () => {
      if (frm.doc.shift_a) return { filters: [['Shift Type', 'name', '!=', frm.doc.shift_a]] };
      return {};
    });
    frm.set_query('shift_a', () => {
      if (frm.doc.shift_b) return { filters: [['Shift Type', 'name', '!=', frm.doc.shift_b]] };
      return {};
    });
  },

  refresh(frm) {
    if (frm.is_new()) frm.set_value('status', frm.doc.status || 'Draft');

    // Load Employees (merge, don't duplicate)
    frm.add_custom_button(__('Load Employees'), () => {
      if (!ensure_fetch_window(frm)) return;
      fetch_and_merge(frm, true);
    });

    // Preview uses server logic (respects settings + child stay flags)
    frm.add_custom_button(__('Preview Swap'), () => {
      const data = r.message || {};
const allowMulti = !!data.allow_multiple_assignments;
const overlapCount = data.overlaps_in_creation_window || 0;

const note = allowMulti
  ? ''
  : (overlapCount > 0
      ? __('<br><span class="text-danger">HR Settings disallow multiple assignments per day. {0} overlap(s) detected in creation window {1} → {2}. Turn ON "Cancel Existing" or change dates.</span>',
            [overlapCount,
             frappe.datetime.str_to_user((data.creation_window || [])[0] || ''),
             frappe.datetime.str_to_user((data.creation_window || [])[1] || '')])
      : '');

frappe.msgprint({
  title: __('Preview'),
  message: __(
    'Fetch Window: {0} → {1}<br/>Create Window: {2} → {3}<br/>A → B: <b>{4}</b> | B → A: <b>{5}</b>{6}{7}',
    [
      frappe.datetime.str_to_user((data.fetch_window || [])[0] || ''),
      frappe.datetime.str_to_user((data.fetch_window || [])[1] || ''),
      frappe.datetime.str_to_user((data.creation_window || [])[0] || ''),
      frappe.datetime.str_to_user((data.creation_window || [])[1] || ''),
      (data.a_to_b || []).length, (data.b_to_a || []).length,
      (data.stayed && data.stayed.length) ? ('<br/>Stayed: ' + data.stayed.join(', ')) : '',
      note
    ]
  ),
  indicator: overlapCount > 0 && !allowMulti ? 'red' : 'blue'
});
    });

    // Execute by submitting
    if (frm.doc.docstatus === 0) {
      frm.add_custom_button(__('Execute Swap (Submit)'), () => {
        if (!ensure_fetch_window(frm)) return;
        if (!ensure_creation_window(frm)) return;
        frappe.confirm(__('Submit this document to execute the swap?'), () => frm.save('Submit'));
      }).addClass('btn-primary');
    }
  },

  // Clear tables on key changes (user will click Load Employees again)
  shift_a(frm) { clear_children(frm); frm.refresh_field('shift_b'); },
  shift_b(frm) { clear_children(frm); frm.refresh_field('shift_a'); },
  from_date(frm) { clear_children(frm); },
  to_date(frm) { clear_children(frm); },

  // Auto-fill ONLY if both child tables are empty (prevents re-loading on every save)
  after_save(frm) {
    if (
      frm.doc.docstatus === 0 &&
      ensure_fetch_window(frm) &&
      !(frm.doc.shift_a_table && frm.doc.shift_a_table.length) &&
      !(frm.doc.shift_b_table && frm.doc.shift_b_table.length)
    ) {
      fetch_and_merge(frm, false);
    }
  }
});

// ---- helpers ----

function ensure_fetch_window(frm) {
  if (!frm.doc.shift_a || !frm.doc.shift_b || !frm.doc.from_date || !frm.doc.to_date) {
    frappe.msgprint(__('Please fill Shift A, Shift B, From Date and To Date.'));
    return false;
  }
  if (frm.doc.shift_a === frm.doc.shift_b) {
    frappe.msgprint(__('Shift A and Shift B must be different.'));
    return false;
  }
  return true;
}

function ensure_creation_window(frm) {
  // New From/To optional; if one is set, both must be set and valid.
  if (frm.doc.new_from_date || frm.doc.new_to_date) {
    if (!frm.doc.new_from_date || !frm.doc.new_to_date) {
      frappe.msgprint(__('Please fill both New From Date and New To Date (or leave both empty).'));
      return false;
    }
    if (frappe.datetime.str_to_obj(frm.doc.new_to_date) < frappe.datetime.str_to_obj(frm.doc.new_from_date)) {
      frappe.msgprint(__('New To Date must be on or after New From Date.'));
      return false;
    }
  }
  return true;
}

function clear_children(frm) {
  if ((frm.doc.shift_a_table && frm.doc.shift_a_table.length) ||
      (frm.doc.shift_b_table && frm.doc.shift_b_table.length)) {
    frm.set_value('shift_a_table', []);
    frm.set_value('shift_b_table', []);
    frm.refresh_field('shift_a_table');
    frm.refresh_field('shift_b_table');
  }
}

/**
 * Merge loader: adds only employees not already present in the child tables.
 * Respects user's "Stay In Current Shift" ticks already set in rows.
 */
function fetch_and_merge(frm, toast) {
  frm.call('get_employees_for_window').then(r => {
    const msg = r.message || {};

    // Current sets to avoid duplicates
    const currentA = new Set((frm.doc.shift_a_table || []).map(x => x.employee));
    const currentB = new Set((frm.doc.shift_b_table || []).map(x => x.employee));

    // Add A rows if not present
    (msg.a_rows || []).forEach(row => {
      if (row.employee && !currentA.has(row.employee)) {
        const child = frm.add_child('shift_a_table');
        child.employee = row.employee;
        child.employee_name = row.employee_name;
        child.stay_in_current_shift = row.stay_in_current_shift ? 1 : 0; // user can edit later
        child.assigned_to = row.assigned_to;
        child.from_date = row.from_date;
        child.to_date = row.to_date;
        currentA.add(row.employee);
      }
    });

    // Add B rows if not present
    (msg.b_rows || []).forEach(row => {
      if (row.employee && !currentB.has(row.employee)) {
        const child = frm.add_child('shift_b_table');
        child.employee = row.employee;
        child.employee_name = row.employee_name;
        child.stay_in_current_shift = row.stay_in_current_shift ? 1 : 0;
        child.assigned_to = row.assigned_to;
        child.from_date = row.from_date;
        child.to_date = row.to_date;
        currentB.add(row.employee);
      }
    });

    frm.refresh_field('shift_a_table');
    frm.refresh_field('shift_b_table');

    if (toast) {
      const aCount = (frm.doc.shift_a_table || []).length;
      const bCount = (frm.doc.shift_b_table || []).length;
      frappe.msgprint({
        title: __('Employees Loaded'),
        message: __('A: {0} &nbsp; | &nbsp; B: {1}', [aCount, bCount]),
        indicator: 'blue'
      });
    }
  });
}
