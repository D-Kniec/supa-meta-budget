from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Category:
    subcategory_id: int
    category_id: int
    category: str
    subcategory: str
    type: str  
    color_hex: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def display_name(self):
        return f"{self.category} - {self.subcategory}"

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(
            subcategory_id=data.get("subcategory_id"),
            category_id=data.get("category_id"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            type=data.get("type"), 
            color_hex=data.get("color_hex"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None
        )

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "category_id": self.category_id,
            "type": self.type,
            "color_hex": self.color_hex
        }