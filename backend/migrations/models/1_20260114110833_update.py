from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sys_role" ADD "status" INT NOT NULL DEFAULT 1;
        ALTER TABLE "sys_role" ADD "remark" VARCHAR(255);
        COMMENT ON COLUMN "sys_role"."code" IS '角色编码（用于鉴权与 JWT roles）';
        ALTER TABLE "sys_menu" ADD "auth_code" VARCHAR(100) UNIQUE;
        ALTER TABLE "sys_menu" ADD "type" VARCHAR(20) NOT NULL DEFAULT 'menu';
        ALTER TABLE "sys_menu" ADD "active_path" VARCHAR(255);
        ALTER TABLE "sys_menu" ALTER COLUMN "path" DROP NOT NULL;
        COMMENT ON COLUMN "sys_menu"."path" IS '路由路径（按钮可为空）';
        COMMENT ON COLUMN "sys_menu"."name" IS '菜单名称（路由 name，需全局唯一）';
        COMMENT ON COLUMN "sys_menu"."component" IS '前端组件标识（如 /system/menu/list 或 IFrameView）';
        
COMMENT ON COLUMN "sys_role"."status" IS '状态：1启用 0禁用';
COMMENT ON COLUMN "sys_role"."remark" IS '备注';
COMMENT ON COLUMN "sys_menu"."auth_code" IS '权限标识（菜单/按钮/接口权限码）';
COMMENT ON COLUMN "sys_menu"."type" IS '菜单类型：catalog/menu/embedded/link/button';
COMMENT ON COLUMN "sys_menu"."active_path" IS '激活菜单路径（用于高亮）';
        CREATE TABLE "sys_role_menu" (
    "sys_role_id" INT NOT NULL REFERENCES "sys_role" ("id") ON DELETE CASCADE,
    "menu_id" INT NOT NULL REFERENCES "sys_menu" ("id") ON DELETE CASCADE
);
        COMMENT ON TABLE "sys_role_menu" IS '角色菜单/权限关系';
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_sys_menu_name_dbc684" ON "sys_menu" ("name");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sys_menu" DROP CONSTRAINT IF EXISTS "sys_menu_name_key";
        DROP INDEX IF EXISTS "uid_sys_menu_name_dbc684";
        DROP INDEX IF EXISTS "uid_sys_menu_auth_co_15c354";
        DROP TABLE IF EXISTS "sys_role_menu";
        ALTER TABLE "sys_menu" DROP COLUMN "auth_code";
        ALTER TABLE "sys_menu" DROP COLUMN "type";
        ALTER TABLE "sys_menu" DROP COLUMN "active_path";
        ALTER TABLE "sys_menu" ALTER COLUMN "path" SET NOT NULL;
        COMMENT ON COLUMN "sys_menu"."path" IS '路由路径';
        COMMENT ON COLUMN "sys_menu"."name" IS '菜单名称';
        COMMENT ON COLUMN "sys_menu"."component" IS '前端组件路径/标识';
        ALTER TABLE "sys_role" DROP COLUMN "status";
        ALTER TABLE "sys_role" DROP COLUMN "remark";
        COMMENT ON COLUMN "sys_role"."code" IS '角色编码';"""


MODELS_STATE = (
    "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"
)
