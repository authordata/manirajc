import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hearu.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "hearu-secret-change-in-production")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()
