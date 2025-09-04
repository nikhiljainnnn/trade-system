import pandas as pd
import numpy as np
import random
import datetime
from utils.fetch_intraday import fetch_bitcoin_intraday
from utils.fetch_option_chain import fetch_option_chain, get_next_weekly_expiry
from utils.indicators import add_technical_indicators
import yaml

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def create_mock_option_data(expiry_date):
    """Create mock Bitcoin option chain data for testing"""
    # Current Bitcoin price (approximate)
    current_btc = 60000
    
    # Generate strike prices around current Bitcoin level
    strikes = np.arange(current_btc - 10000, current_btc + 10000, 1000)
    
    records = []
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for strike in strikes:
        # Call option
        call_premium = max(0, current_btc - strike) + random.uniform(500, 2000)
        records.append({
            'Datetime': now,
            'Strike': strike,
            'Type': 'CE',
            'Expiry': expiry_date,
            'LTP': round(call_premium, 2),
            'IV': round(random.uniform(60, 100), 2),  # Bitcoin has higher IV
            'OI': int(random.uniform(100, 1000)),     # Lower OI for Bitcoin
            'Volume': int(random.uniform(10, 500))    # Lower volume for Bitcoin
        })
        
        # Put option
        put_premium = max(0, strike - current_btc) + random.uniform(500, 2000)
        records.append({
            'Datetime': now,
            'Strike': strike,
            'Type': 'PE',
            'Expiry': expiry_date,
            'LTP': round(put_premium, 2),
            'IV': round(random.uniform(60, 100), 2),  # Bitcoin has higher IV
            'OI': int(random.uniform(100, 1000)),     # Lower OI for Bitcoin
            'Volume': int(random.uniform(10, 500))    # Lower volume for Bitcoin
        })
    
    return pd.DataFrame(records)

def create_mock_atm_calls(index_df, atm_strike):
    """Create mock Bitcoin ATM call option data aligned with index_df timestamps"""
    # Create mock data with timestamps matching the index_df
    atm_calls_list = []
    
    for idx, row in index_df.iterrows():
        # Extract Close value safely
        if isinstance(row['Close'], pd.Series):
            close_val = row['Close'].iloc[0]
        elif hasattr(row['Close'], 'item'):
            close_val = row['Close'].item()
        else:
            close_val = float(row['Close'])
            
        # Extract Datetime value safely
        if isinstance(row['Datetime'], pd.Series):
            datetime_val = row['Datetime'].iloc[0]
        else:
            datetime_val = row['Datetime']
        
        # Ensure datetime is properly formatted
        if not isinstance(datetime_val, pd.Timestamp):
            datetime_val = pd.to_datetime(datetime_val)
        
        # Generate realistic Bitcoin option data based on the index price
        call_premium = max(0, close_val - atm_strike) + random.uniform(500, 2000)
        atm_calls_list.append({
            'Datetime': datetime_val,
            'Call_LTP': round(call_premium, 2),
            'Call_IV': round(random.uniform(60, 100), 2),  # Bitcoin has higher IV
            'Call_OI': int(random.uniform(100, 1000)),     # Lower OI for Bitcoin
            'Call_Volume': int(random.uniform(10, 500))    # Lower volume for Bitcoin
        })
    
    mock_df = pd.DataFrame(atm_calls_list)
    # Ensure datetime column is properly typed
    mock_df['Datetime'] = pd.to_datetime(mock_df['Datetime'])
    return mock_df

def prepare_merged_data(expiry_date=None):
    # If no expiry date is provided, use the configuration
    if expiry_date is None:
        config = load_config()
        if config.get('use_weekly_options', True):
            expiry_date = get_next_weekly_expiry()
        else:
            # Use a default expiry date if weekly options are disabled
            expiry_date = config.get('expiry_date', '2025-05-02')
    
    # Get Bitcoin price data
    index_df = fetch_bitcoin_intraday()
    index_df = add_technical_indicators(index_df)

    option_df = fetch_option_chain(expiry_date)
    
    # If option_df is None or empty, create a mock dataframe for testing
    if option_df is None or len(option_df) == 0:
        print("Creating mock Bitcoin option data for testing...")
        option_df = create_mock_option_data(expiry_date)
    
    # Get ATM Strike nearest to latest Close
    latest_price_row = index_df.iloc[-1]
    if isinstance(latest_price_row["Close"], pd.Series):
        latest_price = latest_price_row["Close"].iloc[0]
    elif hasattr(latest_price_row["Close"], 'item'):
        latest_price = latest_price_row["Close"].item()
    else:
        latest_price = float(latest_price_row["Close"])
    # For Bitcoin, round to nearest 1000
    config = load_config()
    strike_gap = config.get('strike_gap', 1000)  # Default to 1000 for Bitcoin
    atm_strike = round(latest_price / strike_gap) * strike_gap
    
    # Print option_df structure for debugging
    print(f"Option DataFrame shape: {option_df.shape}")
    print(f"Option DataFrame columns: {option_df.columns}")
    print(f"Option DataFrame dtypes: {option_df.dtypes}")
    
    # Try a different approach - filter using boolean indexing
    try:
        # Convert Strike to numeric if it's not already
        if option_df['Strike'].dtype == 'object':
            option_df['Strike'] = pd.to_numeric(option_df['Strike'], errors='coerce')
        
        # Filter for ATM calls using boolean indexing
        atm_calls_df = option_df[
            (option_df['Strike'] == atm_strike) & 
            (option_df['Type'] == 'CE')
        ].copy()
        
        # If we found ATM calls, rename columns
        if not atm_calls_df.empty:
            atm_calls = pd.DataFrame({
                'Datetime': atm_calls_df['Datetime'],
                'Call_LTP': atm_calls_df['LTP'],
                'Call_IV': atm_calls_df['IV'],
                'Call_OI': atm_calls_df['OI'],
                'Call_Volume': atm_calls_df['Volume']
            })
        else:
            atm_calls = pd.DataFrame()
    except Exception as e:
        print(f"Error filtering ATM calls: {e}")
        # Fall back to empty DataFrame
        atm_calls = pd.DataFrame()
    
    # If no ATM calls found, create mock data
    if atm_calls.empty:
        print("No ATM calls found, creating mock data...")
        atm_calls = create_mock_atm_calls(index_df, atm_strike)

    # Ensure datetime columns are properly formatted and reset any multi-index
    index_df = index_df.reset_index(drop=True)
    atm_calls = atm_calls.reset_index(drop=True)
    
    # Convert datetime columns to pandas datetime if they aren't already
    index_df['Datetime'] = pd.to_datetime(index_df['Datetime'])
    atm_calls['Datetime'] = pd.to_datetime(atm_calls['Datetime'])
    
    # Sort both dataframes by datetime
    index_df = index_df.sort_values("Datetime").reset_index(drop=True)
    atm_calls = atm_calls.sort_values("Datetime").reset_index(drop=True)
    
    # Merge the index data with option data using asof merge
    try:
        df = pd.merge_asof(index_df, atm_calls, on="Datetime", direction='nearest')
    except Exception as e:
        print(f"Error in merge_asof: {e}")
        print("Falling back to simple merge...")
        # Fallback: create a simple merged dataframe
        df = index_df.copy()
        
        # Add option data columns with default values
        if not atm_calls.empty:
            # Use the first available option data for all rows
            first_option = atm_calls.iloc[0]
            df['Call_LTP'] = first_option.get('Call_LTP', 1000.0)
            df['Call_IV'] = first_option.get('Call_IV', 75.0)
            df['Call_OI'] = first_option.get('Call_OI', 500)
            df['Call_Volume'] = first_option.get('Call_Volume', 100)
        else:
            # Use default values based on BTC price
            df['Call_LTP'] = latest_price * 0.02  # 2% of BTC price
            df['Call_IV'] = 75.0
            df['Call_OI'] = 500
            df['Call_Volume'] = 100
    
    # Drop any remaining NaN values
    df = df.dropna()
    
    print(f"Final merged data shape: {df.shape}")
    if len(df) > 0:
        print(f"Date range: {df['Datetime'].min()} to {df['Datetime'].max()}")
        close_min = float(df['Close'].min())
        close_max = float(df['Close'].max())
        print(f"BTC price range: ${close_min:.2f} - ${close_max:.2f}")
    
    return df

if __name__ == "__main__":
    df = prepare_merged_data()
    df.to_csv("data/model_input_data.csv", index=False)
    print(df.head())
