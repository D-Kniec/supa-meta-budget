import sys
from pathlib import Path
from typing import Dict, Any
from pydantic import Field, Json, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SECRET_KEY: str | None = None
    
    DEFAULT_USER_ID: str | None = None
    DEBUG: bool = False
    
    MB_DB_USER: str = "metabase_admin"
    MB_DB_PASS: str | None = None
    MB_DB_NAME: str = "metabase_config"

    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str
    DB_PASSWORD: str

    USERS_MAPPING: Json[Dict[str, Any]] = Field(default="{}")

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    if not ENV_PATH.exists():
        print(f"\n[CRITICAL ERROR] Configuration file (.env) not found!")
        print(f"Searched path: {ENV_PATH}")
        print("\n>>> PLEASE RUN THE FOLLOWING COMMAND TO INITIALIZE THE PROJECT:")
        print("    make setup\n")
        sys.exit(1)

    try:
        return Settings()
    except ValidationError as e:
        print("\n[CONFIGURATION ERROR] Invalid or missing variables in .env:")
        
        for error in e.errors():
            field_name = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            print(f" - {field_name}: {message}")
            
        print("\nPlease update your .env file manually or run 'make setup' to fix configuration.\n")
        sys.exit(1)