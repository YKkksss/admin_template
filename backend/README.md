# 后端服务（FastAPI）

本目录用于实现项目的后端服务，技术栈以 `FastAPI + Tortoise ORM + Aerich + Pydantic Settings + uv` 为核心。

## 快速开始

1. 进入后端目录并安装依赖（会创建本地虚拟环境）：

```bash
cd backend
uv sync
```

2. 启动开发服务：

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. 访问：

- Swagger：`http://localhost:8000/docs`
- OpenAPI：`http://localhost:8000/openapi.json`

## 环境变量

请参考 `backend/.env.example`，复制为 `backend/.env` 后再按需调整。

说明：
- 当使用 PostgreSQL 且目标库不存在时，启动阶段会尝试自动创建数据库（需要账号具备 `CREATE DATABASE` 权限，并可连接到 `postgres` 或 `template1`）。
- 开发联调阶段可通过 `INIT_SUPERUSER=true` 初始化超级管理员账号（参数见 `.env.example`），生产环境请关闭或移除。

## 数据库迁移（Aerich）

本项目使用 Aerich 管理 Tortoise ORM 的迁移，配置位于 `backend/pyproject.toml` 的 `[tool.aerich]`。

常用命令：

```bash
cd backend

# 首次初始化（会生成 migrations 并创建初始迁移）
uv run aerich init-db

# 生成迁移文件
uv run aerich migrate --name "add_new_field"

# 应用迁移
uv run aerich upgrade

# 回滚迁移（示例：回滚 1 次）
uv run aerich downgrade -1
```
