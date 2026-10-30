"""
Installation and Setup Functions for ZA Local

This module handles installation, uninstallation, and migration setup
for the South African localization app.
"""

import re
from contextlib import contextmanager

import frappe
from frappe.utils.fixtures import import_fixtures

from za_local.utils.hrms_detection import is_hrms_installed

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
	# row migration, GL account repair, and statutory salary component
	# formula application all moved to ir's own after_migrate
	# (ir.ir_setup.install.*, ir.ir_vat.setup.*, ir/fixtures/
	# salary_component.json) - no longer called from here.
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

# apply_statutory_formulas/_update_statutory_formulas_in_child_tables
# (superseded by ir/fixtures/salary_component.json's static formula values),
# _merge_tax_rebates_from_file (confirmed zero callers), and
# load_data_from_json/insert_record (their only caller, test_data_loading.py,
# was retired along with the sa_setup/data/*.json files it loaded, now that
# the equivalent master data lives in ir's own fixtures) were all removed as
# part of absorbing za_local into ir.
