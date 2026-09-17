# Frappe HRMS — Portable & Reproducible Docker Environment

> **One-Command Setup for Any Windows Laptop with Docker Desktop & VS Code**

```powershell
# 1. Clone repository
git clone <repository-url> hrms
cd hrms

# 2. Run automated setup (pre-checks Docker, configures .env, restores seed database, launches services)
.\setup.ps1
```

---

## Verified Local URLs

| Service                 | Local URL                                                                                                                                              | Notes                                          |
| :---------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------- |
| **MAIN HRMS URL**       | **[http://localhost:8000/hrms](http://localhost:8000/hrms)**                                                                                           | Primary Employee & HR Self-Service Portal      |
| **Frappe Desk / Admin** | **[http://localhost:8000/app](http://localhost:8000/app)**                                                                                             | Frappe Framework & ERPNext Management Desk     |
| **Firebase Status API** | **[http://localhost:8000/api/method/hrms.api.firebase_auth.firebase_status](http://localhost:8000/api/method/hrms.api.firebase_auth.firebase_status)** | Health endpoint for Firebase Auth integration  |
| **Socket.IO Realtime**  | `http://localhost:9000`                                                                                                                                | Realtime push notification & WebSocket gateway |

**Default Admin Credentials:**

- **Username:** `Administrator`
- **Password:** `admin`

---

## Daily PowerShell Workflow Commands

From the repository root (or inside `.\scripts\`):

| Command         | Action                                                         | Data Safety                               |
| :-------------- | :------------------------------------------------------------- | :---------------------------------------- |
| `.\setup.ps1`   | First-time automated bootstrap & verification                  | Idempotent; preserves existing volumes    |
| `.\start.ps1`   | Starts containers & verifies availability                      | Safe; fast startup                        |
| `.\stop.ps1`    | Stops containers                                               | Safe; preserves all persistent volumes    |
| `.\restart.ps1` | Restarts all containers cleanly                                | Safe; preserves all data                  |
| `.\status.ps1`  | Live container health, open ports & DB counts                  | Read-only diagnostic check                |
| `.\logs.ps1`    | View logs (`.\logs.ps1 -Follow` or `-Service frappe`)          | Read-only log viewer                      |
| `.\update.ps1`  | Rebuilds changed layers & runs safe migrations                 | Preserves database; runs `bench migrate`  |
| `.\backup.ps1`  | Creates on-demand backup in `.backups/` (`-Seed` updates seed) | Safe; creates snapshot                    |
| `.\restore.ps1` | Restores snapshot from backup directory                        | Interactive confirmation before overwrite |
| `.\reset.ps1`   | Completely destroys containers & volumes                       | Destructive; requires typing `RESET`      |

---

<div align="center">
	<a href="https://frappe.io/hr">
		<img src=".github/frappe-hr-logo.png" height="80px" width="80px" alt="Frappe HR Logo">
	</a>
	<h2>Frappe HR</h2>
	<p align="center">
		<p>Open Source, modern, and easy-to-use HR and Payroll Software</p>
	</p>

[![CI](https://github.com/frappe/hrms/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/frappe/hrms/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/frappe/hrms/branch/develop/graph/badge.svg?token=0TwvyUg3I5)](https://codecov.io/gh/frappe/hrms)

<a href="https://trendshift.io/repositories/10972" target="_blank"><img src="https://trendshift.io/api/badge/repositories/10972" alt="frappe%2Fhrms | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

</div>

<div align="center">
	<img src=".github/hrms-hero.png"/>
</div>

<div align="center">
	<a href="https://frappe.io/hr">Website</a>
	-
	<a href="https://docs.frappe.io/hr/introduction">Documentation</a>
</div>

## Frappe HR

Frappe HR has everything you need to drive excellence within the company. It's a complete HRMS solution with over 13 different modules right from Employee Management, Onboarding, Leaves, to Payroll, Taxation, and more!

## Motivation

When Frappe team started growing in terms of size, we needed an open-source HR and Payroll software. We didn't find any "true" open-source HR software out there and so decided to build one ourselves.
Initially, it was a set of modules within ERPNext but version 14 onwards, as the modules became more mature, Frappe HR was created as a separate product.

## Key Features

- **Employee Lifecycle**: From onboarding employees, managing promotions and transfers, all the way to documenting feedback with exit interviews, make life easier for employees throughout their life cycle.
- **Leave and Attendance**: Configure leave policies, pull regional holidays with a click, check-in and check-out with geolocation capturing, track leave balances and attendance with reports.
- **Expense Claims and Advances**: Manage employee advances, claim expenses, configure multi-level approval workflows, all this with seamless integration with ERPNext accounting.
- **Performance Management**: Track goals, align goals with key result areas (KRAs), enable employees to evaluate themselves, make managing appraisal cycles easy.
- **Payroll & Taxation**: Create salary structures, configure income tax slabs, run standard payroll, accommodate additional salaries and off cycle payments, view income breakup on salary slips and so much more.
- **Frappe HR Mobile App**: Apply for and approve leaves on the go, check-in and check-out, access employee profile right from the mobile app.

<details open>

<summary>View Screenshots</summary>
	<img src=".github/hrms-appraisal.png"/>
	<img src=".github/hrms-requisition.png"/>
	<img src=".github/hrms-attendance.png"/>
	<img src=".github/hrms-salary.png"/>
	<img src=".github/hrms-pwa.png"/>
</details>

### Under the Hood

- [**Frappe Framework**](https://github.com/frappe/frappe): A full-stack web application framework written in Python and Javascript. The framework provides a robust foundation for building web applications, including a database abstraction layer, user authentication, and a REST API.

- [**Frappe UI**](https://github.com/frappe/frappe-ui): A Vue-based UI library, to provide a modern user interface. The Frappe UI library provides a variety of components that can be used to build single-page applications on top of the Frappe Framework.

## Production Setup

### Managed Hosting

You can try [Frappe Cloud](https://frappecloud.com), a simple, user-friendly and sophisticated [open-source](https://github.com/frappe/press) platform to host Frappe applications with peace of mind.

It takes care of installation, setup, upgrades, monitoring, maintenance and support of your Frappe deployments. It is a fully featured developer platform with an ability to manage and control multiple Frappe deployments.

<div>
	<a href="https://frappecloud.com/hrms/signup" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/try-on-fc-white.png">
			<img src="https://frappe.io/files/try-on-fc-black.png" alt="Try on Frappe Cloud" height="28" />
		</picture>
	</a>
</div>

## Development setup

## Development setup

### Docker

You need Docker Desktop and Git. The commands below are portable across team members and keep runtime data in Docker-managed volumes.

#### First-time setup

```powershell
git clone <repository-url> hrms
cd hrms
Copy-Item .env.example .env
docker compose --env-file .env -f docker/docker-compose.yml up -d
docker compose --env-file .env -f docker/docker-compose.yml logs -f frappe
```

The first run downloads the Frappe and ERPNext dependencies and can take several minutes. Open `http://localhost:8000` after the logs show the web process is listening. The development defaults are in `.env`; keep that file local and never commit it.

The named `frappe-bench` volume contains the complete Frappe bench, including the `sites` directory, site configuration, public uploads, private uploads, and installed apps. This keeps those files persistent without nested mounts that behave differently between Docker Desktop installations.
The named Docker volumes contain the local runtime state:

- `docker_mariadb-data` contains the MariaDB database, including Employees, Users, setup-wizard completion, and HRMS transactions.
- `docker_frappe-bench` contains the complete Frappe bench, including the `sites` directory, site configuration, public uploads, private uploads, and installed apps.

The volume prefix comes from `HRMS_VOLUME_PREFIX=docker` in `.env`. Keep the same prefix on every laptop if you want Docker to reuse the same local volumes after container recreation.

#### Daily lifecycle commands

Run these from the repository root:

```powershell
# Start existing containers
docker compose --env-file .env -f docker/docker-compose.yml start

# Stop containers without deleting data
docker compose --env-file .env -f docker/docker-compose.yml stop

# Restart containers without deleting data
docker compose --env-file .env -f docker/docker-compose.yml restart

# Recreate containers while retaining all named volumes
docker compose --env-file .env -f docker/docker-compose.yml up -d --force-recreate

# View Frappe logs
docker compose --env-file .env -f docker/docker-compose.yml logs -f frappe
```

Do not use `docker compose down -v` for normal development. The `-v` option deletes the MariaDB volume and its database. It is only for intentionally destroying a disposable environment.
Do not use `docker compose down -v` for normal development. The `-v` option deletes the MariaDB volume and its database, so the next startup creates a fresh site and Frappe shows the setup wizard again. It is only for intentionally destroying a disposable environment.

#### Backup and restore

Create a database and site-files backup outside the repository:

```powershell
cd docker
.\backup.ps1
```

Backups are written to `.backups/`, which is ignored by Git. Before restoring, stop the application and restore only into a disposable validation site. The restore script refuses to overwrite an existing site; use Frappe's explicit restore command after creating a fresh target site:
Backups are written to `.backups/`, which is ignored by Git. Before restoring manually, stop the application and restore only into a disposable validation site. The restore script refuses to overwrite an existing site; use Frappe's explicit restore command after creating a fresh target site:

```powershell
.\restore.ps1 ..\.backups\<backup-directory> -TargetSite hrms.restore.localhost
```

The database backup is produced by `bench --site <site> backup --with-files --compress`. Never commit backup archives, site files, Docker volumes, Firebase private credentials, or SMTP App Passwords.

#### Shared demo seed

For this project, you can also keep a sanitized development/demo backup in `docker/seed/` so a brand-new laptop starts with the same demo company, users, and Employees instead of opening the setup wizard.

1. Create the desired local state: complete setup, create demo Employees, and verify login.
2. Run `cd docker` and `.\backup.ps1 -Seed`.
3. The generated backup is saved in `.backups/` and copied to `docker/seed/<timestamp>/`.
4. Commit only safe demo data in `docker/seed/`. Do not commit real employee data, private Firebase Admin JSON, SMTP passwords, or production backups.

On a fresh machine, the first `docker compose ... up -d` checks `HRMS_SEED_BACKUP_DIR` and restores the newest seed backup before the site is used. On an existing machine, the script does not overwrite the current site; it keeps using the Docker volumes.

#### Environment and secrets

`.env.example` contains safe development placeholders. Copy it to `.env` and change local values if needed. Phase 1 does not require Firebase or SMTP settings. Later Firebase and Gmail settings will be supplied through local environment/site configuration, not source-code edits.

The default development login is `Administrator` / `admin` unless you change `FRAPPE_ADMIN_PASSWORD` in `.env` before first site creation.

### Phase 2: Firebase authentication

Phase 2 uses Firebase Authentication for email/password authentication and keeps Frappe/MariaDB as the source of truth for users, Employees, roles, permissions, and HRMS data. Firebase UID is only an identity key; the Frappe Employee ID remains canonical.

#### Configuration

Copy `.env.example` to `.env` and provide the shared development Firebase Web configuration:

```dotenv
FIREBASE_API_KEY=your-web-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_APP_ID=your-web-app-id
FIREBASE_UID_FIELD=firebase_uid
```

The backend must also verify ID tokens with Firebase Admin credentials. Use one of these local-only options:

```dotenv
# Recommended for local Docker development. Keep the JSON value in .env only.
FIREBASE_ADMIN_CREDENTIALS_JSON={"type":"service_account",...}

# Alternative when the credential file is mounted or available inside the container.
FIREBASE_ADMIN_CREDENTIALS_FILE=/run/secrets/firebase-admin.json
```

Never commit `.env`, a service-account JSON file, Admin private keys, API passwords, or Firebase credentials. Web API key/project/app values are client configuration, but Admin credentials are server-only. The frontend receives only the Web configuration through the backend `firebase_config` endpoint.

#### Existing-user mapping

Phase 2 does not create Firebase users, Frappe Users, or Employees. A Firebase user must already exist and an enabled Frappe System User must already exist with the same verified email. If the optional `FIREBASE_UID_FIELD` field exists on `User`, UID is matched first; verified email is the fallback mapping. The user must already be linked to an Employee through Frappe's `Employee.user_id` field to use employee-specific routes.

#### Authentication flow

1. The frontend signs in with Firebase Web Auth using email/password.
2. Firebase returns an ID token to the frontend.
3. The frontend sends only that ID token to `login_with_firebase_token`.
4. The backend verifies signature, issuer, audience, expiry, revocation, UID, and email using Firebase Admin SDK.
5. The backend maps the verified identity to an enabled Frappe System User.
6. Frappe's native `login_manager.login_as()` creates the normal Frappe session cookie.
7. Frappe roles and permissions continue to authorize all HRMS API calls.

The Firebase password is never sent to the Frappe backend. Logout invalidates the Frappe session and signs out of Firebase. Browser refresh restores Firebase state and exchanges a fresh ID token for a Frappe session.

#### Phase 2 endpoints

- `hrms.api.firebase_auth.firebase_config` — returns safe Firebase Web configuration.
- `hrms.api.firebase_auth.firebase_status` — reports public configuration and server-verification readiness.
- `hrms.api.firebase_auth.login_with_firebase_token` — verifies an ID token and creates the Frappe session.
- `logout` — existing Frappe logout endpoint, followed by Firebase sign-out in the frontend.

Invalid, expired, revoked, disabled, malformed, or unmapped Firebase accounts receive controlled authentication/permission errors. Raw ID tokens and passwords are not logged.

#### Team setup

Each team member clones the repository, copies `.env.example` to `.env`, adds the shared development Web configuration and server-only Admin credential through their local secret mechanism, then runs the normal Docker startup commands. No source-code edits or machine-specific paths are needed. Firebase Authentication must have Email/Password enabled, and the corresponding Frappe User/Employee mapping must already exist before login can succeed.

### Phase 3: Employee provisioning

Phase 3 provisions login identity from an existing or newly created Frappe Employee without making Firebase the HRMS database. Frappe/MariaDB remains authoritative for Employee records, Frappe Users, roles, permissions, and HRMS data.

When `Create User Automatically` is enabled on a new Employee, HRMS now attempts to:

1. Validate the Employee login email.
2. Create or reuse a Frappe System User for that email.
3. Create or reuse the Firebase Authentication user for that email.
4. Store Firebase UID on `User.firebase_uid`.
5. Link `Employee.user_id` to the Frappe User.
6. Queue a Firebase password setup/reset invitation through Frappe email.

The same operation is available from the Employee form as `Provision Firebase Login`, so failed or partial provisioning can be retried safely. Provisioning is idempotent: an existing linked Frappe User, existing Firebase user, or existing `User.firebase_uid` is reconciled instead of duplicated.

Employee records include provisioning state fields:

- `Firebase Provisioning Status`: `Pending`, `Provisioning`, `Provisioned`, `Failed`, or `Retry Required`.
- `Firebase Invitation Status`: `Not Generated`, `Generated`, `Queued`, `Failed`, or `Not Configured`.
- `Firebase Last Provisioned On`.
- `Firebase Provisioning Message`.

Firebase and MariaDB are separate systems, so failures are recorded as retryable state instead of being treated as one database transaction. If Firebase credentials are missing or Firebase is unavailable, the Employee/Frappe User state remains available for retry and the status is set to `Retry Required`.

Invitation emails use Firebase Admin's password reset/setup link generation. No permanent plaintext password is generated, stored, or emailed. Frappe queues the email through its normal Email Queue; actual delivery still depends on a configured outgoing Email Account.

### Phase 4: Gmail SMTP invitation delivery

Phase 4 configures the development container to create/update Frappe's default outgoing Email Account from local environment variables. This keeps the flow as:

```text
HRMS provisioning -> Frappe Email Queue -> Gmail SMTP -> employee mailbox
```

Copy `.env.example` to `.env` and configure a dedicated project Gmail account:

```dotenv
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-project-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_USE_TLS=true
SMTP_SENDER=your-project-email@gmail.com
```

The Gmail account must have 2-Step Verification enabled and must use a Gmail App Password. Do not use the normal Gmail password. Do not use a personal Gmail account, do not commit SMTP credentials, and do not claim delivery until the Frappe Email Queue has actually sent the message.

On container startup, if `SMTP_USERNAME` and `SMTP_PASSWORD` are present, Docker calls `hrms.api.smtp_config.configure_gmail_smtp_from_env`. That creates or updates the `HRMS Gmail SMTP` Email Account as the default outgoing account with STARTTLS on port 587. The password is stored through Frappe's Password field and is never exposed to the frontend.

Invitation statuses:

- `Not Generated`: no setup link has been generated.
- `Queued`: an invitation exists in Frappe Email Queue but has not necessarily been delivered.
- `Sent`: Frappe Email Queue reports the latest invitation email as sent.
- `Already Queued`: provisioning retry found an active queued/sent invitation and did not enqueue another.
- `Failed` or `Not Configured`: Firebase link generation or email queueing failed and can be retried.

Retrying `Provision Firebase Login` reconciles existing Frappe/Firebase users and does not create duplicate accounts. It also does not send unlimited duplicate invitations when one is already queued or sent. Use `Resend Firebase Invitation` on the Employee form to intentionally generate a fresh Firebase setup link and queue another invitation for an already linked Employee.

Relevant endpoints:

- `hrms.api.employee_provisioning.provision_employee` — authenticated retry/provision endpoint for an Employee. It requires write permission on the Employee and never exposes Firebase Admin credentials.
- `hrms.api.employee_provisioning.resend_invitation` — authenticated resend endpoint. It reuses the existing Employee/User/Firebase account, generates a fresh Firebase setup link, and queues a new Frappe Email Queue entry.
- `hrms.api.smtp_config.gmail_smtp_status` — System Manager-only status endpoint for checking default outgoing SMTP configuration without exposing secrets.

### Local

1. Set up bench by following the [Installation Steps](https://frappeframework.com/docs/user/en/installation) and start the server and keep it running
   ```sh
   $ bench start
   ```
   ```sh
   $ bench start
   ```
2. In a separate terminal window, run the following commands
   ```sh
   $ bench new-site hrms.localhost
   $ bench get-app erpnext
   $ bench get-app hrms
   $ bench --site hrms.localhost install-app hrms
   $ bench --site hrms.localhost add-to-hosts
   ```
   ```sh
   $ bench new-site hrms.localhost
   $ bench get-app erpnext
   $ bench get-app hrms
   $ bench --site hrms.localhost install-app hrms
   $ bench --site hrms.localhost add-to-hosts
   ```
3. You can access the site at `http://hrms.localhost:8080`

---

## Parent Project Integration (`MAIN_PROJECT/HRMS/`)

This HRMS repository is architected as an independent, portable sub-component intended to reside inside a larger parent project:

```text
MAIN_PROJECT/
├── frontend/             # Parent project frontend
├── backend/              # Parent project API / services
├── other-components/
└── HRMS/                 # THIS REPOSITORY (Independent sub-module / folder)
    ├── docker-compose.yml
    ├── .env
    ├── backups/seed/
    ├── scripts/
    │   ├── setup.ps1
    │   ├── start.ps1
    │   ├── ...
    └── hrms/
```

### Key Integration Principles:

1. **No Absolute Paths**: All volume mappings and configurations use relative paths or container-internal mount paths (`/workspace`, `/home/frappe/frappe-bench`).
2. **Customizable Port Mapping**: If the parent project uses port `8000` or `9000`, override HRMS ports in `.env`:
   ```dotenv
   HRMS_WEB_PORT=8081
   HRMS_SOCKETIO_PORT=9001
   ```
3. **Isolated Docker Networking & Volumes**:
   - Compose project name is explicitly set to `hrms` (`COMPOSE_PROJECT_NAME=hrms`).
   - Volumes are prefixed: `docker_mariadb-data`, `docker_frappe-bench`.
   - Networks are isolated (`hrms_default`).
4. **Reverse Proxy / Gateway Routing**:
   If the parent project uses an NGINX or Traefik gateway:
   - Route `/hrms` and `/api/method/hrms.*` to `http://localhost:8000` (or `http://hrms-frappe:8000` if on a shared Docker bridge network).
   - WebSocket `/socket.io/` routes to `http://localhost:9000`.

---

## Git Workflow & Branch Strategy

- **`develop` / `main`**: Stable upstream and tracking branches.
- **`hrms-portable-docker`**: Component development and Docker portability branch.
- **Rules**:
  - Never force-push or rewrite commit history.
  - Development changes should be committed locally and verified before pushing.
  - Updating team members only need to run `.\update.ps1` to pull changes, rebuild if Dockerfiles changed, and run safe migrations without wiping persistent database records.

---

## Troubleshooting & Diagnostics

1. **Port 8000 or 9000 already in use**:
   Change `HRMS_WEB_PORT` or `HRMS_SOCKETIO_PORT` in `.env` to open ports (e.g., `8080` and `9090`), then run `.\restart.ps1`.

2. **Check live container health & records**:

   ```powershell
   .\status.ps1
   ```

   Verifies MariaDB, Redis, Frappe ping, and live database user/employee counts.

3. **Follow logs in realtime**:

   ```powershell
   .\logs.ps1 -Follow
   ```

4. **Accidental corrupted state or want a fresh start from seed**:
   ```powershell
   .\reset.ps1   # Destructive: prompts for confirmation before removing volumes
   .\setup.ps1   # Automatically bootstraps fresh volumes and restores seed backup
   ```

---
