import frappe
from frappe import _
from frappe.permissions import add_user_permission
from frappe.utils import cint, cstr, now, validate_email_address

from firebase_admin import auth as firebase_auth

from hrms.api.firebase_auth import _get_firebase_admin_app


PROVISIONING_PENDING = "Pending"
PROVISIONING = "Provisioning"
PROVISIONED = "Provisioned"
PROVISIONING_FAILED = "Failed"
PROVISIONING_RETRY = "Retry Required"

INVITATION_NOT_GENERATED = "Not Generated"
INVITATION_GENERATED = "Generated"
INVITATION_QUEUED = "Queued"
INVITATION_SENT = "Sent"
INVITATION_FAILED = "Failed"
INVITATION_NOT_CONFIGURED = "Not Configured"
INVITATION_SKIPPED = "Already Queued"

INVITATION_TERMINAL_OR_ACTIVE = {INVITATION_QUEUED, INVITATION_SENT, INVITATION_SKIPPED}


def _set_employee_provisioning_state(
	employee: str,
	status: str,
	message: str | None = None,
	invitation_status: str | None = None,
	touch_timestamp: bool = False,
) -> None:
	values = {"firebase_provisioning_status": status}
	if message is not None:
		values["firebase_provisioning_message"] = message[:500]
	if invitation_status is not None:
		values["firebase_invitation_status"] = invitation_status
	if touch_timestamp:
		values["firebase_last_provisioned_on"] = now()

	frappe.db.set_value("Employee", employee, values, update_modified=False)


def _get_employee_login_email(employee) -> str:
	email = employee.prefered_email or employee.company_email or employee.personal_email or employee.user_id
	if not email:
		frappe.throw(_("A company or personal email is required to provision employee login."))

	return validate_email_address(email, True).lower()


def _validate_employee_email_is_available(employee_name: str, email: str) -> None:
	duplicate = frappe.db.sql(
		"""
		select name
		from `tabEmployee`
		where name != %(employee)s
			and status = 'Active'
			and (
				user_id = %(email)s
				or company_email = %(email)s
				or personal_email = %(email)s
				or prefered_email = %(email)s
			)
		limit 1
		""",
		{"employee": employee_name, "email": email},
		as_dict=True,
	)
	if duplicate:
		frappe.throw(
			_("Email {0} is already associated with active Employee {1}.").format(
				frappe.bold(email), frappe.bold(duplicate[0].name)
			),
			frappe.DuplicateEntryError,
		)


def _split_employee_name(employee):
	employee_name = (employee.employee_name or employee.name).split()
	first_name = employee_name[0] if employee_name else employee.name
	middle_name = ""
	last_name = ""
	if len(employee_name) >= 3:
		middle_name = employee_name[1]
		last_name = " ".join(employee_name[2:])
	elif len(employee_name) == 2:
		last_name = employee_name[1]

	return first_name, middle_name, last_name


def _ensure_employee_role(user) -> None:
	roles = {role.role for role in user.get("roles")}
	if "Employee" not in roles:
		user.append_roles("Employee")


def _ensure_frappe_user(employee, email: str):
	if employee.user_id:
		if not frappe.db.exists("User", employee.user_id):
			frappe.throw(_("Linked User {0} does not exist.").format(employee.user_id))
		user = frappe.get_doc("User", employee.user_id)
		if user.email and user.email.lower() != email:
			frappe.throw(
				_("Linked User {0} email does not match Employee login email {1}.").format(
					frappe.bold(user.name), frappe.bold(email)
				)
			)
	else:
		user = frappe.get_doc("User", email) if frappe.db.exists("User", email) else None
		if user:
			linked_employee = frappe.db.get_value(
				"Employee",
				{"user_id": user.name, "name": ("!=", employee.name), "status": "Active"},
				"name",
			)
			if linked_employee:
				frappe.throw(
					_("User {0} is already linked to active Employee {1}.").format(
						frappe.bold(user.name), frappe.bold(linked_employee)
					),
					frappe.DuplicateEntryError,
				)
		else:
			first_name, middle_name, last_name = _split_employee_name(employee)
			user = frappe.new_doc("User")
			user.update(
				{
					"email": email,
					"enabled": employee.status == "Active",
					"first_name": first_name,
					"middle_name": middle_name,
					"last_name": last_name,
					"gender": employee.gender,
					"birth_date": employee.date_of_birth,
					"phone": employee.cell_number,
					"bio": employee.bio,
					"send_welcome_email": 0,
				}
			)
			user.flags.ignore_permissions = True
			user.flags.no_welcome_mail = True
			user.insert(ignore_permissions=True)

		frappe.db.set_value("Employee", employee.name, "user_id", user.name, update_modified=False)
		employee.user_id = user.name

	user.enabled = employee.status == "Active"
	_ensure_employee_role(user)
	user.flags.ignore_permissions = True
	user.flags.no_welcome_mail = True
	user.save(ignore_permissions=True)

	if cint(employee.create_user_permission):
		if not frappe.db.exists("User Permission", {"user": user.name, "allow": "Employee", "for_value": employee.name}):
			add_user_permission("Employee", employee.name, user.name, ignore_permissions=True)
		if employee.company and not frappe.db.exists("User Permission", {"user": user.name, "allow": "Company", "for_value": employee.company}):
			add_user_permission("Company", employee.company, user.name, ignore_permissions=True)

	return user


def _get_existing_firebase_user_by_email(email: str):
	try:
		return firebase_auth.get_user_by_email(email)
	except firebase_auth.UserNotFoundError:
		return None


def _get_existing_firebase_user_by_uid(uid: str):
	try:
		return firebase_auth.get_user(uid)
	except firebase_auth.UserNotFoundError:
		return None


def _ensure_firebase_user(user, employee, email: str, password: str | None = None):
	_get_firebase_admin_app()

	if user.firebase_uid:
		firebase_user = _get_existing_firebase_user_by_uid(user.firebase_uid)
		if firebase_user:
			if firebase_user.email and firebase_user.email.lower() != email:
				frappe.throw(_("Mapped Firebase UID belongs to a different email address."))
		else:
			firebase_user = _get_existing_firebase_user_by_email(email)
	else:
		firebase_user = _get_existing_firebase_user_by_email(email)

	if not firebase_user:
		try:
			create_kwargs = {
				"email": email,
				"display_name": employee.employee_name,
				"disabled": employee.status != "Active",
				"email_verified": True,
				"password": password or "Employee@123",
			}
			firebase_user = firebase_auth.create_user(**create_kwargs)
		except firebase_auth.EmailAlreadyExistsError:
			firebase_user = firebase_auth.get_user_by_email(email)
		except Exception:
			# If password policy fails or other issue, retry without password
			firebase_user = firebase_auth.create_user(
				email=email,
				display_name=employee.employee_name,
				disabled=employee.status != "Active",
				email_verified=True,
			)
		except firebase_auth.EmailAlreadyExistsError:
			firebase_user = firebase_auth.get_user_by_email(email)

	uid_owner = frappe.db.get_value("User", {"firebase_uid": firebase_user.uid}, "name")
	if uid_owner and uid_owner != user.name:
		frappe.throw(
			_("Firebase UID is already mapped to another Frappe User {0}.").format(
				frappe.bold(uid_owner)
			),
			frappe.DuplicateEntryError,
		)

	if user.firebase_uid != firebase_user.uid:
		user.db_set("firebase_uid", firebase_user.uid, update_modified=False)
		user.firebase_uid = firebase_user.uid

	if firebase_user.disabled != (employee.status != "Active"):
		firebase_user = firebase_auth.update_user(
			firebase_user.uid, disabled=employee.status != "Active"
		)

	return firebase_user


def _get_existing_mapped_firebase_user(user, email: str):
	_get_firebase_admin_app()

	if user.get("firebase_uid"):
		firebase_user = _get_existing_firebase_user_by_uid(user.firebase_uid)
		if firebase_user:
			if firebase_user.email and firebase_user.email.lower() != email:
				frappe.throw(_("Mapped Firebase UID belongs to a different email address."))
			return firebase_user

	firebase_user = _get_existing_firebase_user_by_email(email)
	if not firebase_user:
		frappe.throw(_("Firebase account does not exist for {0}. Provision the employee first.").format(email))

	uid_owner = frappe.db.get_value("User", {"firebase_uid": firebase_user.uid}, "name")
	if uid_owner and uid_owner != user.name:
		frappe.throw(
			_("Firebase UID is already mapped to another Frappe User {0}.").format(
				frappe.bold(uid_owner)
			),
			frappe.DuplicateEntryError,
		)

	if user.firebase_uid != firebase_user.uid:
		user.db_set("firebase_uid", firebase_user.uid, update_modified=False)
		user.firebase_uid = firebase_user.uid

	return firebase_user


def _get_latest_invitation_queue_status(employee_name: str) -> str | None:
	queue = frappe.db.get_value(
		"Email Queue",
		{
			"reference_doctype": "Employee",
			"reference_name": employee_name,
		},
		["name", "status"],
		order_by="creation desc",
		as_dict=True,
	)
	if not queue:
		return None

	if queue.status == "Sent":
		return INVITATION_SENT
	if queue.status in ("Not Sent", "Sending", "Partially Sent"):
		return INVITATION_QUEUED
	if queue.status == "Error":
		return INVITATION_FAILED

	return None


def _sync_invitation_status_from_email_queue(employee) -> str:
	queue_status = _get_latest_invitation_queue_status(employee.name)
	if queue_status and queue_status != employee.get("firebase_invitation_status"):
		frappe.db.set_value(
			"Employee",
			employee.name,
			"firebase_invitation_status",
			queue_status,
			update_modified=False,
		)
		employee.firebase_invitation_status = queue_status

	return employee.get("firebase_invitation_status") or INVITATION_NOT_GENERATED


def _invitation_message(employee, user, email: str, link: str) -> str:
	display_name = employee.employee_name or user.full_name or user.name
	return _(
		"""
		<p>Hello {0},</p>
		<p>Welcome to HRMS. Your employee login has been created for <strong>{1}</strong>.</p>
		<p>Use the secure link below to set your Firebase password, then sign in to HRMS with your email address.</p>
		<p><a href="{2}">Set up your HRMS password</a></p>
		<p>This link is personal to you. Do not share it with anyone.</p>
		"""
	).format(display_name, email, link)


def _queue_firebase_invitation(user, employee, email: str, force: bool = False) -> str:
	current_status = _sync_invitation_status_from_email_queue(employee)
	if not force and current_status in INVITATION_TERMINAL_OR_ACTIVE:
		return current_status

	try:
		link = firebase_auth.generate_password_reset_link(email)
	except Exception:
		frappe.logger("employee_provisioning").warning("Could not generate Firebase setup link")
		return INVITATION_FAILED

	try:
		frappe.sendmail(
			recipients=email,
			subject=_("Set up your HRMS login"),
			message=_invitation_message(employee, user, email, link),
			reference_doctype="Employee",
			reference_name=employee.name,
			delayed=True,
			retry=3,
			redact_message_after_send=True,
		)
		return INVITATION_QUEUED
	except frappe.OutgoingEmailError:
		frappe.clear_last_message()
		frappe.log_error(
			message="No configured outgoing email account was available for Employee invitation.",
			title="Firebase invitation email not configured",
		)
		return INVITATION_NOT_CONFIGURED
	except Exception:
		frappe.log_error(
			message="Employee invitation email could not be queued.",
			title="Firebase invitation email failed",
		)
		return INVITATION_FAILED


def provision_employee_login(
	employee: str,
	send_invitation: int = 1,
	ignore_permissions: bool = False,
	password: str | None = None,
):
	employee_doc = frappe.get_doc("Employee", employee)
	if not ignore_permissions:
		employee_doc.check_permission("write")

	if employee_doc.get("firebase_provisioning_status") == PROVISIONED and employee_doc.user_id:
		user = frappe.get_doc("User", employee_doc.user_id)
		if user.get("firebase_uid"):
			invitation_status = _sync_invitation_status_from_email_queue(employee_doc)
			return {
				"status": PROVISIONED,
				"employee": employee_doc.name,
				"user": user.name,
				"firebase_uid": user.firebase_uid,
				"invitation_status": invitation_status,
			}

	_set_employee_provisioning_state(
		employee_doc.name,
		PROVISIONING,
		_("Provisioning employee login."),
		employee_doc.get("firebase_invitation_status") or INVITATION_NOT_GENERATED,
	)

	try:
		email = _get_employee_login_email(employee_doc)
		_validate_employee_email_is_available(employee_doc.name, email)
		user = _ensure_frappe_user(employee_doc, email)
		firebase_user = _ensure_firebase_user(user, employee_doc, email)
		firebase_user = _ensure_firebase_user(user, employee_doc, email, password=password)
		try:
			from firebase_admin import firestore
			fs = firestore.client()
			fs.collection("users").document(firebase_user.uid).set({
				"email": email,
				"name": employee_doc.employee_name or employee_doc.name,
				"role": "Employee",
				"is_admin": False,
			}, merge=True)
		except Exception:
			frappe.logger("employee_provisioning").warning(
				"Firestore sync failed for %s", employee_doc.name
			)
		invitation_status = (
			_queue_firebase_invitation(user, employee_doc, email)
			if cint(send_invitation)
			else INVITATION_NOT_GENERATED
		)
	except Exception as error:
		message = cstr(error)
		frappe.clear_messages()
		_set_employee_provisioning_state(
			employee_doc.name,
			PROVISIONING_RETRY,
			message or _("Provisioning failed and can be retried."),
			INVITATION_FAILED,
		)
		return {
			"status": PROVISIONING_RETRY,
			"employee": employee_doc.name,
			"user": employee_doc.user_id,
			"firebase_uid": None,
			"invitation_status": INVITATION_FAILED,
			"message": message,
		}

	final_status = (
		PROVISIONED
		if not cint(send_invitation)
		or invitation_status in (INVITATION_QUEUED, INVITATION_SENT, INVITATION_SKIPPED)
		else PROVISIONING_RETRY
	)
	final_message = (
		_("Employee login provisioned with Firebase UID {0}.").format(firebase_user.uid)
		if final_status == PROVISIONED
		else _("Employee login was provisioned, but the invitation email needs attention.")
	)

	_set_employee_provisioning_state(
		employee_doc.name,
		final_status,
		final_message,
		invitation_status,
		touch_timestamp=True,
	)

	return {
		"status": final_status,
		"employee": employee_doc.name,
		"user": user.name,
		"firebase_uid": firebase_user.uid,
		"invitation_status": invitation_status,
	}


def resend_employee_invitation(employee: str, ignore_permissions: bool = False):
	employee_doc = frappe.get_doc("Employee", employee)
	if not ignore_permissions:
		employee_doc.check_permission("write")

	try:
		email = _get_employee_login_email(employee_doc)
		if not employee_doc.user_id:
			frappe.throw(_("Employee must be provisioned before resending an invitation."))

		user = frappe.get_doc("User", employee_doc.user_id)
		firebase_user = _get_existing_mapped_firebase_user(user, email)
		invitation_status = _queue_firebase_invitation(user, employee_doc, email, force=True)
	except Exception as error:
		message = cstr(error)
		frappe.clear_messages()
		_set_employee_provisioning_state(
			employee_doc.name,
			PROVISIONING_RETRY,
			message or _("Invitation resend failed and can be retried."),
			INVITATION_FAILED,
		)
		return {
			"status": PROVISIONING_RETRY,
			"employee": employee_doc.name,
			"user": employee_doc.user_id,
			"firebase_uid": None,
			"invitation_status": INVITATION_FAILED,
			"message": message,
		}

	status = PROVISIONED if invitation_status in (INVITATION_QUEUED, INVITATION_SENT) else PROVISIONING_RETRY
	_set_employee_provisioning_state(
		employee_doc.name,
		status,
		_("Invitation resend requested for {0}.").format(email),
		invitation_status,
		touch_timestamp=status == PROVISIONED,
	)

	return {
		"status": status,
		"employee": employee_doc.name,
		"user": user.name,
		"firebase_uid": firebase_user.uid,
		"invitation_status": invitation_status,
	}


@frappe.whitelist(methods=["POST"])
def provision_employee(employee: str, send_invitation: int = 1):
	if frappe.session.user == "Guest":
		frappe.throw(_("Login is required to provision employee login."), frappe.PermissionError)

	return provision_employee_login(employee, send_invitation=send_invitation)


@frappe.whitelist(methods=["POST"])
def resend_invitation(employee: str):
	if frappe.session.user == "Guest":
		frappe.throw(_("Login is required to resend employee invitation."), frappe.PermissionError)

	return resend_employee_invitation(employee)
