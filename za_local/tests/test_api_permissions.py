import frappe

from za_local.tests.compat import UnitTestCase


class TestWhitelistedEndpointPermissions(UnitTestCase):
	def test_state_changing_endpoints_accept_post_only(self):
		from za_local.overrides.journal_entry import (
			force_delete_all_cancelled_payroll_journal_entries,
			force_delete_cancelled_payroll_journal_entry,
		)

		for method in (
			force_delete_all_cancelled_payroll_journal_entries,
			force_delete_cancelled_payroll_journal_entry,
		):
			self.assertEqual(
				frappe.allowed_http_methods_for_whitelisted_func[method],
				["POST"],
			)
