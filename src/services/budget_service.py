import random
import os
import re
import json
import unicodedata
import hashlib
import colorsys
from typing import List, Dict, Any
from uuid import UUID, uuid4
from repositories.transaction_repo import TransactionRepository
from repositories.wallet_repo import WalletRepository
from repositories.category_repo import CategoryRepository
from repositories.budget_goal_repo import BudgetGoalRepository
from models.transaction import Transaction
from core.config import settings
from services.user_service import UserService

class BudgetService:
    def __init__(self):
        if settings.SUPABASE_URL and not settings.SUPABASE_URL.endswith("/"):
            settings.SUPABASE_URL = f"{settings.SUPABASE_URL}/"

        self.transaction_repo = TransactionRepository()
        self.wallet_repo = WalletRepository()
        self.category_repo = CategoryRepository()
        self.goal_repo = BudgetGoalRepository()
        self.user_service = UserService()
        
        self.supabase = self.transaction_repo.supabase
        
        self._wallets_cache = {}
        self._categories_cache = []
        #self.reload_cache()

    def reload_cache(self):
        self._categories_cache = self.category_repo.get_all()
        wallets = self.wallet_repo.get_all_active()
        self._wallets_cache = {str(w.id): w.wallet_name for w in wallets}

    def _get_dynamic_color(self, name_str: str, alpha: float = 0.8) -> str:
        if not name_str:
            return "#BDBDBDB4"
        
        hash_obj = hashlib.md5(name_str.encode('utf-8'))
        hash_digest = hash_obj.hexdigest()
        hue_hex = hash_digest[:6]
        hue_int = int(hue_hex, 16)
        hue_float = (hue_int % 360) / 360.0
        
        r, g, b = colorsys.hsv_to_rgb(hue_float, 0.6, 0.8)
        r_i, g_i, b_i = int(r * 255), int(g * 255), int(b * 255)
        a_i = int(alpha * 255)
        
        return f"#{r_i:02X}{g_i:02X}{b_i:02X}{a_i:02X}"

    def get_active_user_id(self) -> str:
        return self.user_service.get_active_user_id()

    def get_unique_authors(self) -> List[str]:
        txs = self.transaction_repo.get_all()
        authors = set(str(t.created_by_fk) for t in txs if t.created_by_fk)
        return list(authors)

    def get_ui_transactions(self) -> List[Dict[str, Any]]:
        self.reload_cache()
        transactions = self.transaction_repo.get_all()
        categories_map = {c.subcategory_id: c for c in self._categories_cache}
        
        users_map = self.user_service.get_users()
        
        ui_data = []
        
        for tx in transactions:
            bg_color = "#1b1c1d"
            cat_obj = categories_map.get(tx.subcategory_fk)
            
            if cat_obj and cat_obj.color_hex:
                bg_color = cat_obj.color_hex
            elif cat_obj:
                bg_color = self._get_dynamic_color(cat_obj.category)
            
            author_id = str(tx.created_by_fk)
            author_display = users_map.get(author_id, f"...{author_id[-4:]}")
            author_color = self.user_service.get_user_color(author_id)

            ui_data.append({
                "id": tx.id,
                "date": tx.transaction_date.isoformat(),
                "amount": f"{tx.amount:.2f}",
                "author": author_display,
                "author_id": author_id,
                "author_color": author_color,
                "category": tx.category_name,
                "subcategory": tx.subcategory_name,
                "type": tx.type, 
                "status": tx.status.value,
                "from_wallet": self._wallets_cache.get(str(tx.wallet_fk), "Nieznany"),
                "to_wallet": self._wallets_cache.get(str(tx.to_wallet_fk), "-") if tx.to_wallet_fk else "-",
                "sentiment": tx.sentiment.value if tx.sentiment else "-",
                "tag": tx.tag or "",
                "description": tx.description or "",
                "in_stats": "Tak" if not tx.is_excluded_from_stats else "Nie",
                "attachment_path": tx.attachment_path,
                "attachment_type": tx.attachment_type,
                "row_color": bg_color,
                "updated_at": str(tx.updated_at) if hasattr(tx, "updated_at") and tx.updated_at else None,
                "created_at": str(tx.created_at) if hasattr(tx, "created_at") and tx.created_at else None
            })
        return ui_data

    def _sanitize_filename(self, filename: str) -> str:
        filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
        filename = filename.replace(' ', '_')
        filename = re.sub(r'[^\w.-]', '', filename)
        return filename
    def __enter__(self):
        return self
    

    def __exit__(self, exc_type, exc_val, exc_tb):

        if hasattr(self, 'close'):
            self.close()
        return False
    def upload_attachment(self, file_path: str, folder: str = "transactions") -> str:
        try:
            original_name = os.path.basename(file_path)
            safe_name = self._sanitize_filename(original_name)
            
            if not safe_name or safe_name.strip() == "":
                safe_name = f"{uuid4()}{os.path.splitext(original_name)[1]}"

            safe_folder = self._sanitize_filename(folder)
            bucket_name = "attachments"

            existing_files = []
            try:
                res = self.supabase.storage.from_(bucket_name).list(safe_folder)
                if res:
                    existing_files = [f['name'] for f in res]
            except Exception:
                pass 

            final_name = safe_name
            name_root, ext = os.path.splitext(safe_name)
            counter = 2

            while final_name in existing_files:
                final_name = f"{name_root}_{counter}{ext}"
                counter += 1

            storage_path = f"{safe_folder}/{final_name}"

            with open(file_path, "rb") as f:
                self.supabase.storage.from_(bucket_name).upload(
                    path=storage_path,
                    file=f,
                    file_options={
                        "content-type": "application/octet-stream",
                        "x-upsert": "false" 
                    }
                )
            return storage_path
        except Exception as e:
            print(f"SERVICE ERROR (Upload): {e}")
            return None

    def get_attachment_url(self, storage_path: str) -> str:
        try:
            if not storage_path:
                return None
            storage_path = storage_path.lstrip('/')
            res = self.supabase.storage.from_("attachments").get_public_url(storage_path)
            return res
        except Exception as e:
            print(f"SERVICE ERROR (URL): {e}")
            return None
            
    def download_attachment_content(self, storage_path: str) -> bytes:
        try:
            data = self.supabase.storage.from_("attachments").download(storage_path)
            return data
        except Exception as e:
            print(f"SERVICE ERROR (Download bytes): {e}")
            return None

    def delete_transactions(self, transaction_ids: List[UUID]) -> bool:
        try:
            for tx_id in transaction_ids:
                self.transaction_repo.delete(tx_id)
            return True
        except Exception:
            return False

    def get_transaction_by_id(self, transaction_id: UUID) -> Dict[str, Any]:
        tx = self.transaction_repo.get_by_id(transaction_id)
        if not tx:
            return None
        return {
            "transaction_date": tx.transaction_date.isoformat(),
            "amount": float(tx.amount),
            "type": tx.type,
            "wallet_fk": str(tx.wallet_fk),
            "to_wallet_fk": str(tx.to_wallet_fk) if tx.to_wallet_fk else None,
            "subcategory_fk": tx.subcategory_fk,
            "sentiment": tx.sentiment.value if tx.sentiment else None,
            "tag": tx.tag,
            "description": tx.description,
            "is_excluded_from_stats": tx.is_excluded_from_stats,
            "attachment_path": tx.attachment_path,
            "attachment_type": tx.attachment_type
        }

    def update_transaction_multiple_fields(self, transaction_id: UUID, fields: Dict[str, Any]) -> bool:
        try:
            if "transaction_type" in fields:
                new_type = fields.pop("transaction_type")
                default_cat = next((c for c in self._categories_cache if c.type == new_type), None)
                
                if default_cat:
                    fields["subcategory_fk"] = default_cat.subcategory_id
                else:
                    return False

            return self.transaction_repo.update(transaction_id, fields)
        except Exception:
            return False

    def update_transaction_field(self, transaction_id: UUID, field_name: str, value: Any) -> bool:
        if field_name == "transaction_type":
            return self.update_transaction_multiple_fields(transaction_id, {"transaction_type": value})
        return self.update_transaction_multiple_fields(transaction_id, {field_name: value})

    def get_wallets_for_combo(self):
        return self.wallet_repo.get_all_active()

    def get_categories_for_combo(self):
        return self._categories_cache

    def get_categories_by_type(self, type_str: str) -> List[str]:
        filtered = [c.category for c in self._categories_cache if c.type == type_str]
        return sorted(list(set(filtered)))

    def get_unique_categories(self) -> List[str]:
        return sorted(list(set(c.category for c in self._categories_cache)))

    def get_subcategories_by_category(self, category_name: str) -> List[Dict[str, Any]]:
        result = []
        for c in self._categories_cache:
            if c.category == category_name:
                result.append({
                    "name": c.subcategory,
                    "id": c.subcategory_id
                })
        return sorted(result, key=lambda x: x["name"])

    def add_transaction(self, data: Dict[str, Any]) -> bool:
        print("\n--- ROZPOCZYNAM DODAWANIE TRANSAKCJI ---")
        try:
            user_id = self.get_active_user_id()
            print(f"DEBUG: Active User ID: {user_id}")
            
            if not user_id:
                print("❌ BŁĄD: Nie znaleziono aktywnego użytkownika (get_active_user_id zwrócił None).")
                print("Sugestia: Wybierz użytkownika w zakładce Opcje lub na górnym pasku.")
                return False
            
            data["created_by_fk"] = user_id

            tx_type = data.get("transaction_type")
            if tx_type:
                data["type"] = tx_type
            
            if tx_type == "TRANSFER" and not data.get("subcategory_fk"):
                print("DEBUG: Typ TRANSFER - szukam kategorii systemowej...")
                transfer_cat = next(
                    (c for c in self._categories_cache 
                     if c.type == "TRANSFER" and c.category == "System" and c.subcategory == "Transfer"), 
                    None
                )
                
                if not transfer_cat:
                    print("DEBUG: Tworzę nową kategorię System/Transfer...")
                    self.category_repo.create({
                        "category_id": -1, "category": "System", "subcategory": "Transfer",
                        "type": "TRANSFER", "color_hex": "#60a5fa"
                    })
                    self.reload_cache()
                    transfer_cat = next((c for c in self._categories_cache if c.subcategory == "Transfer"), None)

                if transfer_cat:
                    data["subcategory_fk"] = transfer_cat.subcategory_id
                else:
                    print("❌ BŁĄD: Nie udało się utworzyć/znaleźć kategorii dla Transferu.")
                    return False

            if not data.get("to_wallet_fk"): data["to_wallet_fk"] = None
            if not data.get("sentiment"): data["sentiment"] = None
            if not data.get("tag"): data["tag"] = None
            if not data.get("description"): data["description"] = None

            print(f"DEBUG: Dane przed konwersją do modelu: {json.dumps(data, default=str)}")
            transaction = Transaction.from_dict(data)
            
            print("DEBUG: Wysyłanie do repozytorium...")
            result = self.transaction_repo.create(transaction)
            
            if result:
                print("✅ SUKCES: Transakcja zapisana w bazie.")
                return True
            else:
                print("❌ BŁĄD BAZY: Repo zwróciło pusty wynik (None). Sprawdź połączenie z Supabase.")
                return False

        except Exception as e:
            import traceback
            print(f"🔥 KRYTYCZNY BŁĄD W SERVICE (Add): {e}")
            print(traceback.format_exc())
            return False

    def add_wallet(self, name: str, owner_id: str) -> bool:
        try:
            if self.wallet_repo.create({"wallet_name": name, "owner_name": owner_id, "is_active": True}):
                self.reload_cache()
                return True
            return False
        except Exception:
            return False

    def add_category(self, category: str, subcategory: str, type_str: str, color: str) -> bool:
        try:
            self.reload_cache()
            existing_cat = next((c for c in self._categories_cache if c.category == category), None)
            new_id = existing_cat.category_id if existing_cat else random.randint(10000, 99999)

            if self.category_repo.create({
                "category_id": new_id,
                "category": category, 
                "subcategory": subcategory, 
                "type": type_str,
                "color_hex": color
            }):
                self.reload_cache()
                return True
            return False
        except Exception:
            return False

    def update_category(self, subcat_id: int, category: str, subcategory: str, type_str: str, color: str) -> bool:
        try:
            if self.category_repo.update(subcat_id, {
                "category": category, "subcategory": subcategory, "type": type_str, "color_hex": color
            }):
                self.reload_cache()
                return True
            return False
        except Exception:
            return False

    def delete_wallet(self, wallet_id: UUID, cascade: bool = False) -> bool:
        try:
            if cascade:
                self.transaction_repo.delete_by_field("wallet_fk", str(wallet_id))
                self.transaction_repo.delete_by_field("to_wallet_fk", str(wallet_id))
            
            if self.wallet_repo.delete(wallet_id):
                self.reload_cache()
                return True
            return False
        except Exception as e:
            print(f"SERVICE ERROR (Delete Wallet): {e}")
            return False

    def delete_category(self, subcat_id: int, cascade: bool = False) -> bool:
        try:
            if cascade:
                self.transaction_repo.delete_by_field("subcategory_fk", subcat_id)
            
            if self.category_repo.delete(subcat_id):
                self.reload_cache()
                return True
            return False
        except Exception as e:
            print(f"SERVICE ERROR (Delete Category): {e}")
            return False

    def get_budget_goals(self):
        return self.goal_repo.get_all()

    def set_budget_goal(self, tag: str, amount: float) -> bool:
        try:
            return self.goal_repo.upsert(tag, amount)
        except Exception as e:
            print(f"SERVICE ERROR (Set Goal): {e}")
            return False

    def delete_budget_goal(self, goal_id: int) -> bool:
        try:
            return self.goal_repo.delete(goal_id)
        except Exception as e:
            print(f"SERVICE ERROR (Delete Goal): {e}")
            return False

    def get_unique_tags(self) -> List[str]:
        txs = self.transaction_repo.get_all()
        tags = set(t.tag for t in txs if t.tag)
        return sorted(list(tags))

    def save_last_entry_prefs(self, prefs: Dict[str, Any]) -> None:
        try:
            prefs_path = os.path.join(os.getcwd(), "user_prefs.json")
            with open(prefs_path, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, ensure_ascii=False, indent=4, default=str)
        except Exception as e:
            print(f"SERVICE WARNING (Save Prefs): {e}")

    def load_last_entry_prefs(self) -> Dict[str, Any]:
        try:
            prefs_path = os.path.join(os.getcwd(), "user_prefs.json")
            if os.path.exists(prefs_path):
                with open(prefs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def reload_cache(self) -> None:
        self._categories_cache = self.category_repo.get_all()
        wallets = self.wallet_repo.get_all_active()
        self._wallets_cache = {str(w.id): w.wallet_name for w in wallets}

    def get_cache_snapshot(self) -> Dict[str, Any]:
        if hasattr(self.user_service, 'load_users'):
             self.user_service.load_users()
             
        return {
            "wallets": self._wallets_cache.copy(),
            "categories": list(self._categories_cache),
            "users": self.user_service.get_users()
        }

    def hydrate_cache(self, snapshot: Dict[str, Any]) -> None:
        if not snapshot:
            return
        
        if "wallets" in snapshot:
            self._wallets_cache = snapshot["wallets"]
            
        if "categories" in snapshot:
            self._categories_cache = snapshot["categories"]