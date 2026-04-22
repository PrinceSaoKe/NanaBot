# NanaBot

[English](README.md) | 简体中文

娜娜 Bot 是一个基于 [NapCatQQ](https://github.com/NapNeko/NapCatQQ)、[NoneBot2](https://github.com/nonebot/nonebot2) 和 [OneBot V11](https://github.com/botuniverse/onebot-11) 的 QQ 机器人，允许 QQ 用户在私聊、群聊中与其互动。当前运行环境为 Python `3.11.3`。

## 功能说明

当前功能列表正在整理中。

## 命令说明

普通用户命令：

- `/ping`
  用于检测机器人是否在线，返回 `pong`。
- `/帮助`
  仅显示当前用户有权限执行的命令。
- `/关于`
  查看娜娜 Bot 的简介。
- `/今天吃什么`
  随机推荐今天吃什么。
- `/今天喝什么`
  随机推荐今天喝什么。
- `/查看菜单 菜品|饮品`
  查看对应类型的全部菜单。
- `/猜成语`
  开启一局汉兜游戏。
- `/提示`
  查看当前汉兜游戏提示。
- `/结束`
  结束当前汉兜游戏。

管理员命令（仅超管）：

- `/添加菜单 <名称> 菜品|饮品 <图片>`
  添加菜单图片。
- `/删除菜单 <名称> 菜品|饮品`
  删除菜单图片。
- `/白名单`
  查看群白名单和用户白名单。
- `/添加白名单 群 <群号>`
  添加群白名单。
- `/添加白名单 用户 <QQ号>`
  添加用户白名单。
- `/移除白名单 群 <群号>`
  移除群白名单。
- `/移除白名单 用户 <QQ号>`
  移除用户白名单。
- `/限流`
  查看当前限流配置。
- `/开启限流`
  开启限流。
- `/关闭限流`
  关闭限流。
- `/设置限流 用户|群|私聊 <窗口秒数> <最大次数> <封禁秒数>`
  更新限流参数。

## 安装依赖

1. 创建或激活虚拟环境。
2. 通过依赖文件统一安装：

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. 可选：使用 `nb plugin install <插件名>` 安装第三方 NoneBot 插件。写入 `pyproject.toml` 的插件会在启动时自动加载。

## 配置说明

将 `.env.example` 重命名为 `.env`，然后填写你自己的配置。

`.env` 示例：

```env
HOST=127.0.0.1
PORT=8080
LOG_LEVEL=INFO
COMMAND_START=["/"]
NICKNAME=["Bot名字"]
ONEBOT_ACCESS_TOKEN=replace-with-your-token
SUPERUSERS=["你的QQ号"]
```

字段含义：

- `HOST`：NanaBot 监听地址。
- `PORT`：NoneBot 服务端口。
- `LOG_LEVEL`：日志级别。
- `COMMAND_START`：NoneBot 识别命令时使用的前缀列表。当前配置为 `["/"]`，像 `/ping`、`/帮助` 会被识别为命令。
- `NICKNAME`：NoneBot 使用的机器人昵称列表。`nonebot_plugin_whateat_pic` 这类插件会取第一个昵称作为回复中显示的机器人名字。
- `ONEBOT_ACCESS_TOKEN`：NanaBot 与 NapCatQQ 之间共用的访问令牌，必须和 NapCatQQ 中配置的 Token 完全一致。
- `SUPERUSERS`：允许使用管理员命令的 QQ 账号列表。

配置数据存储在 `data/config.json`：

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

限流规则：

- 先执行白名单检查，再执行限流检查。
- 仅对命令消息做限流。
- 群聊同时应用 `user` 和 `group` 两个维度。
- 私聊同时应用 `user` 和 `private` 两个维度。
- 超管执行安全管理命令时豁免限流，避免把机器人锁死。

## 启动 NanaBot

在项目根目录执行：

```powershell
python main.py
```

## 连接 NapCatQQ

- 仓库地址：<https://github.com/NapNeko/NapCatQQ>
- 官方文档：<https://napneko.github.io/>

安装并启动 NapCatQQ 后：

1. 打开 NapCatQQ WebUI。
2. 进入网络配置。
3. 新建一个 `WebSocket Client`。
4. 将反向 WebSocket 地址设置为：

```text
ws://127.0.0.1:8080/onebot/v11/ws
```

5. 在 NapCatQQ 和 `.env` 中配置相同的 Token。
6. 启用连接，并确认状态变为已连接。

## 联系方式

- 开发者：骚客
- 邮箱：`2596818595@qq.com`（请注明来意）
