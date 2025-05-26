from . import __version__ as app_version

app_name = "itec_integrations"
app_title = "Itec Integrations"
app_publisher = "Abbass Chokor"
app_description = "Itec Integrations is a custom Frappe application developed for Itec, designed to centralize and manage system integrations with commercial partners. This app enables seamless synchronization of stock, pricing, and product information between Itec and third-party platforms such as suppliers, resellers, and logistic partners."
app_icon = "octicon octicon-file-directory"
app_color = "blue"
app_email = "abbasschokor225@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/itec_integrations/css/itec_integrations.css"
# app_include_js = "/assets/itec_integrations/js/itec_integrations.js"

# include js, css files in header of web template
# web_include_css = "/assets/itec_integrations/css/itec_integrations.css"
# web_include_js = "/assets/itec_integrations/js/itec_integrations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "itec_integrations/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Stylus Sync Stock Setting": "public/js/stylus_sync_stock_setting.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "itec_integrations.install.before_install"
# after_install = "itec_integrations.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "itec_integrations.uninstall.before_uninstall"
# after_uninstall = "itec_integrations.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "itec_integrations.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------


scheduler_events = {
	"all": [],
	"daily": [],
	"daily_long": [],
	"hourly": [
	"itec_integrations.itec_integrations.doctype.stylus_sync_stock_setting.stylus_sync_stock_setting.run_sync",
	],
	"hourly_long": [

	],
	"weekly": [],
	"monthly": [],
	"cron": {
		# Every five minutes
		"*/5 * * * *": [
			
		],
	},
}


# Testing
# -------

# before_tests = "itec_integrations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "itec_integrations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "itec_integrations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["itec_integrations.utils.before_request"]
# after_request = ["itec_integrations.utils.after_request"]

# Job Events
# ----------
# before_job = ["itec_integrations.utils.before_job"]
# after_job = ["itec_integrations.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"itec_integrations.auth.validate"
# ]

