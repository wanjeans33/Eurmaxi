#!/usr/bin/env bash
# 一键部署脚本（Bitnami Lightsail + Apache + mod_wsgi）
# 用法（服务器上）：
#   sudo bash deploy/deploy.sh            # 默认分支 main
#   sudo bash deploy/deploy.sh develop    # 指定分支

set -euo pipefail
BRANCH="${1:-main}"

# === 路径配置（按你的项目实际情况）===
PROJECT_ROOT="/opt/bitnami/projects/solar/Eurmaxi"
VHOST_SRC="$PROJECT_ROOT/solar-vhost.conf"
VHOST_DST="/opt/bitnami/apache/conf/vhosts/solar-vhost.conf"

# Bitnami 自带 Python & Pip（与 mod_wsgi 一致）
PY="/opt/bitnami/python/bin/python3"
PIP="/opt/bitnami/python/bin/pip3"

log() { echo -e "\n[deploy] $*"; }

trap 'echo "[deploy] ❌ 部署中断（上一条命令失败）。查看日志：/opt/bitnami/apache/logs/solar-error.log"; exit 1' ERR

log "切到项目根目录：$PROJECT_ROOT"
cd "$PROJECT_ROOT"

log "拉取最新代码：origin $BRANCH"
git fetch --all --prune
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

log "安装/更新依赖（requirements.txt）"
$PIP install -r requirements.txt

log "数据库迁移"
$PY manage.py migrate --noinput

log "收集静态文件"
$PY manage.py collectstatic --noinput

log "安装 Apache vhost 到目标目录（会覆盖）"
if [[ ! -f "$VHOST_SRC" ]]; then
  echo "[deploy] 找不到 vhost 源文件：$VHOST_SRC"
  exit 1
fi

# 备份旧配置（保留最近 3 份）
if [[ -f "$VHOST_DST" ]]; then
  ts="$(date +%Y%m%d-%H%M%S)"
  cp "$VHOST_DST" "${VHOST_DST}.bak.$ts"
  ls -1t ${VHOST_DST}.bak.* 2>/dev/null | tail -n +4 | xargs -r rm -f
fi

cp "$VHOST_SRC" "$VHOST_DST"

log "检查 Apache 配置语法"
sudo /opt/bitnami/apache/bin/apachectl -t

log "重启 Apache"
sudo /opt/bitnami/ctlscript.sh restart apache

log "✅ 部署完成！现在访问：http://3.75.185.85/"
