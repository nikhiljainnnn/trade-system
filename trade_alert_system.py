import pandas as pd
import joblib
import time
import yaml
import os
import json
from telegram import Bot
import schedule
from datetime import datetime
from utils.fetch_intraday import fetch_bitcoin_intraday
from utils.fetch_option_chain import fetch_option_chain
from utils.indicators import add_technical_indicators
from merge_data import prepare_merged_data

# Load configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Initialize Telegram bot
bot = Bot(token=config['telegram_bot_token'])
chat_id = config['telegram_chat_id']

# Load the trained model and preprocessing components
def load_model():
    model_path = 'models/trade_model.pkl'
    scaler_path = 'models/feature_scaler.pkl'
    selector_path = 'models/feature_selector.pkl'
    
    if not os.path.exists(model_path):
        print(f"Model file not found at {model_path}. Please train the model first.")
        return None, None, None
    
    model = joblib.load(model_path)
    
    # Load scaler and selector if they exist
    scaler = None
    selector = None
    
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
        print("Loaded feature scaler")
    
    if os.path.exists(selector_path):
        selector = joblib.load(selector_path)
        print("Loaded feature selector")
    
    return model, scaler, selector

# Generate trade signals
def generate_signals():
    print(f"\n{'-'*50}\nGenerating signals at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Add delay to prevent API rate limiting
        time.sleep(config.get('api_rate_limit_delay', 5))
        
        # Get expiry date based on config
        from utils.fetch_option_chain import get_next_weekly_expiry
        
        expiry_date = None
        if config.get('use_weekly_options', True):
            expiry_date = get_next_weekly_expiry()
            print(f"Using weekly expiry date: {expiry_date}")
        
        # Prepare data with retry logic
        df = None
        for attempt in range(config.get('max_retries', 3)):
            try:
                df = prepare_merged_data(expiry_date)
                if df is not None and not df.empty:
                    break
            except Exception as e:
                print(f"Data preparation attempt {attempt + 1} failed: {e}")
                if attempt < config.get('max_retries', 3) - 1:
                    time.sleep(config.get('retry_delay', 10))
                
        if df is None or df.empty:
            print("⚠️ Failed to prepare data after all attempts. Using cached data if available.")
            # Try to load cached data
            cache_file = 'data/last_successful_data.pkl'
            if os.path.exists(cache_file):
                df = pd.read_pickle(cache_file)
                print("✓ Loaded cached data for analysis")
            else:
                send_alert(f"⚠️ Failed to prepare data for signal generation. No cached data available.")
                return
        else:
            # Cache successful data
            os.makedirs('data', exist_ok=True)
            df.to_pickle('data/last_successful_data.pkl')
            print("✓ Data cached for future use")
            
        # Load model and preprocessing components
        model, scaler, selector = load_model()
        if model is None:
            send_alert(f"⚠️ Failed to load prediction model.")
            return
            
        # Get latest data point
        latest_data = df.iloc[-1:]
        
        # Load the metadata to get the exact features used during training
        metadata_path = 'models/model_metadata.json'
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            expected_features = metadata.get('features', [])
        else:
            # Fallback to a basic set of features
            expected_features = [
                "Close", "Volume", "RSI_14", "MACD", "Call_LTP", "Call_IV", "Call_OI", "Call_Volume"
            ]
        
        print(f"Expected features: {expected_features[:10]}...")  # Show first 10
        print(f"Available columns: {list(latest_data.columns)[:10]}...")  # Show first 10
        
        # Check which features are available
        available_features = [col for col in expected_features if col in latest_data.columns]
        
        if len(available_features) < len(expected_features):
            print(f"Warning: Only {len(available_features)}/{len(expected_features)} expected features available")
        
        # Extract the features
        try:
            features = latest_data[available_features]
            
            # Apply the same preprocessing as during training
            if selector is not None:
                # If we have a feature selector, we need the original feature set first
                original_features = [
                    "Close", "Volume", "RSI_14", "RSI_21", "RSI_7", "RSI_Momentum", "Stoch_K", "Stoch_D", "Williams_R",
                    "MACD", "MACD_Signal", "MACD_Histogram", "MACD_Std", "MACD_Signal_Std",
                    "EMA_9", "EMA_21", "EMA_50", "EMA_200", "EMA_Cross_Short", "EMA_Cross_Long",
                    "BB_Width", "BB_Position", "ATR", "ATR_Percent", "Volatility_Breakout", "Volatility_Regime",
                    "VWAP_Distance", "Volume_ROC", "Higher_High", "Lower_Low", "Support_Distance", "Resistance_Distance",
                    "ADX", "Trending_Market", "Choppiness", "Momentum_Confluence",
                    "Close_Lag_1", "Close_Lag_2", "Close_Lag_3", "Close_Lag_5",
                    "RSI_Lag_1", "RSI_Lag_2", "RSI_Lag_3", "RSI_Lag_5",
                    "MACD_Lag_1", "MACD_Lag_2", "MACD_Lag_3", "MACD_Lag_5",
                    "Close_SMA_5", "Close_SMA_20", "Close_Std_20", "Close_Skew_20", "Close_Kurt_20",
                    "Return_3d", "Return_5d", "Return_10d", "Return_20d",
                    "Volatility_3d", "Volatility_5d", "Volatility_10d", "Volatility_20d",
                    "Call_LTP", "Call_IV", "Call_OI", "Call_Volume",
                    "Crypto_Fear_Greed", "Is_Weekend", "Hour", "Is_US_Hours", "Is_Asian_Hours"
                ]
                
                available_original = [col for col in original_features if col in latest_data.columns]
                if len(available_original) >= 10:  # Need at least 10 features
                    features_for_selection = latest_data[available_original]
                    features = selector.transform(features_for_selection)
                    # Convert back to DataFrame with selected feature names
                    features = pd.DataFrame(features, columns=available_features, index=latest_data.index)
            
            # Apply scaling if available
            if scaler is not None:
                features_scaled = scaler.transform(features)
                features = pd.DataFrame(features_scaled, columns=features.columns, index=features.index)
            
        except Exception as e:
            print(f"Error preparing features: {e}")
            # Fallback to basic features
            basic_features = ['Close', 'Call_LTP', 'Call_IV', 'Call_OI', 'Call_Volume']
            available_basic = [col for col in basic_features if col in latest_data.columns]
            if available_basic:
                features = latest_data[available_basic]
            else:
                send_alert(f"❌ No usable features available for prediction")
                return
        
        # Make prediction
        prediction = model.predict(features)[0]
        prediction_proba = model.predict_proba(features)[0]
        confidence = max(prediction_proba) * 100
        
        # Current market data
        current_price = latest_data['Close'].values[0]
        
        # Get RSI value (try different column names)
        if 'RSI_14' in latest_data.columns:
            current_rsi = latest_data['RSI_14'].values[0]
        elif 'RSI' in latest_data.columns:
            current_rsi = latest_data['RSI'].values[0]
        else:
            current_rsi = 50.0  # Default neutral RSI
            
        current_macd = latest_data['MACD'].values[0] if 'MACD' in latest_data.columns else 0.0
        current_call_ltp = latest_data['Call_LTP'].values[0] if 'Call_LTP' in latest_data.columns else 0.0
        
        # Format the signal message based on prediction
        if prediction == 1:  # Buy CALL signal
            signal_emoji = "🟢 BUY CALL OPTION"
            action_text = f"Buy {config['index_symbol']} CALL options"
            option_type = "CALL"
        elif prediction == 2:  # Buy PUT signal
            signal_emoji = "🔴 BUY PUT OPTION"
            action_text = f"Buy {config['index_symbol']} PUT options"
            option_type = "PUT"
        else:
            signal_emoji = "⚪ NO ACTION"
            action_text = "No trade recommendation"
            option_type = "NONE"
        
        # Calculate recommended strike price
        strike_gap = config.get('strike_gap', 1000)  # Default to 1000 for Bitcoin
        if option_type == "CALL":
            # For calls, round up to nearest strike above current price
            recommended_strike = int(current_price / strike_gap) * strike_gap + strike_gap
        elif option_type == "PUT":
            # For puts, round down to nearest strike below current price
            recommended_strike = int(current_price / strike_gap) * strike_gap
        else:
            recommended_strike = int(current_price / strike_gap) * strike_gap
        
        # Create detailed message
        message = f"*{config['index_name']} WEEKLY OPTIONS ALERT*\n\n"
        message += f"*Signal:* {signal_emoji} (Confidence: {confidence:.2f}%)\n"
        
        if option_type != "NONE":
            message += f"*Action:* {action_text}\n"
            message += f"*Recommended Strike:* {recommended_strike}\n"
            message += f"*Expiry Date:* {expiry_date}\n"
        
        # Use $ for Bitcoin/USD
        currency_symbol = "$" if "BTC" in config.get('index_symbol', '').upper() else "₹"
        
        message += f"*Current Price:* {currency_symbol}{current_price:.2f}\n"
        message += f"*RSI:* {current_rsi:.2f}\n"
        message += f"*MACD:* {current_macd:.4f}\n"
        
        # Add additional crypto-specific indicators if available
        if "BB_Width" in latest_data.columns:
            message += f"*BB Width:* {latest_data['BB_Width'].values[0]:.4f}\n"
        
        if "ATR" in latest_data.columns:
            message += f"*ATR:* {latest_data['ATR'].values[0]:.2f}\n"
        
        if option_type == "CALL":
            message += f"*ATM Call Premium:* {currency_symbol}{current_call_ltp:.2f}\n"
        
        message += f"\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Only send alerts for high confidence signals and actual trade recommendations
        confidence_threshold = config.get('signal_confidence_threshold', 70)
        if confidence >= confidence_threshold and option_type != "NONE":
            send_alert(message)
            print(f"Signal generated: {signal_emoji} with {confidence:.2f}% confidence")
        else:
            print(f"No alert sent - {'Low confidence' if confidence < confidence_threshold else 'No action'} signal")
            
    except Exception as e:
        error_msg = f"❌ Error generating signals: {str(e)}"
        print(error_msg)
        send_alert(error_msg)

# Send alert via Telegram
def send_alert(message):
    try:
        bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        print(f"Alert sent successfully to chat ID: {chat_id}")
    except Exception as e:
        print(f"Failed to send Telegram alert: {str(e)}")

# Check if current time is valid for trading
def is_market_hours():
    # For crypto which trades 24/7, we'll check if we're in a reasonable trading window
    # to avoid excessive alerts during very low liquidity hours
    
    if config.get('crypto_exchange', '').lower() == 'deribit':
        # Crypto markets are 24/7, but we can optionally limit alerts to certain hours
        # if specified in config
        trading_hours_only = config.get('limit_trading_hours', False)
        
        if not trading_hours_only:
            return True  # Always generate signals for 24/7 markets if no limits set
        
        now = datetime.now()
        # Optional: Define high-liquidity hours (e.g., 8 AM to 10 PM)
        # This is just a suggestion and can be adjusted based on preferences
        market_open = now.replace(hour=8, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=22, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    else:
        # For traditional markets, use standard market hours
        now = datetime.now()
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Standard market hours: 9:15 AM to 3:30 PM
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close

# Schedule the signal generation
def schedule_alerts():
    # Convert minutes to string format for schedule
    interval_mins = config['fetch_interval']
    
    # Schedule the job to run only during market hours
    def job():
        if is_market_hours():
            print(f"Market is open. Generating signals...")
            generate_signals()
        else:
            print(f"Market is closed. Skipping signal generation.")
    
    # Schedule the job
    schedule.every(interval_mins).minutes.do(job)
    
    # Send startup message
    startup_message = f"🚀 *{config['index_name']} Trade Alert System Started*\n\n"
    startup_message += f"Monitoring {config['index_name']} for trade signals\n"
    
    # Different message for crypto vs traditional markets
    if config.get('crypto_exchange', '').lower() == 'deribit':
        if config.get('limit_trading_hours', False):
            startup_message += f"Alerts will be sent every {interval_mins} minute(s) during configured trading hours\n"
        else:
            startup_message += f"Alerts will be sent every {interval_mins} minute(s) 24/7 (crypto markets)\n"
    else:
        startup_message += f"Alerts will be sent every {interval_mins} minute(s) during market hours (9:15 AM - 3:30 PM, Mon-Fri)\n"
    
    startup_message += f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    send_alert(startup_message)
    
    print(f"Alert system scheduled to run every {interval_mins} minute(s) during market hours")
    print("Press Ctrl+C to stop")
    
    # Run the job immediately once if within market hours
    if is_market_hours():
        generate_signals()
    else:
        print("Market is currently closed. Will check for signals when market opens.")
        send_alert("⏰ Market is currently closed. Will send alerts when market opens.")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    schedule_alerts()