# Bitcoin Options Alert System 🚀

**High-Accuracy Bitcoin Options Trading Alerts via Telegram**

This system provides real-time Bitcoin options trading signals with a target accuracy of 90%+ using advanced machine learning and technical analysis.

## 🎯 Features

- **90%+ Accuracy Target**: Advanced ensemble ML models with comprehensive feature engineering
- **Real-time Alerts**: Telegram notifications for BTC options (CALL/PUT) signals
- **Multi-source Data**: Enhanced data fetching from multiple APIs for reliability
- **Advanced Indicators**: 40+ technical indicators optimized for Bitcoin trading
- **Options Profitability**: Actual profit/loss based signal labeling
- **24/7 Operation**: Designed for cryptocurrency markets

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Your Telegram Chat ID
```bash
python get_telegram_chat_id.py
```
Message your bot and copy the chat ID to `config.yaml`

### 3. Run Complete Setup
```bash
python setup_btc_system.py
```
This will test everything and train your model.

### 4. Start Alert System
```bash
python main.py --alert
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

- **telegram_chat_id**: Your Telegram chat ID
- **signal_confidence_threshold**: Minimum confidence (85% recommended)
- **fetch_interval**: How often to check for signals (5 minutes recommended)
- **option_type**: "call", "put", or "both"
- **min_profit_threshold**: Minimum expected profit (25% recommended)

## 🔧 Commands

```bash
# Complete pipeline (recommended for first run)
python main.py --all

# Individual steps
python main.py --prepare    # Fetch and prepare data
python main.py --train      # Train the model
python main.py --alert      # Start alert system

# Setup and testing
python setup_btc_system.py  # Complete system test
python get_telegram_chat_id.py  # Get Telegram chat ID
```

## 🎯 Achieving 90%+ Accuracy

### Model Features
- **Ensemble Methods**: Random Forest + XGBoost + LightGBM + Gradient Boosting
- **40+ Technical Indicators**: Multi-timeframe RSI, MACD, Bollinger Bands, VWAP, etc.
- **Profit-based Labeling**: Signals based on actual option profitability
- **Advanced Feature Engineering**: 60+ engineered features including lag variables

### Signal Quality
- **High Confidence**: Only 85%+ model confidence signals
- **Profit Threshold**: Minimum 25% expected profit
- **Volume Filter**: Minimum option volume and open interest
- **Volatility Filter**: 3% minimum price movement

## ⚠️ Important Notes

1. **Paper Trading First**: Test signals before real trading
2. **Risk Management**: Never risk more than you can afford to lose
3. **Market Conditions**: Performance varies with volatility
4. **Continuous Monitoring**: Check performance regularly

---

**⚡ Ready to achieve 90%+ accuracy in Bitcoin options trading!**

## Features

- Fetches real-time Bitcoin/USD or Nifty index data and option chain information
- Automatically identifies weekly expiry options
- Calculates technical indicators (RSI, MACD, Bollinger Bands, ATR, VWAP)
- Trains a machine learning model to predict specific CALL or PUT option buy signals
- Sends high-confidence trade alerts with recommended strike prices via Telegram
- Configurable market hours (24/7 for crypto or standard market hours for indices)
- Configurable parameters via config.yaml

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Telegram bot token (get from [@BotFather](https://t.me/botfather))
- Telegram chat ID (use [@userinfobot](https://t.me/userinfobot))

### Installation

1. Clone the repository or download the source code

2. Create and activate a virtual environment (recommended)
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Configure the system by editing `config.yaml`:
   ```yaml
   telegram_bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
   telegram_chat_id: "YOUR_TELEGRAM_CHAT_ID"
   use_weekly_options: true  # Set to true to use weekly expiry options
   weekly_expiry_day: "friday"  # Day of the week for weekly expiry (friday for Bitcoin, thursday for Nifty)
   strike_gap: 1000  # Strike price gap (1000 for Bitcoin, 50 for Nifty)
   index_symbol: "BTC-USD"  # Use "BTC-USD" for Bitcoin or "^NSEI" for Nifty
   index_name: "BITCOIN"  # Use "BITCOIN" or "NIFTY"
   fetch_interval: 15  # in minutes
   signal_confidence_threshold: 75  # Minimum confidence percentage to send alerts
   option_type: "both"  # Options: "call", "put", or "both"
   crypto_exchange: "deribit"  # Only needed for crypto trading
   limit_trading_hours: false  # Set to true to limit crypto alerts to specific hours
   ```

## Usage

### Running the Complete Pipeline

To run the complete pipeline (data preparation, model training, and alert system):

```
python main.py --all
```

or simply:

```
python main.py
```

### Running Individual Components

1. Prepare data only:
   ```
   python main.py --prepare
   ```

2. Train model only (requires prepared data):
   ```
   python main.py --train
   ```

3. Start alert system only (requires trained model):
   ```
   python main.py --alert
   ```

## How It Works

1. **Data Collection**: The system fetches Bitcoin/USD or Nifty intraday data and option chain information.

2. **Feature Engineering**: Technical indicators (RSI, MACD, Bollinger Bands, ATR, VWAP) are calculated and combined with option data.

3. **Model Training**: A Random Forest classifier is trained to predict specific call/put buy signals based on historical data.

4. **Signal Generation**: The trained model analyzes real-time market data to generate trade signals with specific option type recommendations (CALL or PUT).

5. **Alert Delivery**: High-confidence signals with recommended strike prices for weekly expiry options are sent to your Telegram chat.

## Project Structure

- `main.py`: Main entry point for running the system
- `config.yaml`: Configuration settings
- `trade_alert_system.py`: Handles signal generation and Telegram alerts
- `train_model.py`: Trains the prediction model
- `merge_data.py`: Combines index and option data
- `label_data.py`: Labels historical data for training
- `utils/`: Utility functions for data fetching and indicators
  - `fetch_intraday.py`: Fetches Bitcoin/USD or Nifty intraday data
  - `fetch_option_chain.py`: Fetches option chain data from Deribit (for Bitcoin) or NSE (for Nifty)
  - `indicators.py`: Calculates technical indicators with crypto-specific optimizations

## Customization

- Switch between Bitcoin and Nifty trading by changing the `index_symbol` and related settings in `config.yaml`
- Adjust the `fetch_interval` in `config.yaml` to change how frequently signals are generated
- Modify the confidence threshold in `config.yaml` to control alert frequency
- For crypto trading, enable/disable 24/7 alerts with the `limit_trading_hours` setting
- Add additional technical indicators in `utils/indicators.py`
- Experiment with different ML models in `train_model.py`

## Disclaimer

This system is for educational purposes only. Trading financial instruments, especially cryptocurrencies, involves significant risk, and past performance is not indicative of future results. Cryptocurrency markets are highly volatile and can experience extreme price movements. Always conduct your own research before making investment decisions.