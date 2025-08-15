from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Job Scraper API"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str = "sqlite:///./jobs.db"
    host: str = "0.0.0.0"
    port: int = 8000
    
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()