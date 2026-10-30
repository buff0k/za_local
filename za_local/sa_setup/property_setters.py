# Copyright (c) 2025, Cohenix and contributors
# For license information, please see license.txt

"""
Property Setters for za_local app.

Every property setter this module used to define has been absorbed into
ir's own fixture (ir/ir/fixtures/property_setter.json) as part of
absorbing za_local into ir - ir now independently creates/maintains all
45 on every migrate via the standard fixture mechanism.
"""


def get_property_setters():
	"""
	Intentionally empty - every property setter za_local used to define is
	now ir's own fixture.

	Kept only so uninstall.py's remove_property_setters() has a (now empty)
	dict to read dynamically; it must never delete property setters ir
	still needs.
	"""
	return {}
