from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Job Scraper API"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str = "mysql+pymysql://root:password@localhost:3306/job_scraper"
    host: str = "0.0.0.0"
    port: int = 8000
    
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_database: str = "job_scraper"
    
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()