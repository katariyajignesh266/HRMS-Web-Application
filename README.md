# Frappe HRMS — Customized, Portable & Reproducible Docker Environment

> A customized Frappe HRMS development environment focused on Docker portability, persistent data, automated setup, Gmail SMTP email delivery, backup/restore, and a reproducible local development workflow.

This repository is based on the open-source **Frappe HRMS** project and contains project-specific changes made for the HRMS development environment.

Repository: https://github.com/katariyajignesh266/HRMS-Web-Application  
Development branch: `hrms-development`

---

## What Was Customized


### Major customizations

- Portable Docker environment for Windows + Docker Desktop.
- Persistent MariaDB and Frappe Bench Docker volumes.
- Automated first-run site/bench bootstrap.
- Optional sanitized seed backup restoration.
- PowerShell lifecycle, backup and restore tooling.
- Gmail SMTP configuration from environment variables.
- Frappe Email Queue integration for outgoing emails.
- Automatic configuration of the default outgoing Email Account during container startup.
- SMTP status reporting for System Managers without exposing credentials.
- Frontend support for the HRMS employee application under the `/hrms` route.
- Docker-compatible frontend asset build using Vite.
- Persistent developer mode, scheduler and migration handling.
- Safe update/rebuild workflow that preserves persistent database records.
- Protection against accidentally recreating or overwriting an existing persistent site.
- Reproducible local setup intended for team members using Docker Desktop.

---

## Architecture

The customized environment keeps **Frappe/MariaDB as the source of truth for HRMS data**.

```text
                    ┌─────────────────────────┐
                    │       Employee          │
                    │      HRMS Web App       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Frappe / HRMS       │
                    │  Roles + Permissions    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │        MariaDB          │
                    │     HRMS Database       │
                    └─────────────────────────┘

                    Outgoing Email Flow

HRMS / Frappe Document or Action
        │
        ▼
Frappe Email Queue
        │
        ▼
Gmail SMTP
        │
        ▼
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
