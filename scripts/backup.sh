#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# CloudBoard – Database Backup Script (Module 18)
#
# Usage:
#   ./scripts/backup.sh [output_dir]
#
# Default output_dir: ./backups
# Requires: pg_dump, PGPASSWORD or .pgpass configured
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="${POSTGRES_DB:-cloudboard}"
DB_USER="${POSTGRES_USER:-cloudboard}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5435}"
BACKUP_FILE="${BACKUP_DIR}/cloudboard_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "▶  Starting CloudBoard DB backup → ${BACKUP_FILE}"
PGPASSWORD="${POSTGRES_PASSWORD:-cloudboard}" \
  pg_dump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --no-password \
    --format=plain \
    --no-owner \
    --no-acl \
    "${DB_NAME}" | gzip > "${BACKUP_FILE}"

echo "✅  Backup complete: ${BACKUP_FILE} ($(du -sh "${BACKUP_FILE}" | cut -f1))"

# Retain only the last 7 daily backups
find "${BACKUP_DIR}" -name "cloudboard_*.sql.gz" -mtime +7 -delete
echo "🗑   Old backups pruned (keeping last 7 days)."
