import logging
import os
import time
import asyncio
import threading
from flask import Flask
import yfinance as yf
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Exness Gold Trading Bot Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8969292356:AAFovvKTKKf1nUG1l5IYBDZtutwPsJMalJE")
# Aapka Telegram Chat ID jahan auto alerts aayenge
CHAT_ID = None  

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

last_signal = None

def get_exness_gold_analysis():
    # Fetch Gold Spot Price
    df = yf.download(tickers='XAUUSD=X', period='1d', interval='5m')
    if df.empty:
        df = yf.download(tickers='GC=F', period='1d', interval='5m')
        
    if df.empty:
        return None, None, "Market Data Error"
    
    close_prices = df['Close'].squeeze()
    rsi_series = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()
    
    current_rsi = rsi_series.iloc[-1]
    current_price = close_prices.iloc[-1]

    signal = "HOLD"
    if current_rsi <= 32:
        signal = "BUY"
    elif current_rsi >= 68:
        signal = "SELL"
        
    return current_price, current_rsi, signal

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.message.chat_id
    await update.message.reply_text(
        "⚡ **Exness Gold Automation Active!**\n\n"
        "Mai har 1 minute me Exness Gold Market analyze karunga.\n"
        "Jab bhi BUY ya SELL ka solid signal milega, mai aapko instant notification bhej dunga!"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price, rsi, signal = get_exness_gold_analysis()
    if price is None:
        await update.message.reply_text("Error fetching market price.")
        return
    
    msg = (
        f"📊 **Exness Gold (XAUUSD) Status**\n\n"
        f"💰 Price: ${price:.2f}\n"
        f"📉 RSI: {rsi:.2f}\n"
        f"🎯 Action: **{signal}**"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

# Background Loop jo continuous market analyze karke auto-alert bhejega
async def auto_market_monitor(app):
    global last_signal, CHAT_ID
    while True:
        try:
            if CHAT_ID:
                price, rsi, signal = get_exness_gold_analysis()
                if signal in ["BUY", "SELL"] and signal != last_signal:
                    alert_msg = (
                        f"🚨 **EXNESS TRADE SIGNAL ALERT** 🚨\n\n"
                        f"🪙 **Pair:** Gold (XAU/USD)\n"
                        f"💥 **Signal:** {signal} NOW\n"
                        f"💵 **Price:** ${price:.2f}\n"
                        f"📊 **RSI:** {rsi:.2f}\n\n"
                        f"⚠️ Exness me immediate {signal} entry le sakte hain!"
                    )
                    await app.bot.send_message(chat_id=CHAT_ID, text=alert_msg, parse_mode='Markdown')
                    last_signal = signal
        except Exception as e:
            logging.error(f"Error in monitor: {e}")
        await asyncio.sleep(60) # Har 60 second me check karega

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    # Run auto background monitoring task
    loop = asyncio.get_event_loop()
    loop.create_task(auto_market_monitor(app))
    
    print("Bot fully automated and active...")
    app.run_polling()

if __name__ == '__main__':
    main()
