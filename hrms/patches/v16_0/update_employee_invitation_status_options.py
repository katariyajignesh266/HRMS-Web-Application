import frappe


INVITATION_STATUS_OPTIONS = "\nNot Generated\nGenerated\nQueued\nSent\nFailed\nNot Configured\nAlready Queued"


def execute():
	if frappe.db.exists("Custom Field", "Employee-firebase_invitation_status"):
		frappe.db.set_value(
			"Custom Field",
			"Employee-firebase_invitation_status",
			"options",
			INVITATION_STATUS_OPTIONS,
			update_modified=False,
		)
