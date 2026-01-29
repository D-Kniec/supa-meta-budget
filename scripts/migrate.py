import os
import psycopg2
from pathlib import Path

def run_migration():
    env_vars = {}
    base_dir = Path(__file__).parent.parent
    env_path = base_dir / ".env"
    
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, val = line.strip().split("=", 1)
                    env_vars[key] = val

    try:
        conn = psycopg2.connect(
            host=env_vars.get("DB_HOST"),
            database="postgres",
            user=env_vars.get("DB_USER", "postgres"),
            password=env_vars.get("DB_PASSWORD"),
            port=env_vars.get("DB_PORT", "5432")
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("Connected to database.")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    sql_file_path = base_dir / "database" / "migrations" / "V1.0.2__Base_Schema_Deployment.sql"
    
    if not sql_file_path.exists():
        print(f"SQL file not found: {sql_file_path}")
        return

    print(f"Executing: {sql_file_path.name}")
    with open(sql_file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    try:
        cursor.execute(sql_content)
        print("Migration successful.")
    except Exception as e:
        if "already exists" in str(e):
            print("Tables already exist.")
        else:
            print(f"SQL Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()