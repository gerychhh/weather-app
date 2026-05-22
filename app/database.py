from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

if not settings.database_url:
    raise RuntimeError("Database URL not found.")

engine = create_engine(settings.database_url)
SessoinLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass