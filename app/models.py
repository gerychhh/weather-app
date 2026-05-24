from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class WeatherQuery(Base):
    __tablename__ = "weather_queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(100))
    temperature: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(20))
    served_from_cache: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
