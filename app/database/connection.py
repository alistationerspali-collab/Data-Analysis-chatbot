"""SQL Server connection via SQLAlchemy + pyodbc."""
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from app.config import settings


def get_engine():
    connection_url = URL.create(
        "mssql+pyodbc",
        username=settings.db_user,
        password=settings.db_pass,
        host=settings.db_server,
        database=settings.db_name,
        query={"driver": settings.db_driver},
    )
    return create_engine(connection_url, pool_pre_ping=True)


engine = get_engine()