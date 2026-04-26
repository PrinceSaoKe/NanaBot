import httpx
from nonebot import get_driver


def _get_deepseek_settings() -> tuple[str, str, str, float]:
    """
    读取 DeepSeek 配置。

    返回：
    - `(api_key, base_url, model, timeout_seconds)`：
      - `api_key`: DeepSeek API Key。
      - `base_url`: DeepSeek API 基础地址。
      - `model`: 模型名称，例如 `deepseek-chat`。
      - `timeout_seconds`: 请求超时时间（秒）。
    """
    config = get_driver().config
    api_key = str(getattr(config, "deepseek_api_key", "") or "").strip()
    base_url = str(getattr(config, "deepseek_base_url", "https://api.deepseek.com/v1") or "").strip()
    model = str(getattr(config, "deepseek_model", "deepseek-chat") or "").strip()
    timeout_raw = getattr(config, "deepseek_timeout_seconds", 60)

    try:
        timeout_seconds = float(timeout_raw)
    except (TypeError, ValueError):
        timeout_seconds = 60.0

    if timeout_seconds <= 0:
        timeout_seconds = 60.0

    return api_key, base_url, model, timeout_seconds


async def chat_with_deepseek(prompt: str) -> str:
    """
    调用 DeepSeek 对话接口并返回文本回复。

    参数：
    - prompt: 用户输入的纯文本提问内容，不能为空字符串。

    返回：
    - DeepSeek 返回的文本内容。

    异常：
    - `ValueError`：当 `prompt` 为空或未配置 `DEEPSEEK_API_KEY` 时抛出。
    - `RuntimeError`：当接口返回结构异常或空回复时抛出。
    - `httpx.HTTPError`：当网络请求失败时抛出。
    """
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise ValueError("问题内容不能为空。")

    api_key, base_url, model, timeout_seconds = _get_deepseek_settings()
    if not api_key:
        raise ValueError("未配置 DEEPSEEK_API_KEY。")

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": normalized_prompt}],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices") if isinstance(data, dict) else None
    if not choices:
        raise RuntimeError("DeepSeek 返回内容为空。")

    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = str(message.get("content", "") or "").strip()
    if not content:
        raise RuntimeError("DeepSeek 返回内容为空。")
    return content
