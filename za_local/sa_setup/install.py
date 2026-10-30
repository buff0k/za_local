"""
Installation and Setup Functions for ZA Local

This module handles installation, uninstallation, and migration setup
for the South African localization app.
"""

import re
from contextlib import contextmanager
from pathlib import Path

import frappe
from frappe import _
from frappe.utils.fixtures import import_fixtures

from za_local.utils.file_utils import read_app_json
from za_local.utils.hrms_detection import is_hrms_installed
from za_local.utils.statutory_rates import (
	get_sdl_rate,
	get_uif_employee_rate,
	get_uif_monthly_cap,
)

_SUPPRESS_SETUP_WARNING_FLAG = "za_local_suppress_setup_warnings"
_DUPLICATE_PERMISSION_MESSAGE = (
	"Rule for this doctype, role, permlevel and if-owner combination already exists."
)


def _normalise_message_text(message) -> str:
	if isinstance(message, dict):
		message = message.get("message") or message.get("msg") or message.get("title")

	text = str(message or "")
	text = re.sub(r"<[^>]*>", " ", text)
	return " ".join(text.split())

def _is_known_benign_setup_warning(message) -> bool:
	text = _normalise_message_text(message)

	if not text:
		return False

	return (
		text.startswith("Accounts not set for Salary Component ")
		or _DUPLICATE_PERMISSION_MESSAGE == text
		or (
			text.startswith("User ")
			and (
				"Removed Employee role as there is no mapped employee." in text
				or "Removed Employee Self Service role as there is no mapped employee." in text
			)
		)
	)

def _get_local_flags():
	if not getattr(frappe.local, "flags", None):
		frappe.local.flags = frappe._dict()
	return frappe.local.flags

def _setup_warning_suppression_enabled() -> bool:
	try:
		return bool(getattr(_get_local_flags(), _SUPPRESS_SETUP_WARNING_FLAG, False))
	except Exception:
		return False

def _set_setup_warning_suppression(enabled: bool) -> bool:
	flags = _get_local_flags()
	previous = bool(getattr(flags, _SUPPRESS_SETUP_WARNING_FLAG, False))
	setattr(flags, _SUPPRESS_SETUP_WARNING_FLAG, bool(enabled))
	return previous

def enable_known_setup_warning_filter() -> None:
	"""Install a flag-gated msgprint filter for noisy core/HRMS setup messages."""
	if getattr(frappe.msgprint, "_za_local_setup_warning_filter", False):
		return

	original_msgprint = frappe.msgprint

	def filtered_msgprint(msg=None, *args, **kwargs):
		if _setup_warning_suppression_enabled() and _is_known_benign_setup_warning(msg):
			return None
		return original_msgprint(msg, *args, **kwargs)

	filtered_msgprint._za_local_setup_warning_filter = True
	filtered_msgprint._za_local_original_msgprint = original_msgprint
	frappe.msgprint = filtered_msgprint

def start_setup_warning_suppression() -> None:
	enable_known_setup_warning_filter()
	_set_setup_warning_suppression(True)

def stop_setup_warning_suppression() -> None:
	_set_setup_warning_suppression(False)

@contextmanager
def suppress_known_setup_warnings():
	enable_known_setup_warning_filter()
	previous = _set_setup_warning_suppression(True)
	try:
		yield
	finally:
		_set_setup_warning_suppression(previous)

def sync_za_local():
	"""
	Unified sync: import standard fixtures.

	Custom field/property setter creation moved to ir's own fixtures
	(ir/ir/fixtures/custom_field.json, property_setter.json) as part of
	absorbing za_local into ir - ir now independently creates/maintains
	these on every migrate via the standard fixture mechanism, so this
	app no longer needs to. setup_custom_fields/ensure_vat_custom_fields/
	apply_property_setters still exist in their own modules, now unused
	here - kept only because za_local's own test suite still imports some
	of them directly.
	"""
	import_fixtures("za_local")

def after_install():
	with suppress_known_setup_warnings():
		return _after_install()

def _after_install():
	"""
	Run after app installation.

	Unified setup order (sync_za_local): fixtures → custom fields + property setters → custom records.

	Note: All one-time setup/backfill tasks that used to run here unconditionally
	on every install/migrate (invalid DocType Link cleanup, legacy IRP5 field
	migration, ETI Payroll Settings default, Accounts Settings for VAT, and the
	now-empty legacy module/workspace/navigation housekeeping) have moved to
	ir's own patches.txt (ir.patches.cleanup_invalid_doctype_links,
	migrate_irp5_legacy_source_fields, ensure_eti_payroll_settings_defaults,
	set_accounts_settings_for_za_vat) or been dropped outright as part of
	absorbing za_local into ir - see the migration history for details.
	"""
	sync_za_local()  # fixtures only - custom fields/property setters are now ir's
	# Company-scoped tax config, rate-pack/travel-rate seeding, VAT account
	# row migration, and GL account repair all moved to ir's own
	# after_migrate (ir.ir_setup.install.*, ir.ir_vat.setup.*) - no longer
	# called from here.
	apply_statutory_formulas()
	print("\n" + "=" * 80)
	print("South African Localization installed successfully!")
	print("=" * 80)
	print("\nNext steps:")
	print("1. Configure Company SA registration numbers")
	if is_hrms_installed():
		print("2. Set up Payroll Settings with SA statutory components")
		print("3. Configure ETI Slabs and Tax Rebates")
		print("4. Set up COIDA and VAT settings if applicable")
		print("5. Configure Business Trip Settings for travel allowances")
	else:
		print("2. Configure VAT, COIDA, and Business Trip Settings if applicable")
		print("3. Install HRMS only if payroll and employee compliance are required")
	print("=" * 80 + "\n")

def after_migrate():
	with suppress_known_setup_warnings():
		return _after_migrate()

def _after_migrate():
	"""
	Run after migrations.

	Same sync order as install (sync_za_local): fixtures → custom fields + property setters → custom records.

	See _after_install()'s docstring for where the one-time setup/backfill
	tasks that used to run here unconditionally (invalid DocType Link
	cleanup, legacy IRP5 field migration, ETI Payroll Settings default,
	Accounts Settings for VAT, legacy module/workspace/navigation
	housekeeping) ended up.
	"""
	sync_za_local()  # fixtures only - custom fields/property setters are now ir's

def before_migrate():
	"""
	Run before schema sync during bench migrate.
	- Rename module "COIDA" to "SA COIDA" in DB so Frappe loads za_local.sa_coida (not za_local.coida).
	- Clear app_modules cache so module list is rebuilt from modules.txt.
	"""
	if not frappe.db:
		return
	try:
		# Update any DocType or Report that still has module "COIDA" to "SA COIDA"
		for doctype in ("DocType", "Report"):
			if frappe.db.table_exists(doctype):
				frappe.db.set_value(
					doctype,
					{"module": "COIDA"},
					"module",
					"SA COIDA",
					update_modified=False,
				)
		# Ensure cache is cleared so app_modules is rebuilt from modules.txt (SA COIDA not COIDA)
		frappe.cache().delete_value("app_modules")
		frappe.cache().delete_value("installed_app_modules")
	except Exception as e:
		frappe.log_error(f"before_migrate (za_local): {e}", "ZA Local before_migrate")
		# Don't fail migrate
		pass

def apply_statutory_formulas():
	"""Ensure statutory Salary Components and Company Contribution rows carry correct formulas.
	- UIF Employee & Employer: 1% of gross pay capped at 177.12
	- SDL: 1% of gross pay
	Also enable Amount based on Formula on these components and child rows.
	"""
	print("Applying statutory formulas to salary components and company contribution rows...")

	if not frappe.db.table_exists("Salary Component"):
		print("  ⊙ Skipping statutory formula updates (Salary Component DocType not available)")
		return

	from za_local.utils.statutory_rates import find_rate_pack

	if not find_rate_pack():
		frappe.log_error(
			title="ZA Local statutory formulas not refreshed",
			message=(
				"No statutory rate pack exists for the current tax year. "
				"Existing Salary Component formulas were preserved."
			),
		)
		print("  ! No current statutory rate pack; existing formulas preserved")
		return

	uif_monthly_cap = get_uif_monthly_cap()
	uif_employee_rate = get_uif_employee_rate()
	sdl_rate = get_sdl_rate()
	uif_cap_amount = uif_monthly_cap * uif_employee_rate
	uif_formula = (
		f"(gross_pay * {uif_employee_rate}) if (gross_pay * {uif_employee_rate}) <= "
		f"{uif_cap_amount} else {uif_cap_amount}"
	)
	sdl_formula = f"gross_pay * {sdl_rate}"

	component_updates = {
		"UIF Employee Contribution": {
			"amount_based_on_formula": 1,
			"formula": uif_formula,
		},
		"UIF Employer Contribution": {
			"amount_based_on_formula": 1,
			"formula": uif_formula,
			"type": "Company Contribution",
		},
		"SDL Contribution": {
			"amount_based_on_formula": 1,
			"formula": sdl_formula,
			"type": "Company Contribution",
		},
	}

	for canonical_name, fields in component_updates.items():
		if frappe.db.exists("Salary Component", canonical_name):
			try:
				frappe.db.set_value("Salary Component", canonical_name, fields)
			except Exception as e:
				print(f"  ! Could not update Salary Component {canonical_name}: {e}")

	# Update draft Salary Structure rows only. Salary Slip child rows are statutory
	# snapshots and must never be rewritten by install or migrate.
	_update_statutory_formulas_in_child_tables(component_updates)

	print("✓ Statutory formulas applied")

def _update_statutory_formulas_in_child_tables(component_updates: dict[str, dict]):
	if not frappe.db.table_exists("Company Contribution"):
		print("  ⊙ Skipping Company Contribution child row updates (DocType not available)")
	else:
		for name, fields in component_updates.items():
			if name not in ("UIF Employer Contribution", "SDL Contribution"):
				continue
			frappe.db.sql(
				"""
				UPDATE `tabCompany Contribution`
				SET amount_based_on_formula = 1, formula = %(formula)s
				WHERE salary_component = %(name)s
					AND parenttype = 'Salary Structure'
					AND docstatus = 0
				""",
				{"name": name, "formula": fields["formula"]},
			)

def _merge_tax_rebates_from_file(file_path: Path) -> None:
	"""Merge a tax_rebates_*.json fixture into the Single DocType without discarding other years."""
	try:
		data = read_app_json(file_path)
	except Exception as e:
		print(f"  ! Could not read {file_path.name}: {e}")
		return

	if not isinstance(data, dict) or data.get("doctype") != "Tax Rebates and Medical Tax Credit":
		# Not in expected single-doc format
		return

	payroll_periods_rebates = data.get("tax_rebates_rate") or []
	payroll_periods_medical = data.get("medical_tax_credit") or []

	if not payroll_periods_rebates and not payroll_periods_medical:
		return

	doc = frappe.get_single("Tax Rebates and Medical Tax Credit")

	# Helper to upsert rows by payroll_period
	def upsert_child(child_table_name: str, new_rows: list[dict]):
		if not new_rows:
			return
		child_rows = list(doc.get(child_table_name) or [])
		index = {row.get("payroll_period"): row for row in child_rows}

		for nr in new_rows:
			pp = nr.get("payroll_period")
			if not pp:
				continue
			if pp in index:
				row = index[pp]
				for field, value in nr.items():
					if field != "name":
						row.set(field, value)
			else:
				child_rows.append(nr)

		doc.set(child_table_name, child_rows)

	upsert_child("tax_rebates_rate", payroll_periods_rebates)
	upsert_child("medical_tax_credit", payroll_periods_medical)

	doc.flags.ignore_permissions = True
	doc.save()

def load_data_from_json(file_path):
	"""
	Load data from JSON file and insert into database.

	Args:
		file_path: Path to JSON file
	"""
	data = read_app_json(file_path)

	# Handle different JSON formats
	if isinstance(data, dict):
		# Check if it's a single record (has "doctype" key)
		if "doctype" in data:
			# Single record
			insert_record(data)
		else:
			# Dict with DocType as key
			for doctype, records in data.items():
				for record in records:
					# Add doctype to record if not present
					if "doctype" not in record:
						record["doctype"] = doctype
					insert_record(record)
	elif isinstance(data, list):
		# List of records
		for record in data:
			insert_record(record)

def insert_record(record):
	"""
	Insert a single record, skip if exists.
	Handles both regular DocTypes and Single DocTypes.
	Also handles child tables (like Holiday List with holidays).

	Args:
		record: Dict with doctype and field values
	"""
	doctype = record.get("doctype")

	# Determine the name field - different DocTypes use different name fields
	# Standard: "name"
	# Salary Component: "salary_component"
	# Holiday List: "holiday_list_name"
	name = record.get("name") or record.get("salary_component") or record.get("holiday_list_name")

	# Check if it's a Single DocType
	meta = frappe.get_meta(doctype)
	is_single = meta.issingle

	# Handle company field - set to first company if empty
	if "company" in record and not record.get("company"):
		companies = frappe.get_all("Company", limit=1)
		if companies:
			record["company"] = companies[0].name

	try:
		# Suppress validation warnings during setup (e.g., "Accounts not set")
		# These are expected and users will configure accounts later
		_message_log = frappe.local.message_log
		frappe.local.message_log = []

		if is_single:
			# For Single DocTypes, always update (don't check exists)
			doc = frappe.get_single(doctype)
			# Update fields from record
			for key, value in record.items():
				if key != "doctype":
					doc.set(key, value)
			doc.save(ignore_permissions=True)
			print(f"  ✓ Updated Single DocType: {doctype}")
		else:
			# For regular DocTypes, check if exists
			# Special handling for Holiday List - check by holiday_list_name
			if doctype == "Holiday List" and name:
				exists = frappe.db.exists("Holiday List", name)
			elif name:
				exists = frappe.db.exists(doctype, name)
			else:
				# If no name field, check if we should create anyway
				exists = False

			if not exists:
				# Create the document
				# frappe.get_doc() automatically handles child tables when you pass them in the record dict
				# For Holiday List, the "holidays" array will be automatically converted to child table rows
				# Each item in the "holidays" array becomes a row in the Holiday child table
				doc = frappe.get_doc(record)
				if doctype == "Salary Component":
					with suppress_known_setup_warnings():
						doc.insert(ignore_permissions=True, ignore_mandatory=True)
				else:
					doc.insert(ignore_permissions=True, ignore_mandatory=True)

				created_name = name or doc.name
				print(f"  ✓ Created {doctype}: {created_name}")

				# Auto-submit submittable doctypes (e.g. Income Tax Slab) so they are ready to use
				try:
					if meta.is_submittable and hasattr(doc, "submit") and doc.docstatus == 0:
						doc.submit()
						print(f"    → Submitted {doctype}: {created_name}")
				except Exception as submit_err:
					print(f"    ! Warning: Could not submit {doctype} {created_name}: {submit_err}")

				# For Holiday List, verify holidays were saved
				if doctype == "Holiday List":
					# Reload document to get latest state from database
					doc.reload()
					holiday_count = len(doc.get("holidays", [])) if hasattr(doc, "get") else 0
					if holiday_count > 0:
						print(f"    → Added {holiday_count} holidays to '{created_name}'")
					else:
						# If no holidays in doc, check the original record
						holiday_count_from_record = len(record.get("holidays", []))
						if holiday_count_from_record > 0:
							print(
								f"    ! Warning: {holiday_count_from_record} holidays in record but not saved."
							)
							print(
								"    ! This may indicate a child table field name mismatch or HRMS not fully installed."
							)
						else:
							print("    ! Warning: No holidays found in record")
			else:
				print(f"  ⊙ Skipped {doctype}: {name} (already exists)")

		# Restore message log
		frappe.local.message_log = _message_log
	except Exception as e:
		# Restore message log even on error
		frappe.local.message_log = _message_log
		print(f"  ✗ Error with {doctype} {name or 'unknown'}: {e}")

		# For Holiday List, provide more specific error information
		if doctype == "Holiday List":
			print("    ! Holiday List creation failed. Check:")
			print("      - Is HRMS installed? (Holiday List is an HRMS DocType)")
			print("      - Does the record have 'holidays' child table array?")
			print("      - Are holiday items properly formatted with 'holiday_date' and 'description'?")

		import traceback

		traceback.print_exc()
