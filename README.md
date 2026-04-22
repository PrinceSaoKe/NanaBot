# NanaBot

English | [简体中文](README.zh-CN.md)

NanaBot is a QQ bot built on top of [NapCatQQ](https://github.com/NapNeko/NapCatQQ), [NoneBot2](https://github.com/nonebot/nonebot2), and [OneBot V11](https://github.com/botuniverse/onebot-11), allowing QQ users to interact with it in both private and group chats. The current runtime environment is Python `3.11.3`.

## Feature Description

The current feature list is still being organized.

## Command Description

Regular user commands:

- `/ping`
  Returns `pong` to verify connectivity.
- `/帮助`
  Shows only the commands available to the current user.
- `/关于`
  Shows a short introduction to NanaBot.
- `/今天吃什么`
  Randomly recommends something to eat today.
- `/今天喝什么`
  Randomly recommends something to drink today.
- `/查看菜单 菜品|饮品`
  Shows all menu items for the given type.
- `/猜成语`
  Starts one handle game.
- `/提示`
  Shows one hint for the current handle game.
- `/结束`
  Ends the current handle game.

Admin commands (superuser only):

- `/添加菜单 <名称> 菜品|饮品 <图片>`
  Adds a menu image.
- `/删除菜单 <名称> 菜品|饮品`
  Deletes a menu image.
- `/白名单`
  Shows group and user whitelists.
- `/添加白名单 群 <群号>`
  Adds a group to the whitelist.
- `/添加白名单 用户 <QQ号>`
  Adds a user to the whitelist.
- `/移除白名单 群 <群号>`
  Removes a group from the whitelist.
- `/移除白名单 用户 <QQ号>`
  Removes a user from the whitelist.
- `/限流`
  Shows the current rate limit configuration.
- `/开启限流`
  Enables rate limiting.
- `/关闭限流`
  Disables rate limiting.
- `/设置限流 用户|群|私聊 <窗口秒数> <最大次数> <封禁秒数>`
  Updates rate limit settings.

## Installation

1. Create or activate a virtual environment.
2. Install dependencies from the dependency file:

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. Optional: install third-party NoneBot plugins with `nb plugin install <plugin_name>`. Plugins declared in
   `pyproject.toml` will be loaded automatically on startup.

## Configuration

Rename `.env.example` to `.env`, then fill in your own configuration.

Example `.env`:

```env
HOST=127.0.0.1
PORT=8080
LOG_LEVEL=INFO
COMMAND_START=["/"]
ONEBOT_ACCESS_TOKEN=replace-with-your-token
SUPERUSERS=["your-qq-number"]
```

Field notes:

- `HOST`: The bind address used by NanaBot.
- `PORT`: The service port used by NoneBot.
- `LOG_LEVEL`: The log verbosity level.
- `COMMAND_START`: The command prefix list recognized by NoneBot. With `["/"]`, messages such as `/ping` and `/帮助`
  will be treated as commands.
- `ONEBOT_ACCESS_TOKEN`: The shared access token used between NanaBot and NapCatQQ. It must match the token configured in NapCatQQ.
- `SUPERUSERS`: QQ accounts allowed to use admin commands.

Config data is persisted in `data/config.json`:

```json
{
  "group_whitelist": [],
  "user_whitelist": [],
  "rate_limit": {
    "enabled": true,
    "user_window_seconds": 10,
    "user_max_requests": 5,
    "group_window_seconds": 10,
    "group_max_requests": 15,
    "private_window_seconds": 10,
    "private_max_requests": 5,
    "block_seconds": 30
  }
}
```

Rate limit behavior:

- Whitelist checks run before rate limiting.
- Only command messages are rate-limited.
- Group messages apply both `user` and `group` scopes.
- Private messages apply both `user` and `private` scopes.
- Superuser security management commands are exempt to avoid lockout.

## Run NanaBot

Start NanaBot from the project root:

```powershell
python main.py
```

## Connect NapCatQQ

- Repository: <https://github.com/NapNeko/NapCatQQ>
- Documentation: <https://napneko.github.io/>

After NapCatQQ is installed and running:

1. Open the NapCatQQ WebUI.
2. Go to network settings.
3. Create a new `WebSocket Client`.
4. Set the reverse WebSocket URL to:

```text
ws://127.0.0.1:8080/onebot/v11/ws
```

5. Set the same token in both NapCatQQ and `.env`.
6. Enable the connection and confirm that it becomes connected.

## Contact

- Developer: 骚客
- Email: `2596818595@qq.com` (please state your purpose)
