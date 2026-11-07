from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from itertools import islice


@dataclass(frozen=True)
class RateLimitPolicy:
    """Token-bucket policy: sustained requests per window and burst capacity."""

    requests_per_window: int
    time_window: float
    burst_capacity: int

    def __post_init__(self) -> None:
        if self.requests_per_window <= 0:
            raise ValueError("requests_per_window must be positive")
        if self.time_window <= 0:
            raise ValueError("time_window must be positive")
        if self.burst_capacity <= 0:
            raise ValueError("burst_capacity must be positive")

    @property
    def refill_rate(self) -> float:
        return self.requests_per_window / self.time_window


@dataclass(slots=True)
class _Bucket:
    tokens: float
    timestamp: float
    policy: RateLimitPolicy


class RateLimiter:
    """Per-client token buckets with callback-supplied policy and bounded cleanup.

    The first two constructor arguments retain the legacy API and defaults.
    For legacy callers, burst capacity defaults to max_requests, matching the
    old token bucket's initial capacity. New integrations should pass
    ``policy_for_client`` and may pass ``burst_capacity`` if using legacy mode.
    """

    def __init__(
        self,
        max_requests: int = 10_000,
        time_window: float = 60.0,
        *,
        burst_capacity: int | None = None,
        policy_for_client: Callable[[str], RateLimitPolicy] | None = None,
        cleanup_interval: float = 300.0,
        cleanup_batch_size: int = 256,
    ) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if time_window <= 0:
            raise ValueError("time_window must be positive")
        if cleanup_interval <= 0:
            raise ValueError("cleanup_interval must be positive")
        if cleanup_batch_size <= 0:
            raise ValueError("cleanup_batch_size must be positive")

        self._legacy_policy = RateLimitPolicy(
            requests_per_window=max_requests,
            time_window=time_window,
            burst_capacity=max_requests if burst_capacity is None else burst_capacity,
        )
        # Preserve the legacy public configuration attributes.
        self.max_requests = max_requests
        self.time_window = time_window
        self.refill_rate = max_requests / time_window
        self._policy_for_client = policy_for_client
        self._cleanup_interval = cleanup_interval
        self._cleanup_batch_size = cleanup_batch_size
        self.clients: dict[str, _Bucket] = {}
        self._next_cleanup_at: float | None = None
        self._cleanup_remaining: int | None = None

    def _get_policy(self, api_key: str) -> RateLimitPolicy:
        if self._policy_for_client is None:
            return self._legacy_policy
        policy = self._policy_for_client(api_key)
        if not isinstance(policy, RateLimitPolicy):
            raise TypeError("policy_for_client must return a RateLimitPolicy")
        return policy

    def _cleanup(self, timestamp: float) -> None:
        if self._next_cleanup_at is None:
            self._next_cleanup_at = timestamp + self._cleanup_interval
            return
        if self._cleanup_remaining is None:
            if timestamp < self._next_cleanup_at:
                return
            self._cleanup_remaining = len(self.clients)

        # Visit a bounded batch and rotate survivors to the end. This avoids
        # both a full-map allocation and mutation-invalidated iterators.
        batch_size = min(self._cleanup_batch_size, self._cleanup_remaining)
        api_keys = list(islice(self.clients, batch_size))
        for api_key in api_keys:
            bucket = self.clients.get(api_key)
            if bucket is not None:
                elapsed = timestamp - bucket.timestamp
                refilled = min(
                    float(bucket.policy.burst_capacity),
                    bucket.tokens + elapsed * bucket.policy.refill_rate,
                )
                if elapsed >= 0 and refilled >= bucket.policy.burst_capacity:
                    del self.clients[api_key]
                else:
                    self.clients.pop(api_key)
                    self.clients[api_key] = bucket
            self._cleanup_remaining -= 1

        if self._cleanup_remaining == 0:
            self._cleanup_remaining = None
            self._next_cleanup_at = timestamp + self._cleanup_interval

    def cleanup(self, timestamp: float) -> None:
        """Run one bounded cleanup batch; safe to call from a periodic job.

        ``timestamp`` must use the same non-decreasing time source as requests.
        ``allow_request`` also advances cleanup, so a separate scheduler is
        optional when request traffic is sufficient.
        """
        self._cleanup(timestamp)

    def allow_request(self, api_key: str, timestamp: float) -> bool:
        policy = self._get_policy(api_key)
        bucket = self.clients.get(api_key)
        if bucket is None:
            tokens = float(policy.burst_capacity)
        else:
            elapsed = timestamp - bucket.timestamp
            # Accrue elapsed time at the previous policy, then clamp to a new
            # policy's burst capacity before applying that policy going forward.
            tokens = min(
                float(policy.burst_capacity),
                bucket.tokens + max(0.0, elapsed) * bucket.policy.refill_rate,
            )

        allowed = tokens >= 1
        if allowed:
            tokens -= 1

        # Denials do not consume tokens, but the observation time advances so
        # refill is computed only once over the monotonic timeline.
        self.clients[api_key] = _Bucket(tokens, timestamp, policy)
        self._cleanup(timestamp)
        return allowed
