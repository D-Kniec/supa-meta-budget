from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from uuid import UUID

class TransactionType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"

class TransactionStatus(Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"

class TransactionSentiment(Enum):
    FUNDAMENT = "Fundament"
    ROZWOJ = "Rozwój"
    NAGRODA = "Nagroda"
    NIEDOSYT = "Niedosyt"
    MEGA = "Mega"
    RUTYNA = "Rutyna"
    TRAGEDIA = 'Tragedia'

@dataclass
class Transaction:
    amount: Decimal
    wallet_fk: UUID
    subcategory_fk: int
    created_by_fk: UUID
    
    type: str 
    category_name: str
    subcategory_name: str
    
    id: Optional[UUID] = None
    transaction_date: date = date.today()
    to_wallet_fk: Optional[UUID] = None
    status: TransactionStatus = TransactionStatus.COMPLETED
    sentiment: Optional[TransactionSentiment] = None
    tag: Optional[str] = None
    is_excluded_from_stats: bool = False
    attachment_path: Optional[str] = None
    attachment_type: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    @staticmethod
    def _to_uuid(value: Any) -> Optional[UUID]:
        if value is None or isinstance(value, UUID):
            return value
        return UUID(str(value))

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        cat_data = data.get("dim_categories") or {}
        
        resolved_type = (
            cat_data.get("type") or 
            data.get("type") or 
            data.get("transaction_type") or 
            "UNKNOWN"
        )
        
        return cls(
            id=cls._to_uuid(data.get("id")),
            amount=Decimal(str(data["amount"])),
            transaction_date=date.fromisoformat(data["transaction_date"]) if isinstance(data["transaction_date"], str) else data["transaction_date"],
            
            type=resolved_type,
            category_name=cat_data.get("category", "-"),
            subcategory_name=cat_data.get("subcategory", "-"),
            
            wallet_fk=cls._to_uuid(data["wallet_fk"]),
            to_wallet_fk=cls._to_uuid(data.get("to_wallet_fk")),
            status=TransactionStatus(data.get("status", "COMPLETED")),
            subcategory_fk=int(data["subcategory_fk"]),
            created_by_fk=cls._to_uuid(data["created_by_fk"]),
            sentiment=TransactionSentiment(data["sentiment"]) if data.get("sentiment") else None,
            tag=data.get("tag"),
            is_excluded_from_stats=bool(data.get("is_excluded_from_stats", False)),
            attachment_path=data.get("attachment_path"),
            attachment_type=data.get("attachment_type"),
            description=data.get("description"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

    def to_dict(self) -> dict:
        data = {
            "amount": float(self.amount),
            "transaction_date": self.transaction_date.isoformat(),
            "wallet_fk": str(self.wallet_fk),
            "status": self.status.value,
            "subcategory_fk": self.subcategory_fk,
            "created_by_fk": str(self.created_by_fk),
            "is_excluded_from_stats": self.is_excluded_from_stats,
            "tag": self.tag,
            "attachment_path": self.attachment_path,
            "attachment_type": self.attachment_type,
            "description": self.description
        }
        if self.id: data["id"] = str(self.id)
        if self.to_wallet_fk: data["to_wallet_fk"] = str(self.to_wallet_fk)
        if self.sentiment: data["sentiment"] = self.sentiment.value
        return data