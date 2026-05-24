from datetime import datetime, timedelta

from fastapi import Request


rate_limit_storage: dict[str, list[datetime]] = {}


def is_rate_limited(request: Request, limit: int = 30, window_seconds: int = 60) -> bool:
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    recent_requests = [
        request_time
        for request_time in rate_limit_storage.get(client_ip, [])
        if request_time >= window_start
    ]

    if len(recent_requests) >= limit:
        rate_limit_storage[client_ip] = recent_requests
        return True

    recent_requests.append(now)
    rate_limit_storage[client_ip] = recent_requests
    return False
