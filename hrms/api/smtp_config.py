import os

import frappe
from frappe import _
from frappe.utils import cint


SMTP_ACCOUNT_NAME = "HRMS Gmail SMTP"


def _env(name: str, fallback: str | None = None) -> str:
	return (os.environ.get(name) or (os.environ.get(fallback) if fallback else "") or "").strip()


def _smtp_settings_from_env() -> dict:
	username = _env("SMTP_USERNAME", "SMTP_EMAIL_ACCOUNT")
	password = _env("SMTP_PASSWORD", "SMTP_EMAIL_PASSWORD")
	sender = _env("SMTP_SENDER") or username

	return {
		"host": _env("SMTP_HOST") or "smtp.gmail.com",
		"port": cint(_env("SMTP_PORT") or 587),
		"username": username,
		"password": password,
		"sender": sender,
		"use_tls": (_env("SMTP_USE_TLS") or "true").lower() in ("1", "true", "yes", "on"),
	}


def _safe_status(configured: bool, message: str | None = None) -> dict:
	settings = _smtp_settings_from_env()
	return {
		"configured": configured,
		"host": settings["host"],
		"port": settings["port"],
		"username_configured": bool(settings["username"]),
		"sender": settings["sender"] if configured else "",
		"password_configured": bool(settings["password"]),
		"use_tls": settings["use_tls"],
		"message": message,
	}


def configure_gmail_smtp_from_env() -> dict:
	settings = _smtp_settings_from_env()
	if not settings["username"] or not settings["password"]:
		return _safe_status(False, _("SMTP_USERNAME and SMTP_PASSWORD are not configured."))

	account_name = (
		frappe.db.get_value("Email Account", {"email_id": settings["sender"], "enable_outgoing": 1}, "name")
		or SMTP_ACCOUNT_NAME
	)
	account = (
		frappe.get_doc("Email Account", account_name)
		if frappe.db.exists("Email Account", account_name)
		else frappe.new_doc("Email Account")
	)

	account.update(
		{
			"email_account_name": SMTP_ACCOUNT_NAME,
			"email_id": settings["sender"],
			"service": "GMail",
			"enable_incoming": 0,
			"enable_outgoing": 1,
			"default_outgoing": 1,
			"always_use_account_email_id_as_sender": 1,
			"always_use_account_name_as_sender_name": 1,
			"track_email_status": 1,
			"login_id_is_different": settings["username"] != settings["sender"],
			"login_id": settings["username"] if settings["username"] != settings["sender"] else None,
			"smtp_server": settings["host"],
			"smtp_port": settings["port"],
			"use_tls": 1 if settings["use_tls"] else 0,
			"use_ssl_for_outgoing": 0,
			"no_smtp_authentication": 0,
			"awaiting_password": 0,
		}
	)
	account.password = settings["password"]

	previous_in_patch = getattr(frappe.local.flags, "in_patch", False)
	frappe.local.flags.in_patch = True
	try:
		if account.is_new():
			account.insert(ignore_permissions=True)
		else:
			account.save(ignore_permissions=True)
	finally:
		frappe.local.flags.in_patch = previous_in_patch

	frappe.db.commit()
	return _safe_status(True, _("Configured Frappe outgoing Email Account for Gmail SMTP."))


@frappe.whitelist(methods=["GET"])
def gmail_smtp_status() -> dict:
	if frappe.session.user == "Guest":
		frappe.throw(_("Login is required to inspect SMTP configuration."), frappe.PermissionError)
	frappe.only_for("System Manager")

	account = frappe.db.get_value(
		"Email Account",
		{"enable_outgoing": 1, "default_outgoing": 1},
		["name", "email_id", "smtp_server", "smtp_port", "use_tls", "awaiting_password"],
		as_dict=True,
	)
	if not account:
		return _safe_status(False, _("No default outgoing Email Account is configured."))

	settings = _smtp_settings_from_env()
	return {
		"configured": True,
		"email_account": account.name,
		"sender": account.email_id,
		"host": account.smtp_server,
		"port": cint(account.smtp_port),
		"use_tls": bool(cint(account.use_tls)),
		"username_configured": bool(settings["username"]),
		"password_configured": bool(settings["password"]) and not cint(account.awaiting_password),
	}
