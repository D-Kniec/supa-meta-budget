import os
import getpass

REQUIRED_VARS = [
    ("SUPABASE_URL", "Enter Supabase URL"),
    ("SUPABASE_SECRET_KEY", "Enter Supabase Secret Key"),
    ("DB_HOST", "Enter Database Host"),
    ("DB_USER", "Enter Database User"),
    ("DB_PASSWORD", "Enter Database Password"),
    ("MB_DB_PASS", "Set Metabase Database Password")
]

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")

    print(f"Configuration for: {env_path}\n")

    if os.path.exists(env_path):
        overwrite = input(".env file already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            return

    env_content = []

    for var_name, prompt in REQUIRED_VARS:
        if "PASSWORD" in var_name or "KEY" in var_name or "PASS" in var_name:
            value = getpass.getpass(f"{prompt} [{var_name}]: ")
        else:
            value = input(f"{prompt} [{var_name}]: ")
        
        env_content.append(f"{var_name}={value}")

    env_content.append("DEBUG=False")
    env_content.append("DB_PORT=5432")
    env_content.append("MB_DB_USER=metabase_admin")
    env_content.append("MB_DB_NAME=metabase_config")

    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(env_content))
        print(f"\n.env file created successfully.")
    except Exception as e:
        print(f"\nError writing file: {e}")

if __name__ == "__main__":
    main()