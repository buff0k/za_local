"""
South African Localization: Custom Fields and DocType Links

The Custom Field fixtures this module used to define (Section 1/2) have
all been absorbed into ir's own fixtures (ir/ir/fixtures/custom_field.json)
as part of absorbing za_local into ir - ir now independently creates/
maintains every za_* custom field on every migrate via the standard
fixture mechanism. get_custom_field_fixtures() stays as an intentionally
empty stub: za_local/sa_setup/uninstall.py's remove_custom_fields() reads
it dynamically at uninstall time, and this app must never delete fields
ir still needs.

Section 3 (DocType Links for Connections tab) is unrelated to custom
fields and is not yet absorbed - see the migration history.
"""

import frappe

from za_local.utils.hrms_detection import is_hrms_installed


def get_custom_field_fixtures():
	"""Intentionally empty - every za_* Custom Field is now ir's own fixture.

	Kept only so uninstall.py's remove_custom_fields() has a (now empty)
	list to read dynamically; it must never delete fields ir still needs.
	"""
	return []


# ---------------------------------------------------------------------------
# Section 3: Custom records (DocType Links for Connections tab)
# ---------------------------------------------------------------------------

_HRMS_ONLY_DOCTYPE_LINK_PARENTS = frozenset({"Employee", "Payroll Entry", "Expense Claim"})

_HRMS_ONLY_DOCTYPE_LINK_TARGETS = frozenset(
	{
		"Bursary Benefit",
		"Cellphone Benefit",
		"Company Car Benefit",
		"Employee Final Settlement",
		"Fringe Benefit",
		"Fuel Card Benefit",
		"Housing Benefit",
		"Leave Encashment SA",
		"Low Interest Loan Benefit",
		"Payroll Payment Batch",
		"Retirement Fund",
		"Tax Directive",
		"Travel Allowance Rate",
		"UIF U19 Declaration",
	}
)


def _doctype_exists_for_link(doctype: str) -> bool:
	try:
		return bool(frappe.db.exists("DocType", doctype))
	except Exception:
		# hooks.py imports this before a site connection in some commands. In
		# that context, avoid mutating the hook output based on unavailable DB.
		return True


def _get_doctype_link_records():
	"""DocType Link records; filtered by HRMS availability."""
	hrms_installed = is_hrms_installed()
	records = [
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Tax & Compliance",
			"link_doctype": "Tax Directive",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Fringe Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Company Car Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Housing Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Low Interest Loan Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Cellphone Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Fuel Card Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Benefits",
			"link_doctype": "Bursary Benefit",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "Leave Encashment SA",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Separation",
			"link_doctype": "Employee Final Settlement",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Tax & Compliance",
			"link_doctype": "UIF U19 Declaration",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Employee",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Training & Development",
			"link_doctype": "Skills Development Record",
			"link_fieldname": "employee",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Company",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "Retirement Fund",
			"link_fieldname": "company",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Company",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "Travel Allowance Rate",
			"link_fieldname": "company",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Company",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Training & Development",
			"link_doctype": "Workplace Skills Plan",
			"link_fieldname": "company",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Company",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Training & Development",
			"link_doctype": "Annual Training Report",
			"link_fieldname": "company",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Payroll Entry",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Payroll",
			"link_doctype": "Payroll Payment Batch",
			"link_fieldname": "payroll_entry",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Bargaining Council",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Sectoral Compliance",
			"link_doctype": "Industry Specific Contribution",
			"link_fieldname": "bargaining_council",
			"custom": 1,
		},
		{
			"doctype": "DocType Link",
			"parent": "Expense Claim",
			"parentfield": "links",
			"parenttype": "DocType",
			"group": "Travel",
			"link_doctype": "Business Trip",
			"link_fieldname": "expense_claim",
			"custom": 1,
		},
	]
	if not hrms_installed:
		records = [
			r for r in records
			if r.get("parent") not in _HRMS_ONLY_DOCTYPE_LINK_PARENTS
			and r.get("link_doctype") not in _HRMS_ONLY_DOCTYPE_LINK_TARGETS
		]
	records = [
		r for r in records
		if _doctype_exists_for_link(r.get("parent")) and _doctype_exists_for_link(r.get("link_doctype"))
	]
	return records


def get_za_local_custom_records():
	"""Used by hooks: returns list of DocType Link records (for Connections tab)."""
	return _get_doctype_link_records()
