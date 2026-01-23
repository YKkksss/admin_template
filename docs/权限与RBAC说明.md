# 权限与 RBAC 说明

本文档用于说明本项目的权限设计、数据模型、前后端交互方式，以及如何新增“接口级权限”（API 权限）与“按钮/操作权限”并完成授权。

## 1. 目标与原则

- **统一数据源**：权限点、菜单、按钮都统一存放在 `sys_menu` 表中，通过 `type` 区分。
- **RBAC 模型**：用户 ←(多对多)→ 角色 ←(多对多)→ 菜单/权限点。
- **后端强制拦截**：前端的显隐只能提升体验，安全性必须依赖后端校验（403）。
- **超级管理员全放行**：角色编码为 `super`（由 `SUPERUSER_ROLE_CODE` 配置）默认拥有全部菜单与全部权限码。

## 2. 核心概念

### 2.1 用户（User）

- 表：`sys_user`
- 关键字段：
  - `username`：用户名（唯一）
  - `password_hash`：密码哈希
  - `real_name`：姓名
  - `is_active`：是否启用（禁用后无法登录）
  - `dept_id`：所属部门（可空）

### 2.2 角色（Role）

- 表：`sys_role`
- 关键字段：
  - `name`：角色名称（展示）
  - `code`：角色编码（写入 JWT 的 `roles`，用于鉴权）
  - `status`：状态

### 2.3 菜单与权限点（Menu / Permission）

本项目将“菜单路由节点”和“权限点（按钮/操作/接口权限）”统一存储在 `sys_menu`：

- 表：`sys_menu`
- 关键字段：
  - `type`：节点类型
    - `catalog`：目录（仅用于分组）
    - `menu`：菜单（对应一个页面路由）
    - `embedded` / `link`：内嵌/外链（前端用 IFrameView 渲染）
    - `button`：权限点（不产生路由，用于按钮/接口权限）
  - `auth_code`：权限码（可空；建议在需要鉴权的节点上填写）
  - `path` / `component`：仅对 `menu/catalog/link/embedded` 有意义
  - `meta`：前端菜单渲染元信息（图标、标题、排序、隐藏等）

你可以把 `type='button'` 的节点理解为：

- **一个权限点 = 一个 `authCode`**
- 它不一定真的对应“页面上的按钮”，也可以代表“接口权限”（例如查询、导出、审批等）

## 3. 数据表关系（简化）

- `sys_user`：用户
- `sys_role`：角色
- `sys_menu`：菜单 + 权限点（button）
- `sys_user_role`：用户-角色（多对多）
- `sys_role_menu`：角色-菜单/权限点（多对多）
- `sys_dept`：部门（树结构，可选）

## 4. 运行时流程：菜单、按钮权限与 API 权限

### 4.1 登录与 JWT

- 登录成功后后端签发 JWT，包含：
  - `sub`：用户名
  - `roles`：角色编码列表（来自 `sys_user_role`）

### 4.2 菜单/路由权限（能不能“看到并进入页面”）

- 前端登录后请求：`GET /api/v1/menu/all`
- 后端返回**该用户可访问的菜单树**（过滤掉 `type='button'`），用于前端动态路由与侧边栏渲染。
- 如果某个菜单节点未被授权到用户角色：
  - 后端不会下发该菜单
  - 前端不会生成该动态路由（自然也就无法进入）

### 4.3 权限码（按钮显隐 / 操作点）

- 前端会请求：`GET /api/v1/auth/codes`
- 后端返回：当前用户可用的 `authCode` 列表（来自 `sys_menu.auth_code` + `sys_role_menu`）
- 前端可用这些 `authCode` 做按钮显隐、操作入口控制。

### 4.4 API 权限（后端强制拦截）

当你希望“即使用户通过抓包/脚本直接调用接口也必须被拒绝”，就需要在后端接口加权限依赖校验。

本项目提供了统一的权限依赖：

- `backend/app/api/v1/deps.py` 中的 `require_permissions(...)`
- 行为：
  - 若用户包含超级管理员角色编码（默认 `super`）→ 放行
  - 否则计算当前用户的权限码集合（同 `/auth/codes`）
  - 缺少任一必须权限码 → 返回 403 “无权限”

目前系统管理相关接口已经按权限码进行了 API 级拦截（示例）：

- 菜单管理：`System:Menu:List/Create/Edit/Delete`
- 角色管理：`System:Role:List/Create/Edit/Delete`
- 部门管理：`System:Dept:List/Create/Edit/Delete`
- 用户管理：`System:User:List/Create/Edit/Delete/ResetPassword`

## 5. “接口权限”怎么创建？

接口权限的创建包含两部分：**创建权限码** 与 **接口使用该权限码**。

### 5.1 创建权限码（在菜单管理里新增 button 节点）

步骤：

1. 打开前端页面：系统管理 → 菜单管理
2. 选择一个父节点（通常是某个业务菜单），点击“新增下级”
3. `类型(type)` 选择 `button`
4. 填写 `authCode`（必须唯一），例如：
   - `Order:Query`
   - `Order:Export`
   - `Order:Approve`
5. 保存

此时权限点已经进入 `sys_menu`，可以在“角色管理”里勾选授权。

### 5.2 让接口真正受控（在后端接口加校验）

在对应接口上增加依赖，例如：

- 查询接口需要：`Order:Query`
- 导出接口需要：`Order:Export`

做法是在 FastAPI 路由上使用 `Depends(require_permissions('Order:Query'))`。

## 6. 授权：角色与用户

### 6.1 给角色授权

1. 系统管理 → 角色管理 → 新增/编辑角色
2. 勾选权限树（包含菜单节点与 button 权限点）
3. 保存

数据会写入 `sys_role_menu`。

### 6.2 给用户分配角色

1. 系统管理 → 用户管理
2. 新增/编辑用户 → 选择角色
3. 保存

数据会写入 `sys_user_role`。

## 7. authCode 命名规范建议

推荐格式（易读、易扩展、便于搜索）：

- `模块:资源:动作`

示例：

- `System:User:List`
- `System:User:Create`
- `Order:Order:List`
- `Order:Order:Export`

注意：

- **统一大小写与分隔符**（建议固定使用 `:`）
- **同一动作使用同一命名**（例如统一 `List/Create/Edit/Delete`）
- 保持 **可推断性**：看到权限码就能大概知道作用范围

## 8. 两种常见权限设计方式（对比）

### 方案 A：菜单权限与接口权限合一（推荐默认）

- 菜单节点（`type=menu`）也填写 `authCode`，例如 `Order:List`
- 列表接口也要求 `Order:List`

优点：

- 不会出现“进得去页面但拉不到数据”的体验问题
- 授权更直观：给了菜单就等于给了页面核心接口能力

缺点：

- 不利于极少数场景：希望允许进入页面但不允许查询数据

### 方案 B：菜单权限与接口权限分离

- 菜单节点不填 `authCode`（只控制路由可见）
- 列表接口要求独立权限点（`type=button`）例如 `Order:Query`

优点：

- 权限颗粒更细，可以允许进入页面但限制关键操作/数据

缺点：

- 更容易出现“页面可见但操作 403”的情况，需要前端额外做提示与降级

## 9. 常见问题排查

### 9.1 进入页面后接口 403（无权限）

排查顺序：

1. 用当前账号调用 `GET /api/v1/auth/codes` 看是否包含所需权限码
2. 进入“角色管理”确认角色是否勾选了对应 `button` 节点（或菜单节点的 `authCode`）
3. 确认后端接口上是否使用了对应的 `require_permissions(...)`，且权限码字符串一致

### 9.2 看不到某个菜单/路由

1. 用当前账号调用 `GET /api/v1/menu/all` 看是否下发该菜单
2. 检查角色是否绑定了该菜单节点（`sys_role_menu`）
3. 检查 `sys_menu.status=1`（禁用菜单不会下发）

### 9.3 按钮不显示

1. 检查 `/api/v1/auth/codes` 是否包含按钮对应 `authCode`
2. 检查菜单管理中该 `button` 节点是否填写了 `authCode`
3. 检查角色授权是否勾选了该 `button` 节点

## 10. 关键代码位置（方便二次开发）

- 权限依赖：`backend/app/api/v1/deps.py`
- 菜单/权限码计算：`backend/app/services/menu.py`
- 动态菜单下发：`backend/app/api/v1/endpoints/menu.py`
- 权限码下发：`backend/app/api/v1/endpoints/auth.py`
- 菜单/角色/部门/用户管理接口：
  - `backend/app/api/v1/endpoints/system/menu.py`
  - `backend/app/api/v1/endpoints/system/role.py`
  - `backend/app/api/v1/endpoints/system/dept.py`
  - `backend/app/api/v1/endpoints/system/user.py`

---

如果你希望增加一个“权限点列表”页面（平铺查看所有 `authCode`、搜索、查看被哪些角色引用），可以在现有“菜单管理”基础上补一个只读/筛选视图，后端只需提供一个 `GET /system/permission/list`（从 `sys_menu` 过滤 `auth_code is not null`）即可。

