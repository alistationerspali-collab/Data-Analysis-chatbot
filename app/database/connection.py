"""SQL Server connection via SQLAlchemy + pyodbc."""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from app.config import settings

QUERY_TIMEOUT_SECONDS = 30  # hard statement timeout -- generous enough for normal use


def get_engine():
    connection_url = URL.create(
        "mssql+pyodbc",
        username=settings.db_user,
        password=settings.db_pass,
        host=settings.db_server,
        database=settings.db_name,
        query={"driver": settings.db_driver},
    )
    engine = create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"timeout": 10, "autocommit": True},
    )

    @event.listens_for(engine, "connect")
    def set_query_timeout(dbapi_connection, connection_record):
        # pyodbc-level query execution timeout (separate from connect timeout
        # and separate from SQL Server's own LOCK_TIMEOUT). If ANY query -- for
        # any reason -- runs longer than this, pyodbc itself aborts it.
        dbapi_connection.timeout = QUERY_TIMEOUT_SECONDS

    return engine


engine = get_engine()