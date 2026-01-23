from typing import List, Any
from core.database import supabase
from models.category import Category

class CategoryRepository:
    def __init__(self):
        self.supabase = supabase
        self.table = "dim_categories"

    def get_all(self) -> List[Category]:
        response = self.supabase.table(self.table).select("*").is_("deleted_at", "null").execute()
        return [Category.from_dict(row) for row in response.data]

    def create(self, category_data: dict) -> bool:
        response = self.supabase.table(self.table).insert(category_data).execute()
        return len(response.data) > 0

    def update(self, subcategory_id: int, updates: dict) -> bool:
        try:
            self.supabase.table(self.table).update(updates).eq("subcategory_id", subcategory_id).execute()
            return True
        except Exception:
            return False
    
    def delete(self, subcategory_id: Any) -> bool:
        response = self.supabase.table(self.table).delete().eq("subcategory_id", subcategory_id).execute()
        return len(response.data) > 0