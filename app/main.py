from fastapi import FastAPI, Request, Form, Query
from fastapi.templating import Jinja2Templates
import httpx
from typing import Annotated
from .config import settings

from app.database import SessionLocal
from app.models import WeatherQuery


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request : Request, page: int = Query(1, ge=1)):
    history, total_pages = get_history(page=page)

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "history": history,
            "total_pages": total_pages,
            "page": page,
        },
    )

@app.post("/weather")
async def weather(
    request : Request,
    city: Annotated[str, Form()],
    unit: Annotated[str, Form()]
):
    try:
        weather_data = get_weather_data(city, unit)
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

def get_weather_data(
    city: str,
    unit: str
) -> dict[str, str | float]:
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
            served_from_cache=False
        )

        session.add(query)
        session.commit()

def get_history(page: int, per_page: int = 10) -> tuple[list[WeatherQuery], int]:
    with SessionLocal() as session:
        total = session.query(WeatherQuery).count()
        total_pages = (total + per_page - 1) // per_page
        history = (
            session.query(WeatherQuery)
            .order_by(WeatherQuery.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
    return history, total_pages