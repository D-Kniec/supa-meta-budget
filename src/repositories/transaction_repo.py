from typing import List, Optional, Any
from uuid import UUID
from core.database import supabase
from models.transaction import Transaction

class TransactionRepository:
    def __init__(self):
        self.supabase = supabase
        self.table = "fact_transactions"

    def get_all(self) -> List[Transaction]:
        response = self.supabase.table(self.table)\
            .select("*, dim_categories(type, category, subcategory, color_hex)")\
            .order("transaction_date", desc=True)\
            .range(0, 9999)\
            .execute()
        return [Transaction.from_dict(row) for row in response.data]

    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        response = self.supabase.table(self.table)\
            .select("*, dim_categories(type, category, subcategory, color_hex)")\
            .eq("id", str(transaction_id))\
            .execute()
        if response.data:
            return Transaction.from_dict(response.data[0])
        return None

    def create(self, transaction: Transaction):
        data = transaction.to_dict()
        if "id" in data:
            del data["id"]
        response = self.supabase.table(self.table).insert(data).execute()
        return response.data

    def update(self, transaction_id: UUID, fields: dict) -> bool:
        try:
            self.supabase.table(self.table).update(fields).eq("id", str(transaction_id)).execute()
            return True
        except Exception:
            return False

    def delete(self, transaction_id: UUID) -> bool:
        try:
            self.supabase.table(self.table).delete().eq("id", str(transaction_id)).execute()
            return True
        except Exception:
            return False

    def delete_by_field(self, field_name: str, value: Any) -> bool:
        try:
            self.supabase.table(self.table).delete().eq(field_name, value).execute()
            return True
        except Exception:
            return False