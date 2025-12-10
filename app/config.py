from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Security
    api_keys: str = "your-secret-api-key-here"  # Comma-separated list of valid API keys
    
    # CORS Settings
    cors_origins: str = "*"  # Comma-separated list of allowed origins
    
    # Application Settings
    app_name: str = "Pi Finance API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Settings
    api_port: int = 8080  # Port for the API server
    
    # Cache Settings
    cache_enabled: bool = True  # Enable price caching
    cache_ttl_days: int = 7  # Keep tickers in cache for 7 days after last request
    cache_refresh_interval_minutes: int = 30  # Refresh cached prices every 30 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_api_keys(self) -> List[str]:
        """Parse API keys from comma-separated string."""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

