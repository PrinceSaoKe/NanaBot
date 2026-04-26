from nonebot import get_driver


def get_bot_nicknames() -> list[str]:
    """
    获取机器人昵称列表（来源于 `.env` 的 `NICKNAME` 配置）。

    返回：
    - 机器人昵称字符串列表。
    - 若未配置昵称，则返回空列表。
    """
    raw_nickname = getattr(get_driver().config, "nickname", None)
    if raw_nickname is None:
        return []
    if isinstance(raw_nickname, str):
        normalized = raw_nickname.strip()
        return [normalized] if normalized else []

    nicknames: list[str] = []
    for item in raw_nickname:
        normalized = str(item).strip()
        if normalized:
            nicknames.append(normalized)
    return nicknames


def get_primary_bot_nickname(default_name: str = "机器人") -> str:
    """
    获取机器人首选昵称。

    参数：
    - default_name: 当未配置 `NICKNAME` 时返回的兜底昵称。

    返回：
    - 优先返回 `NICKNAME` 的第一个有效昵称；
      若不存在有效昵称，则返回 `default_name`。
    """
    nicknames = get_bot_nicknames()
    if nicknames:
        return nicknames[0]
    return default_name
