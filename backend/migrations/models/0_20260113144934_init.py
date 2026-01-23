from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "sys_user" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "real_name" VARCHAR(50) NOT NULL,
    "avatar" VARCHAR(255),
    "home_path" VARCHAR(255),
    "is_active" BOOL NOT NULL DEFAULT True
);
COMMENT ON COLUMN "sys_user"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_user"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_user"."id" IS '主键ID';
COMMENT ON COLUMN "sys_user"."username" IS '用户名';
COMMENT ON COLUMN "sys_user"."password_hash" IS '密码哈希';
COMMENT ON COLUMN "sys_user"."real_name" IS '真实姓名';
COMMENT ON COLUMN "sys_user"."avatar" IS '头像';
COMMENT ON COLUMN "sys_user"."home_path" IS '首页路径';
COMMENT ON COLUMN "sys_user"."is_active" IS '是否启用';
COMMENT ON TABLE "sys_user" IS '用户模型。';
CREATE TABLE IF NOT EXISTS "sys_role" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL,
    "code" VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON COLUMN "sys_role"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_role"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_role"."id" IS '主键ID';
COMMENT ON COLUMN "sys_role"."name" IS '角色名称';
COMMENT ON COLUMN "sys_role"."code" IS '角色编码';
COMMENT ON TABLE "sys_role" IS '角色模型（RBAC）。';
CREATE TABLE IF NOT EXISTS "sys_menu" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL,
    "path" VARCHAR(255) NOT NULL UNIQUE,
    "component" VARCHAR(255),
    "meta" JSONB,
    "status" INT NOT NULL DEFAULT 1,
    "parent_id" INT REFERENCES "sys_menu" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "sys_menu"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_menu"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_menu"."id" IS '主键ID';
COMMENT ON COLUMN "sys_menu"."name" IS '菜单名称';
COMMENT ON COLUMN "sys_menu"."path" IS '路由路径';
COMMENT ON COLUMN "sys_menu"."component" IS '前端组件路径/标识';
COMMENT ON COLUMN "sys_menu"."meta" IS '菜单元信息（图标、标题、排序等）';
COMMENT ON COLUMN "sys_menu"."status" IS '状态：1启用 0禁用';
COMMENT ON COLUMN "sys_menu"."parent_id" IS '父级菜单';
COMMENT ON TABLE "sys_menu" IS '菜单模型（用于动态路由）。';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "sys_user_role" (
    "sys_user_id" INT NOT NULL REFERENCES "sys_user" ("id") ON DELETE CASCADE,
    "role_id" INT NOT NULL REFERENCES "sys_role" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "sys_user_role" IS '用户角色关系';
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_sys_user_ro_sys_use_ed7daf" ON "sys_user_role" ("sys_user_id", "role_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "8fs1+JaA=="
)
