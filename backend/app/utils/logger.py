"""日志工具（基础版本）。"""

import logging


def setup_logging(level: str = "INFO") -> None:
    """配置全局日志（可根据项目需要扩展为结构化日志）。"""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
