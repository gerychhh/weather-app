from datetime import datetime, timedelta
from time import perf_counter

import httpx

from app.config import settings
from app.database import SessionLocal
from app.logging_config import log_event
from app.models import WeatherQuery


def get_weather_data(city: str, unit: str) -> dict[str, str | float | bool]:
    api_key = settings.openweathermap_api_key

    if not api_key:
        raise RuntimeError(
            "API key not found. Please set the OPENWEATHERMAP_API_KEY environment variable."
        )

    start_time = perf_counter()

    try:
        response = httpx.get(
            settings.openweathermap_api_url,
            params={"q": city, "units": unit, "appid": api_key},
            timeout=10,
        )

    except httpx.RequestError as exc:
        duration_ms = round((perf_counter() - start_time) * 1000, 2)
        log_event(
            "external_api_error",
            provider="openweathermap",
            city=city,
            unit=unit,
            duration_ms=duration_ms,
            error=str(exc),
        )
        raise

    duration_ms = round((perf_counter() - start_time) * 1000, 2)
    log_event(
        "external_api_latency",
        provider="openweathermap",
        city=city,
        unit=unit,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    response.raise_for_status()
    data = response.json()

    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "unit": unit,
    }


def save_weather_query(weather_data: dict[str, str | float | bool]) -> None:
    with SessionLocal() as session:
        query = WeatherQuery(
            city=str(weather_data["city"]),
            temperature=float(weather_data["temperature"]),
            description=str(weather_data["description"]),
            unit=str(weather_data["unit"]),
            served_from_cache=bool(weather_data["served_from_cache"]),
        )

        session.add(query)
        session.commit()


def get_cached_weather(city: str, unit: str) -> WeatherQuery | None:
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

    with SessionLocal() as session:
        return (
            session.query(WeatherQuery)
            .filter(WeatherQuery.city.ilike(city))
            .filter(WeatherQuery.unit == unit)
            .filter(WeatherQuery.created_at >= five_minutes_ago)
            .filter(WeatherQuery.served_from_cache.is_(False))
            .order_by(WeatherQuery.created_at.desc())
            .first()
        )
