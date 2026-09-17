import os
import json
from functools import lru_cache

import frappe
from frappe import _
from frappe.exceptions import AuthenticationError
from frappe.permissions import add_user_permission
from frappe.utils import nowdate

try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials
except ImportError:
    firebase_admin = None
    firebase_auth = None
    credentials = None


def get_firebase_config() -> dict:
    """Read Firebase configuration from site config or process environment."""
    conf = getattr(frappe, "conf", {}) or {}

    return {
        "api_key": conf.get("FIREBASE_API_KEY") or os.getenv("FIREBASE_API_KEY"),
        "project_id": conf.get("FIREBASE_PROJECT_ID") or os.getenv("FIREBASE_PROJECT_ID"),
        "auth_domain": conf.get("FIREBASE_AUTH_DOMAIN") or os.getenv("FIREBASE_AUTH_DOMAIN"),
        "app_id": conf.get("FIREBASE_APP_ID") or os.getenv("FIREBASE_APP_ID"),
        "uid_field": conf.get("FIREBASE_UID_FIELD") or os.getenv("FIREBASE_UID_FIELD", "firebase_uid"),
        "admin_credentials_json": conf.get("FIREBASE_ADMIN_CREDENTIALS_JSON")
        or os.getenv("FIREBASE_ADMIN_CREDENTIALS_JSON"),
        "admin_credentials_file": conf.get("FIREBASE_ADMIN_CREDENTIALS_FILE")
        or os.getenv("FIREBASE_ADMIN_CREDENTIALS_FILE"),
    }


@lru_cache(maxsize=1)
def _get_firebase_admin_app():
    if firebase_admin is None:
        frappe.throw(_("Firebase Admin SDK is not installed on the server."), frappe.AuthenticationError)

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    config = get_firebase_config()
    credentials_json = config.get("admin_credentials_json")
    credentials_file = config.get("admin_credentials_file")
    if credentials_json:
        try:
            credential_info = json.loads(credentials_json)
        except json.JSONDecodeError:
            frappe.throw(_("Firebase server credentials are invalid."), frappe.AuthenticationError)
    elif credentials_file:
        try:
            with open(credentials_file) as file:
                credential_info = json.load(file)
        except (OSError, json.JSONDecodeError):
            frappe.throw(_("Firebase server credentials are invalid."), frappe.AuthenticationError)
    else:
        frappe.throw(
            _("Firebase server verification is not configured."), frappe.AuthenticationError
        )

    options = {"projectId": config.get("project_id")} if config.get("project_id") else None
    return firebase_admin.initialize_app(credentials.Certificate(credential_info), options)


def _get_mapped_frappe_user(decoded_token: dict) -> str | None:
    config = get_firebase_config()
    uid = decoded_token.get("uid")
    email = (decoded_token.get("email") or "").strip().lower()
    email_verified = decoded_token.get("email_verified")
    uid_field = config.get("uid_field")

    if uid_field and frappe.get_meta("User").has_field(uid_field):
        user = frappe.db.get_value("User", {uid_field: uid}, "name")
        if user:
            return user

    if email and email_verified:
        users = frappe.get_all("User", filters={"email": email}, pluck="name", limit=2)
        if len(users) == 1:
            return users[0]
        if len(users) > 1:
            frappe.logger("firebase_auth").warning("Ambiguous Frappe users found for verified Firebase email")

    return None


def _get_default_company() -> str | None:
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
        or frappe.db.get_value("Company", {}, "name", order_by="creation asc")
    )


def _get_default_gender() -> str | None:
    return (
        frappe.db.get_value("Gender", "Prefer not to say", "name")
        or frappe.db.get_value("Gender", "Other", "name")
        or frappe.db.get_value("Gender", {}, "name", order_by="creation asc")
    )


def _split_user_name(user_doc) -> tuple[str, str, str]:
    parts = (user_doc.full_name or user_doc.first_name or user_doc.email or user_doc.name).split()
    first_name = user_doc.first_name or (parts[0] if parts else user_doc.name)
    middle_name = user_doc.middle_name or ""
    last_name = user_doc.last_name or ""

    if not user_doc.first_name and len(parts) >= 3:
        middle_name = parts[1]
        last_name = " ".join(parts[2:])
    elif not user_doc.first_name and len(parts) == 2:
        last_name = parts[1]

    return first_name, middle_name, last_name


def _ensure_employee_role(user_doc) -> None:
    if "Employee" not in {role.role for role in user_doc.get("roles")}:
        user_doc.append_roles("Employee")


def _ensure_employee_for_user(user: str, firebase_uid: str | None = None) -> str:
    if user == "Administrator":
        return ""

    employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
    if employee:
        return employee

    user_doc = frappe.get_doc("User", user)
    uid_field = get_firebase_config().get("uid_field")

    if firebase_uid and uid_field and frappe.get_meta("User").has_field(uid_field) and not user_doc.get(uid_field):
        user_doc.db_set(uid_field, firebase_uid, update_modified=False)
        user_doc.set(uid_field, firebase_uid)

    _ensure_employee_role(user_doc)
    user_doc.flags.ignore_permissions = True
    user_doc.flags.no_welcome_mail = True
    user_doc.save(ignore_permissions=True)

    email = (user_doc.email or user_doc.name or "").strip().lower()
    if not email:
        frappe.throw(_("A verified email is required to create an Employee record."))

    existing_employee = frappe.db.sql(
        """
        select name, company
        from `tabEmployee`
        where status = 'Active'
            and (
                user_id = %(user)s
                or personal_email = %(email)s
                or company_email = %(email)s
                or prefered_email = %(email)s
            )
        order by creation desc
        limit 1
        """,
        {"user": user, "email": email},
        as_dict=True,
    )
    if existing_employee:
        employee_doc = frappe.get_doc("Employee", existing_employee[0].name)
        if not employee_doc.user_id:
            employee_doc.db_set("user_id", user_doc.name, update_modified=False)
        if not frappe.db.exists("User Permission", {"user": user_doc.name, "allow": "Employee", "for_value": employee_doc.name}):
            add_user_permission("Employee", employee_doc.name, user_doc.name, ignore_permissions=True)
        if employee_doc.company and not frappe.db.exists("User Permission", {"user": user_doc.name, "allow": "Company", "for_value": employee_doc.company}):
            add_user_permission("Company", employee_doc.company, user_doc.name, ignore_permissions=True)
        return employee_doc.name

    company = _get_default_company()
    if not company:
        frappe.throw(_("Default Company is required to create an Employee record."))

    gender = _get_default_gender()
    first_name, middle_name, last_name = _split_user_name(user_doc)
    employee_doc = frappe.new_doc("Employee")
    employee_doc.update(
        {
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "employee_name": user_doc.full_name or " ".join(filter(None, [first_name, middle_name, last_name])),
            "gender": gender,
            "date_of_birth": user_doc.birth_date or "1970-01-01",
            "user_id": user_doc.name,
            "personal_email": email,
            "company_email": email,
            "company": company,
            "status": "Active",
            "date_of_joining": nowdate(),
            "create_user_automatically": 0,
            "create_user_permission": 1,
            "create_user_permission": 0,
        }
    )
    employee_doc.flags.ignore_permissions = True
    employee_doc.insert(ignore_permissions=True)

    add_user_permission("Employee", employee_doc.name, user_doc.name, ignore_permissions=True)
    add_user_permission("Company", company, user_doc.name, ignore_permissions=True)
    if not frappe.db.exists("User Permission", {"user": user_doc.name, "allow": "Employee", "for_value": employee_doc.name}):
        add_user_permission("Employee", employee_doc.name, user_doc.name, ignore_permissions=True)
    if not frappe.db.exists("User Permission", {"user": user_doc.name, "allow": "Company", "for_value": company}):
        add_user_permission("Company", company, user_doc.name, ignore_permissions=True)

    return employee_doc.name


def _verify_firebase_id_token(id_token: str | None) -> dict:
    if not id_token or not isinstance(id_token, str):
        frappe.throw(_("A Firebase ID token is required."), frappe.AuthenticationError)

    try:
        _get_firebase_admin_app()
        return firebase_auth.verify_id_token(id_token, check_revoked=True)
        return firebase_auth.verify_id_token(id_token, check_revoked=True, clock_skew_seconds=10)
        return firebase_auth.verify_id_token(id_token, check_revoked=True, clock_skew_seconds=60)
    except Exception as error:
        if firebase_auth and isinstance(
            error,
            (
                firebase_auth.ExpiredIdTokenError,
                firebase_auth.InvalidIdTokenError,
                firebase_auth.RevokedIdTokenError,
                firebase_auth.UserDisabledError,
            ),
        ):
            frappe.logger("firebase_auth").warning("Firebase token rejected: %s", type(error).__name__)
            frappe.logger("firebase_auth").warning("Firebase token rejected: %s: %s", type(error).__name__, error)
            frappe.throw(_("Your Firebase session is invalid or expired."), frappe.AuthenticationError)
        if isinstance(error, AuthenticationError):
            raise
        frappe.logger("firebase_auth").error("Firebase verification failed: %s", type(error).__name__)
        frappe.logger("firebase_auth").error("Firebase verification failed: %s: %s", type(error).__name__, error)
        frappe.throw(_("Firebase authentication is unavailable."), frappe.AuthenticationError)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def login_with_firebase_token(id_token: str | None = None):
    """Verify a Firebase ID token and create the corresponding Frappe session."""
    decoded_token = _verify_firebase_id_token(id_token)
    user = _get_mapped_frappe_user(decoded_token)

    if not user or not frappe.db.get_value("User", user, "enabled"):
        frappe.logger("firebase_auth").warning("No enabled Frappe user mapped for Firebase identity")
        frappe.throw(_("Your Firebase account is not mapped to an enabled HRMS user."), frappe.AuthenticationError)

    if frappe.db.get_value("User", user, "user_type") != "System User":
        frappe.throw(_("This account cannot access the HRMS application."), frappe.PermissionError)

    _ensure_employee_for_user(user, decoded_token.get("uid"))

    frappe.local.login_manager.login_as(user)
    return {"message": "Logged In", "user": user, "firebase_uid": decoded_token.get("uid")}


@frappe.whitelist(allow_guest=True)
def firebase_config():
    """Return only Firebase Web SDK values safe for client-side initialization."""
    config = get_firebase_config()
    return {
        "configured": bool(config.get("api_key") and config.get("project_id") and config.get("app_id")),
        "api_key": config.get("api_key"),
        "auth_domain": config.get("auth_domain") or (
            f"{config.get('project_id')}.firebaseapp.com" if config.get("project_id") else None
        ),
        "project_id": config.get("project_id"),
        "app_id": config.get("app_id"),
    }


@frappe.whitelist(allow_guest=True)
def firebase_status():
    config = get_firebase_config()
    return {
        "configured": bool(config.get("api_key") and config.get("project_id") and config.get("app_id")),
        "project_id": config.get("project_id"),
        "server_verification_configured": bool(
            config.get("admin_credentials_json") or config.get("admin_credentials_file")
        ),
    }
