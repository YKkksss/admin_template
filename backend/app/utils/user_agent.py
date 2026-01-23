"""User-Agent 解析工具（轻量级实现，不引入额外依赖）。"""

from __future__ import annotations

import re


def parse_os(user_agent: str | None) -> str | None:
    ua = (user_agent or "").lower()
    if not ua:
        return None

    if "windows nt" in ua:
        return "Windows"
    if "mac os x" in ua and "iphone" not in ua and "ipad" not in ua:
        return "macOS"
    if "android" in ua:
        return "Android"
    if "iphone" in ua or "ipad" in ua:
        return "iOS"
    if "linux" in ua:
        return "Linux"
    return None


def parse_browser(user_agent: str | None) -> str | None:
    ua = (user_agent or "")
    if not ua:
        return None

    # 顺序很重要：Edge/Chrome/Safari 的 UA 有重叠
    patterns: list[tuple[str, str]] = [
        (r"Edg/([\\d.]+)", "Edge"),
        (r"Chrome/([\\d.]+)", "Chrome"),
        (r"Firefox/([\\d.]+)", "Firefox"),
        (r"Version/([\\d.]+).*Safari", "Safari"),
    ]
    for pattern, name in patterns:
        m = re.search(pattern, ua)
        if m:
            ver = m.group(1)
            return f"{name} {ver}" if ver else name
    return None

