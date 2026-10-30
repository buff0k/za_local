"""
Chart of Accounts Setup for South Africa

This module handles loading the South African Chart of Accounts
for companies during setup and provides integration helpers
for the ERPNext setup wizard.
"""

import frappe
from frappe import _

from za_local.utils.file_utils import read_app_json, resolve_app_path


def load_sa_chart_of_accounts(company):
	"""
	Augment an existing company Chart of Accounts with South African accounts.

	ERPNext creates the base chart during company setup. ZA Local does not
	create or replace that chart here; it only adds ZA-specific statutory
	accounts after the base accounts exist.

	Args:
		company: Company name for which to load the chart
	"""
	if not company:
		frappe.log_error(
			"Company is required to load Chart of Accounts",
			"ZA Local Chart of Accounts",
		)
		return False
	if not frappe.db.exists("Company", company):
		frappe.log_error(
			f"Company '{company}' does not exist",
			"ZA Local Chart of Accounts",
		)
		return False

	try:
		# Company should already have a base chart created by ERPNext's setup wizard.
		# We only *augment* that chart with SA-specific tax accounts.
		existing_accounts = frappe.db.count("Account", {"company": company})
		if existing_accounts == 0:
			# If no accounts exist yet, don't try to build an entire chart here.
			# Let ERPNext's own setup logic handle the base chart, then ZA can be
			# applied later via a separate action.
			frappe.log_error(
				f"No accounts found for company {company} when attempting to load ZA Chart of Accounts. "
				"Skipping ZA chart augmentation.",
				"ZA Local Chart of Accounts",
			)
			return False

		# Add SA-specific tax accounts into the existing chart.
		# We derive the insertion points (Current Assets / Current Liabilities
		# and Tax Assets / Tax Liabilities) from the live chart so this works
		# with any standard template (Standard, Standard with Numbers, etc.).
		_add_sa_tax_accounts(company)
		return True

	except Exception as e:
		frappe.log_error(
			f"Error loading Chart of Accounts for {company}: {e!s}\n{frappe.get_traceback()}",
			"ZA Local Chart of Accounts",
		)
		# Do not re-raise: allow setup wizard to complete; user can add SA accounts later if needed
		return False


def _get_root_account(company, root_type):
	"""Find the existing root account by root_type (works with any chart naming)."""
	name = frappe.db.get_value(
		"Account",
		{"company": company, "root_type": root_type, "parent_account": ("in", ("", None))},
		"name",
	)
	return frappe.get_doc("Account", name) if name else None


def _get_account_by_name_and_parent(company, account_name, parent_account_name):
	"""Find an account by company, account_name, and parent (by name)."""
	parent = frappe.db.get_value(
		"Account",
		{"company": company, "account_name": parent_account_name},
		"name",
	)
	if not parent:
		return None
	name = frappe.db.get_value(
		"Account",
		{"company": company, "account_name": account_name, "parent_account": parent},
		"name",
	)
	return frappe.get_doc("Account", name) if name else None


def _get_child_account_under(company, parent_doc, preferred_names):
	"""
	Find a direct child account of parent_doc whose account_name is in preferred_names
	or starts with the first preferred name (handles translated/suffixed names).
	"""
	children = frappe.get_all(
		"Account",
		filters={"company": company, "parent_account": parent_doc.name},
		fields=["name", "account_name"],
	)
	if not children:
		return None
	preferred = list(preferred_names)
	for c in children:
		if c.account_name in preferred:
			return frappe.get_doc("Account", c.name)
		if preferred and c.account_name and c.account_name.startswith(preferred[0]):
			return frappe.get_doc("Account", c.name)
	return None


def _get_or_create_tax_group_under(company, parent_account_doc, preferred_names, account_type="Tax"):
	"""Find existing tax group under parent (e.g. Duties and Taxes / Tax Liabilities) or create one."""
	for preferred_name in preferred_names:
		existing = frappe.db.get_value(
			"Account",
			{
				"company": company,
				"account_name": preferred_name,
				"parent_account": parent_account_doc.name,
				"is_group": 1,
			},
			"name",
		)
		if existing:
			return frappe.get_doc("Account", existing)
	# Create first preferred name
	return _get_or_create_account(
		company, preferred_names[0], account_type,
		parent=parent_account_doc.name, is_group=1
	)


def _add_sa_tax_accounts(company):
	"""
	Add only SA-specific tax accounts to an existing chart.

	This function does **not** replace the chart. It assumes a standard ERPNext
	chart (e.g. Application of Funds / Source of Funds) already exists for the
	company and injects ZA tax ledgers in the expected groups:
	- Current Assets > Tax Assets
	- Current Liabilities > Tax Liabilities or Duties and Taxes
	"""
	# Find existing roots by root_type (don't assume "Liabilities" / "Assets" names)
	liabilities_root = _get_root_account(company, "Liability")
	assets_root = _get_root_account(company, "Asset")
	if not liabilities_root or not assets_root:
		raise ValueError(
			f"Could not find Chart of Accounts roots for company {company} "
			f"(Liability root={bool(liabilities_root)}, Asset root={bool(assets_root)})"
		)

	# Find Current Liabilities / Current Assets: try by parent doc first (resilient to naming), then by name+parent
	current_liabilities = _get_child_account_under(
		company, liabilities_root, ["Current Liabilities"]
	)
	if not current_liabilities:
		current_liabilities = _get_account_by_name_and_parent(
			company, "Current Liabilities", liabilities_root.account_name
		)
	current_assets = _get_child_account_under(
		company, assets_root, ["Current Assets"]
	)
	if not current_assets:
		current_assets = _get_account_by_name_and_parent(
			company, "Current Assets", assets_root.account_name
		)
	if not current_liabilities or not current_assets:
		raise ValueError(
			f"Could not find Current Liabilities or Current Assets for company {company}"
		)

	# Use existing Tax Liabilities / Duties and Taxes group or create Tax Liabilities
	tax_liabilities = _get_or_create_tax_group_under(
		company, current_liabilities, ["Tax Liabilities", "Duties and Taxes"]
	)
	tax_assets = _get_or_create_tax_group_under(
		company, current_assets, ["Tax Assets"]
	)

	# Add SA tax ledgers under the groups.
	# We keep the set small and explicit so behaviour is predictable and
	# independent of the JSON template structure.
	liability_tax_accounts = [
		"VAT Collected - Sales",
		"VAT Payable - SARS",
		"PAYE Payable - SARS",
		"UIF Employee Contribution",
		"UIF Employer Contribution",
		"SDL Payable - SARS",
		"COIDA Payable",
	]
	for account_name in liability_tax_accounts:
		_get_or_create_account(
			company,
			account_name,
			"Tax",
			parent=tax_liabilities.name,
			is_group=0,
		)

	asset_tax_accounts = [
		"VAT Paid - Purchases",
	]
	for account_name in asset_tax_accounts:
		_get_or_create_account(
			company,
			account_name,
			"Tax",
			parent=tax_assets.name,
			is_group=0,
		)

	expense_root = _get_root_account(company, "Expense")
	if not expense_root:
		return

	indirect_expenses = _get_child_account_under(
		company, expense_root, ["Indirect Expenses", "Expenses"]
	) or expense_root

	employer_contribution_group = _get_or_create_account(
		company,
		"Employer Payroll Contributions",
		"Expense Account",
		parent=indirect_expenses.name,
		is_group=1,
	)

	for account_name in (
		"Salaries and Wages",
		"COIDA Expense",
		"UIF Employer Expense",
		"SDL Expense",
		"Pension Fund Employer Expense",
		"Medical Aid Employer Expense",
	):
		_get_or_create_account(
			company,
			account_name,
			"Expense Account",
			parent=employer_contribution_group.name,
			is_group=0,
		)


def _get_or_create_account(company, account_name, account_type, parent=None, is_group=0, root_type=None):
	"""
	Get existing account or create it if it doesn't exist.

	Args:
		company: Company name
		account_name: Account name
		account_type: Account type
		parent: Parent account name
		is_group: Whether account is a group
		root_type: Root type (for root accounts only)

	Returns:
		Account document
	"""
	# Try to find existing account
	existing = frappe.db.get_value(
		"Account",
		{"company": company, "account_name": account_name},
		"name"
	)

	if existing:
		return frappe.get_doc("Account", existing)

	# Create new account
	account_doc = frappe.get_doc({
		"doctype": "Account",
		"company": company,
		"account_name": account_name,
		"account_type": account_type,
		"parent_account": parent or "",
		"is_group": is_group,
		"root_type": root_type,
	})

	if root_type:
		account_doc.flags.ignore_mandatory = True

	account_doc.flags.ignore_permissions = True
	account_doc.insert()

	return account_doc

