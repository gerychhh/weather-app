import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    openweathermap_api_key: str | None = os.getenv("OPENWEATHERMAP_API_KEY")
    openweathermap_api_url: str = "https://api.openweathermap.org/data/2.5/weather"
    database_url: str | None = os.getenv("DATABASE_URL")

settings = Settings()
