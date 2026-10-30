from za_local.sa_setup.custom_fields import get_custom_field_fixtures
from za_local.tests.compat import UnitTestCase


class TestStatutorySetup(UnitTestCase):
	# test_public_holiday_fixtures_match_official_2025_to_2027_dates moved to
	# ir/ir/ir_setup/test_statutory_data.py - the holiday_list_*.json data
	# files moved to ir/ir/ir_setup/data/ as part of absorbing za_local into ir.

	def test_all_custom_field_fixture_names_are_unique(self):
		names = [row["name"] for row in get_custom_field_fixtures()]
		self.assertEqual(len(names), len(set(names)))

	def test_controller_consumed_compliance_fields_are_owned_by_app(self):
		fixtures = {(row["dt"], row["fieldname"]) for row in get_custom_field_fixtures()}
		required = {
			("Salary Component", "za_is_annual_bonus"),
			("Salary Slip", "za_paye_inclusion_adjustment"),
			("Payroll Settings", "za_official_interest_rate"),
			("Leave Type", "za_bcea_compliant"),
			("Leave Type", "za_applicable_gender"),
			("Leave Type", "za_medical_certificate_required_after"),
			("Employee Separation", "za_termination_type"),
			("Employee Separation", "za_notice_period_days"),
			("Employee Separation", "za_severance_pay"),
			("Employee Separation", "za_leave_payout"),
		}
		self.assertTrue(required.issubset(fixtures), required - fixtures)

	# test_future_rate_pack_probe_is_non_throwing and
	# test_future_statutory_calculation_still_fails_loudly moved to
	# ir/ir/tests/test_statutory_compliance.py along with
	# za_local.utils.statutory_rates itself, as part of absorbing za_local
	# into ir.

	# test_company_contribution_is_a_standard_app_doctype moved to
	# ir/ir/ir_payroll/doctype/company_contribution/test_company_contribution.py
	# - Company Contribution moved to ir_payroll as part of absorbing
	# za_local into ir.
