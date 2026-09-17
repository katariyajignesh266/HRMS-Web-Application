from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import get_custom_fields


def execute():
	employee_fields = {"Employee": get_custom_fields().get("Employee", [])}
	create_custom_fields(employee_fields, ignore_validate=True)
