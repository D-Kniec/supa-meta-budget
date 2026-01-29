import os
import sys
import time

class Style:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(f"{Style.PURPLE}{Style.BOLD}")
    print(r"""
   _____ _    _ _____            __  __ ______ _______            
  / ____| |  | |  __ \   /\     |  \/  |  ____|__   __|   /\    
 | (___ | |  | | |__) | /  \    | \  / | |__     | |     /  \   
  \___ \| |  | |  ___/ / /\ \   | |\/| |  __|    | |    / /\ \  
  ____) | |__| | |    / ____ \  | |  | | |____   | |   / ____ \ 
 |_____/ \____/|_|   /_/    \_\ |_|  |_|______|  |_|  /_/    \_\ 
                                                                 
          >> BUDGET MANAGEMENT SYSTEM CONFIGURATOR <<
    """)
    print(f"{Style.END}")
    print(f"{Style.CYAN} Welcome to the automated setup wizard.{Style.END}")
    print(f"{Style.CYAN} Please follow the instructions to connect your Supabase infrastructure.{Style.END}")
    print("-" * 70)

def ask_value(label, key_name, example, default=None, is_password=False):
    print(f"\n{Style.BOLD}[?] {label}{Style.END}")
    print(f"    {Style.DARKCYAN}Target Variable: {key_name}{Style.END}")
    if example:
        print(f"    {Style.YELLOW}Example: {example}{Style.END}")
    
    if default:
        prompt = f"    {Style.GREEN}Enter value (Default: {default}): {Style.END}"
    else:
        prompt = f"    {Style.GREEN}Enter value: {Style.END}"

    val = input(prompt).strip()
    
    if not val and default:
        return default
    return val

def save_env(content):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    
    print(f"\n{Style.BOLD}----------------------------------------------------------------------{Style.END}")
    print(f"{Style.BLUE}[i] Saving configuration to: {env_path}...{Style.END}")
    
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        time.sleep(1)
        print(f"{Style.GREEN}{Style.BOLD}[SUCCESS] Configuration file generated successfully!{Style.END}")
        print(f"{Style.GREEN}[SUCCESS] You are ready to run the migration.{Style.END}")
        print(f"{Style.BOLD}----------------------------------------------------------------------{Style.END}")
    except Exception as e:
        print(f"{Style.RED}[ERROR] Failed to write file: {e}{Style.END}")

def main():
    os.system("") 
    print_banner()

    print(f"\n{Style.BOLD}{Style.UNDERLINE}SECTION 1: SUPABASE API CONFIGURATION{Style.END}")
    
    supabase_url = ask_value(
        "Paste your Supabase Project URL", 
        "SUPABASE_URL", 
        "https://xyzcompany.supabase.co"
    )
    
    supabase_key = ask_value(
        "Paste your 'anon' / 'public' API Key", 
        "SUPABASE_SECRET_KEY", 
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )

    print(f"\n{Style.BOLD}{Style.UNDERLINE}SECTION 2: DATABASE CONNECTION (TRANSACTION POOLER){Style.END}")
    print(f"{Style.YELLOW}(!) Go to: Supabase -> Settings -> Database -> Connection Parameters{Style.END}")
    print(f"{Style.YELLOW}(!) Ensure 'Use connection pooling' is CHECKED (Mode: Transaction){Style.END}")

    db_host = ask_value(
        "Paste the Host Address (from pooler settings)", 
        "DB_HOST", 
        "aws-0-eu-central-1.pooler.supabase.com"
    )

    db_user = ask_value(
        "Paste the User string (Must include project ID!)", 
        "DB_USER", 
        "postgres.atqxghczahjwyqxmxxiv"
    )

    db_pass = ask_value(
        "Enter your Database Password", 
        "DB_PASSWORD", 
        "YourStrongPassword123!"
    )

    db_port = ask_value(
        "Enter Port Number", 
        "DB_PORT", 
        "6543 (Standard for Pooler)", 
        default="6543"
    )

    print(f"\n{Style.BOLD}{Style.UNDERLINE}SECTION 3: LOCAL APPLICATION SECURITY{Style.END}")
    
    mb_pass = ask_value(
        "Set a local admin password for Metabase integration", 
        "MB_DB_PASS", 
        "secure123", 
        default="secure123"
    )

    env_content = [
        f"SUPABASE_URL={supabase_url}",
        f"SUPABASE_SECRET_KEY={supabase_key}",
        f"DB_HOST={db_host}",
        f"DB_USER={db_user}",
        f"DB_PASSWORD={db_pass}",
        f"DB_PORT={db_port}",
        f"MB_DB_PASS={mb_pass}",
        "DEBUG=False",
        "DB_NAME=postgres",
        "MB_DB_USER=metabase_admin",
        "MB_DB_NAME=metabase_config",
        "USERS_MAP={}",
        "DEFAULT_USER_ID="
    ]

    save_env(env_content)

if __name__ == "__main__":
    main()