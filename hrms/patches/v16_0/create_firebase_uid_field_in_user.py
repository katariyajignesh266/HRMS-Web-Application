from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import get_custom_fields


def execute():
	user_fields = {"User": get_custom_fields().get("User", [])}
	create_custom_fields(user_fields, ignore_validate=True)
