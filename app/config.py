"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    db_server: str = "localhost"
    db_name: str = "BusyComp0001_db12025"
    db_user: str = "chatbot_reader"
    db_pass: str = ""
    db_driver: str = "ODBC Driver 17 for SQL Server"

    # Groq / LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # App
    max_critic_iterations: int = 3

    class Config:
        env_file = ".env"


settings = Settings()