import logging
import os
import threading
from flask import Flask
import yfinance as yf
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Web Server Render ke liye
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Exness Gold Trading Bot Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# Telegram Bot Token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8969292356:AAFovvKTKKf1nUG1l5IYBDZtutwPsJMalJE")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

last_signal = None

def get_exness_gold_analysis():
    # Exness Real Time Gold Spot Price Data
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
    chat_id = update.message.chat_id
    context.job_queue.run_repeating(auto_market_monitor, interval=60, first=5, chat_id=chat_id)
    
    await update.message.reply_text(
        "⚡ **Exness Gold Automation Active!**\n\n"
        "Bot har 1 minute me Exness Gold Market check karega.\n"
        "Jab bhi BUY ya SELL signal milega, aapko instant alert bhej dega!"
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

# Automatic Background Job (JobQueue)
async def auto_market_monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_signal
    chat_id = context.job.chat_id
    
    price, rsi, signal = get_exness_gold_analysis()
    if signal in ["BUY", "SELL"] and signal != last_signal:
        alert_msg = (
            f"🚨 **EXNESS TRADE SIGNAL ALERT** 🚨\n\n"
            f"🪙 **Pair:** Gold (XAU/USD)\n"
            f"💥 **Signal:** {signal} NOW\n"
            f"💵 **Price:** ${price:.2f}\n"
            f"📊 **RSI:** {rsi:.2f}\n\n"
            f"⚠️ Exness me immediate {signal} trade laga sakte hain!"
        )
        await context.bot.send_message(chat_id=chat_id, text=alert_msg, parse_mode='Markdown')
        last_signal = signal

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    print("Bot starting polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
