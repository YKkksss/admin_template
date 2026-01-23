from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sys_user" ADD "introduction" VARCHAR(255);
        COMMENT ON COLUMN "sys_user"."introduction" IS '个人简介';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sys_user" DROP COLUMN "introduction";"""


MODELS_STATE = (
    "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"
)
