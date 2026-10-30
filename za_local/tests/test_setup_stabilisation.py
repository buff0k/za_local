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

class TestNavigationStabilisation(UnitTestCase):
	# test_workspace_paths_exclude_payroll_without_hrms,
	# test_sidebar_module_mapping_uses_area_modules_for_boot_permissions,
	# test_desktop_layout_repair_merges_missing_child_icons and
	# test_desktop_layout_repair_removes_payroll_without_hrms deleted along
	# with the legacy Workspace Sidebar/Desktop Icon navigation machinery
	# they tested (_sa_workspace_definition_paths, _za_sidebar_workspace_
	# names, _sidebar_module_for_workspace, _repair_za_local_desktop_
	# layouts, _sanitize_workspace_navigation, etc.) - confirmed unreachable
	# since the one thing that used to call into it (the ZA Local Setup
	# wizard's run_za_local_setup) was repointed to ir weeks earlier. This
	# is exactly the deprecated nav mechanism the migration plan said to
	# delete outright, not port, once nothing real depends on it any more.

	def test_app_permission_requires_system_manager_system_user(self):
		from za_local.api import check_app_permission

		with (
			patch("za_local.api.frappe.session", frappe._dict(user="manager@example.com")),
			patch("za_local.api.frappe.db.get_value", return_value="System User"),
			patch("za_local.api.frappe.get_roles", return_value=["System Manager"]),
		):
			self.assertTrue(check_app_permission())

		with (
			patch("za_local.api.frappe.session", frappe._dict(user="accounts@example.com")),
			patch("za_local.api.frappe.db.get_value", return_value="System User"),
			patch("za_local.api.frappe.get_roles", return_value=["Accounts Manager"]),
		):
			self.assertFalse(check_app_permission())

		with (
			patch("za_local.api.frappe.session", frappe._dict(user="portal@example.com")),
			patch("za_local.api.frappe.db.get_value", return_value="Website User"),
			patch("za_local.api.frappe.get_roles", return_value=["System Manager"]),
		):
			self.assertFalse(check_app_permission())

	# test_workspace_navigation_removes_hrms_only_and_missing_targets,
	# test_manual_setup_rejects_hrms_options_without_hrms,
	# test_manual_setup_allows_hrms_options_with_hrms and
	# test_manual_setup_feedback_identifies_erpnext_only_mode deleted along
	# with _sanitize_workspace_navigation/validate_za_local_setup_hrms_
	# options/build_za_local_setup_feedback - same dead setup-wizard/nav
	# machinery as above, confirmed zero remaining callers.

# TestConnectionLinkStabilisation deleted along with custom_fields.py's
# _get_doctype_link_records/get_za_local_custom_records - "custom_records"
# was never a real Frappe/ERPNext/HRMS hook, so this was never actually
# consumed. Rebuilt properly (and tested as live, working migrate
# behaviour rather than a mocked unit test) in ir.setup.doctype_connections,
# as part of absorbing za_local into ir.
