from typing import List, Optional, Dict, Any
from core.database import supabase

class UserRepository:
    def __init__(self):
        self.supabase = supabase
        self.table = "dim_users"

    def get_all(self) -> List[Dict[str, Any]]:
        response = self.supabase.table(self.table).select("*").execute()
        return response.data

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        response = self.supabase.table(self.table).select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        return None

    def upsert(self, user_data: Dict[str, Any]) -> bool:
        try:
            self.supabase.table(self.table).upsert(user_data).execute()
            return True
        except Exception as e:
            print(f"REPO ERROR (User Upsert): {e}")
            return False

    def update_field(self, user_id: str, field: str, value: Any) -> bool:
        try:
            self.supabase.table(self.table).update({field: value}).eq("id", user_id).execute()
            return True
        except Exception:
            return False