from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, PrivateMessageEvent
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from services.auth import is_superuser
from services.config_store import (
    add_to_whitelist,
    get_rate_limit_config,
    is_group_allowed,
    is_user_allowed,
    load_config,
    remove_from_whitelist,
    set_rate_limit_enabled,
    update_rate_limit,
)
from services.rate_limit import rate_limiter

WHITELIST_COMMANDS = {
    "/白名单",
    "/添加白名单",
    "/移除白名单",
    "/whitelist",
    "/whitelist_add",
    "/whitelist_remove",
}
RATE_LIMIT_COMMANDS = {
    "/限流",
    "/开启限流",
    "/关闭限流",
    "/设置限流",
    "/rate_limit",
    "/rate_limit_on",
    "/rate_limit_off",
    "/rate_limit_set",
}
SECURITY_MANAGEMENT_COMMANDS = WHITELIST_COMMANDS | RATE_LIMIT_COMMANDS


def _is_security_management_command(text: str) -> bool:
    """
    判断消息是否为安全管理命令。

    参数：
    - text: 纯文本消息内容。

    返回：
    - `True` 表示命中白名单或限流管理命令。
    - `False` 表示不是安全管理命令。
    """
    return any(text.startswith(command) for command in SECURITY_MANAGEMENT_COMMANDS)


def _is_command_message(text: str) -> bool:
    """
    判断消息是否命中命令前缀。

    参数：
    - text: 纯文本消息内容。

    返回：
    - `True` 表示消息使用了 `COMMAND_START` 中的任一前缀。
    - `False` 表示消息不是命令消息。
    """
    command_starts = get_driver().config.command_start
    if isinstance(command_starts, str):
        prefixes = [command_starts]
    else:
        prefixes = [str(item) for item in command_starts]
    return any(text.startswith(prefix) for prefix in prefixes if prefix)


@event_preprocessor
async def security_guard(bot, event) -> None:
    """
    执行全局安全拦截。

    参数：
    - bot: 当前机器人实例，由 NoneBot 注入。
    - event: 当前事件对象，仅处理群消息和私聊消息。

    规则：
    - 先检查白名单，不在白名单中则直接忽略。
    - 仅对命令消息执行限流检查。
    - 超管执行安全管理命令时始终放行，避免把机器人锁死。
    """
    if isinstance(event, GroupMessageEvent):
        user_id = event.get_user_id()
        text = event.get_plaintext().strip()

        if is_superuser(user_id) and _is_security_management_command(text):
            return

        # 非白名单群不响应任何消息。
        if not is_group_allowed(event.group_id):
            raise IgnoredException("当前群不在白名单中")

        if not _is_command_message(text):
            return

        result = rate_limiter.check_group_event(
            user_id=str(user_id),
            group_id=str(event.group_id),
            config=get_rate_limit_config(),
        )
        if not result.allowed:
            raise IgnoredException(
                f"触发限流（群聊）：{result.reason}，请在 {result.retry_after_seconds} 秒后重试"
            )
        return

    if isinstance(event, PrivateMessageEvent):
        user_id = event.get_user_id()
        text = event.get_plaintext().strip()

        if is_superuser(user_id) and _is_security_management_command(text):
            return

        # 非白名单用户不能在私聊中与机器人交互。
        if not is_user_allowed(user_id):
            raise IgnoredException("当前用户不在白名单中")

        if not _is_command_message(text):
            return

        result = rate_limiter.check_private_event(
            user_id=str(user_id),
            config=get_rate_limit_config(),
        )
        if not result.allowed:
            raise IgnoredException(
                f"触发限流（私聊）：{result.reason}，请在 {result.retry_after_seconds} 秒后重试"
            )


# 白名单管理命令仅允许超级管理员执行。
whitelist = on_command("白名单", aliases={"whitelist"}, priority=10, block=True, permission=SUPERUSER)
whitelist_add = on_command(
    "添加白名单",
    aliases={"whitelist_add"},
    priority=10,
    block=True,
    permission=SUPERUSER,
)
whitelist_remove = on_command(
    "移除白名单",
    aliases={"whitelist_remove"},
    priority=10,
    block=True,
    permission=SUPERUSER,
)

# 限流管理命令仅允许超级管理员执行。
rate_limit = on_command("限流", aliases={"rate_limit"}, priority=10, block=True, permission=SUPERUSER)
rate_limit_on = on_command(
    "开启限流",
    aliases={"rate_limit_on"},
    priority=10,
    block=True,
    permission=SUPERUSER,
)
rate_limit_off = on_command(
    "关闭限流",
    aliases={"rate_limit_off"},
    priority=10,
    block=True,
    permission=SUPERUSER,
)
rate_limit_set = on_command(
    "设置限流",
    aliases={"rate_limit_set"},
    priority=10,
    block=True,
    permission=SUPERUSER,
)


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
    - `target_type` 仅允许 `群`、`用户`、`group` 或 `user`。
    - `target_id` 仅允许数字字符串。

    返回：
    - `(target_type, target_id)` 表示解析成功。
    - `None` 表示参数格式不合法。
    """
    parts = args.extract_plain_text().strip().split()
    if len(parts) != 2:
        return None

    target_type, target_id = parts
    target_type_mapping = {
        "群": "group",
        "用户": "user",
        "group": "group",
        "user": "user",
    }
    normalized_target_type = target_type_mapping.get(target_type)
    if not normalized_target_type:
        return None
    if not target_id.isdigit():
        return None

    return normalized_target_type, target_id


@whitelist_add.handle()
async def handle_whitelist_add(args: Message = CommandArg()) -> None:
    """
    新增群或用户到白名单。

    参数：
    - args: 命令参数，格式必须是：
      `群 <群号>` 或 `用户 <QQ号>`。
    """
    parsed = _parse_target(args)
    if not parsed:
        await whitelist_add.finish("用法：/添加白名单 群 <群号> 或 /添加白名单 用户 <QQ号>")

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
      `群 <群号>` 或 `用户 <QQ号>`。
    """
    parsed = _parse_target(args)
    if not parsed:
        await whitelist_remove.finish("用法：/移除白名单 群 <群号> 或 /移除白名单 用户 <QQ号>")

    target_type, target_id = parsed
    removed = remove_from_whitelist(target_type, target_id)
    if not removed:
        await whitelist_remove.finish("目标不在白名单中。")

    target_name = "群" if target_type == "group" else "用户"
    await whitelist_remove.finish(f"已将{target_name} {target_id} 移出白名单。")


@rate_limit.handle()
async def handle_rate_limit() -> None:
    """
    查看当前限流配置。
    """
    config = get_rate_limit_config()
    status = "开启" if config.enabled else "关闭"
    await rate_limit.finish(
        "限流配置：\n"
        f"- 状态：{status}\n"
        f"- 用户：{config.user_window_seconds}s 内最多 {config.user_max_requests} 次\n"
        f"- 群聊：{config.group_window_seconds}s 内最多 {config.group_max_requests} 次\n"
        f"- 私聊：{config.private_window_seconds}s 内最多 {config.private_max_requests} 次\n"
        f"- 触发限流后冷却时长：{config.block_seconds}s"
    )


@rate_limit_on.handle()
async def handle_rate_limit_on() -> None:
    """
    启用限流开关。
    """
    set_rate_limit_enabled(True)
    await rate_limit_on.finish("已开启限流。")


@rate_limit_off.handle()
async def handle_rate_limit_off() -> None:
    """
    关闭限流开关。
    """
    set_rate_limit_enabled(False)
    await rate_limit_off.finish("已关闭限流。")


def _parse_rate_limit_args(args: Message) -> tuple[str, int, int, int] | None:
    """
    解析限流设置命令参数。

    参数：
    - args: 命令参数消息体，期望格式为 `<scope> <window> <max> <block>`。

    允许值：
    - `scope` 仅允许 `用户`、`群`、`私聊`、`user`、`group` 或 `private`。
    - `window`、`max`、`block` 必须是大于 0 的整数。

    返回：
    - `(scope, window, max_requests, block_seconds)` 表示解析成功。
    - `None` 表示参数格式不合法。
    """
    parts = args.extract_plain_text().strip().split()
    if len(parts) != 4:
        return None

    scope, window, max_requests, block_seconds = parts
    scope_mapping = {
        "用户": "user",
        "群": "group",
        "私聊": "private",
        "user": "user",
        "group": "group",
        "private": "private",
    }
    normalized_scope = scope_mapping.get(scope)
    if not normalized_scope:
        return None
    if not (window.isdigit() and max_requests.isdigit() and block_seconds.isdigit()):
        return None

    parsed_window = int(window)
    parsed_max = int(max_requests)
    parsed_block = int(block_seconds)
    if parsed_window <= 0 or parsed_max <= 0 or parsed_block <= 0:
        return None

    return normalized_scope, parsed_window, parsed_max, parsed_block


@rate_limit_set.handle()
async def handle_rate_limit_set(args: Message = CommandArg()) -> None:
    """
    更新限流配置。

    参数：
    - args: 命令参数，格式必须是：
      `用户 <窗口秒数> <最大次数> <封禁秒数>`、
      `群 <窗口秒数> <最大次数> <封禁秒数>`、
      `私聊 <窗口秒数> <最大次数> <封禁秒数>`。
    """
    parsed = _parse_rate_limit_args(args)
    if not parsed:
        await rate_limit_set.finish(
            "用法：/设置限流 用户|群|私聊 <窗口秒数> <最大次数> <封禁秒数>"
        )

    scope, window, max_requests, block_seconds = parsed
    updated = update_rate_limit(scope, window, max_requests, block_seconds)
    scope_name = {"user": "用户", "group": "群", "private": "私聊"}[scope]
    await rate_limit_set.finish(
        f"已更新限流：scope={scope_name}，window={window}s，max={max_requests}，block={updated.block_seconds}s。"
    )
