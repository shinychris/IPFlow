# 数据备份与恢复

> IPFlow 商业化部署的数据保护方案。建议在生产环境配置定时备份并定期演练恢复。

## 一、备份内容

| 数据 | 说明 | 工具 |
|------|------|------|
| **PostgreSQL** | 全部业务数据（用户、项目、材料、订阅、支付订单等） | `pg_dump` |
| **MinIO / S3** | 上传的源码包、证明材料、图样、导出包 | `mc`（MinIO Client） |

## 二、备份脚本

脚本位于 `scripts/backup.sh`，自动从 `.env` 读取配置。

```bash
# 立即执行一次备份
./scripts/backup.sh

# 自定义保留天数（默认 7 天）
BACKUP_RETAIN_DAYS=14 ./scripts/backup.sh
```

备份产物结构：
```
backups/
└── 20260630_001500/
    ├── db.sql.gz          # PostgreSQL 全库转储（gzip 压缩）
    ├── storage.tar.gz     # MinIO 桶打包（若 mc 可用）
    └── CHECKSUM.sha256    # 完整性校验清单
```

### 定时备份（cron）

```bash
# 每日凌晨 3 点备份，日志写入 /var/log/ipflow-backup.log
# crontab -e
0 3 * * * cd /path/to/IPFlow && ./scripts/backup.sh >> /var/log/ipflow-backup.log 2>&1
```

建议配合监控：cron 失败（脚本非零退出）触发告警（接入 Sentry / Webhook）。

### 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `DATABASE_URL` | （必填） | PostgreSQL 连接串 |
| `STORAGE_ENDPOINT` | `localhost:9000` | MinIO 端点 |
| `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` | | MinIO 凭证 |
| `STORAGE_BUCKET` | `ipflow` | 桶名 |
| `BACKUP_DIR` | `./backups` | 本地备份根目录 |
| `BACKUP_RETAIN_DAYS` | `7` | 保留天数 |

## 三、恢复流程

### 1. 恢复 PostgreSQL

```bash
# 解压并恢复到目标数据库
gunzip -c backups/20260630_001500/db.sql.gz | psql "$DATABASE_URL"
```

⚠️ 恢复会覆盖现有数据，务必先在测试环境验证，并对生产库做恢复前快照。

### 2. 恢复 MinIO 对象存储

```bash
# 解压并同步回 MinIO 桶
export MC_HOST_ipflow="http://$STORAGE_ACCESS_KEY:$STORAGE_SECRET_KEY@$STORAGE_ENDPOINT"
tar -xzf backups/20260630_001500/storage.tar.gz -C /tmp/restore
mc mirror --overwrite /tmp/restore/storage "ipflow/$STORAGE_BUCKET"
```

### 3. 校验完整性

```bash
# 对比备份时的校验清单
cd backups/20260630_001500
sha256sum -c CHECKSUM.sha256
```

## 四、异地容灾（推荐）

本地备份不足以应对主机故障，建议**异地复制**：

- **方案 A（对象存储同步）**：用 `rclone` 或 `aws s3 sync` 把 `backups/` 同步到云对象存储（OSS/S3/COS），开启版本控制。
- **方案 B（数据库托管）**：使用云数据库（RDS/PolarDB）自带的自动备份与时间点恢复（PITR），免去自维护 pg_dump。

```bash
# 方案 A 示例：每日同步备份到 OSS
rclone sync /path/to/IPFlow/backups oss:ipflow-backups/ --backup-dir archive/$(date +%Y%m%d)
```

## 五、备份演练

定期（至少每月一次）执行恢复演练：
1. 在隔离的测试环境恢复备份
2. 验证关键业务数据可读（登录、项目列表、导出包下载）
3. 记录恢复耗时，确保 RTO（恢复时间目标）满足业务要求
