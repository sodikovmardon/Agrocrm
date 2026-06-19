import json
import time
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as aioredis

from app.core.config import settings

redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def set_key(
    key: str,
    value: Union[str, bytes, Dict[str, Any], List[Any]],
    ttl: Optional[int] = None,
) -> bool:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, default=str)
    return await redis_client.set(key, value, ex=ttl)


async def get_key(key: str) -> Optional[str]:
    return await redis_client.get(key)


async def get_json(key: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    value = await redis_client.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


async def delete_key(key: str) -> int:
    return await redis_client.delete(key)


async def key_exists(key: str) -> bool:
    return await redis_client.exists(key) > 0


async def set_expiry(key: str, ttl: int) -> bool:
    return await redis_client.expire(key, ttl)


async def check_rate_limit(
    identifier: str,
    max_requests: int = settings.RATE_LIMIT_PER_MINUTE,
    window_seconds: int = 60,
) -> Dict[str, Any]:
    now = int(time.time())
    window_start = now - window_seconds
    key = f"ratelimit:{identifier}:{window_start // window_seconds}"
    current = await redis_client.get(key)
    if current is None:
        await redis_client.set(key, 1, ex=window_seconds)
        count = 1
    else:
        count = await redis_client.incr(key)
    remaining = max(0, max_requests - count)
    reset_time = ((window_start // window_seconds) + 1) * window_seconds
    return {
        "allowed": count <= max_requests,
        "remaining": remaining,
        "reset_at": reset_time,
    }


async def store_parsed_entry(
    entry_id: str,
    operations: List[Dict[str, Any]],
    warnings: List[str],
    ttl: int = settings.REDIS_ENTRY_TTL_SECONDS,
) -> None:
    data = {
        "operations": operations,
        "warnings": warnings,
        "created_at": time.time(),
    }
    await set_key(f"parsed_entry:{entry_id}", data, ttl=ttl)


async def get_parsed_entry(entry_id: str) -> Optional[Dict[str, Any]]:
    return await get_json(f"parsed_entry:{entry_id}")


async def delete_parsed_entry(entry_id: str) -> None:
    await delete_key(f"parsed_entry:{entry_id}")


async def close_redis() -> None:
    await redis_client.aclose()
