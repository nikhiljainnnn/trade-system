import pandas as pd
import numpy as np
import yaml
import os
from datetime import datetime, timedelta

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def calculate_option_profitability(df, lookback_periods=[3, 5, 10, 15, 30]):
    """Calculate actual option profitability for more accurate labeling"""
    
    config = load_config()
    
    # Bitcoin options typically have shorter time to expiry
    is_crypto = 'BTC' in config.get('index_symbol', '').upper()
    if is_crypto:
        lookback_periods = [2, 3, 5, 10, 15]  # Shorter periods for crypto
    
    # Calculate returns for different periods
    for period in lookback_periods:
        df[f'Return_{period}'] = df['Close'].pct_change(periods=period).shift(-period)
        df[f'Max_Return_{period}'] = df['Close'].rolling(window=period).max().shift(-period) / df['Close'] - 1
        df[f'Min_Return_{period}'] = df['Close'].rolling(window=period).min().shift(-period) / df['Close'] - 1
    
    # Calculate volatility-adjusted returns
    df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
    
    return df

def simulate_option_trades(df, call_premium=None, put_premium=None):
    """Simulate actual option trades to determine profitability"""
    
    results = []
    
    for i, row in df.iterrows():
        if pd.isna(row['Call_LTP']) or pd.isna(row['Close']):
            continue
            
        current_price = row['Close']
        call_price = row['Call_LTP'] if call_premium is None else call_premium
        put_price = row.get('Put_LTP', call_price * 0.8) if put_premium is None else put_premium  # Estimate put price
        
        # Simulate different holding periods
        for period in [3, 5, 10, 15]:
            if f'Return_{period}' not in row or pd.isna(row[f'Return_{period}']):
                continue
                
            future_return = row[f'Return_{period}']
            future_price = current_price * (1 + future_return)
            
            # Calculate option values at expiry (simplified Black-Scholes approximation)
            # For simplicity, assuming options expire at the money
            
            # Call option profit/loss
            call_payoff = max(0, future_price - current_price)  # Simplified ATM call
            call_profit = call_payoff - call_price
            call_profit_pct = call_profit / call_price if call_price > 0 else 0
            
            # Put option profit/loss  
            put_payoff = max(0, current_price - future_price)  # Simplified ATM put
            put_profit = put_payoff - put_price
            put_profit_pct = put_profit / put_price if put_price > 0 else 0
            
            results.append({
                'index': i,
                'period': period,
                'call_profit_pct': call_profit_pct,
                'put_profit_pct': put_profit_pct,
                'underlying_return': future_return,
                'volatility': row['Volatility'] if 'Volatility' in row else 0
            })
    
    return pd.DataFrame(results)

def label_signals_advanced(df: pd.DataFrame) -> pd.DataFrame:
    """Advanced signal labeling based on actual option profitability"""
    
    config = load_config()
    
    # Profit thresholds for signal generation
    min_profit_threshold = config.get('min_profit_threshold', 0.20)  # 20% minimum profit
    high_confidence_threshold = config.get('high_confidence_threshold', 0.50)  # 50% for high confidence
    
    # Calculate option profitability metrics
    df = calculate_option_profitability(df)
    
    # Simulate option trades
    option_results = simulate_option_trades(df)
    
    if option_results.empty:
        print("Warning: No option simulation results. Using basic labeling.")
        return label_signals_basic(df)
    
    # Aggregate results by index to get best signals
    best_signals = option_results.groupby('index').agg({
        'call_profit_pct': ['max', 'mean'],
        'put_profit_pct': ['max', 'mean'],
        'period': lambda x: x.iloc[0]  # Best period for this signal
    }).reset_index()
    
    # Flatten column names
    best_signals.columns = ['index', 'call_max_profit', 'call_avg_profit', 
                           'put_max_profit', 'put_avg_profit', 'best_period']
    
    # Merge back with original data
    df = df.reset_index()
    df = df.merge(best_signals, left_index=True, right_on='index', how='left')
    
    # Generate signals based on profitability
    def generate_signal(row):
        call_profit = row.get('call_max_profit', 0)
        put_profit = row.get('put_max_profit', 0)
        
        # Determine the best option strategy
        if call_profit > min_profit_threshold and call_profit > put_profit:
            return 1  # BUY CALL
        elif put_profit > min_profit_threshold and put_profit > call_profit:
            return 2  # BUY PUT
        else:
            return 0  # NO ACTION
    
    def generate_confidence(row):
        call_profit = row.get('call_max_profit', 0)
        put_profit = row.get('put_max_profit', 0)
        
        max_profit = max(call_profit, put_profit)
        
        if max_profit > high_confidence_threshold:
            return 'HIGH'
        elif max_profit > min_profit_threshold:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    df['Signal'] = df.apply(generate_signal, axis=1)
    df['Signal_Confidence'] = df.apply(generate_confidence, axis=1)
    
    # Add signal descriptions
    df['Signal_Type'] = df['Signal'].map({
        0: 'NO_ACTION',
        1: 'BUY_CALL', 
        2: 'BUY_PUT'
    })
    
    # Add expected profit information
    df['Expected_Profit'] = df.apply(
        lambda row: row.get('call_max_profit', 0) if row['Signal'] == 1 
        else (row.get('put_max_profit', 0) if row['Signal'] == 2 else 0), axis=1
    )
    
    # Filter for quality signals
    option_type = config.get('option_type', 'both').lower()
    
    if option_type == 'call':
        df = df[df['Signal'].isin([0, 1])]  # Only CALL and NO_ACTION
    elif option_type == 'put':
        df = df[df['Signal'].isin([0, 2])]  # Only PUT and NO_ACTION
    # else: keep all signals ('both')
    
    # For training, we want a balanced dataset, so we'll keep some NO_ACTION signals
    # but prioritize profitable signals
    
    action_signals = df[df['Signal'] != 0]  # Profitable signals
    no_action_signals = df[df['Signal'] == 0].sample(n=min(len(action_signals), len(df[df['Signal'] == 0])), 
                                                     random_state=42)  # Balanced NO_ACTION signals
    
    # Combine and shuffle
    df_balanced = pd.concat([action_signals, no_action_signals]).sample(frac=1, random_state=42)
    
    # Remove rows with missing values
    df_balanced = df_balanced.dropna(subset=['Signal', 'Close', 'Call_LTP'])
    
    print(f"Signal distribution after advanced labeling:")
    print(df_balanced['Signal_Type'].value_counts())
    print(f"Confidence distribution:")
    print(df_balanced['Signal_Confidence'].value_counts())
    
    return df_balanced

def label_signals_basic(df: pd.DataFrame, threshold=0.02) -> pd.DataFrame:
    """Basic signal labeling as fallback"""
    
    config = load_config()
    
    # Use a higher threshold for crypto (more volatile)
    is_crypto = 'BTC' in config.get('index_symbol', '').upper()
    if is_crypto:
        threshold = config.get('volatility_threshold', 0.03)  # 3% for Bitcoin
    
    # Calculate future returns for multiple periods and take the best
    periods = [3, 5, 10]
    for period in periods:
        df[f'Return_{period}'] = df['Close'].pct_change(periods=period).shift(-period)
    
    # Use the maximum absolute return across periods for signal strength
    df['Max_Return'] = df[[f'Return_{p}' for p in periods]].abs().max(axis=1)
    df['Best_Return'] = df[[f'Return_{p}' for p in periods]].iloc[:, 0]  # Use shortest period as primary
    
    # Only generate signals for significant moves
    df['Signal'] = df.apply(
        lambda row: 1 if row['Best_Return'] > threshold and row['Max_Return'] > threshold
        else (2 if row['Best_Return'] < -threshold and row['Max_Return'] > threshold else 0), axis=1
    )
    
    df['Signal_Type'] = df['Signal'].map({
        0: 'NO_ACTION',
        1: 'BUY_CALL',
        2: 'BUY_PUT'
    })
    
    df['Signal_Confidence'] = df['Max_Return'].apply(
        lambda x: 'HIGH' if x > threshold * 2 else ('MEDIUM' if x > threshold else 'LOW')
    )
    
    # Filter based on option type preference
    option_type = config.get('option_type', 'both').lower()
    if option_type == 'call':
        df = df[df['Signal'].isin([0, 1])]
    elif option_type == 'put':
        df = df[df['Signal'].isin([0, 2])]
    
    # Remove rows with no signal for training (keep some for balance)
    action_signals = df[df['Signal'] != 0]
    no_action_signals = df[df['Signal'] == 0].sample(n=min(len(action_signals) // 2, len(df[df['Signal'] == 0])), 
                                                     random_state=42)
    
    df_final = pd.concat([action_signals, no_action_signals]).sample(frac=1, random_state=42)
    df_final = df_final.dropna()
    
    return df_final

def label_signals(df: pd.DataFrame, use_advanced=True) -> pd.DataFrame:
    """Main function to label signals with option for advanced or basic labeling"""
    
    print(f"Labeling signals for {len(df)} data points...")
    
    # Check if we have sufficient data for advanced labeling
    required_columns = ['Close', 'Call_LTP', 'Call_IV', 'Call_OI', 'Call_Volume']
    has_required_data = all(col in df.columns for col in required_columns)
    
    if use_advanced and has_required_data and len(df) > 100:
        print("Using advanced option profitability labeling...")
        try:
            result = label_signals_advanced(df)
            if len(result) > 10:  # Ensure we have enough labeled data
                return result
            else:
                print("Advanced labeling produced insufficient data, falling back to basic labeling...")
        except Exception as e:
            print(f"Advanced labeling failed: {e}. Using basic labeling...")
    
    print("Using basic signal labeling...")
    return label_signals_basic(df)

if __name__ == "__main__":
    # Test the labeling function
    if not os.path.exists("data/model_input_data.csv"):
        print("No input data found. Run data preparation first.")
    else:
        df = pd.read_csv("data/model_input_data.csv")
        labeled_df = label_signals(df)
        labeled_df.to_csv("data/labeled_data.csv", index=False)
        print(f"Labeled data saved with {len(labeled_df)} samples")
