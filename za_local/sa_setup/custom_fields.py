"""
South African Localization: Custom Fields

Every Custom Field this module used to define has been absorbed into
ir's own fixtures (ir/ir/fixtures/custom_field.json) as part of absorbing
za_local into ir - ir now independently creates/maintains every za_*
custom field on every migrate via the standard fixture mechanism.
get_custom_field_fixtures() stays as an intentionally empty stub:
za_local/sa_setup/uninstall.py's remove_custom_fields() reads it
dynamically at uninstall time, and this app must never delete fields ir
still needs.

The DocType Link "Connections tab" records this module used to expose via
get_za_local_custom_records() (wired to a "custom_records" hook that was
never actually a real Frappe/ERPNext/HRMS hook, and so was never
consumed) have been rebuilt properly in
ir.setup.doctype_connections.ensure_doctype_connection_links/
ensure_employee_links, run from ir's own after_migrate.
"""


def get_custom_field_fixtures():
	"""Intentionally empty - every za_* Custom Field is now ir's own fixture.

	Kept only so uninstall.py's remove_custom_fields() has a (now empty)
	list to read dynamically; it must never delete fields ir still needs.
	"""
	return []
