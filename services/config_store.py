import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from services.whitelist_store import (
    add_whitelist_entry,
    initialize_whitelist_store,
    is_allowed,
    list_whitelist,
    remove_whitelist_entry,
)


@dataclass
class RateLimitConfig:
    """限流配置模型。"""

    # 是否启用限流。
    enabled: bool = True
    # 用户维度限流窗口（秒）。
    user_window_seconds: int = 10
    # 用户维度窗口内最大请求次数。
    user_max_requests: int = 5
    # 群维度限流窗口（秒）。
    group_window_seconds: int = 10
    # 群维度窗口内最大请求次数。
    group_max_requests: int = 15
    # 私聊维度限流窗口（秒）。
    private_window_seconds: int = 10
    # 私聊维度窗口内最大请求次数。
    private_max_requests: int = 5
    # 触发限流后的封禁时长（秒）。
    block_seconds: int = 30


DEFAULT_DEEPSEEK_SYSTEM_PROMPT = (
    "你是一个QQ用户，名字叫{bot_name}。"
    "回答要像真人聊天，简短、直接、自然。"
    "默认用1到3句短句回答，除非用户明确要求详细。"
    "不要使用Markdown标题、列表或长段落。"
)


@dataclass
class DeepSeekChatConfig:
    """DeepSeek 聊天配置模型。"""

    # DeepSeek 系统提示词模板，允许使用 `{bot_name}` 占位符。
    system_prompt: str = DEFAULT_DEEPSEEK_SYSTEM_PROMPT
    # 单次回复允许的最大 token 数。
    max_tokens: int = 180
    # 每个会话最多保留的上下文消息条数。
    max_context_messages: int = 20


@dataclass
class BotConfig:
    """机器人配置模型。"""

    # 允许响应的QQ群号列表（字符串形式）。
    group_whitelist: list[str] = field(default_factory=list)
    # 允许响应私聊的QQ号列表（字符串形式）。
    user_whitelist: list[str] = field(default_factory=list)
    # 限流配置。
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    # DeepSeek 聊天配置。
    deepseek_chat: DeepSeekChatConfig = field(default_factory=DeepSeekChatConfig)


CONFIG_DIR = Path("data")
CONFIG_PATH = CONFIG_DIR / "config.json"


def _normalize_ids(values: list[str] | None) -> list[str]:
    """
    标准化 ID 列表，确保配置可预测且稳定。

    参数：
    - values: 原始 ID 列表，元素通常是群号或 QQ 号。

    返回：
    - 处理后的列表：去空白、去重、排序，元素均为字符串。
    """
    if not values:
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _normalize_positive_int(value: int | str | None, default: int) -> int:
    """
    将输入值标准化为正整数。

    参数：
    - value: 待处理值，允许 `int`、数字字符串或 `None`。
    - default: value 非法时使用的默认值，必须是正整数。

    返回：
    - 正整数结果。
    """
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parse_rate_limit_config(raw: dict | None) -> RateLimitConfig:
    """
    从原始字典解析限流配置。

    参数：
    - raw: 原始限流配置字典，可为 `None`。

    返回：
    - 标准化后的 `RateLimitConfig`。
    """
    if not isinstance(raw, dict):
        return RateLimitConfig()

    return RateLimitConfig(
        enabled=bool(raw.get("enabled", True)),
        user_window_seconds=_normalize_positive_int(raw.get("user_window_seconds"), 10),
        user_max_requests=_normalize_positive_int(raw.get("user_max_requests"), 5),
        group_window_seconds=_normalize_positive_int(raw.get("group_window_seconds"), 10),
        group_max_requests=_normalize_positive_int(raw.get("group_max_requests"), 15),
        private_window_seconds=_normalize_positive_int(raw.get("private_window_seconds"), 10),
        private_max_requests=_normalize_positive_int(raw.get("private_max_requests"), 5),
        block_seconds=_normalize_positive_int(raw.get("block_seconds"), 30),
    )


def _parse_deepseek_chat_config(raw: dict | None) -> DeepSeekChatConfig:
    """
    从原始字典解析 DeepSeek 聊天配置。

    参数：
    - raw: 原始 DeepSeek 聊天配置字典，可为 `None`。

    返回：
    - 标准化后的 `DeepSeekChatConfig`。
    """
    if not isinstance(raw, dict):
        return DeepSeekChatConfig()

    system_prompt = str(raw.get("system_prompt", DEFAULT_DEEPSEEK_SYSTEM_PROMPT) or "").strip()
    if not system_prompt:
        system_prompt = DEFAULT_DEEPSEEK_SYSTEM_PROMPT

    return DeepSeekChatConfig(
        system_prompt=system_prompt,
        max_tokens=_normalize_positive_int(raw.get("max_tokens"), 180),
        max_context_messages=_normalize_positive_int(raw.get("max_context_messages"), 20),
    )


def _ensure_config_file() -> None:
    """
    确保配置目录和配置文件存在。

    当 `data/config.json` 不存在时，会自动创建并写入默认配置结构。
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        save_config(BotConfig())
    initialize_whitelist_store()


def load_config() -> BotConfig:
    """
    从磁盘加载配置并返回配置对象。

    返回：
    - `BotConfig`：已标准化后的完整配置。
    """
    _ensure_config_file()
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return BotConfig(
        group_whitelist=list_whitelist("group"),
        user_whitelist=list_whitelist("user"),
        rate_limit=_parse_rate_limit_config(raw.get("rate_limit")),
        deepseek_chat=_parse_deepseek_chat_config(raw.get("deepseek_chat")),
    )


def save_config(config: BotConfig) -> None:
    """
    保存配置到 `data/config.json`。

    参数：
    - config: 待保存的配置对象。

    说明：
    - 保存前会对 ID 列表和限流配置进行标准化，避免脏数据。
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    normalized = BotConfig(
        group_whitelist=[],
        user_whitelist=[],
        rate_limit=_parse_rate_limit_config(asdict(config.rate_limit)),
        deepseek_chat=_parse_deepseek_chat_config(asdict(config.deepseek_chat)),
    )
    CONFIG_PATH.write_text(
        json.dumps(asdict(normalized), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_rate_limit_config() -> RateLimitConfig:
    """
    获取当前限流配置。

    返回：
    - `RateLimitConfig`：当前限流配置快照。
    """
    return load_config().rate_limit


def get_deepseek_chat_config() -> DeepSeekChatConfig:
    """
    获取当前 DeepSeek 聊天配置。

    返回：
    - `DeepSeekChatConfig`：当前 DeepSeek 聊天配置快照。
    """
    return load_config().deepseek_chat


def set_rate_limit_enabled(enabled: bool) -> None:
    """
    设置限流开关状态。

    参数：
    - enabled: `True` 表示启用限流，`False` 表示关闭限流。
    """
    config = load_config()
    config.rate_limit.enabled = enabled
    save_config(config)


def update_rate_limit(
        scope: str,
        window_seconds: int | str,
        max_requests: int | str,
        block_seconds: int | str,
) -> RateLimitConfig:
    """
    按作用域更新限流参数。

    参数：
    - scope: 作用域，仅允许 `user`、`group` 或 `private`。
    - window_seconds: 限流窗口秒数，必须是正整数。
    - max_requests: 窗口内最大请求次数，必须是正整数。
    - block_seconds: 触发限流后的封禁秒数，必须是正整数。

    返回：
    - 更新后的 `RateLimitConfig`。

    异常：
    - `ValueError`：scope 非法。
    """
    config = load_config()
    rate_limit = config.rate_limit

    normalized_window = _normalize_positive_int(window_seconds, rate_limit.user_window_seconds)
    normalized_max = _normalize_positive_int(max_requests, rate_limit.user_max_requests)
    normalized_block = _normalize_positive_int(block_seconds, rate_limit.block_seconds)

    if scope == "user":
        rate_limit.user_window_seconds = normalized_window
        rate_limit.user_max_requests = normalized_max
    elif scope == "group":
        rate_limit.group_window_seconds = normalized_window
        rate_limit.group_max_requests = normalized_max
    elif scope == "private":
        rate_limit.private_window_seconds = normalized_window
        rate_limit.private_max_requests = normalized_max
    else:
        raise ValueError(f"Unsupported rate limit scope: {scope}")

    rate_limit.block_seconds = normalized_block
    save_config(config)
    return rate_limit


def is_group_allowed(group_id: int | str) -> bool:
    """
    判断群号是否在群白名单中。

    参数：
    - group_id: 群号，允许 `int` 或 `str`。

    返回：
    - `True` 表示允许，`False` 表示不允许。
    """
    return is_allowed("group", group_id)


def is_user_allowed(user_id: int | str) -> bool:
    """
    判断用户是否在私聊白名单中。

    参数：
    - user_id: QQ 号，允许 `int` 或 `str`。

    返回：
    - `True` 表示允许，`False` 表示不允许。
    """
    return is_allowed("user", user_id)


def add_to_whitelist(target_type: str, target_id: int | str) -> bool:
    """
    向指定白名单新增一个 ID。

    参数：
    - target_type: 白名单类型，仅允许 `group` 或 `user`。
      - `group`: 操作群白名单 `group_whitelist`
      - `user`: 操作用户白名单 `user_whitelist`
    - target_id: 目标 ID，允许 `int` 或 `str`。

    返回：
    - `True`：新增成功。
    - `False`：目标已存在于对应白名单。

    异常：
    - `ValueError`：`target_type` 不是 `group` 或 `user`。
    """
    return add_whitelist_entry(target_type, target_id)


def remove_from_whitelist(target_type: str, target_id: int | str) -> bool:
    """
    从指定白名单移除一个 ID。

    参数：
    - target_type: 白名单类型，仅允许 `group` 或 `user`。
      - `group`: 操作群白名单 `group_whitelist`
      - `user`: 操作用户白名单 `user_whitelist`
    - target_id: 目标 ID，允许 `int` 或 `str`。

    返回：
    - `True`：移除成功。
    - `False`：目标不存在于对应白名单。

    异常：
    - `ValueError`：`target_type` 不是 `group` 或 `user`。
    """
    return remove_whitelist_entry(target_type, target_id)
