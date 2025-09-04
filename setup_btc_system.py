#!/usr/bin/env python3
"""
Bitcoin Options Alert System - Setup and Testing Script
This script sets up and tests the complete BTC options trading system for 90%+ accuracy
"""

import os
import sys
import subprocess
import pandas as pd
import yaml
from datetime import datetime

def print_banner():
    print("="*60)
    print("🚀 BITCOIN OPTIONS ALERT SYSTEM SETUP")
    print("🎯 Target: 90%+ Accuracy BTC Options Trading")
    print("="*60)

def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking dependencies...")
    
    required = [
        'pandas', 'numpy', 'scikit-learn', 'ta', 'requests', 
        'yfinance', 'schedule', 'python-telegram-bot',
        'xgboost', 'lightgbm'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"   ❌ {package}")
    
    if missing:
        print(f"\n⚠️  Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            print("✅ All packages installed!")
        except:
            print("❌ Install failed. Run: pip install " + " ".join(missing))
            return False
    
    return True

def setup_directories():
    """Create necessary directories"""
    print("\n📁 Setting up directories...")
    for directory in ['data', 'models', 'logs']:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ {directory}/")

def test_system_components():
    """Test all system components"""
    print("\n🧪 Testing system components...")
    
    # Test data fetching
    try:
        from utils.fetch_intraday import fetch_bitcoin_intraday
        btc_data = fetch_bitcoin_intraday(interval="5m", period="1d")
        if btc_data is not None and not btc_data.empty:
            print(f"   ✅ Bitcoin data: {len(btc_data)} records")
            print(f"   💰 Current BTC: ${btc_data['Close'].iloc[-1]:.2f}")
        else:
            print("   ❌ Bitcoin data fetch failed")
            return False
    except Exception as e:
        print(f"   ❌ Data fetch error: {e}")
        return False
    
    # Test configuration
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        if config.get('telegram_chat_id') == 'YOUR_TELEGRAM_CHAT_ID':
            print("   ⚠️  Telegram chat ID not set")
            print("   💡 Run: python get_telegram_chat_id.py")
        else:
            print("   ✅ Configuration looks good")
    except:
        print("   ❌ Configuration error")
        return False
    
    return True

def run_complete_pipeline():
    """Run the complete data and training pipeline"""
    print("\n🔄 Running complete pipeline...")
    
    try:
        from main import prepare_data, label_and_train
        
        print("   Preparing data...")
        if not prepare_data():
            print("   ❌ Data preparation failed")
            return False
        
        print("   Training model...")
        if not label_and_train():
            print("   ❌ Model training failed")
            return False
        
        # Check accuracy
        if os.path.exists("models/model_metadata.json"):
            import json
            with open("models/model_metadata.json", "r") as f:
                metadata = json.load(f)
            
            accuracy = metadata.get('accuracy', 0)
            print(f"   📊 Model Accuracy: {accuracy:.2%}")
            
            if accuracy >= 0.90:
                print("   🎯 EXCELLENT! 90%+ accuracy achieved!")
            elif accuracy >= 0.85:
                print("   👍 Good accuracy achieved")
            else:
                print("   ⚠️  Consider collecting more data")
        
        print("   ✅ Pipeline completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Pipeline error: {e}")
        return False

def display_next_steps(success):
    """Display next steps"""
    print("\n" + "="*60)
    print("📋 SETUP COMPLETE")
    print("="*60)
    
    if success:
        print("\n🎉 Your Bitcoin Options Alert System is ready!")
        print("\n🚀 TO START:")
        print("   python main.py --alert   # Start alert system")
        print("   python main.py --all     # Full pipeline")
        
        print("\n📱 TELEGRAM SETUP:")
        print("   1. Run: python get_telegram_chat_id.py")
        print("   2. Message your bot to get chat ID")
        print("   3. Update config.yaml with your chat ID")
        
        print("\n⚙️  FOR 90%+ ACCURACY:")
        print("   - Monitor performance daily")
        print("   - Retrain weekly with new data")
        print("   - Adjust confidence thresholds")
    else:
        print("\n❌ Some issues detected. Fix above errors first.")
    
    print("\n" + "="*60)

def main():
    """Main setup function"""
    print_banner()
    
    success = True
    
    # Run all setup steps
    if not check_dependencies():
        success = False
    
    setup_directories()
    
    if not test_system_components():
        success = False
    
    if success and not run_complete_pipeline():
        success = False
    
    display_next_steps(success)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)