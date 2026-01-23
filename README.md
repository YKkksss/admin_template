# admin_template

基于 **vue-vben-admin 5.x（Ant Design Vue）** + **FastAPI** 的后台管理系统模板项目，目标是沉淀一套可复用的“开箱即用”基础能力（认证、RBAC、动态菜单、系统管理常用模块等），便于后续快速二次开发。

## 目录结构

```text
admin_template/
├─ web/                       # 前端（pnpm monorepo）
│  └─ apps/web-antd/           # 当前使用的前端实现（Ant Design Vue）
├─ backend/                   # 后端（FastAPI + Tortoise ORM + Aerich + uv）
├─ docs/                      # 项目文档（开发文档、权限说明等）
└─ dev.bat                    # Windows 一键启动脚本（前端/后端）
```

## 已落地的基础模块（持续完善中）

- 认证与授权：JWT 登录/注册、获取当前用户、权限码下发（RBAC）
- 动态路由/菜单：后端下发菜单树，前端按权限生成路由与侧边栏（混合模式：少量静态 + 大量后端动态）
- 系统管理：用户/角色/部门/菜单管理
- 数据字典：字典类型 + 字典数据（字典数据页作为跳转页，不单独在菜单中展示）
- 参数配置：系统配置项维护
- 日志审计：登录日志、操作日志（后端中间件自动记录非 GET 请求）
- 消息通知/发布（开发中）：通知列表、发布范围、实时推送规划

## 快速开始（推荐）

### 方式 A：Windows 一键启动

在项目根目录双击或命令行执行：

```bat
dev.bat
```

按提示选择：
- 1：启动前端（web / dev:antd）
- 2：启动后端（backend / uvicorn）

### 方式 B：手动启动

#### 1) 前端

要求：Node.js >= 20、pnpm >= 10（建议使用 corepack）

```bash
cd web
corepack enable
pnpm install
pnpm dev:antd
```

访问：`http://localhost:5666`

说明：开发环境下前端会将 `/api/*` 代理到后端 `http://localhost:8000/api/v1/*`（配置见 `web/apps/web-antd/vite.config.mts`）。

#### 2) 后端

要求：Python 3.12+、uv

```bash
cd backend
uv sync --all-groups
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：
- Swagger：`http://localhost:8000/docs`
- OpenAPI：`http://localhost:8000/openapi.json`

## 配置说明

### 后端环境变量

- 模板：`backend/.env.example`
- 实际使用：复制为 `backend/.env` 并按需修改

关键点：
- 数据库：支持 PostgreSQL（推荐）；启动阶段会尝试“自动创建数据库”（需要账号具备 `CREATE DATABASE` 权限，且可连接到 `postgres` 或 `template1` 管理库）。
- PostgreSQL SSL：若遇到 `unexpected connection_lost()` 这类握手异常，可将 `POSTGRES_SSL=false`（以实际部署环境为准）。
- 开发期初始化超级管理员：设置 `INIT_SUPERUSER=true` 且提供 `SUPERUSER_PASSWORD`；生产环境请关闭或移除。

### 数据库迁移（Aerich）

常用命令（后端目录执行）：

```bash
cd backend
uv run aerich migrate --name "your_change"
uv run aerich upgrade
```

## 权限与菜单（必看）

权限设计说明与扩展方式见：`docs/权限与RBAC说明.md`  
总体开发规划与接口约定见：`docs/开发文档.md`

## 常见问题

- 前端能打开但接口 404/不通：确认后端已启动在 `8000`，并检查 `web/apps/web-antd/vite.config.mts` 的代理配置。
- 后端端口占用：修改启动命令的 `--port`，或关闭占用 8000 的进程。
- 数据库连接失败：优先检查 `backend/.env` 配置与网络可达性；PostgreSQL 服务器不支持 SSL 时确保 `POSTGRES_SSL=false`。

