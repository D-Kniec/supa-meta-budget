from typing import List, Optional
from core.database import supabase
from models.budget_goal import BudgetGoal

class BudgetGoalRepository:
    def __init__(self):
        self.supabase = supabase
        self.table = "dim_budget_goals"

    def get_all(self) -> List[BudgetGoal]:
        response = self.supabase.table(self.table)\
            .select("*")\
            .order("monthly_target_amount", desc=True)\
            .execute()
        return [BudgetGoal.from_dict(row) for row in response.data]

    def upsert(self, tag: str, amount: float) -> bool:
        data = {
            "tag": tag,
            "monthly_target_amount": amount,
            "is_active": True
        }
        response = self.supabase.table(self.table).upsert(data, on_conflict="tag").execute()
        return len(response.data) > 0

    def delete(self, goal_id: int) -> bool:
        response = self.supabase.table(self.table).delete().eq("id", goal_id).execute()
        return len(response.data) > 0