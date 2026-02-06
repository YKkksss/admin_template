from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "sys_user_session" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL,
    "jti" VARCHAR(64) NOT NULL UNIQUE,
    "ip" VARCHAR(64),
    "user_agent" VARCHAR(512),
    "browser" VARCHAR(100),
    "os" VARCHAR(100),
    "last_seen_at" TIMESTAMPTZ,
    "expires_at" TIMESTAMPTZ,
    "status" INT NOT NULL DEFAULT 1,
    "revoked_at" TIMESTAMPTZ,
    "revoke_reason" VARCHAR(255),
    "revoked_by" VARCHAR(50),
    "user_id" INT NOT NULL REFERENCES "sys_user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_sys_user_se_usernam_0bf756" ON "sys_user_session" ("username", "status");
CREATE INDEX IF NOT EXISTS "idx_sys_user_se_user_id_b9c95a" ON "sys_user_session" ("user_id", "status");
COMMENT ON COLUMN "sys_user_session"."created_at" IS '创建时间';
COMMENT ON COLUMN "sys_user_session"."updated_at" IS '更新时间';
COMMENT ON COLUMN "sys_user_session"."id" IS '主键ID';
COMMENT ON COLUMN "sys_user_session"."username" IS '用户名（冗余字段，便于查询）';
COMMENT ON COLUMN "sys_user_session"."jti" IS 'Token ID（JWT jti）';
COMMENT ON COLUMN "sys_user_session"."ip" IS '登录IP';
COMMENT ON COLUMN "sys_user_session"."user_agent" IS 'User-Agent';
COMMENT ON COLUMN "sys_user_session"."browser" IS '浏览器信息';
COMMENT ON COLUMN "sys_user_session"."os" IS '操作系统';
COMMENT ON COLUMN "sys_user_session"."last_seen_at" IS '最后活跃时间';
COMMENT ON COLUMN "sys_user_session"."expires_at" IS '过期时间（来自 JWT exp）';
COMMENT ON COLUMN "sys_user_session"."status" IS '状态：1在线 0已下线/撤销';
COMMENT ON COLUMN "sys_user_session"."revoked_at" IS '下线时间';
COMMENT ON COLUMN "sys_user_session"."revoke_reason" IS '下线原因';
COMMENT ON COLUMN "sys_user_session"."revoked_by" IS '操作人（用户名）';
COMMENT ON COLUMN "sys_user_session"."user_id" IS '用户';
COMMENT ON TABLE "sys_user_session" IS '用户会话（用于在线用户与强制下线）。';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "sys_user_session";"""


MODELS_STATE = (
    "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"
    "7Okxt0evn2f/bYosc="
)
