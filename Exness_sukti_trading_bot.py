import logging
import os
import threading
from flask import Flask
import yfinance as yf
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Render Free Hosting Flask Server
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Exness Gold Bot is Running Free & Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8969292356:AAFovvKTKKf1nUG1l5IYBDZtutwPsJMalJE")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_gold_analysis():
    try:
        df = yf.download(tickers='GC=F', period='2d', interval='5m')
        if df.empty:
            df = yf.download(tickers='XAUUSD=X', period='2d', interval='5m')
            
        if df.empty:
            return "Market Data abhi unavailable hai (Weekend/Market Closed)."
        
        close_prices = df['Close'].squeeze()
        rsi_series = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()
        
        current_rsi = float(rsi_series.iloc[-1])
        current_price = float(close_prices.iloc[-1])

        signal = "NEUTRAL (WAIT)"
        if current_rsi <= 32:
            signal = "🟢 BUY SIGNAL"
        elif current_rsi >= 68:
            signal = "🔴 SELL SIGNAL"
            
        return (
            f"📊 **Exness Gold (XAU/USD) Live Status**\n\n"
            f"💵 Price: ${current_price:.2f}\n"
            f"📈 RSI (14): {current_rsi:.2f}\n"
            f"💡 Signal: **{signal}**"
        )
    except Exception as e:
        return f"Market analyze karne me error aaya: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Namaste! Exness Gold Bot Active Ho Gaya Hai!**\n\n"
        "Commands:\n"
        "👉 /status - Live Gold (XAUUSD) Price & Buy/Sell Recommendation Check Karein."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response_msg = get_gold_analysis()
    await update.message.reply_text(response_msg, parse_mode='Markdown')

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    print("Bot polling started...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
