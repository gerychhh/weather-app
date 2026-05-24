from fastapi import FastAPI, Request, Form, Query, status
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
import csv
import httpx
from sqlalchemy import text
from typing import Annotated
from datetime import date
from io import StringIO

from app.database import SessionLocal
from app.history import get_history, get_history_for_export
from app.rate_limit import is_rate_limited
from app.weather import get_cached_weather, get_weather_data, save_weather_query


app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
