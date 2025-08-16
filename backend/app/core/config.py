from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Job Scraper API - Marketing Junior Focus"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # Database settings
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "jobuser"
    mysql_password: str = "jobpass"
    mysql_database: str = "job_scraper"
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    # API settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Test database settings (for unit tests)
    test_database_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()