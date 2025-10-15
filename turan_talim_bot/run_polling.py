#!/usr/bin/env python
"""
Run TuranTalim bot in polling mode.
This is useful for development and testing.
"""
import sys
import os

from config import Config
from bot import polling_mode
import asyncio

if __name__ == "__main__":
    print("Starting TuranTalim bot in polling mode...")
    
    # Check if environment variables are set
    if not Config.validate():
        print("Environment variables are not properly set.")
        print("Please run setup_env.py script first.")
        sys.exit(1)
    
    try:
        asyncio.run(polling_mode())
    except KeyboardInterrupt:
        print("\nBot stopped manually.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
