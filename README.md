# Frappe HRMS — Customized, Portable & Reproducible Docker Environment

> A customized Frappe HRMS development environment focused on Docker portability, persistent data, automated setup, Gmail SMTP email delivery, backup/restore, and a reproducible local development workflow.

This repository is based on the open-source **Frappe HRMS** project and contains project-specific changes made for the HRMS development environment.

**Repository:** https://github.com/katariyajignesh266/HRMS-Web-Application  
**Development branch:** `hrms-development`

---

## Project Overview

This project provides a Docker-based HRMS environment that can be set up consistently on a developer machine using Docker Desktop.

The main goals are:

- Keep the HRMS environment portable across developer machines.
- Persist application and database data across container restarts/rebuilds.
- Make first-time setup as automated as possible.
- Provide a reliable local Frappe Desk/Admin environment.
- Support the HRMS employee-facing web application.
- Provide working outgoing email through **Frappe Email Queue + Gmail SMTP**.
- Provide backup and restore utilities for development data.
- Make updates and rebuilds safer without unnecessarily destroying persistent records.
- Keep configuration environment-driven instead of hard-coding machine-specific values.

---

## What Was Customized

### Docker & Infrastructure

- Portable Docker environment designed for Windows + Docker Desktop.
- Persistent MariaDB storage using Docker volumes.
- Persistent Frappe Bench/site data using Docker volumes.
- Automated first-run site and bench bootstrap.
- Idempotent initialization so existing persistent sites are not unnecessarily recreated.
- Environment-variable based configuration through `.env`.
- Docker Compose based service lifecycle.
- Development-friendly scheduler and migration handling.
- Safer rebuild/update workflow while preserving persistent database records.
- Protection against accidentally recreating or overwriting an existing persistent site.
- Reproducible local setup intended for team members using Docker Desktop.

### Database & Persistence

- MariaDB is used as the HRMS database.
- Database data is stored in persistent Docker volumes.
- Frappe Bench data is persisted separately from disposable containers.
- Container recreation should not automatically mean loss of HRMS records.
- Backup and restore scripts are included for development recovery workflows.
- Optional sanitized seed backup restoration can be used when preparing a fresh environment.

### HRMS / Frappe

- Frappe Framework and Frappe HRMS are configured to run inside the Docker environment.
- HRMS employee functionality is available through the Frappe application.
- Role and permission based access remains managed by Frappe.
- Employee management and HRMS configuration are available from Frappe Desk.
- Frontend assets are built in a Docker-compatible workflow.
- Vite-based frontend build support is included where required by the project.
- Development mode, migrations and scheduler handling are integrated into the local workflow.

### Email System

Outgoing email is configured using the Frappe email system with Gmail SMTP.

The working flow is:

```text
HRMS / Frappe Document or Action
        |
        v
Frappe Email Queue
        |
        v
Gmail SMTP
        |
        v
Recipient Mailbox
```

The project includes:

- Gmail SMTP configuration through environment variables.
- Frappe Email Queue integration.
- Automatic configuration of the default outgoing Email Account during startup.
- SMTP status reporting for System Managers without exposing credentials.
- Email delivery through a dedicated project Gmail account.
- Support for Gmail App Password based SMTP authentication.

Example configuration:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-project-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_USE_TLS=true
SMTP_SENDER=your-project-email@gmail.com
```

> Use a dedicated project Gmail account and a Gmail **App Password** for SMTP. Do not use or commit the normal Gmail account password.

---

## Architecture

The customized environment keeps **Frappe/MariaDB as the source of truth for HRMS data**.

```text
                    +-------------------------+
                    |       Employee          |
                    |      HRMS Web App       |
                    +------------+------------+
                                 |
                                 v
                    +-------------------------+
                    |     Frappe / HRMS       |
                    |  Roles + Permissions    |
                    +------------+------------+
                                 |
                                 v
                    +-------------------------+
                    |        MariaDB          |
                    |     HRMS Database       |
                    +-------------------------+

                    Outgoing Email Flow

HRMS / Frappe Document or Action
        |
        v
Frappe Email Queue
        |
        v
Gmail SMTP
        |
        v
Recipient Mailbox
```

---

## Quick Start — Windows + Docker Desktop

### Requirements

- Windows 10/11
- Docker Desktop
- Git
- VS Code recommended
- Internet connection for the first Docker bootstrap

### Clone the development branch

```powershell
git clone -b hrms-development https://github.com/katariyajignesh266/HRMS-Web-Application.git hrms
cd hrms
```

### Create the local environment file

```powershell
Copy-Item .env.example .env
```

Review the values in `.env` before starting the project.

### Start the environment

```powershell
docker compose --env-file .env -f docker/docker-compose.yml up -d
```

### Follow Frappe logs

```powershell
docker compose --env-file .env -f docker/docker-compose.yml logs -f frappe
```

The first bootstrap can take several minutes because the Frappe bench, ERPNext dependencies, HRMS assets and required Python/Node packages may need to be initialized.

### Check running containers

```powershell
docker compose --env-file .env -f docker/docker-compose.yml ps
```

### Stop the environment

```powershell
docker compose --env-file .env -f docker/docker-compose.yml down
```

> Do not use volume deletion commands unless you intentionally want to remove persistent development data.

---

## Verified Local Access

Only the main Frappe Desk/Admin entry point is listed here intentionally.

### Frappe Desk / Admin

**http://localhost:8000/app**

Use this entry point for:

- Administration
- Employee management
- HRMS configuration
- Roles and permissions
- System settings
- Email configuration
- Frappe Email Queue
- Developer and system administration tasks

### Default Administrator

```text
Username: Administrator
Password: admin
```

The administrator password is controlled by `FRAPPE_ADMIN_PASSWORD` in `.env` and should be changed for any non-disposable environment.

---

## Employee Testing Account

A dedicated employee account is available for local testing of the employee-facing HRMS flow.

```text
Email: katariyajignesh266@gmail.com
Password: jignesh&777J
```

### What to test with the Employee account

Use the employee account to verify the employee-side experience, including:

- Employee login
- Employee dashboard
- Employee profile and employee information
- Available HRMS employee features
- Role/permission based access
- Email-triggered workflows where applicable
- Session/logout behavior
- Access restrictions between employee and administrator roles

> **Important:** This account is intended only for development/testing. Do not reuse this password for production, personal accounts, or any external service.

If the repository is ever made public or used outside the controlled development team, replace this test password and move test credentials to a secure local configuration.

---

## Gmail SMTP & Frappe Email Queue

Email delivery is an important working part of this project.

### Email flow

```text
HRMS Event / Frappe Action
          |
          v
Frappe Email Queue
          |
          v
Configured Outgoing Email Account
          |
          v
Gmail SMTP
          |
          v
Recipient
```

### Configuration

SMTP values are provided through environment variables rather than being hard-coded in the application.

Typical values:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-project-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_USE_TLS=true
SMTP_SENDER=your-project-email@gmail.com
```

The normal Gmail password should not be placed in the project. Gmail SMTP should use an App Password where required.

### Email Queue verification

From Frappe Desk, administrators can inspect the Email Queue to verify:

- Emails were generated by Frappe.
- Emails entered the queue.
- SMTP delivery was attempted.
- Delivery status and errors can be investigated when a message fails.

The project also contains SMTP status handling intended to expose configuration status without displaying the SMTP secret.

---

## Persistence & Data Safety

The Docker setup is designed around persistent development data.

### Persistent components

```text
Docker Compose
    |
    +--> MariaDB volume
    |       |
    |       +--> HRMS database records
    |
    +--> Frappe Bench/site volume
            |
            +--> Site configuration
            +--> Installed applications
            +--> Uploaded/application data
```

Because the important data is stored in persistent volumes, normal container recreation should not be treated as a database reset.

### Important

Avoid commands that remove Docker volumes unless a complete reset is intentional.

For example, this is destructive to persistent Docker data:

```powershell
docker compose down -v
```

Use it only when you explicitly want to remove the persistent volumes and start over.

---

## Backup & Restore

The repository includes development-oriented backup and restore tooling.

### Backup

The backup workflow is intended to help preserve:

- MariaDB/site database data
- Frappe site information
- Development configuration required for recovery

Use the provided project scripts where available instead of manually copying random Docker container directories.

### Restore

Restore can be used when:

- Setting up a fresh development machine.
- Recovering from an accidental local reset.
- Preparing a reproducible development environment.
- Loading a sanitized development seed.

Always verify that the backup belongs to the expected project/version before restoring it.

> Production backups and private employee data must not be committed to GitHub.

---

## Project Structure

The repository contains the customized Docker and HRMS development environment.

A simplified structure is:

```text
HRMS-Web-Application/
|
+-- docker/
|   +-- docker-compose.yml
|   +-- Docker-related configuration
|   +-- startup / initialization scripts
|   +-- backup / restore tooling
|
+-- hrms/
|   +-- Frappe HRMS application code
|   +-- frontend / employee application code
|   +-- project-specific changes
|
+-- .env.example
+-- README.md
+-- backup / restore scripts
+-- project documentation
```

> The exact file structure can evolve as development continues. The repository itself is the source of truth for the current implementation.

---

## Development Workflow

Recommended workflow for developers:

### 1. Pull the latest branch

```powershell
git checkout hrms-development
git pull origin hrms-development
```

### 2. Start Docker

```powershell
docker compose --env-file .env -f docker/docker-compose.yml up -d
```

### 3. Check logs if required

```powershell
docker compose --env-file .env -f docker/docker-compose.yml logs -f frappe
```

### 4. Make changes

Use VS Code to work on the project.

### 5. Verify before committing

Check:

- Docker containers are healthy.
- Frappe Desk opens correctly.
- HRMS pages load.
- Employee testing flow works.
- Email Queue works when email functionality is changed.
- No secrets or private files are included in the commit.

### 6. Commit and push

```powershell
git status
git add .
git commit -m "Describe the change"
git push origin hrms-development
```

---

## Updating the Environment

When application or configuration changes are pulled from GitHub:

```powershell
git pull origin hrms-development
```

Then rebuild/restart the required services using the project Docker workflow.

For example:

```powershell
docker compose --env-file .env -f docker/docker-compose.yml up -d --build
```

After an update, verify the application and database before performing any destructive cleanup.

---

## Troubleshooting

### Containers are not starting

Check:

```powershell
docker compose --env-file .env -f docker/docker-compose.yml ps
docker compose --env-file .env -f docker/docker-compose.yml logs -f
```

### Frappe is still initializing

The first startup can take time. Check the `frappe` container logs and wait for the site/bench initialization to complete.

### Database data appears missing

First check whether the correct Docker volumes are still present. Do not immediately recreate the site or run `down -v`.

### Email is not being delivered

Check:

1. `.env` SMTP values.
2. Gmail App Password.
3. Frappe Outgoing Email Account configuration.
4. Frappe Email Queue.
5. Frappe container logs.
6. SMTP connection/authentication errors.

Never paste the SMTP password into GitHub issues, commits or public documentation.

### Frontend assets are not updated

Rebuild the relevant Docker service and check the frontend build output/logs. Make sure the expected Vite/build process completed successfully.

---

## Testing Checklist

### Docker / Infrastructure

- [ ] Docker Desktop is running.
- [ ] All required containers start successfully.
- [ ] MariaDB remains persistent after container recreation.
- [ ] Frappe site remains persistent after restart.
- [ ] First-time bootstrap completes successfully.
- [ ] Existing persistent site is not accidentally recreated.

### Frappe / HRMS

- [ ] Frappe Desk opens at `http://localhost:8000/app`.
- [ ] Administrator login works.
- [ ] Employee records can be managed.
- [ ] Roles and permissions behave as expected.
- [ ] Employee testing account can access the intended employee experience.
- [ ] Logout/session behavior works.

### Email

- [ ] Gmail SMTP configuration is loaded from environment variables.
- [ ] Frappe Outgoing Email Account is configured.
- [ ] Email enters Frappe Email Queue.
- [ ] Email is successfully sent through Gmail SMTP.
- [ ] Recipient receives the message.
- [ ] SMTP credentials are not exposed in logs or UI responses.

### Backup / Restore

- [ ] Backup can be created.
- [ ] Backup can be restored in a test environment.
- [ ] Restored HRMS records are verified.
- [ ] Production/private data is kept outside Git.

---

## Security Notes

Never commit the following to GitHub:

- `.env`
- Gmail App Passwords
- SMTP passwords
- Database passwords
- Real production credentials
- Private employee documents
- Production database backups
- API secrets
- Private keys

Use `.env.example` for configuration templates and keep real secrets in the local `.env`.

For development-only credentials, use dedicated test accounts and replace them before any production deployment.

---

## Parent Project & Upstream

This project is built on top of the open-source Frappe ecosystem.

- **Frappe HRMS:** https://github.com/frappe/hrms
- **Frappe Framework:** https://github.com/frappe/frappe
- **Frappe UI:** https://github.com/frappe/frappe-ui
- **Frappe Documentation:** https://docs.frappe.io/

Project-specific Docker, persistence, email, frontend and development-environment changes are maintained in this repository.

---

## Current Development Focus

The current development environment focuses on a stable and reproducible HRMS foundation:

- Docker-based local deployment
- Persistent MariaDB and Frappe data
- Portable Windows development setup
- HRMS employee application
- Administrator and employee testing
- Gmail SMTP
- Frappe Email Queue
- Backup and restore
- Safer rebuild/update workflows
- Team-friendly setup and documentation

The README intentionally documents the working development environment and the features that are currently relevant for team setup and testing.

---

## License

This project is based on open-source Frappe HRMS. Refer to the upstream project and the license files included in the repository for applicable licensing information.
