#!/usr/bin/env python3
"""
Secure Telegram bot integration test using environment variables
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment variables (secure)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def test_bot_info():
    """Test if bot token is valid"""
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
        return False
        
    try:
        print("🤖 Testing Telegram bot token...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print("✅ Bot token is VALID!")
                print(f"   Bot name: {bot_info.get('first_name')}")
                print(f"   Bot username: @{bot_info.get('username')}")
                print(f"   Bot ID: {bot_info.get('id')}")
                return True
            else:
                print(f"❌ Bot API error: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_send_message():
    """Test sending a message to the chat"""
    if not CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID not found in environment variables!")
        return False
        
    try:
        print(f"\n📱 Testing message send to chat ID: {CHAT_ID}...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        payload = {
            'chat_id': CHAT_ID,
            'text': '🧪 SECURE TEST: Bitcoin Options Alert System\n\n✅ Environment variables are working correctly!\n🔒 Credentials are properly secured.',
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ Test message sent successfully!")
                print("📱 Check your Telegram - you should see the secure test message!")
                return True
            else:
                print(f"❌ Send message error: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Send message error: {e}")
        return False

def main():
    """Run secure Telegram tests"""
    print("🔒 SECURE Telegram Bot Integration Test")
    print("=" * 50)
    
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing environment variables!")
        print("\n🔧 Setup Instructions:")
        print("1. Create .env file in project root")
        print("2. Add: TELEGRAM_BOT_TOKEN=your_bot_token")
        print("3. Add: TELEGRAM_CHAT_ID=your_chat_id")
        print("4. Or set as system environment variables")
        return
    
    tests = [
        ("Bot Token Validation", test_bot_info),
        ("Send Test Message", test_send_message)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your secure setup is working!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()