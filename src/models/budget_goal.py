from dataclasses import dataclass
from typing import Optional

@dataclass
class BudgetGoal:
    id: int
    tag: str
    monthly_target_amount: float
    is_active: bool

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id"),
            tag=data.get("tag"),
            monthly_target_amount=float(data.get("monthly_target_amount", 0.0)),
            is_active=data.get("is_active", True)
        )

    def to_dict(self):
        return {
            "tag": self.tag,
            "monthly_target_amount": self.monthly_target_amount,
            "is_active": self.is_active
        }