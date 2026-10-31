from unittest.mock import patch

import frappe

from za_local.tests.compat import UnitTestCase


class TestHRMSDetection(UnitTestCase):
	def test_hrms_detection_is_site_scoped_when_app_code_exists_elsewhere(self):
		from za_local.utils.hrms_detection import is_hrms_installed

		with (
			patch("za_local.utils.hrms_detection.frappe.get_installed_apps", return_value=["frappe", "erpnext"]),
			patch("za_local.utils.hrms_detection.frappe.db.table_exists", return_value=False),
		):
			self.assertFalse(is_hrms_installed())

	def test_hrms_detection_accepts_only_installed_site_app(self):
		from za_local.utils.hrms_detection import is_hrms_installed

		with patch(
			"za_local.utils.hrms_detection.frappe.get_installed_apps",
			return_value=["frappe", "erpnext", "hrms"],
		):
			self.assertTrue(is_hrms_installed())


class TestSetupWizardStabilisation(UnitTestCase):
	# get_sa_localization_stages/setup_za_localization moved to
	# ir.ir_setup.setup_wizard as part of absorbing za_local into ir - see
	# ir's own test suite for coverage of that stage.

	def test_known_setup_warning_filter_is_flag_gated(self):
		from za_local.sa_setup.install import (
			enable_known_setup_warning_filter,
			stop_setup_warning_suppression,
			suppress_known_setup_warnings,
		)

		delivered = []

		def collect_msgprint(msg=None, *args, **kwargs):
			delivered.append(msg)

		stop_setup_warning_suppression()
		with patch.object(frappe, "msgprint", new=collect_msgprint):
			enable_known_setup_warning_filter()

			frappe.msgprint("Accounts not set for Salary Component Basic")
			with suppress_known_setup_warnings():
				frappe.msgprint("Accounts not set for Salary Component Income Tax")
				frappe.msgprint(
					"Rule for this doctype, role, permlevel and if-owner combination already exists."
				)
				frappe.msgprint(
					"User user@example.com: Removed Employee Self Service role as there is no mapped employee."
				)
				frappe.msgprint("Keep this warning")
			frappe.msgprint("Rule for this doctype, role, permlevel and if-owner combination already exists.")

		self.assertEqual(
			delivered,
			[
				"Accounts not set for Salary Component Basic",
				"Keep this warning",
				"Rule for this doctype, role, permlevel and if-owner combination already exists.",
			],
		)

	# test_salary_component_account_defaults_cover_hrms_and_za_components,
	# test_salary_component_seed_derives_required_component_field_from_name
	# and test_salary_component_setup_skips_without_hrms deleted along with
	# DEFAULT_SALARY_COMPONENT_ACCOUNT_NAMES/create_salary_component_if_not_
	# exists/setup_default_salary_components - confirmed zero callers once
	# the setup-wizard engine they belonged to (unreachable since
	# ZALocalSetup.start_setup() was repointed to ir weeks earlier) was
	# deleted, as part of absorbing za_local into ir.

# TestNavigationStabilisation deleted entirely - every test it held
# (workspace/sidebar/desktop-icon machinery, manual setup HRMS-gating,
# and the Desk-tile permission check) was deleted along with the
# functions it tested, as part of absorbing za_local into ir / Phase 5
# retirement. See ir's own test suite for the equivalent live coverage
# (ir.setup.doctype_connections, ir.ir_setup.setup_wizard, etc.).

# TestConnectionLinkStabilisation deleted along with custom_fields.py's
# _get_doctype_link_records/get_za_local_custom_records - "custom_records"
# was never a real Frappe/ERPNext/HRMS hook, so this was never actually
# consumed. Rebuilt properly (and tested as live, working migrate
# behaviour rather than a mocked unit test) in ir.setup.doctype_connections,
# as part of absorbing za_local into ir.
