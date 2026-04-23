from pathlib import Path

from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent, MessageSegment, PrivateMessageEvent
from nonebot.message import event_preprocessor

from services.config_store import is_group_allowed, is_user_allowed

RULE_IMAGE_CANDIDATES = [
    Path("data/assets/handle_rule.png"),
    Path("data/assets/handle_rules.png"),
]


def _is_handle_start_command(text: str) -> bool:
    """
    判断消息是否为汉兜开局命令。

    参数：
    - text: 当前消息的纯文本内容。

    返回：
    - `True` 表示消息以 `/猜成语` 开头。
    - `False` 表示不是汉兜开局命令。
    """
    return text.startswith("/猜成语")


def _is_allowed_scene(event: MessageEvent) -> bool:
    """
    判断当前会话是否通过白名单校验。

    参数：
    - event: 当前消息事件，仅处理群聊与私聊事件。

    返回：
    - `True` 表示当前事件所在会话允许与机器人交互。
    - `False` 表示当前会话不在白名单中。
    """
    if isinstance(event, GroupMessageEvent):
        return is_group_allowed(event.group_id)
    if isinstance(event, PrivateMessageEvent):
        return is_user_allowed(event.get_user_id())
    return False


def _get_rule_image_path() -> Path | None:
    """
    获取规则说明图片路径。

    返回：
    - 存在的规则图片绝对路径。
    - 若候选图片均不存在，则返回 `None`。
    """
    for path in RULE_IMAGE_CANDIDATES:
        if path.exists():
            return path.resolve()
    return None


@event_preprocessor
async def send_handle_rule_image(bot, event) -> None:
    """
    在汉兜开局前补发规则说明图片。

    参数：
    - bot: 当前机器人实例，仅处理 OneBot V11 Bot。
    - event: 当前消息事件，仅处理群聊与私聊消息。

    说明：
    - 该预处理器不会拦截插件原本的开局逻辑。
    - 命中 `/猜成语` 时，先发送规则图，再继续由 `nonebot_plugin_handle` 正常开局。
    """
    if not isinstance(bot, Bot):
        return
    if not isinstance(event, (GroupMessageEvent, PrivateMessageEvent)):
        return

    text = event.get_plaintext().strip()
    if not _is_handle_start_command(text):
        return
    if not _is_allowed_scene(event):
        return

    image_path = _get_rule_image_path()
    if image_path is None:
        return

    await bot.send(event, MessageSegment.image(image_path.as_uri()))
