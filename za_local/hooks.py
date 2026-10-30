
app_name = "za_local"
app_title = "SA Localisation"
app_publisher = "Cohenix"
app_description = "Comprehensive South African localization for ERPNext covering payroll, tax, VAT, and COIDA compliance"
app_email = "info@cohenix.com"
app_license = "mit"
app_logo_url = "/assets/za_local/images/sa_map_icon.png"
app_home = "/desk/sa-overview"

# Import hook utility functions for conditional configuration
# These are called at import time to generate configuration dynamically
from za_local.sa_setup.custom_fields import get_za_local_custom_records

# Add to Apps Screen (Frappe v16 desk: one App tile with map logo; workspace icons nest under it)
# ------------------
add_to_apps_screen = [
	{
		"name": "za_local",
		"title": "SA Localisation",
		"logo": "/assets/za_local/images/sa_map_icon.png",
		"route": "/desk/sa-overview",
		"has_permission": "za_local.api.check_app_permission",
	}
]

# Apps
# ------------------
# Note: HRMS is optional - za_local works with or without HRMS
# If HRMS is not installed, payroll/HR features will be disabled
required_apps = ["erpnext"]

# Fixtures
# ------------------
fixtures = [
    # Custom Fields: source of truth is setup/custom_fields.py (applied on install/migrate)
    # Property Setters
    {"dt": "Property Setter", "filters": [["module", "in", ["SA Localisation", "SA Payroll", "SA VAT", "SA Labour", "SA COIDA", "SA Setup"]]]},

    # App doctype for v16 compatibility
    # Required for proper app deployment and management in Frappe v16+
    {"dt": "App", "filters": [["name", "=", "za_local"]]},
]

# Includes in <head>
# ------------------
app_include_css = "/assets/za_local/css/za_local.css"
app_include_js = "/assets/za_local/js/za_local_feedback.js"

# Include JS in doctype views
# ------------------
# Base JS files (always available)
# Note: za_local's own DocTypes (e.g. EMP501 Reconciliation) load their client
# scripts automatically from their doctype folder — they must not be listed here.
doctype_js = {}

# Installation
# ------------------
after_install = "za_local.sa_setup.install.after_install"
before_migrate = ["za_local.sa_setup.install.before_migrate"]
after_migrate = ["za_local.sa_setup.install.after_migrate"]

# Uninstallation
# ------------------
after_uninstall = "za_local.sa_setup.uninstall.after_uninstall"

# Setup Wizard Integration
# ------------------
# Do not add a client-side ZA slide to ERPNext's first-run setup wizard.
# ERPNext owns Company, Fiscal Year, CoA and core master creation; za_local
# only contributes a non-blocking server-side post stage below.
setup_wizard_stages = "za_local.sa_setup.setup_wizard.get_sa_localization_stages"

# DocType Class Extensions and Overrides
# ------------------
extend_doctype_class = {}

# Document Events
# ------------------
# Hook on document methods and events
doc_events = {
    # Journal Entry events (existing)
    "Journal Entry": {
        "on_trash": "za_local.overrides.journal_entry.on_trash",
        "on_cancel": "za_local.overrides.journal_entry.on_cancel"
    },

    # Customer validation for SA VAT numbers
    "Customer": {
        "validate": "za_local.custom.customer.validate",
    },

}

# Monkey Patching
# ------------------
# Monkey patches are now applied during installation/migration via setup.monkey_patches
# This ensures patches are applied at the right time, not at import time

# Custom Records (DocType Links for Bidirectional Connections)
# ------------------
# Creates links between za_local DocTypes and standard DocTypes
# These appear in the "Connections" tab of documents
# HRMS-dependent links are filtered conditionally
za_local_custom_records = get_za_local_custom_records()


# Scheduled Tasks
# ------------------
# Automated compliance monitoring and reminders
scheduler_events = {
	"daily_long": [
		"za_local.tasks.daily",
	],
	"weekly_long": [
		"za_local.tasks.weekly",
	],
	"monthly_long": [
		"za_local.tasks.monthly",
		"za_local.tasks.quarterly",
	],
}

# Permissions
# ------------------
# permission_query_conditions = {
#     "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }

# Document Events for Specific Workflows
# ------------------
# doc_events = {
#     "*": {
#         "on_update": "method",
#         "on_cancel": "method",
#         "on_trash": "method"
#     }
# }

# Request Events
# ------------------
# Dropped: apply_chart_patches_on_request only re-applied the 3 monkey
# patches in sa_setup/monkey_patches.py, all confirmed dead/unused -
# no company on this bench has ever used the za_local chart template
# (every one uses ERPNext's own Standard/Standard with Numbers), and
# nothing calls the hrms payroll_entry patch. See the migration history
# for the verification.

# Job Events
# ------------------
# before_job = ["za_local.utils.before_job"]
# after_job = ["za_local.utils.after_job"]

# User Data Protection
# ------------------
# user_data_fields = [
#     {
#         "doctype": "{doctype_1}",
#         "filter_by": "{filter_by}",
#         "redact_fields": ["{field_1}", "{field_2}"],
#         "partial": 1,
#     },
# ]

# Authentication and authorization
# ------------------
# auth_hooks = [
#     "za_local.auth.validate"
# ]

# Translation
# ------------------
# Make all summary doctype labels for South African localization
# override_doctype_dashboards = {
#     "Task": "za_local.task.get_dashboard_data"
# }
