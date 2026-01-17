import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
    DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    MB_DB_USER = os.getenv("MB_DB_USER", "metabase_admin")
    MB_DB_PASS = os.getenv("MB_DB_PASS")
    MB_DB_NAME = os.getenv("MB_DB_NAME", "metabase_config")

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER")   
    DB_PASSWORD = os.getenv("DB_PASSWORD") 

    USERS_MAPPING = {}
    
    @classmethod
    def load_users_map(cls):
        raw_map = os.getenv("USERS_MAP", "{}")
        try:
            cls.USERS_MAPPING = json.loads(raw_map)
        except json.JSONDecodeError:
            print("CONFIG WARNING: Niepoprawny format JSON w USERS_MAP w .env")
            cls.USERS_MAPPING = {}

    @classmethod
    def validate(cls):
        required_vars = [
            "SUPABASE_URL", "SUPABASE_SECRET_KEY", 
            "DB_HOST", "DB_USER", "DB_PASSWORD"
        ]
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Brakujące zmienne w .env: {', '.join(missing)}")

settings = Config()
settings.validate()
settings.load_users_map()