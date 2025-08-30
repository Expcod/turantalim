#!/usr/bin/env bash

set -euo pipefail

# Load .env.backup safely (do not mangle values)
if [ -f ".env.backup" ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env.backup
  set +a
fi

# Required env vars
: "${PGHOST:=localhost}"
: "${PGPORT:=5432}"
: "${PGDATABASE:=turantalim_db}"
: "${PGUSER:=turan_user}"
: "${PGPASSWORD:?Set PGPASSWORD in .env.backup}"

: "${BACKUP_DIR:=/home/user/turantalim/backups}"
: "${RETENTION_DAYS:=30}"

# Telegram
: "${TELEGRAM_BOT_TOKEN:?Set TELEGRAM_BOT_TOKEN in .env.backup}"
: "${TELEGRAM_CHAT_ID:?Set TELEGRAM_CHAT_ID in .env.backup}"

# Minimal debug (do not print token). Useful to detect empty/overridden vars.
echo "[pg_backup] Using chat_id=${TELEGRAM_CHAT_ID}; token_len=${#TELEGRAM_BOT_TOKEN}"

timestamp=$(date +"%Y%m%d_%H%M%S")
host_part=$(hostname -s || echo host)
filename="${PGDATABASE}_${host_part}_${timestamp}.sql.gz"
mkdir -p "$BACKUP_DIR"
filepath="$BACKUP_DIR/$filename"

echo "[pg_backup] Starting backup to $filepath"

export PGPASSWORD
pg_dump --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" --format=plain --file="${filepath%.gz}" "$PGDATABASE"
gzip -f "${filepath%.gz}"

echo "[pg_backup] Uploading to Telegram..."
telegram_api_url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}"

# Upload document
upload_http_body=$(mktemp)
upload_http_code=$(curl -sS -o "$upload_http_body" -w '%{http_code}' \
  -F chat_id="${TELEGRAM_CHAT_ID}" \
  -F caption="${PGDATABASE} backup ${timestamp}" \
  -F document=@"$filepath" \
  "$telegram_api_url/sendDocument")

if [ "$upload_http_code" = "200" ] && grep -q '"ok":true' "$upload_http_body"; then
  echo "[pg_backup] Upload successful."
else
  echo "[pg_backup] Upload failed. HTTP $upload_http_code. Body:" >&2
  cat "$upload_http_body" >&2 || true
  # Try sending a text message to verify chat/token permissions
  msg_http_body=$(mktemp)
  msg_http_code=$(curl -sS -o "$msg_http_body" -w '%{http_code}' \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="${PGDATABASE} backup ${timestamp}: document upload failed (HTTP ${upload_http_code})." \
    "$telegram_api_url/sendMessage")
  echo "[pg_backup] sendMessage probe: HTTP $msg_http_code. Body:" >&2
  cat "$msg_http_body" >&2 || true
fi

echo "[pg_backup] Cleaning up backups older than ${RETENTION_DAYS} days in $BACKUP_DIR"
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete || true

echo "[pg_backup] Done."


