from nonebot import on_command


help_cmd = on_command("help", priority=10, block=True)
about = on_command("about", priority=10, block=True)


@help_cmd.handle()
async def handle_help() -> None:
    await help_cmd.finish(
        "娜娜 Bot 可用命令：\n"
        "普通用户命令：\n"
        "/ping - 连通性测试\n"
        "/help - 查看命令列表\n"
        "/about - 查看机器人简介\n"
        "管理员命令（仅超管）：\n"
        "/whitelist - 查看白名单（仅超管）\n"
        "/whitelist_add group <群号> - 加群白名单（仅超管）\n"
        "/whitelist_add user <QQ号> - 加用户白名单（仅超管）\n"
        "/whitelist_remove group <群号> - 移除群白名单（仅超管）\n"
        "/whitelist_remove user <QQ号> - 移除用户白名单（仅超管）\n"
        "/rate_limit - 查看限流配置（仅超管）\n"
        "/rate_limit_on - 开启限流（仅超管）\n"
        "/rate_limit_off - 关闭限流（仅超管）\n"
        "/rate_limit_set user|group|private <窗口秒数> <最大次数> <冷却秒数> - 更新限流（仅超管）"
    )


@about.handle()
async def handle_about() -> None:
    await about.finish(
        "娜娜 Bot 是一个基于 NapCatQQ、NoneBot2 和 OneBot V11 的 QQ 机器人。\n"
        "开发者：骚客\n"
        "联系方式：2596818595@qq.com（请注明来意）"
    )
