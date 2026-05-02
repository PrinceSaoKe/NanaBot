from nonebot import get_driver, on_message
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.params import Depends
from nonebot_plugin_alconna import Target
from nonebot_plugin_steam_info import bind_data, get_target
from nonebot_plugin_steam_info.steam import get_steam_id

from services.auth import is_superuser

# 通过消息级拦截扩展双参数 steambind，避免与原插件的同名命令注册产生重复告警。
steam_bind_extend = on_message(priority=1, block=False)


def _extract_bind_args(text: str) -> tuple[str, str] | None:
    """
    解析 `/steambind <steamid> <qq号>` 形式的参数。

    参数：
    - text: 去除首尾空白后的纯文本消息内容。

    返回：
    - 成功时返回 `(steamid文本, qq号文本)`。
    - 不匹配双参数 steambind 命令时返回 `None`。
    """
    command_starts = get_driver().config.command_start
    if isinstance(command_starts, str):
        prefixes = [command_starts]
    else:
        prefixes = [str(item) for item in command_starts]

    for prefix in prefixes:
        command_prefix = f"{prefix}steambind"
        if not text.startswith(command_prefix):
            continue

        arg_text = text[len(command_prefix):].strip()
        args = arg_text.split()
        if len(args) != 2:
            return None
        return args[0], args[1]

    return None


@steam_bind_extend.handle()
async def handle_steam_bind_extend(
        event: MessageEvent, target: Target = Depends(get_target)
) -> None:
    """
    扩展 Steam 绑定命令，支持超级管理员为指定 QQ 绑定 Steam ID。

    参数：
    - event: 当前消息事件，用于获取真实发送者 QQ 号与消息内容。
    - target: 当前会话目标，仅允许群聊或其他具备父级上下文的场景。
    """
    bind_args = _extract_bind_args(event.get_plaintext().strip())
    if bind_args is None:
        return

    steam_id_text, target_qq = bind_args

    # 只有超级管理员才能为其他 QQ 代绑，避免普通用户越权修改绑定关系。
    if not is_superuser(event.get_user_id()):
        await steam_bind_extend.finish("只有超级管理员才能为其他 QQ 绑定 Steam ID。")

    if not steam_id_text.isdigit():
        await steam_bind_extend.finish(
            "请输入正确的 Steam ID 或 Steam 好友代码，格式：/steambind <steamid> <QQ号>"
        )

    if not target_qq.isdigit():
        await steam_bind_extend.finish("请输入纯数字 QQ 号，格式：/steambind <steamid> <QQ号>")

    if target is None:
        await steam_bind_extend.finish("该命令暂不支持私聊使用，请在群聊中执行。")

    parent_id = target.parent_id or target.id
    steam_id = get_steam_id(steam_id_text)

    # 直接写入 Steam 插件绑定数据，避免篡改事件发送者身份。
    if user_data := bind_data.get(parent_id, target_qq):
        user_data["steam_id"] = steam_id
        bind_data.save()
        await steam_bind_extend.finish(
            f"已将 QQ {target_qq} 绑定的 Steam ID 更新为 {steam_id}"
        )

    bind_data.add(
        parent_id,
        {"user_id": target_qq, "steam_id": steam_id, "nickname": None},
    )
    bind_data.save()
    await steam_bind_extend.finish(f"已为 QQ {target_qq} 绑定 Steam ID {steam_id}")
