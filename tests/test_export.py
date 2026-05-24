from fastapi.testclient import TestClient

import app.main as main_module


def test_index_accepts_empty_date_query_params(monkeypatch):
    monkeypatch.setattr(main_module, "get_history", lambda **kwargs: ([], 1))

    response = TestClient(main_module.app).get("/?city=&date_from=&date_to=")

    assert response.status_code == 200


def test_export_accepts_empty_date_query_params(monkeypatch):
    captured_filters = {}

    def get_history_for_export(city_filter=None, date_from=None, date_to=None):
        captured_filters.update(
            {
                "city_filter": city_filter,
                "date_from": date_from,
                "date_to": date_to,
            }
        )
        return []

    monkeypatch.setattr(main_module, "get_history_for_export", get_history_for_export)

    response = TestClient(main_module.app).get("/export.csv?city=&date_from=&date_to=")

    assert response.status_code == 200
    assert response.text.startswith("city,temperature,unit")
    assert captured_filters == {
        "city_filter": None,
        "date_from": None,
        "date_to": None,
    }
