from supabase import create_client, Client
from .config import get_settings

settings = get_settings()

class Database:
    _client: Client | None = None
    _admin_client: Client | None = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._client is None:
            cls._client = create_client(
                settings.SUPABASE_URL, 
                settings.SUPABASE_ANON_KEY
            )
        return cls._client

    @classmethod
    def get_admin_client(cls) -> Client:
        if cls._admin_client is None:
            if not settings.SUPABASE_SECRET_KEY:
                raise ValueError("SUPABASE_SECRET_KEY is not configured.")
            
            cls._admin_client = create_client(
                settings.SUPABASE_URL, 
                settings.SUPABASE_SECRET_KEY
            )
        return cls._admin_client

supabase: Client = Database.get_client()