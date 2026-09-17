import os
try:
    os.chdir("/home/frappe/frappe-bench")
    os.makedirs("/home/frappe/logs", exist_ok=True)
    os.makedirs("/home/frappe/frappe-bench/logs", exist_ok=True)
    import frappe
    frappe.init(site="hrms.localhost", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    users = frappe.db.count("User")
    employees = frappe.db.count("Employee")
    companies = frappe.db.count("Company")
    print(f"Users: {users} | Employees: {employees} | Companies: {companies}")
except Exception as e:
    print(f"DB Error: {e}")

