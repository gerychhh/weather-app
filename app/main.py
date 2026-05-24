from fastapi import FastAPI, Request, Form, Query, status
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
import csv
import httpx
from sqlalchemy import text
from typing import Annotated
from datetime import date, datetime, time
from io import StringIO

from app.database import SessionLocal
from app.models import WeatherQuery
from app.weather import get_cached_weather, get_weather_data, save_weather_query


app = FastAPI()
templates = Jinja2Templates(directory="templates")
rate_limit_storage: dict[str, list[datetime]] = {}

@app.get("/")
async def index(
    request: Request,
    page: int = Query(1, ge=1),
    city: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
):
    city_filter = city.strip() if city else None
    history, total_pages = get_history(
        page=page,
        city_filter=city_filter,
        date_from=date_from,
        date_to=date_to,
    )

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "history": history,
            "total_pages": total_pages,
            "page": page,
            "city_filter": city_filter,
            "date_from": date_from,
            "date_to": date_to,
        },
    )

@app.get("/export.csv")
async def export_history(
    city: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
):
    city_filter = city.strip() if city else None
    rows = get_history_for_export(
        city_filter=city_filter,
        date_from=date_from,
        date_to=date_to,
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "city",
        "temperature",
        "unit",
        "description",
        "served_from_cache",
        "created_at",
    ])

    for row in rows:
        writer.writerow([
            row.city,
            row.temperature,
            row.unit,
            row.description,
            row.served_from_cache,
            row.created_at,
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="weather_history.csv"'},
    )

@app.get("/health")
async def health():
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))

    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "unavailable"},
        )

    return {"status": "ok", "database": "ok"}

@app.post("/weather")
async def weather(
    request : Request,
    city: Annotated[str, Form()],
    unit: Annotated[str, Form()]
):
    if is_rate_limited(request):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "Too many requests. Please try again later."},
        )

    try:
        cached_weather = get_cached_weather(city, unit)

        if cached_weather:
            weather_data = {
                "city": cached_weather.city,
                "temperature": cached_weather.temperature,
                "description": cached_weather.description,
                "unit": cached_weather.unit,
                "served_from_cache": True,
            }
        else:
            weather_data = get_weather_data(city, unit)
            weather_data["served_from_cache"] = False

        save_weather_query(weather_data)
        context = {"weather_data": weather_data}

    except httpx.HTTPStatusError:
        context = {"error": "City not found. Please try again."}

    except httpx.RequestError:
        context = {"error": "Network error. Please try again later."}

    except RuntimeError:
        context = {"error": "API key not found. Please set the OPENWEATHERMAP_API_KEY environment variable."}

    history, total_pages = get_history(page=1)

    context["history"] = history
    context["page"] = 1
    context["total_pages"] = total_pages

    return templates.TemplateResponse(request=request, name="index.html", context=context)

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
