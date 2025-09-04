#!/usr/bin/env python3
"""
Test script to verify Telegram bot is working
"""
import requests
import json

# Your bot configuration
BOT_TOKEN = "8381873587:AAEjpFNgDAqf46W6k3fle03fJzkUjwHIfCY"
CHAT_ID = "401420432"

def test_bot_info():
    """Test if bot token is valid"""
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
    try:
        print(f"\n📱 Testing message send to chat ID: {CHAT_ID}...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        payload = {
            'chat_id': CHAT_ID,
            'text': '🧪 TEST MESSAGE: Bitcoin Options Alert System - Cloud Test\n\nIf you see this message, your Telegram integration is working correctly! ✅',
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                message_info = data.get('result', {})
                print("✅ Test message sent successfully!")
                print(f"   Message ID: {message_info.get('message_id')}")
                print(f"   Chat ID: {message_info.get('chat', {}).get('id')}")
                print(f"   Date: {message_info.get('date')}")
                print("\n📱 Check your Telegram now - you should see the test message!")
                return True
            else:
                print(f"❌ Send message error: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Send message error: {e}")
        return False

def test_chat_info():
    """Test if we can get chat information"""
    try:
        print(f"\n🔍 Testing chat access for ID: {CHAT_ID}...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
        
        payload = {'chat_id': CHAT_ID}
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                chat_info = data.get('result', {})
                print("✅ Chat access is working!")
                print(f"   Chat type: {chat_info.get('type')}")
                print(f"   Chat ID: {chat_info.get('id')}")
                if 'first_name' in chat_info:
                    print(f"   User: {chat_info.get('first_name')} {chat_info.get('last_name', '')}")
                return True
            else:
                print(f"❌ Chat access error: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat access error: {e}")
        return False

def main():
    """Run all Telegram tests"""
    print("🧪 Telegram Bot Integration Test")
    print("=" * 50)
    
    tests = [
        ("Bot Token Validation", test_bot_info),
        ("Chat Access Test", test_chat_info),
        ("Send Test Message", test_send_message)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed!")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Telegram tests passed!")
        print("💡 Your bot configuration is correct.")
        print("🔧 The issue might be with Railway environment variables.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("🔧 Fix these issues before proceeding with cloud deployment.")

if __name__ == "__main__":
    main()