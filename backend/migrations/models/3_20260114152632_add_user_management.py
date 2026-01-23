from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sys_user" ADD "dept_id" INT;
        COMMENT ON COLUMN "sys_user"."dept_id" IS '所属部门';
        ALTER TABLE "sys_user" ADD CONSTRAINT "fk_sys_user_sys_dept_a74261d7" FOREIGN KEY ("dept_id") REFERENCES "sys_dept" ("id") ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sys_user" DROP CONSTRAINT IF EXISTS "fk_sys_user_sys_dept_a74261d7";
        ALTER TABLE "sys_user" DROP COLUMN "dept_id";"""


MODELS_STATE = (
    "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"
    "Wjg="
)
