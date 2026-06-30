#!/usr/bin/env bash
# IPFlow 数据备份脚本
#
# 备份 PostgreSQL 数据库 + MinIO 对象存储，按保留策略滚动清理旧备份。
# 适用于 cron 定时执行（建议每日一次）。
#
# 用法：
#   ./scripts/backup.sh                  # 使用环境变量配置
#   BACKUP_RETAIN_DAYS=14 ./scripts/backup.sh
#
# 环境变量（从 .env 或环境读取）：
#   DATABASE_URL          PostgreSQL 连接串（必填）
#   STORAGE_ENDPOINT      MinIO 端点（默认 localhost:9000）
#   STORAGE_ACCESS_KEY    MinIO 访问密钥
#   STORAGE_SECRET_KEY    MinIO 秘密密钥
#   STORAGE_BUCKET        MinIO 桶名（默认 ipflow）
#   BACKUP_DIR            本地备份根目录（默认 ./backups）
#   BACKUP_RETAIN_DAYS    保留天数（默认 7）
#
# 退出码：
#   0 成功；非零表示失败（cron 可据此告警）
set -euo pipefail

# ---------- 加载 .env（若存在）----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$PROJECT_ROOT/.env"
  set +a
fi

# ---------- 配置默认值 ----------
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
BACKUP_RETAIN_DAYS="${BACKUP_RETAIN_DAYS:-7}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_SUBDIR="$BACKUP_DIR/$TIMESTAMP"

STORAGE_ENDPOINT="${STORAGE_ENDPOINT:-localhost:9000}"
STORAGE_BUCKET="${STORAGE_BUCKET:-ipflow}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
err() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; }

# ---------- 前置检查 ----------
if [[ -z "${DATABASE_URL:-}" ]]; then
  err "DATABASE_URL 未配置，无法备份数据库"
  exit 1
fi

if ! command -v pg_dump >/dev/null 2>&1; then
  err "pg_dump 未安装，请先安装 PostgreSQL 客户端工具"
  exit 1
fi

mkdir -p "$BACKUP_SUBDIR"
log "备份目录：$BACKUP_SUBDIR"

# 把 postgresql+asyncpg:// 转为 pg_dump 可用的 postgresql://
PG_URL="${DATABASE_URL/postgresql+asyncpg:\/\//postgresql:\/\/}"
PG_URL="${PG_URL/postgresql+psycopg2:\/\//postgresql:\/\/}"

# ---------- 1. PostgreSQL 备份 ----------
log "开始备份 PostgreSQL ..."
DB_DUMP="$BACKUP_SUBDIR/db.sql.gz"
if pg_dump "$PG_URL" | gzip > "$DB_DUMP"; then
  DB_SIZE=$(du -h "$DB_DUMP" | cut -f1)
  log "PostgreSQL 备份完成：$DB_DUMP ($DB_SIZE)"
else
  err "PostgreSQL 备份失败"
  exit 2
fi

# ---------- 2. MinIO 备份（若 mc 可用）----------
if command -v mc >/dev/null 2>&1; then
  log "开始备份 MinIO 桶 $STORAGE_BUCKET ..."
  # 配置 mc alias（使用环境变量凭证）
  export MC_HOST_ipflow="https://${STORAGE_ACCESS_KEY:-}:${STORAGE_SECRET_KEY:-}@${STORAGE_ENDPOINT}"
  # MinIO 默认 http；若端点含 https 则用 https，否则 http
  PROTO="http"
  if [[ "$STORAGE_ENDPOINT" == *":443" ]] || [[ -n "${STORAGE_USE_SSL:-}" && "${STORAGE_USE_SSL}" == "true" ]]; then
    PROTO="https"
  fi
  export MC_HOST_ipflow="${PROTO}://${STORAGE_ACCESS_KEY:-}:${STORAGE_SECRET_KEY:-}@${STORAGE_ENDPOINT}"

  OBJ_DUMP="$BACKUP_SUBDIR/storage.tar.gz"
  if mc mirror --overwrite "ipflow/$STORAGE_BUCKET" "$BACKUP_SUBDIR/storage" 2>/dev/null \
     && tar -czf "$OBJ_DUMP" -C "$BACKUP_SUBDIR" storage; then
    OBJ_SIZE=$(du -h "$OBJ_DUMP" | cut -f1)
    log "MinIO 备份完成：$OBJ_DUMP ($OBJ_SIZE)"
    rm -rf "$BACKUP_SUBDIR/storage"
  else
    err "MinIO 备份失败（桶可能为空或 mc 配置有误），跳过对象存储备份"
  fi
else
  log "mc (MinIO Client) 未安装，跳过对象存储备份（仅数据库已备份）"
fi

# ---------- 3. 写入校验清单 ----------
CHECKSUM_FILE="$BACKUP_SUBDIR/CHECKSUM.sha256"
( cd "$BACKUP_SUBDIR" && sha256sum *.gz > "$CHECKSUM_FILE" 2>/dev/null || true )
log "校验清单：$CHECKSUM_FILE"

# ---------- 4. 清理过期备份 ----------
log "清理 $BACKUP_RETAIN_DAYS 天前的旧备份 ..."
DELETED=0
if [[ -d "$BACKUP_DIR" ]]; then
  while IFS= read -r old_dir; do
    if [[ -d "$old_dir" ]]; then
      rm -rf "$old_dir"
      DELETED=$((DELETED + 1))
      log "已删除旧备份：$(basename "$old_dir")"
    fi
  done < <(find "$BACKUP_DIR" -maxdepth 1 -type d -name "20*_*" -mtime +"$BACKUP_RETAIN_DAYS")
fi
log "清理完成，删除 $DELETED 个旧备份"

log "备份全部完成 ✓"
exit 0
