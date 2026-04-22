from nonebot import get_driver


def is_superuser(user_id: str) -> bool:
    """
    判断用户是否为超级管理员。

    参数：
    - user_id: 当前用户 QQ 号，使用字符串形式传入。

    返回：
    - `True` 表示该用户存在于 `.env` 的 `SUPERUSERS` 配置中。
    - `False` 表示该用户不是超级管理员。
    """
    return user_id in {str(item) for item in get_driver().config.superusers}
