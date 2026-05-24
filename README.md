# Weather Query App

Simple FastAPI web application for fetching current weather by city, storing query history in PostgreSQL, and viewing/exporting previous queries.

## Features

- Search current weather by city using OpenWeatherMap.
- Choose Celsius or Fahrenheit for each request.
- Store every successful query in PostgreSQL.
- Reuse cached weather for the same city and unit within 5 minutes.
- Show query history with pagination, city filter, and date range filter.
- Export filtered history as CSV.
- Basic per-IP rate limiting for weather requests.
- Health check endpoint for database connectivity.
- Alembic migrations and targeted pytest coverage.

## Requirements

- Python 3.10+
- PostgreSQL
- OpenWeatherMap API key

## Local Setup

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

```env
OPENWEATHERMAP_API_KEY=your_api_key_here
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/weather_app
```

If your database password contains special URL characters, encode them. For example, `@` becomes `%40`.

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

## Docker Compose Quickstart

Set `OPENWEATHERMAP_API_KEY` in your environment or `.env`, then run:

```powershell
docker compose up --build
```

The app will start at:

```text
http://127.0.0.1:8000
```

Docker Compose starts PostgreSQL, waits for it to become healthy, applies Alembic migrations, and then runs the FastAPI app.

## Useful Endpoints

- `GET /` - search form and query history.
- `POST /weather` - fetch weather for a submitted city.
- `GET /export.csv` - export filtered query history.
- `GET /health` - check database connectivity.

Example filtered export:

```text
/export.csv?city=minsk&date_from=2026-05-01&date_to=2026-05-24
```

## Tests

Run:

```powershell
python -m pytest
```

Current tests cover:

- cache reuse vs fresh weather fetch;
- rate limit returning `429` before weather processing;
- history city filtering and pagination.
