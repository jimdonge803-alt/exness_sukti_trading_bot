import logging
import os
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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

last_signal = None

def get_exness_gold_analysis():
    try:
        # Fetch Gold Data
        df = yf.download(tickers='GC=F', period='5d', interval='5m')
        if df.empty:
            df = yf.download(tickers='XAUUSD=X', period='5d', interval='5m')
            
        if df.empty:
            return 4181.10, 50.0, "NEUTRAL (WAIT)"
        
        close_prices = df['Close'].squeeze()
        rsi_series = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()
        
        current_rsi = float(rsi_series.iloc[-1])
        current_price = float(close_prices.iloc[-1])

        signal = "NEUTRAL (WAIT)"
        if current_rsi <= 32:
            signal = "🟢 BUY SIGNAL"
        elif current_rsi >= 68:
            signal = "🔴 SELL SIGNAL"
            
        return current_price, current_rsi, signal
    except Exception as e:
        logging.error(f"Data error: {e}")
        return 4181.10, 50.0, "NEUTRAL (WAIT)"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    # Existing job handle karne ke liye
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()
        
    context.job_queue.run_repeating(auto_market_monitor, interval=60, first=3, chat_id=chat_id, name=str(chat_id))
    
    await update.message.reply_text(
        "⚡ **Exness Gold AI Assistant Active!**\n\n"
        "✅ Automatic Live Market Monitoring Started!\n"
        "Bot har 1 minute me Gold market check karega.\n"
        "Jab bhi BUY ya SELL signal milega, aapko notification mil jayegi.\n\n"
        "📌 Command: /status - Instant Gold Price Check"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price, rsi, signal = get_exness_gold_analysis()
    
    msg = (
        f"📊 **Exness Gold (XAU/USD) Analysis**\n\n"
        f"💵 Live Price: ${price:.2f}\n"
        f"📉 RSI (14): {rsi:.2f}\n"
        f"💡 Recommendation: **{signal}**"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def auto_market_monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_signal
    chat_id = context.job.chat_id
    
    price, rsi, signal = get_exness_gold_analysis()
    if signal in ["🟢 BUY SIGNAL", "🔴 SELL SIGNAL"] and signal != last_signal:
        alert_msg = (
            f"🚨 **EXNESS TRADE ALERT** 🚨\n\n"
            f"🪙 Pair: Gold (XAU/USD)\n"
            f"💥 Signal: **{signal}**\n"
            f"💵 Price: ${price:.2f}\n"
            f"📊 RSI: {rsi:.2f}\n\n"
            f"⚡ Exness app me immediate trade place kar sakte hain!"
        )
        await context.bot.send_message(chat_id=chat_id, text=alert_msg, parse_mode='Markdown')
        last_signal = signal

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
