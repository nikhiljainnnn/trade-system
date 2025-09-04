import os
import time
import schedule
import threading
from flask import Flask, jsonify, request
from datetime import datetime
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your existing modules
from trade_alert_system import generate_signals, send_alert
from main import load_config

app = Flask(__name__)

# Global variable to track system status
system_status = {
    "running": True,
    "last_signal_time": None,
    "total_signals_sent": 0,
    "uptime_start": datetime.now(),
    "errors": []
}

@app.route('/')
def health_check():
    """Health check endpoint for cloud platforms"""
    uptime = datetime.now() - system_status["uptime_start"]
    return jsonify({
        "status": "healthy",
        "service": "Bitcoin Options Alert System",
        "version": "1.0.0",
        "uptime_hours": round(uptime.total_seconds() / 3600, 2),
        "last_signal": system_status["last_signal_time"],
        "total_signals": system_status["total_signals_sent"],
        "running": system_status["running"]
    })

@app.route('/status')
def get_status():
    """Detailed status endpoint"""
    config = load_config()
    uptime = datetime.now() - system_status["uptime_start"]
    
    return jsonify({
        "system_status": system_status,
        "config": {
            "fetch_interval": config.get('fetch_interval', 10),
            "confidence_threshold": config.get('signal_confidence_threshold', 85),
            "telegram_chat_id": config.get('telegram_chat_id', 'configured'),
            "index_symbol": config.get('index_symbol', 'BTC-USD')
        },
        "uptime_details": {
            "start_time": system_status["uptime_start"].isoformat(),
            "current_time": datetime.now().isoformat(),
            "uptime_seconds": uptime.total_seconds()
        }
    })

@app.route('/trigger', methods=['POST'])
def manual_trigger():
    """Manually trigger signal generation"""
    try:
        generate_signals()
        system_status["last_signal_time"] = datetime.now().isoformat()
        system_status["total_signals_sent"] += 1
        return jsonify({"status": "success", "message": "Signal generation triggered manually"})
    except Exception as e:
        system_status["errors"].append({
            "time": datetime.now().isoformat(),
            "error": str(e)
        })
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/logs')
def get_logs():
    """Get recent log entries"""
    try:
        if os.path.exists('alerts.log'):
            with open('alerts.log', 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-50:]  # Last 50 lines
            return jsonify({"logs": recent_logs})
        else:
            return jsonify({"logs": ["No log file found"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration"""
    if request.method == 'GET':
        config = load_config()
        # Don't expose sensitive information
        safe_config = {k: v for k, v in config.items() if 'token' not in k.lower()}
        return jsonify(safe_config)
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            # Update config file (be careful with this in production)
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            # Only allow certain fields to be updated
            allowed_fields = ['fetch_interval', 'signal_confidence_threshold', 'option_type']
            for field in allowed_fields:
                if field in new_config:
                    config[field] = new_config[field]
            
            with open('config.yaml', 'w') as f:
                yaml.dump(config, f)
            
            return jsonify({"status": "success", "message": "Configuration updated"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

def enhanced_generate_signals():
    """Enhanced signal generation with error tracking"""
    try:
        generate_signals()
        system_status["last_signal_time"] = datetime.now().isoformat()
        system_status["total_signals_sent"] += 1
        
        # Keep only last 10 errors
        if len(system_status["errors"]) > 10:
            system_status["errors"] = system_status["errors"][-10:]
            
    except Exception as e:
        error_entry = {
            "time": datetime.now().isoformat(),
            "error": str(e),
            "type": type(e).__name__
        }
        system_status["errors"].append(error_entry)
        print(f"Error in signal generation: {e}")
        
        # Send error alert if too many consecutive errors
        if len(system_status["errors"]) >= 3:
            recent_errors = system_status["errors"][-3:]
            if all(abs(datetime.fromisoformat(err["time"].replace('Z', '+00:00')).timestamp() - 
                      datetime.now().timestamp()) < 3600 for err in recent_errors):
                send_alert(f"⚠️ System Alert: Multiple errors in the last hour. Last error: {str(e)[:100]}")

def run_scheduler():
    """Run the scheduling system in background"""
    config = load_config()
    fetch_interval = config.get('fetch_interval', 10)
    
    print(f"🕐 Scheduling signal generation every {fetch_interval} minutes")
    schedule.every(fetch_interval).minutes.do(enhanced_generate_signals)
    
    # Also run a health check every hour
    schedule.every().hour.do(lambda: print(f"💓 System heartbeat: {datetime.now()}"))
    
    while system_status["running"]:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    print("🚀 Starting Bitcoin Options Alert System - Cloud Version")
    
    # Send startup notification
    try:
        send_alert("🌟 Bitcoin Options Alert System started in the cloud! 24/7 operation active.")
    except:
        print("Could not send startup notification - will continue anyway")
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Get port from environment (Railway sets this automatically)
    port = int(os.environ.get('PORT', 8080))
    
    print(f"🌐 Starting web server on port {port}")
    print(f"📱 Telegram alerts configured for chat ID: {load_config().get('telegram_chat_id', 'Not configured')}")
    print(f"💹 Monitoring: {load_config().get('index_symbol', 'BTC-USD')}")
    
    # Start Flask app (Railway handles the PORT automatically)
    app.run(host='0.0.0.0', port=port, debug=False)