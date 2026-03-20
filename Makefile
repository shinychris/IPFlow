# IPFlow 项目 Makefile
# 开发工作流自动化

.PHONY: help install dev build test lint format clean migrate seed deploy

# 默认目标
help:
	@echo "IPFlow Development Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install      - 安装所有依赖"
	@echo "  make migrate      - 执行数据库迁移"
	@echo "  make seed         - 插入测试数据"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev          - 启动开发服务器（后端+前端）"
	@echo "  make dev-backend  - 仅启动 Python 后端"
	@echo "  make dev-frontend - 仅启动 Next.js 前端"
	@echo ""
	@echo "Build Commands:"
	@echo "  make build        - 构建生产版本"
	@echo "  make build-frontend - 仅构建前端"
	@echo ""
	@echo "Quality Commands:"
	@echo "  make test         - 运行所有测试"
	@echo "  make test-backend - 运行后端测试"
	@echo "  make lint         - 运行代码检查"
	@echo "  make format       - 格式化代码"
	@echo ""
	@echo "Database Commands:"
	@echo "  make migrate      - 执行数据库迁移"
	@echo "  make migrate-down - 回滚数据库迁移"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up    - 启动 Docker 环境"
	@echo "  make docker-down  - 停止 Docker 环境"
	@echo "  make docker-build - 构建 Docker 镜像"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean        - 清理临时文件"
	@echo "  make clean-all    - 清理所有生成文件"

# ============================================
# Setup Commands
# ============================================

install:
	@echo "Installing frontend dependencies..."
	pnpm install
	@echo "Installing backend dependencies..."
	cd backend && pip install -e ".[dev]"

migrate:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade -1

seed:
	cd backend && python scripts/seed_data.py

# ============================================
# Development Commands
# ============================================

dev:
	@echo "Starting development servers..."
	@make dev-backend &
	@sleep 3
	@make dev-frontend &
	@wait

dev-backend:
	cd backend && uvicorn ipflow.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting Next.js development server on http://localhost:3000"
	pnpm dev

# ============================================
# Build Commands
# ============================================

build: build-frontend

build-frontend:
	pnpm build

# ============================================
# Quality Commands
# ============================================

test: test-backend

test-backend:
	cd backend && pytest -v

test-cov:
	cd backend && pytest --cov=src --cov-report=html

lint: lint-backend lint-frontend

lint-backend:
	cd backend && ruff check src/ tests/
	cd backend && mypy src/

lint-frontend:
	@echo "Running frontend type check..."
	pnpm check

format: format-backend format-frontend

format-backend:
	cd backend && black src/ tests/
	cd backend && isort src/ tests/

format-frontend:
	@echo "No frontend formatter configured"

# ============================================
# Docker Commands
# ============================================

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

# ============================================
# Utility Commands
# ============================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean
	rm -rf dist node_modules .next
	cd backend && rm -rf build dist .venv
