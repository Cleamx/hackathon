import os

class Settings:
    PROJECT_NAME: str = "ReadZen"
    PROJECT_VERSION: str = "0.1.0"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sql_app.db")
    
    # Storage
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "uploads")

    # AI - OpenAI API Key (utilise SECRET_KEY du .env)
    OPENAI_API_KEY: str = os.getenv("SECRET_KEY", os.getenv("OPENAI_API_KEY", ""))

settings = Settings()
