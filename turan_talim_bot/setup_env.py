"""
Environment variable setup script for TuranTalim bot.
Run this script to configure your bot environment.
"""
import os
import sys
import dotenv
import getpass

def setup_env():
    """Set up the environment variables for the bot"""
    print("TuranTalim Bot Environment Setup")
    print("=" * 40)
    
    # Create .env file
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    
    # Check if .env file exists
    if os.path.exists(env_path):
        print(f".env file already exists at {env_path}")
        overwrite = input("Do you want to overwrite it? (y/n): ")
        if overwrite.lower() != 'y':
            print("Setup cancelled.")
            return
    
    # Get environment variables
    bot_token = getpass.getpass("Enter your Telegram bot token: ")
    
    domain = input("Enter your domain name (e.g., example.com): ")
    webhook_url = f"https://{domain}/telegram-webhook/"
    
    webhook_port = input("Enter webhook port (default: 8443): ") or "8443"
    
    django_api_url = input("Enter Django API URL (default: http://localhost:8000/api): ") or "http://localhost:8000/api"
    django_api_key = getpass.getpass("Enter Django API key: ")
    
    admin_id = input("Enter your Telegram ID (for admin notifications): ")
    teacher_group_id = input("Enter teacher group ID (or leave blank): ")
    
    database_url = input("Enter database URL (default: sqlite:///turan_talim.db): ") or "sqlite:///turan_talim.db"
    
    # Write to .env file
    with open(env_path, "w") as env_file:
        env_file.write(f"BOT_TOKEN={bot_token}\n")
        env_file.write(f"WEBHOOK_URL={webhook_url}\n")
        env_file.write(f"WEBHOOK_HOST=0.0.0.0\n")
        env_file.write(f"WEBHOOK_PORT={webhook_port}\n")
        env_file.write(f"DJANGO_API_URL={django_api_url}\n")
        env_file.write(f"DJANGO_API_KEY={django_api_key}\n")
        env_file.write(f"ADMIN_ID={admin_id}\n")
        env_file.write(f"TEACHER_GROUP_ID={teacher_group_id}\n")
        env_file.write(f"DATABASE_URL={database_url}\n")
    
    print(f"Environment variables saved to {env_path}")
    print("Setup completed successfully!")

if __name__ == "__main__":
    setup_env()
