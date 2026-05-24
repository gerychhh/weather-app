from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.history import get_history
import app.history as history_module
from app.models import WeatherQuery


def test_get_history_filters_by_city_and_paginates(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(history_module, "SessionLocal", TestSessionLocal)

    now = datetime.utcnow()
    with TestSessionLocal() as session:
        for index in range(12):
            session.add(
                WeatherQuery(
                    city="Minsk",
                    temperature=20 + index,
                    description="clear sky",
                    unit="metric",
                    served_from_cache=False,
                    created_at=now - timedelta(minutes=index),
                )
            )

        session.add(
            WeatherQuery(
                city="London",
                temperature=12,
                description="rain",
                unit="metric",
                served_from_cache=False,
                created_at=now,
            )
        )
        session.commit()

    first_page, total_pages = get_history(page=1, city_filter="min", per_page=10)
    second_page, _ = get_history(page=2, city_filter="min", per_page=10)

    assert total_pages == 2
    assert len(first_page) == 10
    assert len(second_page) == 2
    assert all(row.city == "Minsk" for row in first_page + second_page)
