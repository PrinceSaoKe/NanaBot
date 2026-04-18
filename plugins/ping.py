from nonebot import on_command


ping = on_command("ping", priority=10, block=True)


@ping.handle()
async def handle_ping() -> None:
    await ping.finish("pong")
