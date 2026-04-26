import json
from pathlib import Path

from services.database import get_connection, initialize_database

LEGACY_CONFIG_PATH = Path("data") / "config.json"


def _normalize_target_id(target_id: int | str) -> str:
    """
    将目标 ID 标准化为非空字符串。

    参数：
    - target_id: 群号或 QQ 号，允许 `int` 或 `str`。

    返回：
    - 去除首尾空白后的字符串形式 ID。
    """
    return str(target_id).strip()


def _normalize_target_type(target_type: str) -> str:
    """
    校验并标准化白名单类型。

    参数：
    - target_type: 白名单类型，仅允许 `group` 或 `user`。

    返回：
    - 标准化后的白名单类型。

    异常：
    - `ValueError`：当 `target_type` 不是 `group` 或 `user` 时抛出。
    """
    normalized = str(target_type).strip()
    if normalized not in {"group", "user"}:
        raise ValueError(f"Unsupported whitelist target type: {target_type}")
    return normalized


def _read_legacy_whitelist() -> tuple[list[str], list[str]]:
    """
    读取旧版 JSON 配置中的白名单数据。

    返回：
    - `(group_whitelist, user_whitelist)`，均为去重后的字符串列表。
    """
    if not LEGACY_CONFIG_PATH.exists():
        return [], []

    raw = json.loads(LEGACY_CONFIG_PATH.read_text(encoding="utf-8"))
    groups = sorted({str(item).strip() for item in raw.get("group_whitelist", []) if str(item).strip()})
    users = sorted({str(item).strip() for item in raw.get("user_whitelist", []) if str(item).strip()})
    return groups, users


def _clear_legacy_whitelist() -> None:
    """
    清空旧版 JSON 配置中的白名单字段。

    说明：
    - 仅清空 `group_whitelist` 与 `user_whitelist`。
    - 其他配置，例如限流配置，保持不变。
    """
    if not LEGACY_CONFIG_PATH.exists():
        return

    raw = json.loads(LEGACY_CONFIG_PATH.read_text(encoding="utf-8"))
    raw["group_whitelist"] = []
    raw["user_whitelist"] = []
    LEGACY_CONFIG_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def initialize_whitelist_store() -> None:
    """
    初始化白名单存储，并在需要时迁移旧 JSON 数据。

    说明：
    - 先确保数据库与白名单表存在。
    - 若数据库白名单为空，则尝试从 `data/config.json` 迁移旧白名单数据。
    - 迁移成功后会清空旧 JSON 中的白名单字段，避免双写混乱。
    """
    initialize_database()

    groups, users = _read_legacy_whitelist()
    if not groups and not users:
        return

    with get_connection() as connection:
        connection.executemany(
            "INSERT OR IGNORE INTO whitelist_entries (target_type, target_id) VALUES (?, ?)",
            [("group", group_id) for group_id in groups],
        )
        connection.executemany(
            "INSERT OR IGNORE INTO whitelist_entries (target_type, target_id) VALUES (?, ?)",
            [("user", user_id) for user_id in users],
        )
        connection.commit()

    _clear_legacy_whitelist()


def list_whitelist(target_type: str) -> list[str]:
    """
    获取指定类型的白名单列表。

    参数：
    - target_type: 白名单类型，仅允许 `group` 或 `user`。

    返回：
    - 指定类型下按字典序排列的目标 ID 列表。
    """
    normalized_type = _normalize_target_type(target_type)
    initialize_whitelist_store()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT target_id
            FROM whitelist_entries
            WHERE target_type = ?
            ORDER BY target_id
            """,
            (normalized_type,),
        ).fetchall()
    return [str(row["target_id"]) for row in rows]


def is_allowed(target_type: str, target_id: int | str) -> bool:
    """
    判断目标是否存在于指定白名单中。

    参数：
    - target_type: 白名单类型，仅允许 `group` 或 `user`。
    - target_id: 群号或 QQ 号，允许 `int` 或 `str`。

    返回：
    - `True` 表示目标存在于白名单中。
    - `False` 表示目标不在白名单中。
    """
    normalized_type = _normalize_target_type(target_type)
    normalized_id = _normalize_target_id(target_id)
    initialize_whitelist_store()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM whitelist_entries
            WHERE target_type = ?
              AND target_id = ?
            LIMIT 1
            """,
            (normalized_type, normalized_id),
        ).fetchone()
    return row is not None


def add_whitelist_entry(target_type: str, target_id: int | str) -> bool:
    """
    向指定白名单新增一个目标 ID。

    参数：
    - target_type: 白名单类型，仅允许 `group` 或 `user`。
    - target_id: 群号或 QQ 号，允许 `int` 或 `str`。

    返回：
    - `True` 表示新增成功。
    - `False` 表示目标已存在。
    """
    normalized_type = _normalize_target_type(target_type)
    normalized_id = _normalize_target_id(target_id)
    initialize_whitelist_store()
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT OR IGNORE INTO whitelist_entries (target_type, target_id) VALUES (?, ?)",
            (normalized_type, normalized_id),
        )
        connection.commit()
    return cursor.rowcount > 0


def remove_whitelist_entry(target_type: str, target_id: int | str) -> bool:
    """
    从指定白名单移除一个目标 ID。

    参数：
    - target_type: 白名单类型，仅允许 `group` 或 `user`。
    - target_id: 群号或 QQ 号，允许 `int` 或 `str`。

    返回：
    - `True` 表示移除成功。
    - `False` 表示目标原本不存在。
    """
    normalized_type = _normalize_target_type(target_type)
    normalized_id = _normalize_target_id(target_id)
    initialize_whitelist_store()
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM whitelist_entries WHERE target_type = ? AND target_id = ?",
            (normalized_type, normalized_id),
        )
        connection.commit()
    return cursor.rowcount > 0
