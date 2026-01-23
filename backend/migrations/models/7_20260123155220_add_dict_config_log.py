from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "sys_dict_data" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "type_code" VARCHAR(100) NOT NULL,
    "label" VARCHAR(100) NOT NULL,
    "value" VARCHAR(100) NOT NULL,
    "sort" INT NOT NULL DEFAULT 0,
    "status" INT NOT NULL DEFAULT 1,
    "style" VARCHAR(50),
    "remark" VARCHAR(500),
    CONSTRAINT "uid_sys_dict_da_type_co_3d32d2" UNIQUE ("type_code", "value")
);
CREATE INDEX IF NOT EXISTS "idx_sys_dict_da_type_co_9285f9" ON "sys_dict_data" ("type_code");
COMMENT ON COLUMN "sys_dict_data"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_dict_data"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_dict_data"."id" IS '主键ID';
COMMENT ON COLUMN "sys_dict_data"."type_code" IS '字典类型编码';
COMMENT ON COLUMN "sys_dict_data"."label" IS '字典标签（显示值）';
COMMENT ON COLUMN "sys_dict_data"."value" IS '字典值（实际存储值）';
COMMENT ON COLUMN "sys_dict_data"."sort" IS '排序';
COMMENT ON COLUMN "sys_dict_data"."status" IS '状态：1启用 0禁用';
COMMENT ON COLUMN "sys_dict_data"."style" IS '样式/颜色标记（可选）';
COMMENT ON COLUMN "sys_dict_data"."remark" IS '备注';
COMMENT ON TABLE "sys_dict_data" IS '字典数据（字典项）。';
        CREATE TABLE IF NOT EXISTS "sys_dict_type" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "code" VARCHAR(100) NOT NULL UNIQUE,
    "status" INT NOT NULL DEFAULT 1,
    "remark" VARCHAR(500)
);
COMMENT ON COLUMN "sys_dict_type"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_dict_type"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_dict_type"."id" IS '主键ID';
COMMENT ON COLUMN "sys_dict_type"."name" IS '字典名称';
COMMENT ON COLUMN "sys_dict_type"."code" IS '字典编码（唯一标识）';
COMMENT ON COLUMN "sys_dict_type"."status" IS '状态：1启用 0禁用';
COMMENT ON COLUMN "sys_dict_type"."remark" IS '备注';
COMMENT ON TABLE "sys_dict_type" IS '字典类型（字典分类）。';
        CREATE TABLE IF NOT EXISTS "sys_config" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "key" VARCHAR(100) NOT NULL UNIQUE,
    "value" TEXT NOT NULL,
    "status" INT NOT NULL DEFAULT 1,
    "remark" VARCHAR(500),
    "is_builtin" BOOL NOT NULL DEFAULT False
);
COMMENT ON COLUMN "sys_config"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_config"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_config"."id" IS '主键ID';
COMMENT ON COLUMN "sys_config"."name" IS '配置名称';
COMMENT ON COLUMN "sys_config"."key" IS '配置键（唯一标识）';
COMMENT ON COLUMN "sys_config"."value" IS '配置值';
COMMENT ON COLUMN "sys_config"."status" IS '状态：1启用 0禁用';
COMMENT ON COLUMN "sys_config"."remark" IS '备注';
COMMENT ON COLUMN "sys_config"."is_builtin" IS '是否内置配置（内置配置不允许删除）';
COMMENT ON TABLE "sys_config" IS '系统参数配置（用于运行期可调整的配置项）。';
        CREATE TABLE IF NOT EXISTS "sys_login_log" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT,
    "username" VARCHAR(50),
    "ip" VARCHAR(50),
    "location" VARCHAR(100),
    "browser" VARCHAR(50),
    "os" VARCHAR(50),
    "status" INT,
    "message" VARCHAR(200)
);
COMMENT ON COLUMN "sys_login_log"."id" IS '主键ID';
COMMENT ON COLUMN "sys_login_log"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_login_log"."user_id" IS '用户ID（可为空）';
COMMENT ON COLUMN "sys_login_log"."username" IS '用户名';
COMMENT ON COLUMN "sys_login_log"."ip" IS 'IP地址';
COMMENT ON COLUMN "sys_login_log"."location" IS '登录地点（可选）';
COMMENT ON COLUMN "sys_login_log"."browser" IS '浏览器（可选）';
COMMENT ON COLUMN "sys_login_log"."os" IS '操作系统（可选）';
COMMENT ON COLUMN "sys_login_log"."status" IS '状态：0失败 1成功';
COMMENT ON COLUMN "sys_login_log"."message" IS '消息';
COMMENT ON TABLE "sys_login_log" IS '登录日志。';
        CREATE TABLE IF NOT EXISTS "sys_operation_log" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT,
    "username" VARCHAR(50),
    "module" VARCHAR(50),
    "action" VARCHAR(50),
    "method" VARCHAR(10) NOT NULL,
    "url" VARCHAR(500) NOT NULL,
    "ip" VARCHAR(50),
    "request_data" TEXT,
    "response_data" TEXT,
    "status" INT,
    "duration" INT
);
COMMENT ON COLUMN "sys_operation_log"."id" IS '主键ID';
COMMENT ON COLUMN "sys_operation_log"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_operation_log"."user_id" IS '用户ID（可为空）';
COMMENT ON COLUMN "sys_operation_log"."username" IS '用户名';
COMMENT ON COLUMN "sys_operation_log"."module" IS '操作模块';
COMMENT ON COLUMN "sys_operation_log"."action" IS '操作类型';
COMMENT ON COLUMN "sys_operation_log"."method" IS '请求方法';
COMMENT ON COLUMN "sys_operation_log"."url" IS '请求URL';
COMMENT ON COLUMN "sys_operation_log"."ip" IS 'IP地址';
COMMENT ON COLUMN "sys_operation_log"."request_data" IS '请求数据（脱敏后）';
COMMENT ON COLUMN "sys_operation_log"."response_data" IS '响应数据（摘要）';
COMMENT ON COLUMN "sys_operation_log"."status" IS '状态：0失败 1成功';
COMMENT ON COLUMN "sys_operation_log"."duration" IS '耗时(ms)';
COMMENT ON TABLE "sys_operation_log" IS '操作日志（审计日志）。';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "sys_login_log";
        DROP TABLE IF EXISTS "sys_dict_type";
        DROP TABLE IF EXISTS "sys_operation_log";
        DROP TABLE IF EXISTS "sys_dict_data";
        DROP TABLE IF EXISTS "sys_config";"""


MODELS_STATE = (
    "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"
)
