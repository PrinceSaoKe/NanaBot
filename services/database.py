import sqlite3
from pathlib import Path

DATA_DIR = Path("data")
DATABASE_PATH = DATA_DIR / "nanabot.db"


def get_connection() -> sqlite3.Connection:
    """
    获取 SQLite 数据库连接。

    返回：
    - 指向 `data/nanabot.db` 的 SQLite 连接对象。
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """
    初始化数据库结构。

    说明：
    - 若数据库文件或白名单表不存在，则自动创建。
    - 当前仅初始化白名单表，后续可继续扩展其他业务表。
    """
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS whitelist_entries
            (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT NOT NULL,
                target_id   TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (target_type, target_id)
            )
            """
        )
        connection.commit()
