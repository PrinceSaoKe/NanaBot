from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, PrivateMessageEvent

from services.auth import is_superuser
from services.command_registry import get_visible_commands

help_cmd = on_command("帮助", aliases={"help"}, priority=10, block=True)
about = on_command("关于", aliases={"about"}, priority=10, block=True)


@help_cmd.handle()
async def handle_help(event: MessageEvent) -> None:
    """
    根据当前用户权限展示可执行命令。

    参数：
    - event: 当前消息事件，用于识别发起命令的用户。
    """
    visible_commands = get_visible_commands(is_superuser(event.get_user_id()), isinstance(event, PrivateMessageEvent))
    lines = ["娜娜 Bot 可用命令："]
    for item in visible_commands:
        lines.append(f"{item.command} - {item.description}")
    await help_cmd.finish("\n".join(lines))


@about.handle()
async def handle_about() -> None:
    """
    返回机器人简介。
    """
    await about.finish(
        "娜娜 Bot 是一个基于 NapCatQQ、NoneBot2 和 OneBot V11 的 QQ 机器人。\n"
        "开发者：骚客\n"
        "联系方式：2596818595@qq.com（请注明来意）"
    )
