from dataclasses import dataclass
from uuid import UUID
from typing import Optional

@dataclass
class Wallet:
    id: UUID
    wallet_name: str
    owner_name: str
    is_active: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        return cls(
            id=UUID(data["id"]),
            wallet_name=data["wallet_name"],
            owner_name=data["owner_name"],
            is_active=data.get("is_active", True)
        )