# ==========================================
# IPFlow Backend Dockerfile
# 多阶段构建，生产环境优化
# ==========================================

# 阶段1: 构建依赖
FROM python:3.12-slim as builder

WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制依赖配置
COPY pyproject.toml ./

# 创建虚拟环境并安装依赖
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache -e "."

# 阶段2: 生产镜像
FROM python:3.12-slim as production

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY src/ ./src/

# 非 root 用户运行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.ipflow.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# 阶段3: 开发镜像
FROM python:3.12-slim as development

WORKDIR /app

# 安装开发依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制依赖配置
COPY pyproject.toml ./

# 安装所有依赖（包括开发依赖）
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache -e ".[dev]"

# 复制应用代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.ipflow.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
