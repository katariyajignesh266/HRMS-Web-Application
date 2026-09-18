# Frappe HRMS — Customized, Portable & Reproducible Docker Environment

> A customized Frappe HRMS development environment with Docker Desktop portability, Firebase Authentication integration, automatic Employee account provisioning, Gmail SMTP invitations, persistent database/site storage, backup/restore support, and verified local employee/admin flows.

This repository is based on the open-source **Frappe HRMS** project and contains project-specific changes made for the HRMS development environment.

Repository: https://github.com/katariyajignesh266/HRMS-Web-Application  
Development branch: `hrms-development`

---

## What Was Customized

The upstream Frappe HRMS application was extended rather than replaced. The main project work is concentrated around deployment portability, authentication, employee identity provisioning, email delivery, and local development reliability.

### Major customizations

- Portable Docker environment for Windows + Docker Desktop.
- Persistent MariaDB and Frappe Bench Docker volumes.
- Automated first-run site/bench bootstrap.
- Optional sanitized seed backup restoration.
- PowerShell lifecycle, backup and restore tooling.
- Firebase Authentication integration using Firebase Admin SDK.
- Secure Firebase ID-token verification on the server.
- Firebase UID mapping through a custom `User.firebase_uid` field.
- Firebase identity mapped to Frappe System Users.
- Automatic Employee creation/linking when required by the Firebase login flow.
- Employee-to-Frappe-User-to-Firebase account provisioning.
- Idempotent provisioning and retry handling.
- Employee provisioning status and invitation status fields.
- `Provision Firebase Login` action from the Employee form.
- `Resend Firebase Invitation` action from the Employee form.
- Firebase password setup/reset-link generation.
- Frappe Email Queue integration.
- Gmail SMTP configuration from environment variables.
- SMTP status reporting for System Managers without exposing credentials.
- Firestore user-profile synchronization during Employee provisioning.
- Frontend support for the HRMS employee application under the `/hrms` route.
- Docker-compatible frontend asset build using Vite.
- Persistent developer mode, scheduler and migration handling.
- Explicit protection against accidentally recreating or overwriting an incomplete/persistent site.
- End-to-end authentication and Employee provisioning verification.

---

## Architecture

The customized system keeps **Frappe/MariaDB as the HRMS source of truth**.

Firebase is used for authentication and identity integration; it is not the primary HRMS database.

```text
                    ┌─────────────────────────┐
                    │       Employee          │
                    │    Email + Password     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Firebase Authentication │
                    │   Identity / ID Token   │
                    └────────────┬────────────┘
                                 │
                         Firebase ID Token
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Frappe Firebase API     │
                    │ Admin SDK verification  │
                    └────────────┬────────────┘
                                 │
                      UID / verified email
                                 │
                                 ▼
              ┌────────────────────────────────────┐
              │       Frappe User / Employee      │
              │                                    │
              │ User.firebase_uid                   │
              │ Employee.user_id                    │
              │ Employee permissions                │
              └────────────────┬───────────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │       MariaDB           │
                    │ HRMS source of truth    │
                    └─────────────────────────┘
```

### Employee provisioning flow

```text
Employee created/selected
        │
        ▼
Validate employee login email
        │
        ▼
Create or reuse Frappe User
        │
        ▼
Create or reuse Firebase User
        │
        ▼
Store Firebase UID on User
        │
        ▼
Link Employee.user_id
        │
        ▼
Sync Employee identity to Firebase/Firestore
        │
        ▼
Generate Firebase password setup link
        │
        ▼
Frappe Email Queue
        │
        ▼
Gmail SMTP
        │
        ▼
Employee mailbox
```

---

## Quick Start — Windows + Docker Desktop

### Requirements

- Windows 10/11
- Docker Desktop
- Git
- VS Code recommended
- Internet connection for the first Docker bootstrap

### First-time setup

Clone the development branch:

```powershell
git clone -b hrms-development https://github.com/katariyajignesh266/HRMS-Web-Application.git hrms
cd hrms
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

For a normal development environment, configure the required local Firebase and SMTP secrets in `.env`.

Then start the environment:

```powershell
docker compose --env-file .env -f docker/docker-compose.yml up -d
```

Follow the Frappe container logs:

```powershell
docker compose --env-file .env -f docker/docker-compose.yml logs -f frappe
```

The first bootstrap can take several minutes because the Frappe bench, ERPNext dependencies, HRMS assets and required Python/Node packages may need to be initialized.

---

## Verified Local Access

Only the main Frappe Desk/Admin entry point is listed here intentionally.

### Frappe Desk / Admin

**http://localhost:8000/app**

Use this entry point for administration, Employee management, HRMS configuration and role-based access.

### Default Administrator

```text
Username: Administrator
Password: admin
```

The password is controlled by `FRAPPE_ADMIN_PASSWORD` in `.env` and should be changed for any non-disposable environment.

---

## Employee Testing Account

A dedicated Employee account was used during development to verify the Employee login and dashboard flow.

**Do not commit the real Employee email address or password to a public GitHub README.**

For local testing, keep the credentials in your private `.env`, team documentation, password manager, or another private channel:

```text
Employee email: katariyajignesh266@gmail.com
Employee password: jignesh&777J
Role: Employee
```

The Employee account is intended to verify:

- Email/password authentication.
- Firebase authentication.
- Firebase-to-Frappe identity mapping.
- Employee/User association.
- Employee role permissions.
- Employee dashboard access.
- Attendance/leave/expense/salary self-service areas exposed to the Employee role.
- Logout and subsequent login.
- Session creation after Firebase token verification.

**Important:** never place a real password, Firebase Admin private key, Gmail App Password, or other secret in `README.md`, source code, or Git history.

---

## Authentication Design

### Firebase Authentication

The customized authentication flow uses:

- Firebase Web configuration for client initialization.
- Firebase Admin SDK on the Frappe server.
- Firebase ID tokens as the authentication hand-off.
- `User.firebase_uid` as the optional primary identity mapping.
- Verified Firebase email as the fallback mapping mechanism.
- Native Frappe session creation after successful verification.

The server verifies Firebase tokens before creating the Frappe session.

The authentication flow is:

```text
1. Employee signs in with Firebase
2. Firebase returns an ID token
3. Token is sent to Frappe
4. Firebase Admin SDK verifies the token
5. UID/email is mapped to a Frappe User
6. Frappe verifies that the User is enabled
7. Frappe verifies System User access
8. Employee identity is ensured/mapped
9. Frappe creates the normal session
10. HRMS permissions control subsequent requests
```

Firebase passwords are not passed to the Frappe HRMS database.

### Server-side verification

The server verifies:

- Token validity.
- Expiration.
- Revocation.
- Firebase identity.
- UID mapping.
- Verified email fallback.
- Enabled Frappe User state.
- System User type.

Invalid, expired, revoked, disabled or unmapped accounts are rejected.

---

## Firebase Configuration

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Configure the Firebase Web values locally:

```dotenv
FIREBASE_API_KEY=your-web-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_APP_ID=your-web-app-id
FIREBASE_UID_FIELD=firebase_uid
```

Configure Firebase Admin credentials using one of the supported local-only mechanisms:

```dotenv
FIREBASE_ADMIN_CREDENTIALS_JSON={"type":"service_account",...}
```

or:

```dotenv
FIREBASE_ADMIN_CREDENTIALS_FILE=/run/secrets/firebase-admin.json
```

Admin credentials are server-side secrets and must never be committed.

---

## Employee Provisioning

The Employee provisioning implementation is designed to be **idempotent**.

When an Employee needs an application login, the system can:

1. Validate the Employee login email.
2. Create or reuse the Frappe System User.
3. Assign the Employee role.
4. Link `Employee.user_id`.
5. Create or reuse the Firebase Authentication account.
6. Store the Firebase UID on `User.firebase_uid`.
7. Prevent the same Firebase UID from being mapped to another User.
8. Synchronize the Employee identity to the Firebase/Firestore user document.
9. Generate a Firebase password setup link.
10. Queue the invitation through Frappe Email Queue.

Existing users are reconciled instead of duplicated.

### Employee form actions

The Employee form provides:

- **Provision Firebase Login**
- **Resend Firebase Invitation**

These actions use authenticated server-side endpoints and respect Employee write permissions.

### Provisioning states

Employee provisioning tracks state so failures can be retried rather than leaving the Employee in an unknown state.

Typical states include:

```text
Pending
Provisioning
Provisioned
Failed
Retry Required
```

The Employee record also tracks invitation status, last provisioning time and provisioning messages.

---

## Gmail SMTP Integration

The customized environment can configure Frappe's default outgoing Email Account from environment variables.

Example:

```dotenv
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-project-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_USE_TLS=true
SMTP_SENDER=your-project-email@gmail.com
```

Use a dedicated development/project Gmail account and a Gmail App Password.

Do not use a normal Gmail account password.

The resulting flow is:

```text
Employee Provisioning
        ↓
Firebase password setup link
        ↓
Frappe Email Queue
        ↓
Gmail SMTP
        ↓
Employee mailbox
```

The application tracks invitation states such as:

- Not Generated
- Generated
- Queued
- Sent
- Failed
- Not Configured
- Already Queued

Provisioning retries do not intentionally create duplicate accounts or unlimited duplicate invitations.

A separate resend action is available when a new invitation must be generated.

---

## Custom API Components

### Firebase authentication

`hrms.api.firebase_auth`

Provides:

- Firebase configuration retrieval.
- Firebase Admin SDK initialization.
- Firebase ID-token verification.
- Firebase-to-Frappe User mapping.
- Employee identity assurance.
- Frappe session creation.
- Firebase configuration/status responses.

Important methods:

```text
login_with_firebase_token
firebase_config
firebase_status
```

### Employee provisioning

`hrms.api.employee_provisioning`

Provides:

```text
provision_employee
resend_invitation
provision_employee_login
resend_employee_invitation
```

The implementation handles existing Frappe Users, existing Firebase Users, UID conflicts, Employee linking, invitation status and retryable failures.

### SMTP configuration

`hrms.api.smtp_config`

Provides:

```text
configure_gmail_smtp_from_env
gmail_smtp_status
```

The status endpoint is restricted to System Managers and does not expose SMTP passwords.

---

## Database / Custom Field Changes

The development branch adds migration patches for the Firebase integration.

Relevant patches include:

```text
hrms.patches.v16_0.create_firebase_uid_field_in_user
hrms.patches.v16_0.create_employee_firebase_provisioning_fields
hrms.patches.v16_0.update_employee_invitation_status_options
```

The custom User field:

```text
User.firebase_uid
```

is used to associate a Firebase identity with the corresponding Frappe User.

Employee records receive Firebase provisioning/invitation state fields so that the integration remains observable and retryable.

---

## Docker Environment

The Docker setup uses:

- Frappe Bench
- Frappe Framework
- ERPNext
- Frappe HRMS
- MariaDB
- Redis

Persistent state is kept in named Docker volumes.

### Persistent volumes

```text
${HRMS_VOLUME_PREFIX}_mariadb-data
${HRMS_VOLUME_PREFIX}_frappe-bench
```

With the default configuration:

```text
docker_mariadb-data
docker_frappe-bench
```

The MariaDB volume contains HRMS database records.

The Frappe Bench volume contains the Bench installation, sites, configuration and uploaded files.

This design avoids relying on machine-specific absolute paths.

---

## Docker Bootstrap Behaviour

The custom initialization script performs the following tasks:

1. Detects or initializes the Frappe Bench.
2. Configures MariaDB and Redis to use Docker service names.
3. Installs ERPNext when required.
4. Links the customized HRMS application into the Bench.
5. Installs the Firebase Admin SDK when required.
6. Installs frontend dependencies when required.
7. Creates or restores the Frappe site.
8. Installs HRMS if required.
9. Builds HRMS frontend assets.
10. Runs migrations when required.
11. Configures Gmail SMTP when credentials are present.
12. Enables developer mode.
13. Enables the scheduler.
14. Clears cache.
15. Starts the Frappe development server.

The initialization is designed to be repeatable without destroying existing persistent data.

---

## Daily Development Commands

From the repository root:

### Start

```powershell
docker compose --env-file .env -f docker/docker-compose.yml start
```

### Stop

```powershell
docker compose --env-file .env -f docker/docker-compose.yml stop
```

### Restart

```powershell
docker compose --env-file .env -f docker/docker-compose.yml restart
```

### Recreate containers without deleting volumes

```powershell
docker compose --env-file .env -f docker/docker-compose.yml up -d --force-recreate
```

### View Frappe logs

```powershell
docker compose --env-file .env -f docker/docker-compose.yml logs -f frappe
```

---

## Data Safety

Do **not** use this for normal development:

```powershell
docker compose down -v
```

The `-v` option removes named volumes and can destroy the local MariaDB database and persistent Frappe site state.

Normal development should use:

```text
stop
start
restart
up -d --force-recreate
```

Persistent volumes should only be removed when a deliberately destructive reset is required.

---

## Backup

Create a database/site-files backup:

```powershell
cd docker
.\backup.ps1
```

Backups are stored outside normal source files under:

```text
.backups/
```

The backup process uses Frappe's site backup mechanism with database and site files.

### Seed backup

For a clean development/demo environment:

```powershell
cd docker
.\backup.ps1 -Seed
```

Only sanitized demo data should be committed.

Never commit:

- Real employee records.
- Firebase Admin credentials.
- Service-account private keys.
- Gmail App Passwords.
- SMTP passwords.
- Production backups.
- Private uploaded employee files.

---

## Restore

Restore only into a disposable validation site.

Example:

```powershell
.\restore.ps1 ..\.backups\<backup-directory> -TargetSite hrms.restore.localhost
```

The restore script intentionally refuses to overwrite the normal development site.

---

## Frontend

The HRMS employee interface uses the existing Frappe HR frontend stack with:

- Vue 3
- Vite
- Ionic Vue
- Frappe UI
- Tailwind CSS
- Firebase Web SDK
- Vite PWA tooling

The frontend build command is:

```bash
yarn build
```

The build is configured for the Frappe asset path and generates the HRMS web entry point.

The router uses:

```text
createWebHistory("/hrms")
```

so the employee application remains compatible with the Frappe HRMS route structure.

---

## Employee Experience

The customized Employee application provides access to the HR self-service areas supported by the Employee role, including:

- Employee home/dashboard.
- Attendance.
- Leave management.
- Expense claims.
- Salary slips.
- Employee profile.
- Notifications.
- Settings.
- Password management.
- Other role-authorized HRMS features.

Actual access is controlled by Frappe roles and permissions rather than by Firebase alone.

---

## Authentication and Authorization Separation

A deliberate design decision in this project is to separate identity from authorization.

### Firebase

Responsible for:

- Email/password identity.
- Firebase UID.
- ID-token issuance.
- Authentication state.

### Frappe / MariaDB

Responsible for:

- Employee records.
- Frappe Users.
- Roles.
- Permissions.
- Companies.
- HRMS transactions.
- Employee-to-User relationships.
- Business data.

This keeps HRMS authorization under Frappe even when Firebase is used for authentication.

---

## Testing & Verification

The customized environment was tested through multiple layers.

### Docker / infrastructure verification

Verified:

- Docker containers start successfully.
- MariaDB becomes healthy.
- Redis becomes healthy.
- Frappe responds after startup.
- Persistent volumes survive container recreation.
- Existing site state is reused.
- Fresh environments can bootstrap the site.
- Frontend assets can be built inside the container.
- Migrations execute successfully.

### Firebase verification

Verified:

- Firebase configuration can be loaded.
- Firebase Admin SDK initializes.
- Valid Firebase ID tokens can be verified.
- Missing tokens are rejected.
- Invalid tokens are rejected.
- Expired/revoked/disabled identities are rejected.
- Unmapped Firebase users are rejected.
- Firebase UID mapping works.
- Verified-email fallback mapping works.
- Frappe sessions are created after successful verification.
- Logout/session invalidation behaviour was tested.

### Employee provisioning verification

Verified:

- Employee login email validation.
- Frappe User creation/reuse.
- Employee role assignment.
- Employee.user_id linking.
- Firebase User creation/reuse.
- Firebase UID persistence.
- Duplicate prevention.
- Firebase/Firestore user synchronization.
- Provisioning retry behaviour.
- Invitation generation.
- Invitation queueing.
- Invitation resend.
- Provisioning status updates.

### Gmail SMTP verification

Verified:

- Gmail SMTP configuration can be loaded from environment variables.
- Frappe outgoing Email Account can be created/updated.
- SMTP credentials are not exposed through the status response.
- Firebase setup links can be generated.
- Invitation emails enter the Frappe Email Queue.
- Queue status can be reflected on the Employee record.

### Employee end-to-end verification

The final Employee flow was verified from authentication through HRMS access:

```text
Employee credentials
        ↓
Firebase authentication
        ↓
Firebase ID token
        ↓
Frappe server verification
        ↓
Frappe User mapping
        ↓
Employee mapping
        ↓
Frappe session
        ↓
Employee dashboard
        ↓
Role-based HRMS access
```

The development verification also covered successful login, protected endpoints, logout, rejection of invalid sessions, disabled-user handling and cleanup.

---

## Troubleshooting

### Port already in use

If the default ports are occupied, change the host ports in `.env`:

```dotenv
HRMS_WEB_PORT=8081
HRMS_SOCKETIO_PORT=9001
```

Then recreate the containers:

```powershell
docker compose --env-file .env -f docker/docker-compose.yml up -d --force-recreate
```

### Frappe is still starting

Check:

```powershell
docker compose --env-file .env -f docker/docker-compose.yml logs -f frappe
```

The first initialization can take several minutes.

### Firebase login fails

Check, in order:

1. Firebase Web configuration.
2. Firebase Admin credentials.
3. Firebase Email/Password authentication.
4. Firebase user existence.
5. Frappe User existence/enabled state.
6. `User.firebase_uid` mapping.
7. Employee.user_id mapping.
8. Frappe System User type.
9. Browser console/network errors.
10. Frappe container logs.

### Employee provisioning fails

Check:

- Employee has a valid login email.
- Employee is active.
- Firebase Admin credentials are configured.
- Firebase project is reachable.
- Frappe User is not already linked to another active Employee.
- Firebase UID is not mapped to another Frappe User.
- Default Company exists when automatic Employee creation is required.
- SMTP is configured when an invitation is expected.

Provisioning is designed to be retryable.

### Invitation email is not received

Check:

1. Gmail 2-Step Verification.
2. Gmail App Password.
3. SMTP username/password in `.env`.
4. Frappe default outgoing Email Account.
5. Frappe Email Queue.
6. SMTP status from a System Manager account.
7. Gmail delivery/spam filtering.

A queued message is not the same as confirmed mailbox delivery.

---

## Project Structure

Important customized areas:

```text
HRMS-Web-Application/
├── docker/
│   ├── docker-compose.yml
│   ├── entrypoint.sh
│   ├── init.sh
│   ├── backup.ps1
│   ├── restore.ps1
│   └── seed/
│
├── frontend/
│   ├── src/
│   └── package.json
│
├── hrms/
│   ├── api/
│   │   ├── firebase_auth.py
│   │   ├── employee_provisioning.py
│   │   └── smtp_config.py
│   │
│   ├── patches/
│   │   └── v16_0/
│   │       ├── create_firebase_uid_field_in_user.py
│   │       ├── create_employee_firebase_provisioning_fields.py
│   │       └── update_employee_invitation_status_options.py
│   │
│   ├── public/
│   │   └── js/
│   │       └── erpnext/
│   │           └── employee.js
│   │
│   └── hooks.py
│
├── .env.example
└── README.md
```

---

## Parent Project Integration

The HRMS component is designed to remain portable when placed inside a larger project:

```text
MAIN_PROJECT/
├── frontend/
├── backend/
├── other-components/
└── HRMS/
```

The Docker setup avoids machine-specific absolute paths and supports configurable host ports.

If another service already uses the default host ports, change the HRMS host-port variables in `.env`.

The HRMS Docker network and named volumes are isolated from unrelated projects through the Compose project configuration and volume naming.

---

## Development Principles

1. **Frappe/MariaDB remains the HRMS source of truth.**
2. **Firebase is an authentication/identity layer, not the HRMS database.**
3. **Provisioning is idempotent.**
4. **External-service failures are represented as retryable state.**
5. **Secrets are provided through local environment configuration.**
6. **Persistent Docker volumes are preserved during normal lifecycle operations.**
7. **Backups are treated separately from source code.**
8. **Frappe roles and permissions remain authoritative for HRMS authorization.**
9. **Employee Firebase actions require authenticated Frappe access and appropriate permissions.**
10. **Production credentials and real employee data must never be committed to the repository.**

---

## Git Workflow

The customized work is maintained on:

```text
hrms-development
```

Before pushing development changes:

```powershell
git status
git diff
git add .
git commit -m "Describe the change"
git push origin hrms-development
```

Do not force-push or rewrite shared development history.

When updating an existing environment, prefer migrations and container recreation that preserve named volumes rather than destroying the database.

---

## Source Project

This repository is derived from the open-source **Frappe HRMS** project.

Upstream project:

https://github.com/frappe/hrms

Frappe Framework:

https://github.com/frappe/frappe

Frappe UI:

https://github.com/frappe/frappe-ui

Official Frappe HR documentation:

https://docs.frappe.io/hr/introduction

The upstream project remains the foundation; this branch contains project-specific Docker, authentication, provisioning, SMTP, frontend and development-environment changes.

---

## Security Notes

This is a development environment.

Never commit:

```text
.env
Firebase Admin service-account JSON
Firebase private keys
Gmail App Passwords
SMTP passwords
Real employee passwords
Production database backups
Private employee files
```

If a credential has ever been committed accidentally, rotate the credential instead of relying on deletion from the latest commit.

For a public repository, test credentials should be documented as placeholders rather than real passwords.

---

## Current Status

The customized development environment has been exercised through:

- Docker bootstrap.
- Persistent database/site storage.
- Firebase Admin initialization.
- Firebase token verification.
- Frappe User mapping.
- Employee provisioning.
- Firebase UID persistence.
- Firestore synchronization.
- Gmail SMTP configuration.
- Email Queue invitation handling.
- Invitation resend.
- Employee login.
- Employee dashboard access.
- Protected-route checks.
- Logout/session invalidation.
- Disabled-user rejection.
- Retry and duplicate-prevention scenarios.

The repository is intended to provide a reproducible development setup while preserving the standard Frappe HRMS architecture and permission model.
