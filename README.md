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
- `/猜单词`
  Starts one wordle game.
- `/猜单词 -l <3~8>`
  Starts one wordle game with a custom word length.
- `/提示`
  Shows one hint for the current wordle game.
- `/结束`
  Ends the current wordle game.
- `/猜成语`
  Sends the handle rule image first, then starts one handle game.
- `@BotName <content>`
  Sends the text after `@` to DeepSeek and returns a short conversational reply (default 1-3 sentences); group chats and
  private chats keep separate context memory.
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
NICKNAME=["BotName"]
ONEBOT_ACCESS_TOKEN=replace-with-your-token
SUPERUSERS=["your-qq-number"]
DEEPSEEK_API_KEY=replace-with-your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT_SECONDS=60
```

Field notes:

- `HOST`: The bind address used by NanaBot.
- `PORT`: The service port used by NoneBot.
- `LOG_LEVEL`: The log verbosity level.
- `COMMAND_START`: The command prefix list recognized by NoneBot. With `["/"]`, messages such as `/ping` and `/帮助`
  will be treated as commands.
- `NICKNAME`: The bot nickname list used by NoneBot. Plugins such as `nonebot_plugin_whateat_pic` will use the first
  nickname as the bot name shown in replies.
- `ONEBOT_ACCESS_TOKEN`: The shared access token used between NanaBot and NapCatQQ. It must match the token configured in NapCatQQ.
- `SUPERUSERS`: QQ accounts allowed to use admin commands.
- `DEEPSEEK_API_KEY`: DeepSeek API key. If missing, the `@BotName` chat feature is unavailable.
- `DEEPSEEK_BASE_URL`: DeepSeek API base URL. Default: `https://api.deepseek.com/v1`.
- `DEEPSEEK_MODEL`: DeepSeek model name used for chat. Default: `deepseek-chat`.
- `DEEPSEEK_TIMEOUT_SECONDS`: Request timeout for DeepSeek in seconds. Must be greater than `0`. Default: `60`.

Config data is split across YAML and SQLite:

```yaml
# NanaBot config file
group_whitelist: []
user_whitelist: []

rate_limit:
  enabled: true
  user_window_seconds: 10
  user_max_requests: 5
  group_window_seconds: 10
  group_max_requests: 15
  private_window_seconds: 10
  private_max_requests: 5
  block_seconds: 30

deepseek_chat:
  system_prompt: 你是一个QQ用户，名字叫{bot_name}。回答要像真人聊天，简短、直接、自然。默认用1到3句短句回答，除非用户明确要求详细。不要使用Markdown标题、列表或长段落。
  max_tokens: 180
  max_context_messages: 20
```

- `data/config.yml`: Stores rate limit configuration and DeepSeek chat behavior configuration, with comment support.
- `data/nanabot.db`: Stores group and user whitelist data.
- On first startup after this change, the old `data/config.json` will be migrated automatically to
  `data/config.yml`, and legacy whitelist entries from the old JSON will also be migrated into SQLite.

`deepseek_chat` field notes:

- `system_prompt`: DeepSeek system prompt template. You can use the `{bot_name}` placeholder to inject the bot nickname.
- `max_tokens`: Maximum token budget for a single DeepSeek reply. Must be greater than `0`.
- `max_context_messages`: Maximum number of context messages kept per group or private chat session. Must be greater
  than `0`.

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
