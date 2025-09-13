#!/usr/bin/env python3
"""
Web Service Wrapper for Telegram Bot on Render
Runs bot.py in a background subprocess and exposes health check endpoints
"""

from flask import Flask, jsonify
import os
import sys
import logging
from datetime import datetime, timezone
import subprocess
import threading

# ------------------- Logging -------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ------------------- Environment -------------------
required_vars = ["BOT_TOKEN", "CHANNEL_ID", "BOT_USERNAME", "ADMIN_ID_1"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"❌ Missing environment variables: {missing_vars}")
    sys.exit(1)

# ------------------- Bot Status -------------------
bot_status = {"running": False, "start_time": None, "last_activity": None}

# ------------------- Flask App -------------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    """Basic health check"""
    return jsonify({
        "status": "healthy",
        "service": "Telegram Confession Bot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bot_running": bot_status["running"],
        "uptime": (datetime.now(timezone.utc) - bot_status["start_time"]).total_seconds() if bot_status["start_time"] else 0
    })

@app.route("/health", methods=["GET"])
def health():
    """Detailed health check"""
    return jsonify({
        "status": "ok" if bot_status["running"] else "error",
        "bot_status": bot_status,
        "environment": {var: bool(os.getenv(var)) for var in required_vars}
    })

@app.route("/ping", methods=["GET"])
def ping():
    """Simple ping endpoint"""
    return "pong"

# ------------------- Database Setup -------------------
def setup_database():
    """Run database migrations and setup"""
    try:
        logger.info("🗄️ Setting up database...")
        
        # Import and run migrations
        from migration import run_database_migrations
        run_database_migrations()
        
        logger.info("✅ Database setup completed")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

# ------------------- Start Bot -------------------
def run_bot():
    """Start bot.py as a non-blocking subprocess"""
    try:
        logger.info("🚀 Starting Telegram bot subprocess...")
        bot_status["start_time"] = datetime.now(timezone.utc)
        bot_status["running"] = True

        # First, setup database
        setup_database()

        # Start bot.py without blocking the main thread
        subprocess.Popen([sys.executable, "bot.py"])

    except Exception as e:
        logger.error(f"❌ Bot subprocess error: {e}")
        bot_status["running"] = False
        raise

# ------------------- Main -------------------
if __name__ == "__main__":
    # Start bot in a background daemon thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Start Flask server immediately so Render detects the open port
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🌐 Starting web server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


