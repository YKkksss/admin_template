from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "sys_file" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "storage" VARCHAR(20) NOT NULL DEFAULT 'local',
    "original_name" VARCHAR(255) NOT NULL,
    "file_name" VARCHAR(255) NOT NULL,
    "ext" VARCHAR(20),
    "mime" VARCHAR(100),
    "size" BIGINT NOT NULL,
    "sha256" VARCHAR(64),
    "object_key" VARCHAR(500) NOT NULL,
    "bucket" VARCHAR(100),
    "remark" VARCHAR(255),
    "creator_name" VARCHAR(50),
    "dept_name" VARCHAR(50),
    "creator_id" INT REFERENCES "sys_user" ("id") ON DELETE SET NULL,
    "dept_id" INT REFERENCES "sys_dept" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_sys_file_storage_71ff32" ON "sys_file" ("storage", "created_at");
CREATE INDEX IF NOT EXISTS "idx_sys_file_creator_128c16" ON "sys_file" ("creator_id", "created_at");
CREATE INDEX IF NOT EXISTS "idx_sys_file_dept_id_4bf0ff" ON "sys_file" ("dept_id", "created_at");
COMMENT ON COLUMN "sys_file"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_file"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_file"."id" IS '主键ID';
COMMENT ON COLUMN "sys_file"."storage" IS '存储类型：local/minio/s3';
COMMENT ON COLUMN "sys_file"."original_name" IS '原始文件名';
COMMENT ON COLUMN "sys_file"."file_name" IS '存储文件名';
COMMENT ON COLUMN "sys_file"."ext" IS '文件扩展名（不含 . ）';
COMMENT ON COLUMN "sys_file"."mime" IS 'MIME 类型';
COMMENT ON COLUMN "sys_file"."size" IS '文件大小（字节）';
COMMENT ON COLUMN "sys_file"."sha256" IS 'SHA256（可选，用于去重/校验）';
COMMENT ON COLUMN "sys_file"."object_key" IS '对象 key（本地为相对路径）';
COMMENT ON COLUMN "sys_file"."bucket" IS 'Bucket（minio/s3 预留）';
COMMENT ON COLUMN "sys_file"."remark" IS '备注';
COMMENT ON COLUMN "sys_file"."creator_name" IS '上传人用户名（冗余）';
COMMENT ON COLUMN "sys_file"."dept_name" IS '上传人所属部门名称（冗余）';
COMMENT ON COLUMN "sys_file"."creator_id" IS '上传人';
COMMENT ON COLUMN "sys_file"."dept_id" IS '上传人所属部门';
COMMENT ON TABLE "sys_file" IS '文件/附件（当前仅实现本地存储）。';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "sys_file";"""


MODELS_STATE = (
    "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"
)
