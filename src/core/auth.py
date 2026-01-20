import os
from uuid import UUID
from core.config import Config

class Session:
    USER_ID = None
    USER_EMAIL = ""

    @classmethod
    def initialize(cls):
        if Config.DEFAULT_USER_ID:
            try:
                cls.USER_ID = UUID(Config.DEFAULT_USER_ID)
                cls.USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "user@example.com")
            except Exception as e:
                print(f"AUTH ERROR: {e}")

    @classmethod
    def get_user_id(cls) -> UUID:
        return cls.USER_ID
    
    @classmethod
    def get_user_email(cls) -> str:
        return cls.USER_EMAIL

Session.initialize()