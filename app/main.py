from fastapi import FastAPI, Request, Form, Query
from fastapi.templating import Jinja2Templates
import httpx
from typing import Annotated
from datetime import date, datetime, time, timedelta
from .config import settings

from app.database import SessionLocal
from app.models import WeatherQuery


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

@app.post("/weather")
async def weather(
    request : Request,
    city: Annotated[str, Form()],
    unit: Annotated[str, Form()]
):
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

def get_weather_data(city: str, unit: str) -> dict[str, str | float | bool]:
    api_key = settings.openweathermap_api_key

    if not api_key:
        raise RuntimeError("API key not found. Please set the OPENWEATHERMAP_API_KEY environment variable.")
    
    url = settings.openweathermap_api_url

    response = httpx.get(
        url,
        params={"q": city, "units": unit, "appid": api_key},
        timeout=10)
    
    response.raise_for_status()
    data = response.json()
    
    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "unit": unit,
    }

def save_weather_query(weather_data: dict[str, str | float]) -> None:
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
            .filter(WeatherQuery.served_from_cache == False)
            .order_by(WeatherQuery.created_at.desc())
            .first()
        )

def get_history(
    page: int,
    city_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    per_page: int = 10,
) -> tuple[list[WeatherQuery], int]:
    with SessionLocal() as session:
        query = session.query(WeatherQuery)

        if city_filter:
            query = query.filter(WeatherQuery.city.ilike(f"%{city_filter}%"))

        if date_from:
            start = datetime.combine(date_from, time.min)
            query = query.filter(WeatherQuery.created_at >= start)

        if date_to:
            end = datetime.combine(date_to, time.max)
            query = query.filter(WeatherQuery.created_at <= end)

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
