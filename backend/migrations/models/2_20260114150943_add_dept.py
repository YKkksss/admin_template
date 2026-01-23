from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "sys_dept" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL,
    "status" INT NOT NULL DEFAULT 1,
    "remark" VARCHAR(50),
    "parent_id" INT REFERENCES "sys_dept" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "sys_dept"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_dept"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_dept"."id" IS '主键ID';
COMMENT ON COLUMN "sys_dept"."name" IS '部门名称';
COMMENT ON COLUMN "sys_dept"."status" IS '状态：1启用 0禁用';
COMMENT ON COLUMN "sys_dept"."remark" IS '备注';
COMMENT ON COLUMN "sys_dept"."parent_id" IS '上级部门';
COMMENT ON TABLE "sys_dept" IS '部门模型（用于组织架构与权限管理扩展）。';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "sys_dept";"""


MODELS_STATE = (
    "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"
    "wLqNUuL2/l9S414e/geUACr1"
)
