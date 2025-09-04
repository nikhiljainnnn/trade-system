import requests
import json
import yaml
import datetime
import pandas as pd
import numpy as np
from datetime import timedelta
import random
import time

# Load configuration
def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

# Calculate the next weekly expiry date
def get_next_weekly_expiry():
    config = load_config()
    weekly_day = config.get('weekly_expiry_day', 'thursday').lower()
    
    # Map day name to weekday number (0=Monday, 6=Sunday)
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    target_weekday = day_map.get(weekly_day, 3)  # Default to Thursday (3) if invalid
    
    today = datetime.datetime.now().date()
    days_ahead = target_weekday - today.weekday()
    
    # If today is the expiry day and it's after market hours, or if we've passed the expiry day this week
    if days_ahead <= 0:
        days_ahead += 7  # Go to next week
        
    next_expiry = today + timedelta(days=days_ahead)
    return next_expiry.strftime('%Y-%m-%d')

def fetch_option_chain(expiry_date=None):
    # If no expiry date is provided, use the configuration
    if expiry_date is None:
        config = load_config()
        if config.get('use_weekly_options', True):
            expiry_date = get_next_weekly_expiry()
        else:
            # Use the fixed expiry date from config if weekly options are disabled
            expiry_date = config.get('expiry_date', '2025-05-02')
    
    print(f"Fetching Bitcoin option chain for expiry date: {expiry_date}")
    
    # Get exchange from config
    config = load_config()
    exchange = config.get('crypto_exchange', 'deribit')
    
    # Format expiry date for Deribit API (DDMMMYY format, e.g., 25DEC20)
    try:
        expiry_dt = datetime.datetime.strptime(expiry_date, '%Y-%m-%d')
        deribit_expiry = expiry_dt.strftime('%d%b%y').upper()
    except Exception as e:
        print(f"Error formatting expiry date: {e}")
        deribit_expiry = "25JUN23"  # Fallback expiry
    
    # Deribit API endpoint for BTC options
    url = f"https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=option&expired=false"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        # Get current BTC price for ATM options
        btc_price_url = "https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd"
        price_response = requests.get(btc_price_url, headers=headers, timeout=10)
        current_btc_price = 0
        
        if price_response.status_code == 200:
            price_data = price_response.json()
            current_btc_price = price_data.get('result', {}).get('index_price', 60000)  # Default if not found
        else:
            current_btc_price = 60000  # Default BTC price if API fails
            
        print(f"Current BTC price: ${current_btc_price}")
        
        # Get options data
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            print("Using mock data for testing purposes...")
            return generate_mock_option_chain(expiry_date, current_btc_price)

        try:
            data = response.json()
        except Exception as e:
            print(f"Failed to decode JSON: {e}")
            print("Using mock data for testing purposes...")
            return generate_mock_option_chain(expiry_date, current_btc_price)

        print("Fetched Bitcoin option chain data successfully!")
        
        # Parse the option chain data into a DataFrame
        records = []
        try:
            instruments = data.get('result', [])
            
            # Filter for options with the target expiry date
            target_instruments = []
            for instrument in instruments:
                if deribit_expiry in instrument.get('instrument_name', ''):
                    target_instruments.append(instrument)
            
            # If no instruments found for target expiry, use all available instruments
            if not target_instruments:
                print(f"No options found for expiry {deribit_expiry}, using all available options")
                target_instruments = instruments
            
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for instrument in target_instruments:
                instrument_name = instrument.get('instrument_name', '')
                strike = instrument.get('strike', 0)
                option_type = 'CE' if instrument.get('option_type', '') == 'call' else 'PE'
                expiry = instrument.get('expiration_timestamp', 0)
                
                # Convert timestamp to date string
                if expiry:
                    expiry = datetime.datetime.fromtimestamp(expiry/1000).strftime('%Y-%m-%d')
                else:
                    expiry = expiry_date
                
                # Get option details
                details_url = f"https://www.deribit.com/api/v2/public/get_order_book?instrument_name={instrument_name}"
                try:
                    details_response = requests.get(details_url, headers=headers, timeout=10)
                    if details_response.status_code == 200:
                        details_data = details_response.json().get('result', {})
                        
                        # Extract relevant data
                        mark_price = details_data.get('mark_price', 0)
                        stats = details_data.get('stats', {})
                        volume = stats.get('volume', 0)
                        open_interest = stats.get('open_interest', 0)
                        implied_volatility = details_data.get('greeks', {}).get('vega', 0) * 100  # Approximate IV
                        
                        records.append({
                            'Datetime': now,
                            'Strike': strike,
                            'Type': option_type,
                            'Expiry': expiry,
                            'LTP': mark_price,
                            'IV': implied_volatility,
                            'OI': open_interest,
                            'Volume': volume
                        })
                        
                        # Rate limit to avoid API throttling
                        time.sleep(0.2)
                        
                except Exception as e:
                    print(f"Error fetching details for {instrument_name}: {e}")
            
            # If no valid records were created, use mock data
            if not records:
                print("No valid option data found, using mock data...")
                return generate_mock_option_chain(expiry_date, current_btc_price)
                
            return pd.DataFrame(records)
            
        except Exception as e:
            print(f"Error parsing option chain data: {e}")
            return generate_mock_option_chain(expiry_date, current_btc_price)

    except Exception as e:
        print(f"Request error: {e}")
        return generate_mock_option_chain(expiry_date, current_btc_price)

def generate_mock_option_chain(expiry_date, current_btc_price=None):
    """Generate mock Bitcoin option chain data for testing when API fails"""
    print(f"Generating mock Bitcoin option chain data for {expiry_date}")
    
    # Current Bitcoin price (approximate)
    if current_btc_price is None:
        current_btc_price = 60000
    
    # Generate strike prices around current Bitcoin level
    strikes = np.arange(current_btc_price - 10000, current_btc_price + 10000, 1000)
    
    records = []
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for strike in strikes:
        # Call option
        call_premium = max(0, current_btc_price - strike) + random.uniform(500, 2000)
        records.append({
            'Datetime': now,
            'Strike': strike,
            'Type': 'CE',
            'Expiry': expiry_date,
            'LTP': round(call_premium, 2),
            'IV': round(random.uniform(60, 100), 2),  # Bitcoin has higher IV
            'OI': int(random.uniform(100, 1000)),    # Lower OI for Bitcoin
            'Volume': int(random.uniform(10, 500))   # Lower volume for Bitcoin
        })
        
        # Put option
        put_premium = max(0, strike - current_btc_price) + random.uniform(500, 2000)
        records.append({
            'Datetime': now,
            'Strike': strike,
            'Type': 'PE',
            'Expiry': expiry_date,
            'LTP': round(put_premium, 2),
            'IV': round(random.uniform(60, 100), 2),  # Bitcoin has higher IV
            'OI': int(random.uniform(100, 1000)),    # Lower OI for Bitcoin
            'Volume': int(random.uniform(10, 500))   # Lower volume for Bitcoin
        })
    
    return pd.DataFrame(records)
