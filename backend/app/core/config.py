"""
应用配置（Pydantic Settings）。

说明：
1. 默认读取 backend/.env 文件。
2. 复杂类型（如 list）建议使用 JSON 字符串写入 env，例如：
   CORS_ORIGINS=[\"http://localhost:5173\"]
"""

from pathlib import Path
from urllib.parse import quote

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = Field(default="Admin Template API", description="应用名称")
    APP_VERSION: str = Field(default="0.1.0", description="应用版本号")
    DEBUG: bool = Field(default=True, description="是否开启调试")

    API_V1_STR: str = Field(default="/api/v1", description="API v1 前缀")

    SECRET_KEY: str = Field(default="please-change-me", description="应用密钥")

    POSTGRES_HOST: str | None = Field(default=None, description="PostgreSQL 地址")
    POSTGRES_PORT: int | None = Field(default=None, description="PostgreSQL 端口")
    POSTGRES_USER: str | None = Field(default=None, description="PostgreSQL 用户名")
    POSTGRES_PASSWORD: str | None = Field(default=None, description="PostgreSQL 密码")
    POSTGRES_DB: str | None = Field(default=None, description="PostgreSQL 数据库名")
    POSTGRES_SSL: bool = Field(default=False, description="PostgreSQL 是否启用 SSL")

    DATABASE_URL: str = Field(
        default="sqlite://./dev.db",
        description="数据库连接字符串（Tortoise ORM）",
    )
    REDIS_URL: str | None = Field(default=None, description="Redis 连接字符串（可选）")

    JWT_SECRET_KEY: str = Field(default="please-change-me", description="JWT 密钥")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=120,
        description="AccessToken 过期分钟数",
    )

    INIT_SUPERUSER: bool = Field(
        default=False,
        description="启动时是否初始化超级管理员（仅建议开发环境开启）",
    )
    SUPERUSER_USERNAME: str = Field(default="vben", description="初始化超级管理员用户名")
    SUPERUSER_PASSWORD: str | None = Field(default=None, description="初始化超级管理员密码")
    SUPERUSER_REAL_NAME: str = Field(default="Vben", description="初始化超级管理员真实姓名")
    SUPERUSER_HOME_PATH: str | None = Field(default=None, description="初始化超级管理员首页路径")
    SUPERUSER_AVATAR: str | None = Field(default=None, description="初始化超级管理员头像")
    SUPERUSER_ROLE_CODE: str = Field(default="super", description="初始化超级管理员角色编码")
    SUPERUSER_ROLE_NAME: str = Field(default="超级管理员", description="初始化超级管理员角色名称")

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
        description="允许跨域的来源列表",
    )

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        """
        如果未显式提供 DATABASE_URL，则尝试从 POSTGRES_* 变量拼装。

        说明：
        - 仍以 DATABASE_URL 为主，只有当 DATABASE_URL 使用默认值或为空时才会拼装。
        - 仅对 PostgreSQL 做拼装，其他数据库请直接设置 DATABASE_URL。
        """

        if self.DATABASE_URL and self.DATABASE_URL.strip() != "sqlite://./dev.db":
            return self

        if not all(
            [
                self.POSTGRES_HOST,
                self.POSTGRES_PORT,
                self.POSTGRES_USER,
                self.POSTGRES_PASSWORD,
                self.POSTGRES_DB,
            ],
        ):
            return self

        user = quote(self.POSTGRES_USER or "", safe="")
        password = quote(self.POSTGRES_PASSWORD or "", safe="")
        host = self.POSTGRES_HOST
        port = self.POSTGRES_PORT
        db = self.POSTGRES_DB
        self.DATABASE_URL = f"postgres://{user}:{password}@{host}:{port}/{db}"
        return self


settings = Settings()
