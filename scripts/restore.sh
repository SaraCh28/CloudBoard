#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# CloudBoard – Database Restore Script (Module 18)
#
# Usage:
#   ./scripts/restore.sh <backup_file.sql.gz>
#
# Example:
#   ./scripts/restore.sh ./backups/cloudboard_20260726_120000.sql.gz
#
# ⚠️  This DROPS and recreates the target database!
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

BACKUP_FILE="${1:-}"
DB_NAME="${POSTGRES_DB:-cloudboard}"
DB_USER="${POSTGRES_USER:-cloudboard}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5435}"

if [[ -z "${BACKUP_FILE}" ]]; then
  echo "❌  Usage: $0 <backup_file.sql.gz>"
  exit 1
fi

if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "❌  Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

echo "⚠️   This will DROP and recreate database '${DB_NAME}'."
read -rp "    Type 'yes' to confirm: " CONFIRM
if [[ "${CONFIRM}" != "yes" ]]; then
  echo "Aborted."
  exit 0
fi

echo "▶  Dropping existing database..."
PGPASSWORD="${POSTGRES_PASSWORD:-cloudboard}" \
  psql --host="${DB_HOST}" --port="${DB_PORT}" \
       --username="${DB_USER}" --dbname="postgres" \
       -c "DROP DATABASE IF EXISTS ${DB_NAME};"

echo "▶  Recreating database..."
PGPASSWORD="${POSTGRES_PASSWORD:-cloudboard}" \
  psql --host="${DB_HOST}" --port="${DB_PORT}" \
       --username="${DB_USER}" --dbname="postgres" \
       -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "▶  Restoring from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD:-cloudboard}" \
  psql --host="${DB_HOST}" --port="${DB_PORT}" \
       --username="${DB_USER}" --dbname="${DB_NAME}" \
       --quiet

echo "✅  Restore complete. Database '${DB_NAME}' is ready."
