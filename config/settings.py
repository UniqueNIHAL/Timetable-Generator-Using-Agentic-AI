"""Application configuration settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Cloud Configuration
    gemini_api_key: str
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"
    
    # Database Configuration
    database_url: str = "sqlite:///./timetable.db"
    use_firestore: bool = False
    
    # Application Settings
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8080  # Changed default to 8080 for Cloud Run
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:8080"]
    
    # Agent Configuration
    max_agent_iterations: int = 10
    agent_timeout: int = 300
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
