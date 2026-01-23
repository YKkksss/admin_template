from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "sys_notice" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(200) NOT NULL,
    "message" VARCHAR(500) NOT NULL,
    "content" TEXT NOT NULL,
    "type" INT NOT NULL DEFAULT 1,
    "link" VARCHAR(500)
);
COMMENT ON COLUMN "sys_notice"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_notice"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_notice"."id" IS '主键ID';
COMMENT ON COLUMN "sys_notice"."title" IS '消息标题';
COMMENT ON COLUMN "sys_notice"."message" IS '消息摘要';
COMMENT ON COLUMN "sys_notice"."content" IS '消息详情内容';
COMMENT ON COLUMN "sys_notice"."type" IS '类型：1通知 2公告 3警告';
COMMENT ON COLUMN "sys_notice"."link" IS '跳转链接（可选）';
COMMENT ON TABLE "sys_notice" IS '站内通知/消息内容（可被多用户复用）。';
        CREATE TABLE IF NOT EXISTS "sys_user_notice" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "is_read" BOOL NOT NULL DEFAULT False,
    "read_at" TIMESTAMPTZ,
    "bell_hidden" BOOL NOT NULL DEFAULT False,
    "bell_hidden_at" TIMESTAMPTZ,
    "notice_id" INT NOT NULL REFERENCES "sys_notice" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "sys_user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_sys_user_no_user_id_f8c0ff" UNIQUE ("user_id", "notice_id")
);
COMMENT ON COLUMN "sys_user_notice"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_user_notice"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_user_notice"."id" IS '主键ID';
COMMENT ON COLUMN "sys_user_notice"."is_read" IS '是否已读';
COMMENT ON COLUMN "sys_user_notice"."read_at" IS '已读时间';
COMMENT ON COLUMN "sys_user_notice"."bell_hidden" IS '是否从铃铛列表隐藏';
COMMENT ON COLUMN "sys_user_notice"."bell_hidden_at" IS '铃铛隐藏时间';
COMMENT ON COLUMN "sys_user_notice"."notice_id" IS '消息内容';
COMMENT ON COLUMN "sys_user_notice"."user_id" IS '接收用户';
COMMENT ON TABLE "sys_user_notice" IS '用户收件箱（用户维度的已读/铃铛隐藏等状态）。';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "sys_notice";
        DROP TABLE IF EXISTS "sys_user_notice";"""


MODELS_STATE = (
    "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"
    "/reX5/8DsBsxxA=="
)
