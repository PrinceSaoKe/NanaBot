from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, PrivateMessageEvent
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from services.config_store import (
    add_to_whitelist,
    is_group_allowed,
    is_user_allowed,
    load_config,
    remove_from_whitelist,
)


WHITELIST_COMMANDS = {"/whitelist", "/whitelist_add", "/whitelist_remove"}


def _is_superuser(user_id: str) -> bool:
    """
    判断用户是否为超级管理员。

    参数：
    - user_id: 当前事件的用户 ID（字符串形式）。

    返回：
    - `True` 表示该用户在 `.env` 的 `SUPERUSERS` 中。
    """
    return user_id in {str(item) for item in get_driver().config.superusers}


def _is_whitelist_management_command(text: str) -> bool:
    """
    判断消息是否是白名单管理命令。

    参数：
    - text: 纯文本消息内容。

    返回：
    - `True` 表示消息以白名单管理命令前缀开头。
    """
    return any(text.startswith(command) for command in WHITELIST_COMMANDS)


@event_preprocessor
async def whitelist_guard(bot, event) -> None:
    """
    全局白名单拦截器。

    参数：
    - bot: 当前机器人实例（由 NoneBot 注入）。
    - event: 当前事件对象，仅处理群消息和私聊消息。

    规则：
    - 群聊：群号不在 `group_whitelist` 时忽略事件。
    - 私聊：用户不在 `user_whitelist` 时忽略事件。
    - 超管执行白名单管理命令时始终放行，避免机器人被锁死。
    """
    if isinstance(event, GroupMessageEvent):
        user_id = event.get_user_id()
        text = event.get_plaintext().strip()

        if _is_superuser(user_id) and _is_whitelist_management_command(text):
            return

        if is_group_allowed(event.group_id):
            return
        raise IgnoredException("Group is not in whitelist")

    if isinstance(event, PrivateMessageEvent):
        user_id = event.get_user_id()
        text = event.get_plaintext().strip()

        if _is_superuser(user_id) and _is_whitelist_management_command(text):
            return

        if is_user_allowed(user_id):
            return
        raise IgnoredException("User is not in whitelist")


# 白名单管理命令仅允许超级管理员执行。
whitelist = on_command("whitelist", priority=10, block=True, permission=SUPERUSER)
whitelist_add = on_command("whitelist_add", priority=10, block=True, permission=SUPERUSER)
whitelist_remove = on_command("whitelist_remove", priority=10, block=True, permission=SUPERUSER)


@whitelist.handle()
async def handle_whitelist() -> None:
    """
    查看当前群白名单和用户白名单。
    """
    config = load_config()
    groups = "、".join(config.group_whitelist) if config.group_whitelist else "无"
    users = "、".join(config.user_whitelist) if config.user_whitelist else "无"
    await whitelist.finish(f"群白名单：{groups}\n用户白名单：{users}")


def _parse_target(args: Message) -> tuple[str, str] | None:
    """
    解析白名单命令参数。

    参数：
    - args: 命令参数消息体，期望格式为 `<target_type> <target_id>`。

    允许值：
    - `target_type` 仅允许 `group` 或 `user`。
    - `target_id` 仅允许数字字符串。

    返回：
    - `(target_type, target_id)`：解析成功。
    - `None`：格式不合法。
    """
    parts = args.extract_plain_text().strip().split()
    if len(parts) != 2:
        return None

    target_type, target_id = parts
    if target_type not in {"group", "user"}:
        return None
    if not target_id.isdigit():
        return None

    return target_type, target_id


@whitelist_add.handle()
async def handle_whitelist_add(args: Message = CommandArg()) -> None:
    """
    新增群或用户到白名单。

    参数：
    - args: 命令参数，格式必须是：
      - `group <群号>`
      - `user <QQ号>`
    """
    parsed = _parse_target(args)
    if not parsed:
        await whitelist_add.finish("用法：/whitelist_add group <群号> 或 /whitelist_add user <QQ号>")

    target_type, target_id = parsed
    created = add_to_whitelist(target_type, target_id)
    if not created:
        await whitelist_add.finish("目标已存在于白名单中。")

    target_name = "群" if target_type == "group" else "用户"
    await whitelist_add.finish(f"已将{target_name} {target_id} 加入白名单。")


@whitelist_remove.handle()
async def handle_whitelist_remove(args: Message = CommandArg()) -> None:
    """
    将群或用户从白名单移除。

    参数：
    - args: 命令参数，格式必须是：
      - `group <群号>`
      - `user <QQ号>`
    """
    parsed = _parse_target(args)
    if not parsed:
        await whitelist_remove.finish("用法：/whitelist_remove group <群号> 或 /whitelist_remove user <QQ号>")

    target_type, target_id = parsed
    removed = remove_from_whitelist(target_type, target_id)
    if not removed:
        await whitelist_remove.finish("目标不在白名单中。")

    target_name = "群" if target_type == "group" else "用户"
    await whitelist_remove.finish(f"已将{target_name} {target_id} 移出白名单。")
