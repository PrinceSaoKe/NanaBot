from nonebot import get_driver, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageEvent, PrivateMessageEvent
from nonebot.rule import to_me

from services.chat_memory import chat_memory_store
from services.deepseek_client import chat_with_deepseek

chat_with_ds = on_message(rule=to_me(), priority=20, block=False)


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


def _extract_prompt(bot: Bot, event: MessageEvent) -> str:
    """
    提取发送给 DeepSeek 的文本内容。

    参数：
    - bot: 当前机器人实例，用于识别消息中的 `at` 目标。
    - event: 当前消息事件，仅处理 `GroupMessageEvent` 与私聊消息事件。

    返回：
    - 去除 `@机器人` 后的纯文本内容；若为空则返回空字符串。
    """
    if not isinstance(event, GroupMessageEvent):
        return event.get_plaintext().strip()

    filtered_segments = []
    for segment in event.get_message():
        # 群聊中去掉 @当前机器人 的 segment，避免把 at 文本发给模型。
        if segment.type == "at" and str(segment.data.get("qq")) == str(bot.self_id):
            continue
        filtered_segments.append(segment)
    return Message(filtered_segments).extract_plain_text().strip()


def _get_session_id(event: MessageEvent) -> str:
    """
    生成会话 ID，用于隔离上下文记忆。

    参数：
    - event: 当前消息事件，仅处理群聊与私聊事件。

    返回：
    - 群聊返回 `group:<group_id>`。
    - 私聊返回 `private:<user_id>`。
    - 其他类型事件返回 `private:<user_id>` 兜底。
    """
    if isinstance(event, GroupMessageEvent):
        return f"group:{event.group_id}"
    if isinstance(event, PrivateMessageEvent):
        return f"private:{event.get_user_id()}"
    return f"private:{event.get_user_id()}"


@chat_with_ds.handle()
async def handle_chat_with_ds(bot: Bot, event: MessageEvent) -> None:
    """
    处理“对机器人说话”消息并转发到 DeepSeek。

    参数：
    - bot: 当前机器人实例。
    - event: 当前消息事件。
    """
    prompt = _extract_prompt(bot, event)
    if not prompt:
        await chat_with_ds.finish("发送 /help 可以查看所有指令哦~")

    # 命令消息交给命令插件处理，避免与 `/帮助` 等指令冲突。
    if _is_command_message(prompt):
        return

    session_id = _get_session_id(event)
    history = chat_memory_store.get_history(session_id)

    try:
        answer = await chat_with_deepseek(prompt, history=history)
        # 仅在调用成功后写入上下文，避免失败响应污染历史。
        chat_memory_store.append_turn(session_id, prompt, answer)
    except ValueError as error:
        await chat_with_ds.finish(f"DeepSeek 配置或参数错误：{error}")
    except Exception as error:
        # 统一兜底异常，避免把堆栈暴露给群聊用户。
        print(error)
        await chat_with_ds.finish("DeepSeek 请求失败，请稍后重试。")

    await chat_with_ds.finish(answer)
