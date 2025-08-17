#!/usr/bin/env bash
# One-click deployment script (Bitnami Lightsail + Apache + mod_wsgi)
# Usage (on server):
#   sudo bash deploy/deploy.sh            # default branch main
#   sudo bash deploy/deploy.sh develop    # specify branch

set -euo pipefail
BRANCH="${1:-main}"

# === Path Configuration (adjust for your project) ===
PROJECT_ROOT="/opt/bitnami/projects/solar/Eurmaxi"
VHOST_SRC="$PROJECT_ROOT/solar-vhost.conf"
VHOST_DST="/opt/bitnami/apache/conf/vhosts/solar-vhost.conf"

# Bitnami built-in Python & Pip (consistent with mod_wsgi)
PY="/opt/bitnami/python/bin/python3"
PIP="/opt/bitnami/python/bin/pip3"

log() { echo -e "\n[deploy] $*"; }

trap 'echo "[deploy] ❌ Deployment interrupted (previous command failed). Check logs: /opt/bitnami/apache/logs/solar-error.log"; exit 1' ERR

log "Changing to project root directory: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

log "Fetching latest code: origin $BRANCH"
git fetch --all --prune
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

log "Installing/updating dependencies (requirements.txt)"
$PIP install -r requirements.txt

log "Compiling translation files"
$PY manage.py compilemessages

log "Running database migrations"
$PY manage.py migrate --noinput

log "Collecting static files"
$PY manage.py collectstatic --noinput

log "Installing Apache vhost to target directory (will overwrite)"
if [[ ! -f "$VHOST_SRC" ]]; then
  echo "[deploy] vhost source file not found: $VHOST_SRC"
  exit 1
fi

# Backup old configuration (keep latest 3 copies)
if [[ -f "$VHOST_DST" ]]; then
  ts="$(date +%Y%m%d-%H%M%S)"
  cp "$VHOST_DST" "${VHOST_DST}.bak.$ts"
  ls -1t ${VHOST_DST}.bak.* 2>/dev/null | tail -n +4 | xargs -r rm -f
fi

cp "$VHOST_SRC" "$VHOST_DST"

log "Checking Apache configuration syntax"
sudo /opt/bitnami/apache/bin/apachectl -t

log "Restarting Apache"
sudo /opt/bitnami/ctlscript.sh restart apache

log "✅ Deployment completed! Visit: http://3.75.185.85/"
