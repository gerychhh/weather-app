# Weather Query App

Simple FastAPI web application for fetching current weather by city, storing query history in PostgreSQL, and viewing/exporting previous queries.

## Features

- Search current weather by city using OpenWeatherMap.
- Choose Celsius or Fahrenheit for each request.
- Store every successful query in PostgreSQL.
- Reuse cached weather for the same city and unit within 5 minutes.
- Show query history with pagination, city filter, and date range filter.
- Export full or filtered history as CSV.
- Basic per-IP rate limiting for weather requests.
- Health check endpoint for database connectivity.
- Alembic migrations and targeted pytest coverage.

## Requirements

- OpenWeatherMap API key
- Docker and Docker Compose for the easiest setup
- Python 3.10+ and PostgreSQL if you want to run the app without Docker

## Quick Start With Docker

This is the simplest way to run the project from a clean clone. Docker Compose starts PostgreSQL, applies migrations, and runs the FastAPI app.

Clone the repository and enter the project folder:

```powershell
git clone https://github.com/gerychhh/weather-app.git
cd weather-app
```

Create your local environment file:

```powershell
Copy-Item .env.sample .env
```

Open `.env` and add your OpenWeatherMap API key:

```env
OPENWEATHERMAP_API_KEY=your_api_key_here
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/weather_app
```

For Docker, only `OPENWEATHERMAP_API_KEY` needs to be changed. Docker Compose provides its own database connection for the app.

Run the app:

```powershell
docker compose up --build
```

Open the app:

```text
http://127.0.0.1:8000
```

Stop the app when you are done:

```powershell
docker compose down
```

## Local Setup Without Docker

Use this path if PostgreSQL is already installed locally.

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create `.env` from `.env.sample`:

```powershell
Copy-Item .env.sample .env
```

Then edit `.env`:

```env
OPENWEATHERMAP_API_KEY=your_api_key_here
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/weather_app
```

If your database password contains special URL characters, encode them. For example, `@` becomes `%40`.

Create a local PostgreSQL database named `weather_app`. You can do it from pgAdmin or with:

```powershell
createdb -U postgres weather_app
```

Apply database migrations:

```powershell
python -m alembic upgrade head
```

Run the app:

```powershell
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Useful Endpoints

- `GET /` - search form and query history.
- `POST /weather` - fetch weather for a submitted city.
- `GET /export.csv` - export full or filtered query history.
- `GET /health` - check database connectivity.

Example filtered export:

```text
/export.csv?city=minsk&date_from=2026-05-01&date_to=2026-05-24
```

Without query parameters, the export includes the full query history.

## Tests

Run:

```powershell
python -m pytest
```

Current tests cover:

- cache reuse vs fresh weather fetch;
- rate limit returning `429` before weather processing;
- history city filtering and pagination;
- CSV export with empty filters.
