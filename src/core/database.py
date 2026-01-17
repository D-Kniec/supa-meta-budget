from supabase import create_client, Client
from core.config import Config

class Database:
    _client: Client = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._client is None:
            cls._client = create_client(
                Config.SUPABASE_URL, 
                Config.SUPABASE_SECRET_KEY
            )
        return cls._client

supabase: Client = Database.get_client()