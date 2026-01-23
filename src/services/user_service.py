from typing import Dict, Optional, List
from repositories.user_repo import UserRepository

class UserService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserService, cls).__new__(cls)
            cls._instance.repo = UserRepository()
            cls._instance._users_cache = {} 
            cls._instance._load_cache()
            cls._instance.active_user_id = None
        return cls._instance

    def _load_cache(self):
        data = self.repo.get_all()
        self._users_cache = {u['id']: u for u in data}

    def get_users(self) -> Dict[str, str]:
        self._load_cache()
        return {uid: data['alias'] for uid, data in self._users_cache.items()}

    def register_discovered_users(self, uuid_list: List[str]):
        self._load_cache()
        for uid in uuid_list:
            suid = str(uid)
            if suid not in self._users_cache:
                new_alias = f"User_{suid[:4]}"
                new_user = {
                    "id": suid,
                    "alias": new_alias,
                    "color_hex": "#888888",
                    "default_wallet_fk": None
                }
                self.repo.upsert(new_user)
        self._load_cache()

    def rename_user(self, user_id: str, new_alias: str):
        if self.repo.update_field(str(user_id), "alias", new_alias):
            self._load_cache()

    def set_user_color(self, user_id: str, color_hex: str):
        if self.repo.update_field(str(user_id), "color_hex", color_hex):
            self._load_cache()

    def get_user_color(self, user_id: str) -> str:
        u = self._users_cache.get(str(user_id))
        return u['color_hex'] if u else "#ffffff"

    def get_active_user_id(self) -> Optional[str]:
        return self.active_user_id

    def set_active_user_id(self, user_id: str):
        self.active_user_id = str(user_id)

    def get_default_wallet_id(self, user_id: str = None) -> Optional[str]:
        target = user_id or self.active_user_id
        if not target: return None
        u = self._users_cache.get(str(target))
        return u['default_wallet_fk'] if u else None

    def set_default_wallet_id(self, wallet_id: str, user_id: str = None):
        target = user_id or self.active_user_id
        if target:
            if self.repo.update_field(str(target), "default_wallet_fk", str(wallet_id)):
                self._load_cache()