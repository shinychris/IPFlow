# IPFlow 部署指南

## 1. 部署概述

IPFlow 支持以下部署方式：

| 部署方式 | 适用场景 | 复杂度 |
|----------|----------|--------|
| Docker Compose | 开发环境、小型生产环境 | 低 |
| Kubernetes | 生产环境、大规模部署 | 高 |
| 传统服务器 | 单机部署、测试环境 | 中 |
| 云平台 | AWS/Azure/GCP | 中 |

## 2. 环境要求

### 2.1 最低配置

```
CPU: 2核
内存: 4GB
存储: 50GB SSD
网络: 10Mbps
```

### 2.2 推荐配置

```
CPU: 4核+
内存: 8GB+
存储: 100GB SSD
网络: 100Mbps+
```

### 2.3 依赖服务

| 服务 | 版本 | 用途 |
|------|------|------|
| PostgreSQL | 14+ | 主数据库 |
| Redis | 6+ | 缓存、会话 |
| MinIO | 最新 | 对象存储（可选） |
| Nginx | 1.20+ | 反向代理 |

## 3. Docker Compose 部署

### 3.1 准备工作

```bash
# 克隆项目
git clone https://github.com/your-org/ipflow.git
cd ipflow

# 创建环境文件
cp .env.example .env
```

### 3.2 配置文件

编辑 `.env` 文件：

```bash
# 应用配置
APP_NAME=IPFlow
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-here

# 数据库
DATABASE_URL=postgresql+asyncpg://ipflow:password@db:5432/ipflow

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO
STORAGE_TYPE=minio
STORAGE_ENDPOINT=minio:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=ipflow

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 邮件（可选）
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your-password
```

### 3.3 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  # 应用服务
  app:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: ipflow-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - STORAGE_TYPE=${STORAGE_TYPE}
      - STORAGE_ENDPOINT=${STORAGE_ENDPOINT}
      - STORAGE_ACCESS_KEY=${STORAGE_ACCESS_KEY}
      - STORAGE_SECRET_KEY=${STORAGE_SECRET_KEY}
      - STORAGE_BUCKET=${STORAGE_BUCKET}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
      - minio
    volumes:
      - ./backend:/app
      - app_logs:/app/logs
    networks:
      - ipflow-network

  # 前端服务
  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ipflow-web
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - app
    networks:
      - ipflow-network

  # 数据库
  db:
    image: postgres:15-alpine
    container_name: ipflow-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=ipflow
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=ipflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - ipflow-network

  # Redis
  redis:
    image: redis:7-alpine
    container_name: ipflow-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - ipflow-network

  # MinIO
  minio:
    image: minio/minio:latest
    container_name: ipflow-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${STORAGE_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${STORAGE_SECRET_KEY}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    networks:
      - ipflow-network

  # Nginx（反向代理）
  nginx:
    image: nginx:alpine
    container_name: ipflow-nginx
    restart: unless-stopped
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
      - web
    networks:
      - ipflow-network

volumes:
  postgres_data:
  redis_data:
  minio_data:
  app_logs:

networks:
  ipflow-network:
    driver: bridge
```

### 3.4 启动服务

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 执行数据库迁移
docker-compose exec backend alembic upgrade head

# 创建超级管理员
docker-compose exec backend python -c "
from ipflow.scripts.create_superuser import create_superuser
import asyncio
asyncio.run(create_superuser('admin@example.com', 'Admin123!', '管理员'))
"
```

### 3.5 更新部署

```bash
# 拉取最新代码
git pull

# 重建镜像
docker-compose build

# 重启服务
docker-compose up -d

# 执行迁移
docker-compose exec backend alembic upgrade head
```

## 4. Kubernetes 部署

### 4.1 创建命名空间

```bash
kubectl create namespace ipflow
```

### 4.2 ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ipflow-config
  namespace: ipflow
data:
  APP_NAME: "IPFlow"
  ENVIRONMENT: "production"
  DEBUG: "false"
  DATABASE_URL: "postgresql://ipflow:password@postgres:5432/ipflow"
  REDIS_URL: "redis://redis:6379/0"
```

### 4.3 Secret

```bash
# 创建Secret
kubectl create secret generic ipflow-secrets \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=DATABASE_PASSWORD=$(openssl rand -hex 16) \
  -n ipflow
```

### 4.4 PostgreSQL

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: ipflow
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15-alpine
          env:
            - name: POSTGRES_USER
              value: ipflow
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: ipflow-secrets
                  key: DATABASE_PASSWORD
            - name: POSTGRES_DB
              value: ipflow
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-storage
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 20Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: ipflow
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
```

### 4.5 Redis

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: ipflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: ipflow
spec:
  selector:
    app: redis
  ports:
    - port: 6379
```

### 4.6 应用部署

```yaml
# k8s/app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ipflow-app
  namespace: ipflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ipflow-app
  template:
    metadata:
      labels:
        app: ipflow-app
    spec:
      containers:
        - name: app
          image: your-registry/ipflow-backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: ipflow-config
            - secretRef:
                name: ipflow-secrets
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health/simple
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/simple
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: ipflow-app
  namespace: ipflow
spec:
  selector:
    app: ipflow-app
  ports:
    - port: 8000
```

### 4.7 Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ipflow-ingress
  namespace: ipflow
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - api.ipflow.com
      secretName: ipflow-tls
  rules:
    - host: api.ipflow.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ipflow-app
                port:
                  number: 8000
```

### 4.8 部署命令

```bash
# 应用所有配置
kubectl apply -f k8s/

# 查看部署状态
kubectl get pods -n ipflow

# 查看日志
kubectl logs -f deployment/ipflow-app -n ipflow

# 执行迁移
kubectl exec -it deployment/ipflow-app -n ipflow -- alembic upgrade head
```

## 5. 传统服务器部署

### 5.1 环境准备

```bash
# Ubuntu 22.04
sudo apt update
sudo apt install -y python3.12 python3.12-venv nodejs npm postgresql redis-server nginx

# 创建工作目录
sudo mkdir -p /opt/ipflow
sudo chown $USER:$USER /opt/ipflow
cd /opt/ipflow
```

### 5.2 后端部署

```bash
# 克隆代码
git clone https://github.com/your-org/ipflow.git .

# 创建虚拟环境
cd backend
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e ".[prod]"

# 配置环境变量
sudo tee /etc/systemd/system/ipflow.env << EOF
DATABASE_URL=postgresql://ipflow:password@localhost:5432/ipflow
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
EOF

# 执行迁移
alembic upgrade head

# 创建 systemd 服务
sudo tee /etc/systemd/system/ipflow.service << 'EOF'
[Unit]
Description=IPFlow Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ipflow
Group=ipflow
WorkingDirectory=/opt/ipflow/backend
EnvironmentFile=/etc/systemd/system/ipflow.env
ExecStart=/opt/ipflow/backend/venv/bin/uvicorn ipflow.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable ipflow
sudo systemctl start ipflow
```

### 5.3 前端部署

```bash
cd /opt/ipflow/frontend

# 安装依赖
npm install

# 构建
npm run build

# 复制到Nginx目录
sudo cp -r dist/* /var/www/ipflow/
```

### 5.4 Nginx配置

```nginx
# /etc/nginx/sites-available/ipflow
server {
    listen 80;
    server_name ipflow.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ipflow.com;

    ssl_certificate /etc/ssl/certs/ipflow.crt;
    ssl_certificate_key /etc/ssl/private/ipflow.key;

    # 前端静态文件
    location / {
        root /var/www/ipflow;
        try_files $uri $uri/ /index.html;
        expires 1d;
    }

    # API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 6. 云平台部署

### 6.1 AWS 部署

```bash
# 使用 ECS + Fargate
# 1. 创建 ECR 仓库
aws ecr create-repository --repository-name ipflow

# 2. 构建并推送镜像
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
docker build -t ipflow .
docker tag ipflow:latest $ECR_URL/ipflow:latest
docker push $ECR_URL/ipflow:latest

# 3. 使用 AWS Copilot 部署
copilot init
```

### 6.2 阿里云部署

```bash
# 使用容器服务 ACK
# 1. 创建 ACK 集群
aliyun cs POST /clusters

# 2. 配置 kubectl
aliyun cs GET /k8s/[cluster-id]/user_config

# 3. 部署应用
kubectl apply -f k8s/
```

## 7. SSL证书配置

### 7.1 Let's Encrypt

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d ipflow.com -d www.ipflow.com

# 自动续期
sudo certbot renew --dry-run
```

### 7.2 手动配置

```bash
# 生成私钥
openssl genrsa -out ipflow.key 2048

# 生成 CSR
openssl req -new -key ipflow.key -out ipflow.csr

# 生成自签名证书（测试用）
openssl x509 -req -days 365 -in ipflow.csr -signkey ipflow.key -out ipflow.crt
```

## 8. 监控与日志

### 8.1 日志配置

```bash
# 查看应用日志
sudo journalctl -u ipflow -f

# Docker日志
docker-compose logs -f backend

# K8s日志
kubectl logs -f deployment/ipflow-app -n ipflow
```

### 8.2 监控集成

```yaml
# Prometheus + Grafana
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## 9. 备份与恢复

### 9.1 数据库备份

```bash
# 自动备份脚本
#!/bin/bash
BACKUP_DIR="/backup/ipflow"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份 PostgreSQL
pg_dump -h localhost -U ipflow ipflow > $BACKUP_DIR/db_$DATE.sql

# 备份 MinIO
mc mirror minio/ipflow $BACKUP_DIR/files_$DATE

# 保留最近7天
find $BACKUP_DIR -type f -mtime +7 -delete
```

### 9.2 恢复数据

```bash
# 恢复数据库
psql -h localhost -U ipflow ipflow < backup.sql

# 恢复文件
mc mirror backup/files minio/ipflow
```

## 10. 故障排查

### 10.1 常见问题

**问题1: 数据库连接失败**
```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U ipflow -d ipflow

# 查看日志
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

**问题2: 应用启动失败**
```bash
# 检查环境变量
cat /etc/systemd/system/ipflow.env

# 查看日志
sudo journalctl -u ipflow -n 100 --no-pager

# 手动启动测试
cd /opt/ipflow/backend
source venv/bin/activate
uvicorn ipflow.main:app --host 127.0.0.1 --port 8000
```

**问题3: Nginx 502错误**
```bash
# 检查后端服务
curl http://127.0.0.1:8000/health/simple

# 检查 Nginx 配置
sudo nginx -t

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 10.2 性能调优

```bash
# PostgreSQL 优化
sudo tee -a /etc/postgresql/15/main/postgresql.conf << EOF
max_connections = 200
shared_buffers = 512MB
effective_cache_size = 2GB
work_mem = 16MB
maintenance_work_mem = 256MB
EOF

sudo systemctl restart postgresql

# Nginx 优化
worker_processes auto;
worker_connections 4096;
```

## 11. 安全加固

### 11.1 防火墙配置

```bash
# UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 11.2 安全扫描

```bash
# 依赖安全检查
pip install safety
safety check

# Docker镜像扫描
docker scan ipflow:latest
```

## 12. 维护窗口

### 12.1 计划维护

```bash
# 1. 启用维护模式
curl -X POST https://api.ipflow.com/admin/maintenance -d '{"enabled": true}'

# 2. 备份数据
./scripts/backup.sh

# 3. 更新代码
git pull

# 4. 执行迁移
alembic upgrade head

# 5. 重启服务
sudo systemctl restart ipflow

# 6. 健康检查
curl https://api.ipflow.com/health

# 7. 关闭维护模式
curl -X POST https://api.ipflow.com/admin/maintenance -d '{"enabled": false}'
```
