import os
import pandas as pd
import yaml
import argparse
from utils.fetch_intraday import fetch_nifty_intraday
from utils.fetch_option_chain import fetch_option_chain
from utils.indicators import add_technical_indicators
from merge_data import prepare_merged_data
from label_data import label_signals
from train_model import train_and_save_model
from trade_alert_system import schedule_alerts

# Load configuration
def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

config = load_config()

def prepare_data():
    config = load_config()
    
    print("\n1. Fetching Bitcoin intraday data...")
    
    # Use enhanced data fetching configuration
    interval = config.get('data_fetch_interval', '5m')
    period = config.get('data_lookback_period', '2d')
    
    print(f"   Fetching {interval} data for {period} period...")
    nifty_df = fetch_nifty_intraday(interval=interval, period=period)
    
    if nifty_df is not None and not nifty_df.empty:
        nifty_df.to_csv("data/nifty_intraday.csv", index=False)
        print(f"   ✅ Saved {len(nifty_df)} records to data/nifty_intraday.csv")
    else:
        print("   ❌ Failed to fetch Bitcoin intraday data")
        return False
    
    print("\n2. Fetching Bitcoin option chain data...")
    option_df = fetch_option_chain()  # Let fetch_option_chain determine the expiry date
    if option_df is not None and not option_df.empty:
        option_df.to_csv("data/nifty_option_chain.csv", index=False)
        print(f"   ✅ Saved {len(option_df)} records to data/nifty_option_chain.csv")
    else:
        print("   ❌ Failed to fetch option chain data")
    
    print("\n3. Preparing merged data for model...")
    merged_df = prepare_merged_data()
    if merged_df is not None and not merged_df.empty:
        merged_df.to_csv("data/model_input_data.csv", index=False)
        print(f"   ✅ Saved {len(merged_df)} records to data/model_input_data.csv")
        print(f"   📊 Data shape: {merged_df.shape}")
        print(f"   📈 Price range: ${merged_df['Close'].min():.2f} - ${merged_df['Close'].max():.2f}")
        return True
    else:
        print("   ❌ Failed to prepare merged data")
        return False

def label_and_train():
    print("\n4. Labeling data for training...")
    if not os.path.exists("data/model_input_data.csv"):
        print("   ❌ model_input_data.csv not found. Run prepare_data first.")
        return False
        
    input_df = pd.read_csv("data/model_input_data.csv")
    labeled_df = label_signals(input_df)
    labeled_df.to_csv("data/labeled_data.csv", index=False)
    print(f"   ✅ Saved to data/labeled_data.csv")
    
    print("\n5. Training prediction model...")
    train_and_save_model()
    print(f"   ✅ Model trained and saved to models/trade_model.pkl")
    return True

def start_alert_system():
    print("\n6. Starting trade alert system...")
    schedule_alerts()

def main():
    # Create directories if they don't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    parser = argparse.ArgumentParser(description='Nifty Trade Alert System')
    parser.add_argument('--prepare', action='store_true', help='Prepare data for model')
    parser.add_argument('--train', action='store_true', help='Train the prediction model')
    parser.add_argument('--alert', action='store_true', help='Start the alert system')
    parser.add_argument('--all', action='store_true', help='Run the complete pipeline')
    
    args = parser.parse_args()
    
    if args.all or (not args.prepare and not args.train and not args.alert):
        # Run complete pipeline
        if prepare_data():
            if label_and_train():
                start_alert_system()
    else:
        # Run specific steps
        if args.prepare:
            prepare_data()
        if args.train:
            label_and_train()
        if args.alert:
            start_alert_system()

if __name__ == "__main__":
    main()
