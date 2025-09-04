#!/bin/bash

echo "🚀 Starting Bitcoin Options Alert System in Cloud..."

# Check if model exists, if not train it
if [ ! -f "models/trade_model.pkl" ]; then
    echo "📊 Training model for the first time..."
    python main.py --prepare
    python main.py --train
    echo "✅ Model training completed"
fi

# Start the cloud-compatible main application
echo "🎯 Starting alert system with web interface..."
python cloud_main.py