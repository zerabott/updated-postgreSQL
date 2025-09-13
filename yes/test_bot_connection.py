#!/usr/bin/env python3

import asyncio
from telegram import Bot
from telegram.error import TelegramError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_bot_connection():
    """Test basic bot connection to Telegram"""
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        print("❌ No BOT_TOKEN found in environment")
        return False
    
    try:
        # Create bot instance
        bot = Bot(token=bot_token)
        
        print("🔄 Testing bot connection...")
        
        # Try to initialize and get bot info
        await bot.initialize()
        me = await bot.get_me()
        
        print(f"✅ Bot connection successful!")
        print(f"   Bot ID: {me.id}")
        print(f"   Bot Name: {me.first_name}")
        print(f"   Bot Username: @{me.username}")
        
        # Clean up
        await bot.shutdown()
        return True
        
    except TelegramError as e:
        print(f"❌ Telegram API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bot_connection())
    if success:
        print("\n🎉 Bot is ready to run!")
    else:
        print("\n🔧 Check your internet connection and bot token")
