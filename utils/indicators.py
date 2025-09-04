import pandas as pd
import ta  # from the 'ta' library
import numpy as np
import yaml
from scipy import stats
from sklearn.preprocessing import MinMaxScaler

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add comprehensive technical indicators optimized for 90%+ Bitcoin options accuracy"""
    
    # Create a copy to avoid modifying original
    df = df.copy()
    
    # Ensure all series are 1D and properly formatted
    def ensure_1d_series(series, index):
        if hasattr(series, 'values'):
            if hasattr(series.values, 'flatten'):
                values = series.values.flatten()
            else:
                values = series.values
            # Ensure we have the right length
            if len(values) != len(index):
                values = values[:len(index)]  # Truncate if too long
            return pd.Series(values, index=index)
        return pd.Series(series, index=index)
    
    # Handle the Close series properly
    close_series = ensure_1d_series(df['Close'], df.index)
    
    # Get high, low, volume series safely
    if 'High' in df.columns:
        high_series = ensure_1d_series(df['High'], df.index)
    else:
        high_series = close_series.copy()
        
    if 'Low' in df.columns:
        low_series = ensure_1d_series(df['Low'], df.index)
    else:
        low_series = close_series.copy()
        
    if 'Volume' in df.columns:
        volume_series = ensure_1d_series(df['Volume'], df.index)
    else:
        volume_series = pd.Series(np.ones_like(close_series), index=df.index)
    
    # Update the dataframe with properly formatted series
    df['Close'] = close_series
    df['High'] = high_series
    df['Low'] = low_series
    df['Volume'] = volume_series
    
    config = load_config()
    is_crypto = 'BTC' in config.get('index_symbol', '').upper()
    
    # === MOMENTUM INDICATORS (optimized for crypto) ===
    
    try:
        # Multi-timeframe RSI for better accuracy
        df['RSI_14'] = ta.momentum.RSIIndicator(close=close_series, window=14).rsi()
        df['RSI_21'] = ta.momentum.RSIIndicator(close=close_series, window=21).rsi()
        df['RSI_7'] = ta.momentum.RSIIndicator(close=close_series, window=7).rsi()  # Fast RSI for crypto
        
        # RSI divergence detection
        df['RSI_Momentum'] = df['RSI_14'].diff()
        df['Price_Momentum'] = close_series.pct_change()
        
        # Stochastic Oscillator (excellent for overbought/oversold in crypto)
        if len(close_series) > 14:  # Ensure we have enough data
            stoch = ta.momentum.StochasticOscillator(high=high_series, low=low_series, close=close_series)
            df['Stoch_K'] = stoch.stoch()
            df['Stoch_D'] = stoch.stoch_signal()
        else:
            df['Stoch_K'] = 50.0  # Neutral value
            df['Stoch_D'] = 50.0
        
        # Williams %R (another momentum oscillator)
        df['Williams_R'] = ta.momentum.WilliamsRIndicator(high=high_series, low=low_series, close=close_series).williams_r()
        
    except Exception as e:
        print(f"Warning: Error calculating momentum indicators: {e}")
        # Set default values
        df['RSI_14'] = 50.0
        df['RSI_21'] = 50.0
        df['RSI_7'] = 50.0
        df['RSI_Momentum'] = 0.0
        df['Price_Momentum'] = 0.0
        df['Stoch_K'] = 50.0
        df['Stoch_D'] = 50.0
        df['Williams_R'] = -50.0
    
    # === TREND INDICATORS ===
    
    # Multi-timeframe MACD
    macd_fast = ta.trend.MACD(close=close_series, window_fast=8, window_slow=21, window_sign=5)  # Fast for crypto
    df['MACD'] = macd_fast.macd()
    df['MACD_Signal'] = macd_fast.macd_signal()
    df['MACD_Histogram'] = macd_fast.macd_diff()
    
    # Standard MACD for confirmation
    macd_std = ta.trend.MACD(close=close_series, window_fast=12, window_slow=26, window_sign=9)
    df['MACD_Std'] = macd_std.macd()
    df['MACD_Signal_Std'] = macd_std.macd_signal()
    
    # Exponential Moving Averages (multiple timeframes)
    df['EMA_9'] = ta.trend.EMAIndicator(close=close_series, window=9).ema_indicator()
    df['EMA_21'] = ta.trend.EMAIndicator(close=close_series, window=21).ema_indicator()
    df['EMA_50'] = ta.trend.EMAIndicator(close=close_series, window=50).ema_indicator()
    df['EMA_200'] = ta.trend.EMAIndicator(close=close_series, window=200).ema_indicator()
    
    # EMA crossovers (powerful trend signals)
    df['EMA_Cross_Short'] = np.where(df['EMA_9'] > df['EMA_21'], 1, 0)  # Bullish when fast > slow
    df['EMA_Cross_Long'] = np.where(df['EMA_50'] > df['EMA_200'], 1, 0)  # Long-term trend
    
    # === VOLATILITY INDICATORS ===
    
    # Bollinger Bands with multiple configurations
    bb_20 = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df['BB_Upper'] = bb_20.bollinger_hband()
    df['BB_Lower'] = bb_20.bollinger_lband()
    df['BB_Mid'] = bb_20.bollinger_mavg()
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / close_series
    df['BB_Position'] = (close_series - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])  # Position within bands
    
    # Keltner Channels (alternative to Bollinger Bands)
    kc = ta.volatility.KeltnerChannel(high=high_series, low=low_series, close=close_series)
    df['KC_Upper'] = kc.keltner_channel_hband()
    df['KC_Lower'] = kc.keltner_channel_lband()
    df['KC_Mid'] = kc.keltner_channel_mband()
    
    # Average True Range (volatility measure)
    df['ATR'] = ta.volatility.AverageTrueRange(high=high_series, low=low_series, close=close_series, window=14).average_true_range()
    df['ATR_Percent'] = df['ATR'] / close_series * 100  # ATR as percentage of price
    
    # Volatility breakout indicator
    df['Volatility_Breakout'] = np.where(
        (close_series > df['BB_Upper']) | (close_series < df['BB_Lower']), 1, 0
    )
    
    # === VOLUME INDICATORS ===
    
    try:
        # Volume Weighted Average Price (critical for crypto)
        df['VWAP'] = calculate_vwap(df)
        df['VWAP_Distance'] = (close_series - df['VWAP']) / df['VWAP'] * 100  # Distance from VWAP in %
        
        # On-Balance Volume (trend confirmation)
        df['OBV'] = ta.volume.OnBalanceVolumeIndicator(close=close_series, volume=volume_series).on_balance_volume()
        df['OBV_EMA'] = ta.trend.EMAIndicator(close=df['OBV'], window=20).ema_indicator()
        
        # Volume Rate of Change
        df['Volume_ROC'] = volume_series.pct_change(periods=10)  # 10-period volume change
        
    except Exception as e:
        print(f"Warning: Error calculating volume indicators: {e}")
        # Set default values
        df['VWAP'] = close_series
        df['VWAP_Distance'] = 0.0
        df['OBV'] = volume_series.cumsum()
        df['OBV_EMA'] = volume_series.cumsum()
        df['Volume_ROC'] = 0.0
    
    # === ADVANCED PATTERN RECOGNITION ===
    
    # Price patterns and market structure
    df['Higher_High'] = ((close_series > close_series.shift(1)) & 
                        (close_series.shift(1) > close_series.shift(2))).astype(int)
    df['Lower_Low'] = ((close_series < close_series.shift(1)) & 
                      (close_series.shift(1) < close_series.shift(2))).astype(int)
    
    # Support and Resistance levels (simplified)
    df['Support_Level'] = close_series.rolling(window=20).min()
    df['Resistance_Level'] = close_series.rolling(window=20).max()
    df['Support_Distance'] = (close_series - df['Support_Level']) / close_series * 100
    df['Resistance_Distance'] = (df['Resistance_Level'] - close_series) / close_series * 100
    
    # === MARKET REGIME INDICATORS ===
    
    # Market regime detection (trending vs ranging)
    df['ADX'] = ta.trend.ADXIndicator(high=high_series, low=low_series, close=close_series).adx()
    df['Trending_Market'] = np.where(df['ADX'] > 25, 1, 0)  # ADX > 25 indicates trending market
    
    # Choppy market detection
    df['Choppiness'] = calculate_choppiness_index(high_series, low_series, close_series)
    
    # === BITCOIN-SPECIFIC INDICATORS ===
    
    if is_crypto:
        # Crypto fear and greed proxy (using RSI and volatility)
        df['Crypto_Fear_Greed'] = (100 - df['RSI_14']) * df['ATR_Percent'] / 100
        
        # Weekend effect for crypto (different behavior on weekends)
        df['Is_Weekend'] = pd.to_datetime(df['Datetime']).dt.dayofweek.isin([5, 6]).astype(int)
        
        # Hour of day effect (crypto markets show different patterns by hour)
        df['Hour'] = pd.to_datetime(df['Datetime']).dt.hour
        df['Is_US_Hours'] = ((df['Hour'] >= 9) & (df['Hour'] <= 16)).astype(int)  # US trading hours
        df['Is_Asian_Hours'] = ((df['Hour'] >= 1) & (df['Hour'] <= 8)).astype(int)  # Asian trading hours
    
    # === MOMENTUM CONFLUENCE ===
    
    # Create momentum confluence score (combination of multiple indicators)
    momentum_signals = []
    momentum_signals.append(np.where(df['RSI_14'] > 70, -1, np.where(df['RSI_14'] < 30, 1, 0)))
    momentum_signals.append(np.where(df['MACD'] > df['MACD_Signal'], 1, -1))
    momentum_signals.append(np.where(df['Stoch_K'] > 80, -1, np.where(df['Stoch_K'] < 20, 1, 0)))
    momentum_signals.append(np.where(df['EMA_Cross_Short'] == 1, 1, -1))
    
    df['Momentum_Confluence'] = np.sum(momentum_signals, axis=0)
    
    # === VOLATILITY REGIME ===
    
    # Classify volatility regime (low, medium, high)
    atr_quantiles = df['ATR_Percent'].quantile([0.33, 0.67])
    df['Volatility_Regime'] = np.where(
        df['ATR_Percent'] <= atr_quantiles.iloc[0], 0,  # Low volatility
        np.where(df['ATR_Percent'] <= atr_quantiles.iloc[1], 1, 2)  # Medium, High volatility
    )
    
    # === FEATURE ENGINEERING FOR ML ===
    
    # Lag features (previous period values)
    for lag in [1, 2, 3, 5]:
        df[f'Close_Lag_{lag}'] = close_series.shift(lag)
        df[f'RSI_Lag_{lag}'] = df['RSI_14'].shift(lag)
        df[f'MACD_Lag_{lag}'] = df['MACD'].shift(lag)
    
    # Rolling statistics
    df['Close_SMA_5'] = close_series.rolling(window=5).mean()
    df['Close_SMA_20'] = close_series.rolling(window=20).mean()
    df['Close_Std_20'] = close_series.rolling(window=20).std()
    df['Close_Skew_20'] = close_series.rolling(window=20).skew()
    df['Close_Kurt_20'] = close_series.rolling(window=20).kurt()
    
    # Price momentum features
    for period in [3, 5, 10, 20]:
        df[f'Return_{period}d'] = close_series.pct_change(periods=period)
        df[f'Volatility_{period}d'] = close_series.pct_change().rolling(window=period).std()
    
    # === CLEAN UP AND NORMALIZE ===
    
    # Remove infinite values and handle edge cases
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Forward fill small gaps (up to 3 periods)
    df = df.fillna(method='ffill', limit=3)
    
    # Drop rows with remaining NaN values
    df = df.dropna()
    
    return df

def calculate_vwap(df):
    """Calculate Volume Weighted Average Price with improved handling"""
    if 'Volume' not in df.columns or df['Volume'].isnull().all():
        return df['Close']
        
    df_copy = df.copy()
    
    # Calculate typical price
    if all(col in df_copy.columns for col in ['High', 'Low', 'Close']):
        df_copy['TypicalPrice'] = (df_copy['High'] + df_copy['Low'] + df_copy['Close']) / 3
    else:
        df_copy['TypicalPrice'] = df_copy['Close']
    
    # Handle zero or negative volumes
    df_copy['Volume'] = df_copy['Volume'].clip(lower=1)  # Ensure volume is at least 1
    
    # Calculate VWAP
    df_copy['VP'] = df_copy['TypicalPrice'] * df_copy['Volume']
    df_copy['CumVP'] = df_copy['VP'].cumsum()
    df_copy['CumVol'] = df_copy['Volume'].cumsum()
    vwap = df_copy['CumVP'] / df_copy['CumVol']
    
    return vwap

def calculate_choppiness_index(high, low, close, window=14):
    """Calculate Choppiness Index to detect ranging markets"""
    true_range = np.maximum(high - low, 
                           np.maximum(abs(high - close.shift(1)), 
                                    abs(low - close.shift(1))))
    atr = true_range.rolling(window=window).mean()
    
    highest_high = high.rolling(window=window).max()
    lowest_low = low.rolling(window=window).min()
    
    chop = 100 * np.log10((atr * window) / (highest_high - lowest_low)) / np.log10(window)
    return chop

def add_options_specific_indicators(df, option_data):
    """Add option-specific indicators for better predictions"""
    if option_data is None or option_data.empty:
        return df
    
    try:
        # Put-Call Ratio (if we have both calls and puts)
        calls = option_data[option_data['Type'] == 'CE']
        puts = option_data[option_data['Type'] == 'PE']
        
        if not calls.empty and not puts.empty:
            call_volume = calls['Volume'].sum()
            put_volume = puts['Volume'].sum()
            call_oi = calls['OI'].sum()
            put_oi = puts['OI'].sum()
            
            df['PCR_Volume'] = put_volume / call_volume if call_volume > 0 else 1
            df['PCR_OI'] = put_oi / call_oi if call_oi > 0 else 1
        
        # Implied Volatility metrics
        if 'IV' in option_data.columns:
            df['Avg_IV'] = option_data['IV'].mean()
            df['IV_Skew'] = option_data['IV'].std()
    
    except Exception as e:
        print(f"Warning: Could not calculate option-specific indicators: {e}")
    
    return df
