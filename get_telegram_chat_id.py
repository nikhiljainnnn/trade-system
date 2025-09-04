#!/usr/bin/env python3
"""
Script to get your Telegram Chat ID
Run this script and message your bot to get your chat ID
"""

import yaml
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters
import asyncio

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

BOT_TOKEN = config['telegram_bot_token']

async def handle_message(update, context):
    """Handle incoming messages and print chat ID"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    print(f"\n🎯 FOUND YOUR CHAT ID!")
    print(f"Chat ID: {chat_id}")
    print(f"User: {user.first_name} {user.last_name or ''}")
    print(f"Username: @{user.username or 'N/A'}")
    print(f"\n📝 Add this to your config.yaml:")
    print(f"telegram_chat_id: \"{chat_id}\"")
    
    # Send confirmation message
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Great! Your Chat ID is: `{chat_id}`\n\nI'm ready to send you Bitcoin options alerts!",
        parse_mode='Markdown'
    )

async def main():
    """Main function to run the bot"""
    print("🚀 Starting Telegram Chat ID finder...")
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    print("\n📱 INSTRUCTIONS:")
    print("1. Open Telegram")
    print("2. Search for your bot using the token above")
    print("3. Start a conversation with your bot")
    print("4. Send any message to your bot")
    print("5. Your Chat ID will appear here\n")
    print("⏳ Waiting for messages...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Keep running until interrupted
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n👋 Stopping bot...")
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())