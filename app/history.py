from datetime import date, datetime, time

from app.database import SessionLocal
from app.models import WeatherQuery


def get_history(
    page: int,
    city_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    per_page: int = 10,
) -> tuple[list[WeatherQuery], int]:
    with SessionLocal() as session:
        query = build_history_query(
            session=session,
            city_filter=city_filter,
            date_from=date_from,
            date_to=date_to,
        )

        total = query.count()
        total_pages = max((total + per_page - 1) // per_page, 1)
        history = (
            query
            .order_by(WeatherQuery.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

    return history, total_pages


def get_history_for_export(
    city_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[WeatherQuery]:
    with SessionLocal() as session:
        query = build_history_query(
            session=session,
            city_filter=city_filter,
            date_from=date_from,
            date_to=date_to,
        )

        return query.order_by(WeatherQuery.created_at.desc()).all()


def build_history_query(
    session,
    city_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    query = session.query(WeatherQuery)

    if city_filter:
        query = query.filter(WeatherQuery.city.ilike(f"%{city_filter}%"))

    if date_from:
        start = datetime.combine(date_from, time.min)
        query = query.filter(WeatherQuery.created_at >= start)

    if date_to:
        end = datetime.combine(date_to, time.max)
        query = query.filter(WeatherQuery.created_at <= end)

    return query
