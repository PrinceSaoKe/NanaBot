from collections import defaultdict

from services.config_store import get_deepseek_chat_config


class ChatMemoryStore:
    """
    会话上下文内存存储。

    说明：
    - 按会话 ID（例如 `group:123456`、`private:10001`）隔离上下文。
    - 仅保存 `user` 与 `assistant` 两种角色消息。
    - 超出上限时自动保留最近消息，避免内存无限增长。
    """

    def __init__(self) -> None:
        """
        初始化上下文存储。
        """
        self._memories: dict[str, list[dict[str, str]]] = defaultdict(list)

    def _trim_history(self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        按当前配置裁剪历史消息条数。

        参数：
        - history: 待裁剪的历史消息列表。

        返回：
        - 裁剪后的历史消息列表。
        """
        max_context_messages = get_deepseek_chat_config().max_context_messages
        if len(history) <= max_context_messages:
            return history
        return history[-max_context_messages:]

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        """
        获取会话历史消息副本。

        参数：
        - session_id: 会话 ID，建议格式：
          - 群聊：`group:<group_id>`
          - 私聊：`private:<user_id>`

        返回：
        - 历史消息列表副本，元素格式：
          `{"role": "user"|"assistant", "content": "..."}`。
        """
        normalized_session_id = str(session_id).strip()
        history = self._trim_history(self._memories.get(normalized_session_id, []))
        if normalized_session_id:
            self._memories[normalized_session_id] = history
        return [dict(item) for item in history]

    def append_turn(self, session_id: str, user_message: str, assistant_message: str) -> None:
        """
        追加一轮对话到指定会话。

        参数：
        - session_id: 会话 ID，建议格式：
          - 群聊：`group:<group_id>`
          - 私聊：`private:<user_id>`
        - user_message: 用户本轮输入文本。
        - assistant_message: 模型本轮输出文本。
        """
        normalized_session_id = str(session_id).strip()
        normalized_user_message = str(user_message).strip()
        normalized_assistant_message = str(assistant_message).strip()
        if not normalized_session_id:
            return
        if not normalized_user_message or not normalized_assistant_message:
            return

        history = self._memories[normalized_session_id]
        history.append({"role": "user", "content": normalized_user_message})
        history.append({"role": "assistant", "content": normalized_assistant_message})
        self._memories[normalized_session_id] = self._trim_history(history)

    def clear_session(self, session_id: str) -> None:
        """
        清空指定会话上下文。

        参数：
        - session_id: 会话 ID，建议格式：
          - 群聊：`group:<group_id>`
          - 私聊：`private:<user_id>`
        """
        normalized_session_id = str(session_id).strip()
        if not normalized_session_id:
            return
        self._memories.pop(normalized_session_id, None)


chat_memory_store = ChatMemoryStore()
