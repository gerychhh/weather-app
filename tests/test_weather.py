from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.main as main_module
import app.rate_limit as rate_limit_module


def test_weather_reuses_cached_result(monkeypatch):
    rate_limit_module.rate_limit_storage.clear()
    saved_weather = {}

    cached_weather = SimpleNamespace(
        city="Minsk",
        temperature=21.5,
        description="clear sky",
        unit="metric",
    )

    def fail_external_api_call(city: str, unit: str):
        raise AssertionError("External API should not be called when cache is used")

    def save_weather_query(weather_data):
        saved_weather.update(weather_data)

    monkeypatch.setattr(main_module, "get_cached_weather", lambda city, unit: cached_weather)
    monkeypatch.setattr(main_module, "get_weather_data", fail_external_api_call)
    monkeypatch.setattr(main_module, "save_weather_query", save_weather_query)
    monkeypatch.setattr(main_module, "get_history", lambda page: ([], 1))

    response = TestClient(main_module.app).post(
        "/weather",
        data={"city": "Minsk", "unit": "metric"},
    )

    assert response.status_code == 200
    assert "served from cache" in response.text
    assert saved_weather["served_from_cache"] is True


def test_weather_fetches_fresh_result_when_cache_missing(monkeypatch):
    rate_limit_module.rate_limit_storage.clear()
    saved_weather = {}

    def fetch_weather(city: str, unit: str):
        return {
            "city": city,
            "temperature": 18.0,
            "description": "cloudy",
            "unit": unit,
        }

    def save_weather_query(weather_data):
        saved_weather.update(weather_data)

    monkeypatch.setattr(main_module, "get_cached_weather", lambda city, unit: None)
    monkeypatch.setattr(main_module, "get_weather_data", fetch_weather)
    monkeypatch.setattr(main_module, "save_weather_query", save_weather_query)
    monkeypatch.setattr(main_module, "get_history", lambda page: ([], 1))

    response = TestClient(main_module.app).post(
        "/weather",
        data={"city": "Minsk", "unit": "metric"},
    )

    assert response.status_code == 200
    assert "served from cache" not in response.text
    assert saved_weather["served_from_cache"] is False


def test_rate_limit_returns_429_before_weather_is_saved(monkeypatch):
    rate_limit_module.rate_limit_storage.clear()
    rate_limit_module.rate_limit_storage["testclient"] = [datetime.utcnow()] * 30

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Weather flow should stop before this function is called")

    monkeypatch.setattr(main_module, "get_cached_weather", fail_if_called)
    monkeypatch.setattr(main_module, "get_weather_data", fail_if_called)
    monkeypatch.setattr(main_module, "save_weather_query", fail_if_called)

    response = TestClient(main_module.app).post(
        "/weather",
        data={"city": "Minsk", "unit": "metric"},
    )

    assert response.status_code == 429
    assert response.json() == {"error": "Too many requests. Please try again later."}
