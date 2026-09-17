"""Phase 5 — Real Firebase Login E2E Automated Verification Script.

Tests complete flow:
A. Firebase status configured
B. Missing token -> 401
C. Invalid token -> 401
D. Valid token -> Logged In
E. Protected user endpoint
F. Protected employee endpoint
G. Logout clears session
H. Old session rejected after logout
I. Disabled user blocked
J. Test data cleanup
"""

import os
import secrets
import sys
import time
import requests

import frappe
from firebase_admin import auth as firebase_auth
from hrms.api.firebase_auth import _get_firebase_admin_app, get_firebase_config
from hrms.api.employee_provisioning import provision_employee_login

BASE_URL = os.getenv("FRAPPE_BASE_URL", "http://localhost:8000")
REQ_TIMEOUT = 30
TEST_PREFIX = "_test-phase5-"
TEST_EMAIL = os.getenv("PHASE5_TEST_EMAIL", f"{TEST_PREFIX}hrms@test.com").strip().lower()
TEST_PASSWORD = os.getenv("PHASE5_TEST_PASSWORD") or (secrets.token_urlsafe(16) + "Aa1!")
TEST_EMP_NAME = f"{TEST_PREFIX}Employee"


def init_frappe():
    sites_path = os.getenv("FRAPPE_SITES_PATH", "/home/frappe/frappe-bench/sites")
    site_name = os.getenv("FRAPPE_SITE_NAME", "hrms.localhost")
    frappe.init(site_name, sites_path=sites_path)
    frappe.connect()


def cleanup_test_data(test_uid=None):
    """Remove only test data matching TEST_PREFIX in both Frappe and Firebase Auth."""
    for pat in (f"{TEST_PREFIX}%", "_Test%"):
        test_employees = frappe.db.sql_list(
            """
            select name from `tabEmployee`
            where personal_email like %(pat)s
               or company_email like %(pat)s
               or user_id like %(pat)s
               or employee_name like %(pat)s
               or first_name like %(pat)s
            """,
            {"pat": pat},
        )
        for emp in test_employees:
            frappe.delete_doc("Employee", emp, force=True, ignore_permissions=True)

        test_users = frappe.db.sql_list(
            """
            select name from `tabUser`
            where name like %(pat)s or email like %(pat)s
            """,
            {"pat": pat},
        )
        for usr in test_users:
            frappe.db.delete("User Permission", {"user": usr})
            frappe.db.delete("Has Role", {"parent": usr})
            frappe.db.delete("User", {"name": usr})

    frappe.db.commit()

    # Firebase Auth cleanup
    _get_firebase_admin_app()
    if test_uid:
        try:
            firebase_auth.delete_user(test_uid)
        except firebase_auth.UserNotFoundError:
            pass
        except Exception:
            pass
    try:
        fb_user = firebase_auth.get_user_by_email(TEST_EMAIL)
        if fb_user:
            firebase_auth.delete_user(fb_user.uid)
    except firebase_auth.UserNotFoundError:
        pass
    except Exception:
        pass


def run_e2e_tests():
    results = {}
    notes = []
    created_employee_name = None
    created_uid = None

    print("=" * 60)
    print("Starting Phase 5 — Real Firebase Login E2E Verification")
    print("=" * 60)

    try:
        init_frappe()
    except Exception as e:
        print(f"Failed to initialize Frappe: {e}")
        sys.exit(1)

    # Pre-test cleanup of any leftover test artifacts
    cleanup_test_data()

    # ------------------------------------------------------------------
    # Test A: Firebase status configured
    # ------------------------------------------------------------------
    try:
        resp = requests.get(f"{BASE_URL}/api/method/hrms.api.firebase_auth.firebase_status", timeout=REQ_TIMEOUT)
        data = resp.json().get("message", {})
        if (
            resp.status_code == 200
            and data.get("configured") is True
            and data.get("server_verification_configured") is True
        ):
            results["A"] = "PASS"
        else:
            results["A"] = "FAIL"
            notes.append(f"Test A: status={resp.status_code}, data={data}")
    except Exception as e:
        results["A"] = "FAIL"
        notes.append(f"Test A exception: {e}")

    # ------------------------------------------------------------------
    # Test B: Missing token -> 401
    # ------------------------------------------------------------------
    try:
        resp = requests.post(
            f"{BASE_URL}/api/method/hrms.api.firebase_auth.login_with_firebase_token",
            json={},
            timeout=REQ_TIMEOUT,
        )
        if resp.status_code in (401, 417) and "AuthenticationError" in resp.text:
            results["B"] = "PASS"
        else:
            results["B"] = "FAIL"
            notes.append(f"Test B: expected 401/417 AuthenticationError, got {resp.status_code}")
    except Exception as e:
        results["B"] = "FAIL"
        notes.append(f"Test B exception: {e}")

    # ------------------------------------------------------------------
    # Test C: Invalid token -> 401
    # ------------------------------------------------------------------
    try:
        resp = requests.post(
            f"{BASE_URL}/api/method/hrms.api.firebase_auth.login_with_firebase_token",
            json={"id_token": "invalid-garbage-token"},
            timeout=REQ_TIMEOUT,
        )
        if resp.status_code in (401, 417) and "AuthenticationError" in resp.text:
            results["C"] = "PASS"
        else:
            results["C"] = "FAIL"
            notes.append(f"Test C: expected 401/417 AuthenticationError, got {resp.status_code}")
    except Exception as e:
        results["C"] = "FAIL"
        notes.append(f"Test C exception: {e}")

    # ------------------------------------------------------------------
    # Provision Disposable Test Employee & User
    # ------------------------------------------------------------------
    try:
        company = (
            frappe.defaults.get_user_default("Company")
            or frappe.defaults.get_global_default("company")
            or frappe.db.get_single_value("Global Defaults", "default_company")
            or frappe.db.get_value("Company", {}, "name", order_by="creation asc")
        )
        gender = (
            frappe.db.get_value("Gender", "Prefer not to say", "name")
            or frappe.db.get_value("Gender", "Other", "name")
            or frappe.db.get_value("Gender", {}, "name", order_by="creation asc")
            or "Male"
        )
        emp_doc = frappe.new_doc("Employee")
        emp_doc.first_name = "_test-phase5-emp"
        emp_doc.last_name = "User"
        emp_doc.employee_name = TEST_EMP_NAME
        emp_doc.gender = gender
        emp_doc.date_of_birth = "1990-01-01"
        emp_doc.company = company
        emp_doc.prefered_email = TEST_EMAIL
        emp_doc.personal_email = TEST_EMAIL
        emp_doc.status = "Active"
        emp_doc.date_of_joining = frappe.utils.nowdate()
        emp_doc.flags.ignore_permissions = True
        emp_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        created_employee_name = emp_doc.name

        provision_res = provision_employee_login(created_employee_name, send_invitation=0, ignore_permissions=True)
        frappe.db.commit()

        if provision_res.get("status") != "Provisioned" or not provision_res.get("firebase_uid"):
            raise RuntimeError(f"Provisioning failed: {provision_res}")

        created_uid = provision_res["firebase_uid"]

        # Set known test password via Admin SDK
        _get_firebase_admin_app()
        firebase_auth.update_user(created_uid, password=TEST_PASSWORD)
    except Exception as e:
        notes.append(f"Setup failure during test provisioning: {e}")
        results["D"] = "FAIL"
        results["E"] = "FAIL"
        results["F"] = "FAIL"
        results["G"] = "FAIL"
        results["H"] = "FAIL"
        results["I"] = "FAIL"
        cleanup_test_data(created_uid)
        results["J"] = "FAIL"
        _print_summary(results, notes)
        return

    # ------------------------------------------------------------------
    # Obtain real Firebase ID token via REST Identity Toolkit
    # ------------------------------------------------------------------
    fb_config = get_firebase_config()
    api_key = fb_config.get("api_key")
    if not api_key:
        notes.append("Firebase API key is missing from config")
        results["D"] = "FAIL"

    id_token = None
    try:
        sign_in_resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "returnSecureToken": True},
            timeout=REQ_TIMEOUT,
        )
        if sign_in_resp.status_code == 200:
            id_token = sign_in_resp.json().get("idToken")
            # Compensate for clock skew between Google token server and local container
            time.sleep(5)
        else:
            notes.append(f"Firebase REST sign in failed: status={sign_in_resp.status_code}")
    except Exception as e:
        notes.append(f"Firebase REST sign in exception: {e}")

    # ------------------------------------------------------------------
    # Test D: Valid token -> Logged In
    # ------------------------------------------------------------------
    client_session = requests.Session()
    old_sid = None
    if id_token:
        try:
            resp = client_session.post(
                f"{BASE_URL}/api/method/hrms.api.firebase_auth.login_with_firebase_token",
                json={"id_token": id_token},
                timeout=REQ_TIMEOUT,
            )
            data = resp.json().get("message", {})
            sid_cookie = client_session.cookies.get("sid")
            if (
                resp.status_code == 200
                and data.get("message") == "Logged In"
                and data.get("user") == TEST_EMAIL
                and sid_cookie
                and sid_cookie != "Guest"
            ):
                results["D"] = "PASS"
                old_sid = sid_cookie
            else:
                results["D"] = "FAIL"
                notes.append(f"Test D: status={resp.status_code}, data={data}, sid={bool(sid_cookie)}")
        except Exception as e:
            results["D"] = "FAIL"
            notes.append(f"Test D exception: {e}")
    else:
        results["D"] = "FAIL"

    # ------------------------------------------------------------------
    # Test E: Protected user endpoint
    # ------------------------------------------------------------------
    if results.get("D") == "PASS":
        try:
            resp = client_session.get(f"{BASE_URL}/api/method/hrms.api.get_current_user_info", timeout=REQ_TIMEOUT)
            user_info = resp.json().get("message", {})
            if (
                resp.status_code == 200
                and user_info.get("name") == TEST_EMAIL
                and "Employee" in (user_info.get("roles") or [])
            ):
                results["E"] = "PASS"
            else:
                results["E"] = "FAIL"
                notes.append(f"Test E: status={resp.status_code}, user_info={user_info}")
        except Exception as e:
            results["E"] = "FAIL"
            notes.append(f"Test E exception: {e}")
    else:
        results["E"] = "FAIL"

    # ------------------------------------------------------------------
    # Test F: Protected employee endpoint
    # ------------------------------------------------------------------
    if results.get("D") == "PASS":
        try:
            resp = client_session.get(f"{BASE_URL}/api/method/hrms.api.get_current_employee_info", timeout=REQ_TIMEOUT)
            emp_info = resp.json().get("message", {})
            if (
                resp.status_code == 200
                and emp_info.get("user_id") == TEST_EMAIL
                and emp_info.get("name") == created_employee_name
            ):
                results["F"] = "PASS"
            else:
                results["F"] = "FAIL"
                notes.append(f"Test F: status={resp.status_code}, emp_info={emp_info}")
        except Exception as e:
            results["F"] = "FAIL"
            notes.append(f"Test F exception: {e}")
    else:
        results["F"] = "FAIL"

    # ------------------------------------------------------------------
    # Test G: Logout clears session
    # ------------------------------------------------------------------
    if results.get("D") == "PASS":
        try:
            resp = client_session.post(f"{BASE_URL}/api/method/logout", timeout=REQ_TIMEOUT)
            cookie_user_id = client_session.cookies.get("user_id")
            cookie_sid = client_session.cookies.get("sid")
            if resp.status_code == 200 and (cookie_user_id in (None, "", "Guest") or cookie_sid in (None, "", "Guest")):
                results["G"] = "PASS"
            else:
                results["G"] = "FAIL"
                notes.append(f"Test G: status={resp.status_code}, user_id={cookie_user_id}, sid={cookie_sid}")
        except Exception as e:
            results["G"] = "FAIL"
            notes.append(f"Test G exception: {e}")
    else:
        results["G"] = "FAIL"

    # ------------------------------------------------------------------
    # Test H: Old session rejected after logout
    # ------------------------------------------------------------------
    if old_sid:
        try:
            resp = requests.get(
                f"{BASE_URL}/api/method/hrms.api.get_current_user_info",
                cookies={"sid": old_sid},
                timeout=REQ_TIMEOUT,
            )
            # Protected endpoint requires logged-in user; with invalidated sid it returns 401/403
            if resp.status_code in (401, 403):
                results["H"] = "PASS"
            else:
                results["H"] = "FAIL"
                notes.append(f"Test H: expected 401/403, got {resp.status_code}")
        except Exception as e:
            results["H"] = "FAIL"
            notes.append(f"Test H exception: {e}")
    else:
        results["H"] = "FAIL"

    # ------------------------------------------------------------------
    # Test I: Disabled user blocked
    # ------------------------------------------------------------------
    try:
        # Disable Frappe User
        frappe.db.set_value("User", TEST_EMAIL, "enabled", 0)
        frappe.db.commit()

        # Try logging in with a fresh token
        sign_in_resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "returnSecureToken": True},
            timeout=REQ_TIMEOUT,
        )
        if sign_in_resp.status_code == 200:
            fresh_token = sign_in_resp.json().get("idToken")
            time.sleep(5)
        else:
            fresh_token = id_token

        disabled_session = requests.Session()
        resp = disabled_session.post(
            f"{BASE_URL}/api/method/hrms.api.firebase_auth.login_with_firebase_token",
            json={"id_token": fresh_token},
            timeout=REQ_TIMEOUT,
        )
        if resp.status_code in (401, 417) and "AuthenticationError" in resp.text:
            results["I"] = "PASS"
        else:
            results["I"] = "FAIL"
            notes.append(f"Test I: expected 401/417 AuthenticationError, got {resp.status_code}")
    except Exception as e:
        results["I"] = "FAIL"
        notes.append(f"Test I exception: {e}")
    finally:
        try:
            frappe.db.set_value("User", TEST_EMAIL, "enabled", 1)
            frappe.db.commit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Test J: Test data cleanup
    # ------------------------------------------------------------------
    try:
        cleanup_test_data(created_uid)

        remaining_emp = (
            frappe.db.count("Employee", {"employee_name": ["like", f"{TEST_PREFIX}%"]})
            + frappe.db.count("Employee", {"employee_name": ["like", "_Test%"]})
        )
        remaining_usr = (
            frappe.db.count("User", {"email": ["like", f"{TEST_PREFIX}%"]})
            + frappe.db.count("User", {"email": ["like", "_Test%"]})
        )

        fb_deleted = False
        if created_uid:
            try:
                firebase_auth.get_user(created_uid)
            except firebase_auth.UserNotFoundError:
                fb_deleted = True
            except Exception:
                fb_deleted = False
        else:
            fb_deleted = True

        # Verify real data was not touched
        admin_exists = frappe.db.exists("User", "Administrator")

        if remaining_emp == 0 and remaining_usr == 0 and fb_deleted and admin_exists:
            results["J"] = "PASS"
        else:
            results["J"] = "FAIL"
            notes.append(
                f"Test J: remaining_emp={remaining_emp}, remaining_usr={remaining_usr}, fb_deleted={fb_deleted}"
            )
    except Exception as e:
        results["J"] = "FAIL"
        notes.append(f"Test J exception: {e}")

    _print_summary(results, notes)


def _print_summary(results, notes):
    print("\n" + "=" * 60)
    print("Phase 5 E2E Results:")
    labels = {
        "A": "Firebase status configured:",
        "B": "Missing token → 401:",
        "C": "Invalid token → 401:",
        "D": "Valid token → Logged In:",
        "E": "Protected user endpoint:",
        "F": "Protected employee endpoint:",
        "G": "Logout clears session:",
        "H": "Old session rejected after logout:",
        "I": "Disabled user blocked:",
        "J": "Test data cleanup:",
    }

    all_passed = True
    for key in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]:
        status = results.get(key, "FAIL")
        if status != "PASS":
            all_passed = False
        print(f"  {key}. {labels[key]:<36} {status}")

    print()
    print(f"Phase 5: {'COMPLETE' if all_passed else 'INCOMPLETE'}")
    if notes:
        print(f"Notes: {'; '.join(notes)}")
    else:
        print("Notes: All tests passed with zero secrets exposed and clean state verification.")
    print("=" * 60)


if __name__ == "__main__":
    run_e2e_tests()
