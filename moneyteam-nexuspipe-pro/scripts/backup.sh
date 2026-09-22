#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_DIR:=./backups}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

pg_dump "$DATABASE_URL" --format=custom --file="$BACKUP_DIR/moneyteam_$STAMP.dump"
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup created: $BACKUP_DIR/moneyteam_$STAMP.dump"
