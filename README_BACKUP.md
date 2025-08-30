### PostgreSQL Auto Backup (weekly) with Telegram delivery

This project includes a simple bash script to back up the production PostgreSQL database and send the compressed dump to a Telegram group/channel. It also supports on-disk retention.

Files:
- `scripts/pg_backup.sh` — creates backup, gzips, sends to Telegram, prunes old backups
- `scripts/backup.env.example` — example env file for secrets
- `scripts/cron.example` — crontab line to run weekly at 01:00 Monday

Setup:
1) Create a Telegram bot and add it to your group/channel. Make it admin if the group is restricted. Note the bot token and the chat ID (negative for groups, e.g. `-100...`).
2) Copy env example and fill secrets:
   cp scripts/backup.env.example .env.backup
   # edit .env.backup and set PGPASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
3) Make the script executable and create the backup dir:
   mkdir -p /home/user/turantalim/backups
   chmod +x scripts/pg_backup.sh
4) Test a manual backup:
   /usr/bin/env bash scripts/pg_backup.sh
   # expect a .sql.gz file in backups and a file sent to Telegram
5) Install the cron job for user `user`:
   crontab -l | cat
   (crontab -l 2>/dev/null; echo "$(cat scripts/cron.example)") | crontab -

Notes:
- The script reads `.env` and `.env.backup` if present. Use `.env.backup` to store database password and Telegram credentials.
- By default backups go to `/home/user/turantalim/backups` and are kept for 30 days. Adjust `BACKUP_DIR` and `RETENTION_DAYS` if needed.
- Ensure `pg_dump`, `curl`, and `gzip` are installed on the host.

### When to use backups
- Server/VM failure or data corruption
- Wrong deployment/migration affecting data
- Human mistakes (accidental deletes/updates)
- Cloning prod data to staging/local for diagnostics
- Data export/audit

### Verifying backups
- Telegram: weekly `.sql.gz` file should arrive in your group/channel after Monday 01:00.
- On server:
  tail -n 200 /home/user/turantalim/backups/cron.log
- Manual run:
  /usr/bin/env bash scripts/pg_backup.sh
- Integrity check (no extract):
  gunzip -t /home/user/turantalim/backups/NAME.sql.gz

### Restore guide (full restore)
Backup format is plain SQL compressed with gzip.

1) Prepare the file (ensure it exists locally):
   ls -lh /home/user/turantalim/backups/*.sql.gz

2) Restore into a new database (safer to validate first):
   export PGPASSWORD='your_password'
   createdb -h localhost -p 5432 -U turan_user turantalim_restore
   gunzip -c /home/user/turantalim/backups/NAME.sql.gz | \
     psql -h localhost -p 5432 -U turan_user -d turantalim_restore

3) (Optional) Fix ownership/permissions if needed:
   psql -h localhost -p 5432 -U turan_user -d turantalim_restore -c "ALTER SCHEMA public OWNER TO turan_user;"
   psql -h localhost -p 5432 -U turan_user -d turantalim_restore -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO turan_user;"
   psql -h localhost -p 5432 -U turan_user -d turantalim_restore -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO turan_user;"

4) Point the app to `turantalim_restore` for validation (via settings/env), then revert.

5) Restore to production (downtime/maintenance window):
   # WARNING: drops and recreates prod DB
   dropdb  -h localhost -p 5432 -U turan_user turantalim_db
   createdb -h localhost -p 5432 -U turan_user turantalim_db
   gunzip -c /home/user/turantalim/backups/NAME.sql.gz | \
     psql -h localhost -p 5432 -U turan_user -d turantalim_db

### Partial restores
- Single table/rows: restore full dump into a temporary DB, then copy out required tables/rows with SQL.
- Alternatively, extract relevant statements from the `.sql` and apply carefully with `psql`.

### Cron behavior
- Installed as a user crontab: runs every Monday at 01:00.
- Survives reboots; no extra action required after system restart.
- Logs are appended to `/home/user/turantalim/backups/cron.log`.

### Handy commands
- Show latest backups:
  ls -lt /home/user/turantalim/backups/*.sql.gz | head
- Run backup now:
  /usr/bin/env bash scripts/pg_backup.sh
- View cron log:
  tail -n 200 /home/user/turantalim/backups/cron.log
- Copy backup to local machine:
  scp user@server:/home/user/turantalim/backups/NAME.sql.gz .

### Troubleshooting
- Telegram 404/401: ensure `.env.backup` is sourced correctly. The script now sources it safely; avoid using `grep|xargs` to export vars.
- Validate credentials quickly:
  set -a; source .env.backup; set +a
  curl -sS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
  curl -sS "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getChat?chat_id=${TELEGRAM_CHAT_ID}"
- The script prints HTTP status and body for Telegram upload, and sends a text probe if document upload fails.

