import math
import time
from collections import deque
from dataclasses import dataclass

from services.config_store import RateLimitConfig


@dataclass
class RateLimitResult:
    """限流检查结果。"""

    allowed: bool
    reason: str = ""
    retry_after_seconds: int = 0


class InMemoryRateLimiter:
    """
    基于内存滑动窗口的限流器。

    说明：
    - 当前实现仅在单进程内生效，进程重启后计数会清空。
    - 适合单机部署的第一版防刷场景。
    """

    def __init__(self) -> None:
        # key -> 请求时间戳队列
        self._request_times: dict[str, deque[float]] = {}
        # key -> 封禁截止时间戳
        self._blocked_until: dict[str, float] = {}

    def _get_queue(self, key: str) -> deque[float]:
        """
        获取指定 key 的请求队列。

        参数：
        - key: 限流键，格式示例：`user:123`、`group:456`。

        返回：
        - 对应的请求时间戳队列。
        """
        queue = self._request_times.get(key)
        if queue is None:
            queue = deque()
            self._request_times[key] = queue
        return queue

    def _cleanup(self, key: str, now: float, window_seconds: int) -> None:
        """
        清理窗口外的历史请求和过期封禁记录。

        参数：
        - key: 限流键。
        - now: 当前时间戳。
        - window_seconds: 当前限流窗口秒数，必须是正整数。
        """
        queue = self._get_queue(key)
        threshold = now - window_seconds
        while queue and queue[0] <= threshold:
            queue.popleft()

        blocked_until = self._blocked_until.get(key)
        if blocked_until is not None and blocked_until <= now:
            self._blocked_until.pop(key, None)

        if not queue and key not in self._blocked_until:
            self._request_times.pop(key, None)

    def _hit(
            self,
            key: str,
            now: float,
            window_seconds: int,
            max_requests: int,
            block_seconds: int,
            reason: str,
    ) -> RateLimitResult:
        """
        对单个限流键执行一次命中检查并记录。

        参数：
        - key: 限流键。
        - now: 当前时间戳。
        - window_seconds: 限流窗口秒数，必须是正整数。
        - max_requests: 窗口内最大请求次数，必须是正整数。
        - block_seconds: 触发限流后的封禁秒数，必须是正整数。
        - reason: 触发时返回的原因描述文本。

        返回：
        - `RateLimitResult`：包含是否允许、触发原因、剩余封禁秒数。
        """
        self._cleanup(key, now, window_seconds)

        blocked_until = self._blocked_until.get(key)
        if blocked_until is not None and blocked_until > now:
            retry_after = int(math.ceil(blocked_until - now))
            return RateLimitResult(allowed=False, reason=reason, retry_after_seconds=retry_after)

        queue = self._get_queue(key)
        if len(queue) >= max_requests:
            blocked_until = now + block_seconds
            self._blocked_until[key] = blocked_until
            retry_after = int(math.ceil(blocked_until - now))
            return RateLimitResult(allowed=False, reason=reason, retry_after_seconds=retry_after)

        queue.append(now)
        return RateLimitResult(allowed=True)

    def check_group_event(
            self,
            user_id: str,
            group_id: str,
            config: RateLimitConfig,
    ) -> RateLimitResult:
        """
        检查群聊事件是否超限。

        参数：
        - user_id: 事件触发者 QQ 号（字符串）。
        - group_id: 当前群号（字符串）。
        - config: 限流配置对象。

        返回：
        - `RateLimitResult`：允许则 `allowed=True`，否则包含限流原因。
        """
        if not config.enabled:
            return RateLimitResult(allowed=True)

        now = time.time()
        user_key = f"user:{user_id}"
        user_result = self._hit(
            key=user_key,
            now=now,
            window_seconds=config.user_window_seconds,
            max_requests=config.user_max_requests,
            block_seconds=config.block_seconds,
            reason="用户触发频率过高",
        )
        if not user_result.allowed:
            return user_result

        group_key = f"group:{group_id}"
        return self._hit(
            key=group_key,
            now=now,
            window_seconds=config.group_window_seconds,
            max_requests=config.group_max_requests,
            block_seconds=config.block_seconds,
            reason="群内触发频率过高",
        )

    def check_private_event(self, user_id: str, config: RateLimitConfig) -> RateLimitResult:
        """
        检查私聊事件是否超限。

        参数：
        - user_id: 私聊用户 QQ 号（字符串）。
        - config: 限流配置对象。

        返回：
        - `RateLimitResult`：允许则 `allowed=True`，否则包含限流原因。
        """
        if not config.enabled:
            return RateLimitResult(allowed=True)

        now = time.time()
        user_key = f"user:{user_id}"
        user_result = self._hit(
            key=user_key,
            now=now,
            window_seconds=config.user_window_seconds,
            max_requests=config.user_max_requests,
            block_seconds=config.block_seconds,
            reason="用户触发频率过高",
        )
        if not user_result.allowed:
            return user_result

        private_key = f"private:{user_id}"
        return self._hit(
            key=private_key,
            now=now,
            window_seconds=config.private_window_seconds,
            max_requests=config.private_max_requests,
            block_seconds=config.block_seconds,
            reason="私聊触发频率过高",
        )


rate_limiter = InMemoryRateLimiter()
