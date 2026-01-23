from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sys_notice" ADD "send_all" BOOL NOT NULL DEFAULT False;
        ALTER TABLE "sys_notice" ADD "user_ids" JSONB;
        ALTER TABLE "sys_notice" ADD "creator_id" INT;
        ALTER TABLE "sys_notice" ADD "dept_ids" JSONB;
        COMMENT ON COLUMN "sys_notice"."send_all" IS '是否发送给全部用户';
COMMENT ON COLUMN "sys_notice"."user_ids" IS '发送用户ID列表（可选）';
COMMENT ON COLUMN "sys_notice"."creator_id" IS '发布人';
COMMENT ON COLUMN "sys_notice"."dept_ids" IS '发送部门ID列表（可选）';
        ALTER TABLE "sys_notice" ADD CONSTRAINT "fk_sys_noti_sys_user_edfe7cb9" FOREIGN KEY ("creator_id") REFERENCES "sys_user" ("id") ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sys_notice" DROP CONSTRAINT IF EXISTS "fk_sys_noti_sys_user_edfe7cb9";
        ALTER TABLE "sys_notice" DROP COLUMN "send_all";
        ALTER TABLE "sys_notice" DROP COLUMN "user_ids";
        ALTER TABLE "sys_notice" DROP COLUMN "creator_id";
        ALTER TABLE "sys_notice" DROP COLUMN "dept_ids";"""


MODELS_STATE = (
    "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"
)
