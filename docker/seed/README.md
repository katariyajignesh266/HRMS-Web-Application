# Optional shared development seed

Put a sanitized Frappe backup here when you want a fresh Docker setup to start with the same demo data on every laptop.

The startup script accepts either:

- backup files directly in this folder, or
- timestamped subfolders copied from `.backups/`; the newest subfolder is used.

Expected files are the normal output from:

```sh
bench --site hrms.localhost backup --with-files --compress
```

Only commit development/demo data that is safe for the whole team. Do not commit real employee data, Firebase Admin service-account JSON, SMTP passwords, or production backups.
