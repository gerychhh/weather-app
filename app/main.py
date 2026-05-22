from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
import httpx

load_dotenv()



app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request : Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.post("/weather")
async def weather(request : Request, city: str = Form(...), unit: str = Form(...)):
    weather_data = get_weather_data(city, unit)
    return templates.TemplateResponse(request=request, name="index.html", context={"weather_data": weather_data})

def get_weather_data(city: str, unit: str) -> dict:
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    url = "https://api.openweathermap.org/data/2.5/weather"

    response = httpx.get(url,
                          params={"q": city, "units": unit, "appid": api_key}, timeout=10)
    response.raise_for_status()
    data = response.json()
    return {
        "city" : data["name"],
        "temperature" : data["main"]["temp"],
        "description" : data["weather"][0]["description"],
        "unit" : unit,
    }