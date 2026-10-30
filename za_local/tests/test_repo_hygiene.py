import json
import re
import subprocess
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = APP_ROOT / "za_local"

# Files whose string literals point at shipped assets.
ASSET_REFERENCING_SOURCES = (
	PACKAGE_ROOT / "hooks.py",
)

# "public/js/foo.js" as used by doctype_js, and "/assets/za_local/js/foo.js"
# as used by app_include_js / app_include_css / logo URLs.
_RELATIVE_ASSET = re.compile(r"\"(public/(?:js|css|images)/[\w./-]+)\"")
_ASSETS_URL = re.compile(r"\"/assets/za_local/((?:js|css|images)/[\w./-]+)\"")


class TestRepositoryHygiene(unittest.TestCase):
	def test_client_scripts_do_not_use_synchronous_xhr(self):
		offenders = []
		for path in (PACKAGE_ROOT / "public" / "js").rglob("*.js"):
			if re.search(r"async\s*:\s*false", path.read_text()):
				offenders.append(path.relative_to(PACKAGE_ROOT).as_posix())
		self.assertFalse(offenders, msg=f"Synchronous XHR found in: {offenders}")

	# test_payroll_dialog_uses_dom_text_for_employee_values and
	# test_flexible_benefit_hiding_never_targets_shared_form_sections moved to
	# ir/ir/tests/test_repo_hygiene.py - the JS files they check moved to ir
	# as part of absorbing za_local into ir.

	def test_no_active_duplicate_print_format_jsons(self):
		seen = {}

		for path in PACKAGE_ROOT.rglob("*.json"):
			path_str = path.as_posix()
			if "/print_format/" not in path_str or "/legacy_standard_docs/" in path_str:
				continue
			seen.setdefault(path.stem, []).append(path_str)

		duplicates = {
			name: paths
			for name, paths in seen.items()
			if len(paths) > 1
		}
		self.assertFalse(duplicates, msg=f"Duplicate active print formats found: {duplicates}")

	def test_hook_asset_paths_exist(self):
		"""A hook pointing at a missing asset is a silent no-op: frappe.read_file
		returns None and the script is simply never loaded."""
		missing = []

		for source in ASSET_REFERENCING_SOURCES:
			text = source.read_text()
			referenced = {PACKAGE_ROOT / match for match in _RELATIVE_ASSET.findall(text)}
			referenced |= {PACKAGE_ROOT / "public" / match for match in _ASSETS_URL.findall(text)}

			missing.extend(
				f"{source.name} -> {path.relative_to(PACKAGE_ROOT)}"
				for path in sorted(referenced)
				if not path.exists()
			)

		self.assertFalse(missing, msg=f"Hooks reference assets that do not exist: {missing}")

	def test_no_tracked_cache_or_backup_artifacts(self):
		result = subprocess.run(
			[
				"git",
				"-C",
				str(APP_ROOT),
				"ls-files",
				"*.pyc",
				"*.backup",
			],
			check=True,
			capture_output=True,
			text=True,
		)
		artifacts = sorted(
			line for line in result.stdout.splitlines() if line and (APP_ROOT / line).exists()
		)
		self.assertFalse(artifacts, msg=f"Repository artifacts should not be tracked: {artifacts}")

	def test_standard_json_docs_parse(self):
		json_dirs = (
			PACKAGE_ROOT / "sa_setup" / "workspace",
			PACKAGE_ROOT / "sa_setup" / "onboarding_step",
			PACKAGE_ROOT / "sa_setup" / "module_onboarding",
			PACKAGE_ROOT / "sa_setup" / "form_tour",
			PACKAGE_ROOT / "workspace_sidebar",
			PACKAGE_ROOT / "sa_vat" / "workspace",
			PACKAGE_ROOT / "sa_vat" / "report",
			PACKAGE_ROOT / "sa_vat" / "print_format",
			PACKAGE_ROOT / "sa_vat" / "print_format_field_template",
			PACKAGE_ROOT / "sa_payroll" / "workspace",
			PACKAGE_ROOT / "sa_payroll" / "print_format",
		)

		for json_dir in json_dirs:
			if not json_dir.exists():
				continue

			for path in json_dir.rglob("*.json"):
				with path.open() as handle:
					json.load(handle)

	# test_practitioner_guide_manifest_matches_content moved to
	# ir/ir/tests/test_repo_hygiene.py - practitioner_guide moved to ir as
	# part of absorbing za_local into ir.

	def test_expected_sa_workspace_sidebars_exist(self):
		expected = {
			"sa_vat.json",
			"sa_payroll.json",
			"sa_labour.json",
			"sa_coida.json",
		}
		found = {path.name for path in (PACKAGE_ROOT / "workspace_sidebar").glob("*.json")}
		self.assertTrue(
			expected.issubset(found),
			msg=f"Missing expected workspace sidebar standard docs: {sorted(expected - found)}",
		)
		self.assertNotIn(
			"sa_localisation.json",
			found,
			msg="SA Localisation is an App tile, not a Workspace Sidebar",
		)
		self.assertNotIn(
			"sa_overview.json",
			found,
			msg="SA Overview is not a Workspace Sidebar",
		)

	def test_workspace_sidebars_use_boot_visible_area_modules(self):
		expected_modules = {
			"sa_vat.json": "SA VAT",
			"sa_payroll.json": "SA Payroll",
			"sa_labour.json": "SA Labour",
			"sa_coida.json": "SA COIDA",
		}

		for filename, module in expected_modules.items():
			path = PACKAGE_ROOT / "workspace_sidebar" / filename
			with path.open() as handle:
				data = json.load(handle)
			self.assertEqual(data.get("app"), "za_local")
			self.assertEqual(
				data.get("module"),
				module,
				msg=f"{filename} should not be grouped under SA Localisation",
			)

	# test_expected_sa_module_onboarding_exists moved to ir/ir/tests/
	# test_repo_hygiene.py - sa_setup/module_onboarding/*.json moved to ir
	# (distributed across ir_setup/ir_vat/ir_payroll/ir_labour/ir_coida) as
	# part of absorbing za_local into ir.

	def test_module_sidebars_reference_module_onboarding(self):
		expected = {
			"sa_vat.json": "SA VAT Onboarding",
			"sa_payroll.json": "SA Payroll Onboarding",
			"sa_labour.json": "SA Labour Onboarding",
			"sa_coida.json": "SA COIDA Onboarding",
		}

		for filename, onboarding in expected.items():
			path = PACKAGE_ROOT / "workspace_sidebar" / filename
			with path.open() as handle:
				data = json.load(handle)
			self.assertEqual(
				data.get("module_onboarding"),
				onboarding,
				msg=f"{filename} should attach {onboarding}",
			)

	# test_sa_print_formats_are_module_scoped moved to ir/ir/tests/
	# test_repo_hygiene.py (as test_sa_print_formats_are_file_scoped) -
	# sa_vat/sa_payroll moved to ir_vat/ir_payroll as part of absorbing
	# za_local into ir.
