from dataclasses import dataclass


@dataclass(frozen=True)
class CommandInfo:
    """
    命令展示信息。
    """

    # 展示给用户的命令文本，例如 `/帮助`。
    command: str
    # 命令的中文说明。
    description: str
    # 是否仅超级管理员可见。
    admin_only: bool = False


COMMAND_REGISTRY: list[CommandInfo] = [
    CommandInfo("/ping", "连通性测试"),
    CommandInfo("/帮助", "查看当前用户可执行的命令"),
    CommandInfo("/关于", "查看机器人简介"),
    CommandInfo("/今天吃什么", "随机推荐今天吃什么"),
    CommandInfo("/今天喝什么", "随机推荐今天喝什么"),
    CommandInfo("/查看菜单 菜品|饮品", "查看对应类型的全部菜单"),
    CommandInfo("/猜成语", "开启一局汉兜游戏"),
    CommandInfo("/提示", "查看当前汉兜游戏提示"),
    CommandInfo("/结束", "结束当前汉兜游戏"),
    CommandInfo("/添加菜单 <名称> 菜品|饮品 <图片>", "添加菜单图片", admin_only=True),
    CommandInfo("/删除菜单 <名称> 菜品|饮品", "删除菜单图片", admin_only=True),
    CommandInfo("/白名单", "查看白名单", admin_only=True),
    CommandInfo("/添加白名单 群 <群号>", "添加群白名单", admin_only=True),
    CommandInfo("/添加白名单 用户 <QQ号>", "添加用户白名单", admin_only=True),
    CommandInfo("/移除白名单 群 <群号>", "移除群白名单", admin_only=True),
    CommandInfo("/移除白名单 用户 <QQ号>", "移除用户白名单", admin_only=True),
    CommandInfo("/限流", "查看限流配置", admin_only=True),
    CommandInfo("/开启限流", "开启限流", admin_only=True),
    CommandInfo("/关闭限流", "关闭限流", admin_only=True),
    CommandInfo(
        "/设置限流 用户|群|私聊 <窗口秒数> <最大次数> <封禁秒数>",
        "更新限流参数",
        admin_only=True,
    ),
]


def get_visible_commands(is_superuser: bool) -> list[CommandInfo]:
    """
    获取当前用户可见的命令列表。

    参数：
    - is_superuser: `True` 表示当前用户是超级管理员。

    返回：
    - 当前用户可见的命令展示信息列表。
    """
    if is_superuser:
        return COMMAND_REGISTRY
    return [command for command in COMMAND_REGISTRY if not command.admin_only]
