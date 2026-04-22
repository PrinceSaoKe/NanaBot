# NanaBot

English | [简体中文](README.zh-CN.md)

NanaBot is a QQ bot built on top of [NapCatQQ](https://github.com/NapNeko/NapCatQQ), [NoneBot2](https://github.com/nonebot/nonebot2), and [OneBot V11](https://github.com/botuniverse/onebot-11), allowing QQ users to interact with it in both private and group chats. The current runtime environment is Python `3.11.3`.

## Feature Description

Current feature list is being organized.

## Command Description

Regular user commands:

- `/ping`
  Returns `pong` to verify connectivity.
- `/help`
  Shows the current command list.
- `/about`
  Shows a short introduction to NanaBot.

Admin commands (superuser only):

- `/whitelist`
  Shows group and user whitelists.
- `/whitelist_add group <group_id>`
  Adds a group to whitelist.
- `/whitelist_add user <qq_id>`
  Adds a user to whitelist.
- `/whitelist_remove group <group_id>`
  Removes a group from whitelist.
- `/whitelist_remove user <qq_id>`
  Removes a user from whitelist.
- `/rate_limit`
  Shows the current rate limit config.
- `/rate_limit_on`
  Enables rate limiting.
- `/rate_limit_off`
  Disables rate limiting.
- `/rate_limit_set user|group|private <window_seconds> <max_requests> <block_seconds>`
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
- `COMMAND_START`: The command prefix list recognized by NoneBot. With `["/"]`, messages such as `/ping` and `/help` will be treated as commands.
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

- Whitelist check runs before rate limiting.
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

1. Open NapCatQQ WebUI.
2. Create a new `WebSocket Client` in network settings.
3. Set the reverse WebSocket URL to:

```text
ws://127.0.0.1:8080/onebot/v11/ws
```

4. Set the same token in both NapCatQQ and `.env`.
5. Enable the connection and confirm it becomes connected.

## Contact

- Developer: 骚客
- Email: `2596818595@qq.com` (please state your purpose)
