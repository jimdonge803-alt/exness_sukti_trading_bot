import logging
import os
import threading
from flask import Flask
import yfinance as yf
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Render Web Server (Dummy Server for Free Hosting)
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Exness Gold Trading Bot is Active & Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# Telegram Bot Token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8969292356:AAFovvKTKKf1nUG1l5IYBDZtutwPsJMalJE")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_gold_signal():
    df = yf.download(tickers='GC=F', period='1d', interval='15m')
    if df.empty:
        return "Market Data nahi mil raha hai."
    
    rsi_series = ta.momentum.RSIIndicator(close=df['Close'].squeeze(), window=14).rsi()
    current_rsi = rsi_series.iloc[-1]
    current_price = df['Close'].iloc[-1].item()
    
    signal = "NEUTRAL (WAIT)"
    if current_rsi < 30:
        signal = "🟢 BUY SIGNAL (Oversold Area)"
    elif current_rsi > 70:
        signal = "🔴 SELL SIGNAL (Overbought Area)"
        
    response = (
        f"📊 **GOLD (XAU/USD) Analysis**\n\n"
        f"💵 Current Price: ${current_price:.2f}\n"
        f"📈 RSI (14): {current_rsi:.2f}\n"
        f"💡 Recommendation: **{signal}**"
    )
    return response

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! Mai aapka Gold Trading AI Assistant hu. Commands:\n/status - Live Gold Analysis")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analysis = get_gold_signal()
    await update.message.reply_text(analysis, parse_mode='Markdown')

def main():
    # Flask thread start karein
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Telegram Bot Start Karein
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    print("Bot chalu ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
