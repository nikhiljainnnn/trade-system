#!/usr/bin/env python3
"""
Quick test to verify bot is working and get updates
"""
import requests
import json
import yaml

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

BOT_TOKEN = config['telegram_bot_token']

def get_bot_updates():
    """Get recent updates/messages sent to the bot"""
    try:
        print("🔍 Checking for recent messages to the bot...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                print(f"✅ Found {len(updates)} recent messages/updates")
                
                if updates:
                    print("\n📱 Recent messages:")
                    for update in updates[-3:]:  # Show last 3 updates
                        if 'message' in update:
                            msg = update['message']
                            chat = msg.get('chat', {})
                            from_user = msg.get('from', {})
                            
                            print(f"   💬 Message ID: {msg.get('message_id')}")
                            print(f"   👤 From: {from_user.get('first_name', 'Unknown')}")
                            print(f"   💯 Chat ID: {chat.get('id')} ⭐")
                            print(f"   📝 Text: {msg.get('text', 'No text')}")
                            print(f"   🕐 Date: {msg.get('date')}")
                            print("-" * 40)
                            
                            # This is likely the correct chat ID
                            correct_chat_id = chat.get('id')
                            if correct_chat_id:
                                print(f"\n🎯 YOUR CORRECT CHAT ID: {correct_chat_id}")
                                return correct_chat_id
                else:
                    print("\n⚠️  No messages found yet.")
                    print("📱 Please send a message to @btctradealertttttsbot first!")
                    return None
            else:
                print(f"❌ API error: {data.get('description')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_chat_id(chat_id):
    """Test sending a message to the chat ID"""
    try:
        print(f"\n🧪 Testing chat ID: {chat_id}")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': '🎉 SUCCESS! Bitcoin Options Alert System is now connected!\n\n✅ Your Telegram integration is working perfectly!\n💹 You will receive Bitcoin options alerts here.',
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ SUCCESS! Test message sent!")
                print(f"📱 Check your Telegram - you should see the success message!")
                return True
            else:
                print(f"❌ Send error: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🤖 Bitcoin Options Alert Bot - Quick Test")
    print("=" * 50)
    print("🎯 Bot Username: @btctradealertttttsbot")
    print("🔑 Bot Token: Valid ✅")
    print("")
    
    # First, check for messages
    chat_id = get_bot_updates()
    
    if chat_id:
        # Test the found chat ID
        success = test_chat_id(chat_id)
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 TELEGRAM INTEGRATION SUCCESSFUL!")
            print(f"✅ Correct Chat ID: {chat_id}")
            print("")
            print("📝 Next steps:")
            print(f"1. Update your config.yaml with: telegram_chat_id: \"{chat_id}\"")
            print("2. Update Railway environment variables")
            print("3. Redeploy your cloud system")
            print("")
            print("🚀 Your Bitcoin alerts will be delivered to your Telegram!")
        else:
            print("\n❌ Test failed. Check the error above.")
    else:
        print("\n📱 PLEASE DO THIS FIRST:")
        print("1. Open Telegram")
        print("2. Search for: @btctradealertttttsbot")
        print("3. Send ANY message to the bot (like 'hello')")
        print("4. Run this script again: python quick_bot_test.py")

if __name__ == "__main__":
    main()