#!/bin/bash
# IPFlow 开发环境启动脚本

set -e

echo "🚀 启动 IPFlow 开发环境..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    uv venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查依赖
if ! python -c "import ipflow" 2>/dev/null; then
    echo "📦 安装依赖..."
    uv pip install -e ".[dev]"
fi

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，使用 .env.example"
    cp .env.example .env
fi

# 启动服务
echo "🌐 启动 FastAPI 服务..."
exec uvicorn src.ipflow.main:app --host 0.0.0.0 --port 8000 --reload
