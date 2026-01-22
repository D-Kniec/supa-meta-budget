from typing import List, Optional, Any
from uuid import UUID
from core.database import supabase
from models.wallet import Wallet

class WalletRepository:
    def __init__(self):
        self.supabase = supabase
        self.table = "dim_wallets"

    def get_all_active(self) -> List[Wallet]:
        response = self.supabase.table(self.table).select("*").eq("is_active", True).execute()
        return [Wallet.from_dict(row) for row in response.data]

    def create(self, wallet_data: dict) -> bool:
        response = self.supabase.table(self.table).insert(wallet_data).execute()
        return len(response.data) > 0

    def delete(self, wallet_id: Any) -> bool:
        response = self.supabase.table(self.table).delete().eq("id", str(wallet_id)).execute()
        return len(response.data) > 0