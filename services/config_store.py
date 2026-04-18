import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class BotConfig:
    """机器人配置模型。"""

    # 允许响应的QQ群号列表（字符串形式）。
    group_whitelist: list[str] = field(default_factory=list)
    # 允许响应私聊的QQ号列表（字符串形式）。
    user_whitelist: list[str] = field(default_factory=list)


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


def _ensure_config_file() -> None:
    """
    确保配置目录和配置文件存在。

    当 `data/config.json` 不存在时，会自动创建并写入默认空白名单结构。
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        save_config(BotConfig())


def load_config() -> BotConfig:
    """
    从磁盘加载配置并返回配置对象。

    返回：
    - `BotConfig`：已标准化的白名单配置。
    """
    _ensure_config_file()
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return BotConfig(
        group_whitelist=_normalize_ids(raw.get("group_whitelist")),
        user_whitelist=_normalize_ids(raw.get("user_whitelist")),
    )


def save_config(config: BotConfig) -> None:
    """
    保存配置到 `data/config.json`。

    参数：
    - config: 待保存的配置对象。

    说明：
    - 保存前会对 ID 列表执行标准化，避免重复和脏数据。
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    normalized = BotConfig(
        group_whitelist=_normalize_ids(config.group_whitelist),
        user_whitelist=_normalize_ids(config.user_whitelist),
    )
    CONFIG_PATH.write_text(
        json.dumps(asdict(normalized), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def is_group_allowed(group_id: int | str) -> bool:
    """
    判断群号是否在群白名单中。

    参数：
    - group_id: 群号，允许 `int` 或 `str`。

    返回：
    - `True` 表示允许，`False` 表示不允许。
    """
    return str(group_id) in load_config().group_whitelist


def is_user_allowed(user_id: int | str) -> bool:
    """
    判断用户是否在私聊白名单中。

    参数：
    - user_id: QQ 号，允许 `int` 或 `str`。

    返回：
    - `True` 表示允许，`False` 表示不允许。
    """
    return str(user_id) in load_config().user_whitelist


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
    config = load_config()
    normalized_id = str(target_id).strip()

    if target_type == "group":
        if normalized_id in config.group_whitelist:
            return False
        config.group_whitelist.append(normalized_id)
    elif target_type == "user":
        if normalized_id in config.user_whitelist:
            return False
        config.user_whitelist.append(normalized_id)
    else:
        raise ValueError(f"Unsupported whitelist target type: {target_type}")

    save_config(config)
    return True


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
    config = load_config()
    normalized_id = str(target_id).strip()

    if target_type == "group":
        if normalized_id not in config.group_whitelist:
            return False
        config.group_whitelist.remove(normalized_id)
    elif target_type == "user":
        if normalized_id not in config.user_whitelist:
            return False
        config.user_whitelist.remove(normalized_id)
    else:
        raise ValueError(f"Unsupported whitelist target type: {target_type}")

    save_config(config)
    return True
