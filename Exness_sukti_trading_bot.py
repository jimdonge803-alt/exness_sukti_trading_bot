import logging
import os
import threading
from flask import Flask
import yfinance as yf
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Render Web Server Setup
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Exness Gold AI Mentor Bot is Running Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8969292356:AAFovvKTKKf1nUG1l5IYBDZtutwPsJMalJE")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

last_signal = None

def get_advanced_gold_setup():
    try:
        # Fetch 15-minute candle data for Gold
        df = yf.download(tickers='GC=F', period='5d', interval='15m')
        if df.empty:
            df = yf.download(tickers='XAUUSD=X', period='5d', interval='15m')
            
        if df.empty:
            return None
        
        close = df['Close'].squeeze()
        high = df['High'].squeeze()
        low = df['Low'].squeeze()
        
        # Technical Indicators
        rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi().iloc[-1]
        ema_fast = ta.trend.EMAIndicator(close=close, window=9).ema_indicator().iloc[-1]
        ema_slow = ta.trend.EMAIndicator(close=close, window=21).ema_indicator().iloc[-1]
        atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range().iloc[-1]
        
        current_price = float(close.iloc[-1])
        rsi_val = float(rsi)
        
        action = "WAIT"
        sl = 0.0
        tp1 = 0.0
        tp2 = 0.0
        
        # Strategy Logic: EMA Crossover + RSI Confirmation
        if rsi_val < 38 and ema_fast > ema_slow:
            action = "🟢 BUY"
            sl = current_price - (1.5 * atr)
            tp1 = current_price + (1.5 * atr)
            tp2 = current_price + (3.0 * atr)
        elif rsi_val > 62 and ema_fast < ema_slow:
            action = "🔴 SELL"
            sl = current_price + (1.5 * atr)
            tp1 = current_price - (1.5 * atr)
            tp2 = current_price - (3.0 * atr)
            
        return {
            "price": current_price,
            "rsi": rsi_val,
            "action": action,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "atr": atr
        }
    except Exception as e:
        logging.error(f"Error calculating setup: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    # Clean previous background tasks
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()
        
    # Auto-check market every 60 seconds
    context.job_queue.run_repeating(auto_market_monitor, interval=60, first=3, chat_id=chat_id, name=str(chat_id))
    
    await update.message.reply_text(
        "⚡ **Exness Gold AI Trading Mentor Active!**\n\n"
        "✅ Live Market Monitoring Started (15M Timeframe).\n"
        "Bot continuous market scan karega aur proper **SL / TP Setup** ke saath alert bhejega.\n\n"
        "👉 Check Live Status: /status"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_advanced_gold_setup()
    if not data:
        await update.message.reply_text("Market data abhi unavailable hai, please thodi der me try karein.")
        return
        
    price = data['price']
    rsi = data['rsi']
    action = data['action']
    
    if action in ["🟢 BUY", "🔴 SELL"]:
        msg = (
            f"🎯 **EXNESS GOLD TRADING SETUP**\n\n"
            f"🪙 Pair: **XAU/USD (Gold)**\n"
            f"📊 Action: **{action} NOW**\n"
            f"💵 Entry Price: **${price:.2f}**\n\n"
            f"🛑 Stop Loss (SL): **${data['sl']:.2f}**\n"
            f"🎯 Take Profit 1 (TP1): **${data['tp1']:.2f}**\n"
            f"🚀 Take Profit 2 (TP2): **${data['tp2']:.2f}**\n\n"
            f"📉 RSI: {rsi:.2f}\n"
            f"💡 Recommended Lot Size: **0.01 - 0.02** per $100 Balance"
        )
    else:
        msg = (
            f"📊 **Exness Gold (XAU/USD) Live Status**\n\n"
            f"💵 Live Price: **${price:.2f}**\n"
            f"📉 RSI (14): **{rsi:.2f}**\n"
            f"💡 Current Status: **NEUTRAL (WAIT FOR CLEAR SETUP)**\n\n"
            f"⏳ AI Mentor continuous market watch kar raha hai. Jaise hi confirm setup milega, auto-alert aa jayega!"
        )
        
    await update.message.reply_text(msg, parse_mode='Markdown')

async def auto_market_monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_signal
    chat_id = context.job.chat_id
    
    data = get_advanced_gold_setup()
    if data and data['action'] in ["🟢 BUY", "🔴 SELL"]:
        if data['action'] != last_signal:
            alert_msg = (
                f"🚨 **NEW EXNESS TRADE ALERT** 🚨\n\n"
                f"🪙 Pair: **Gold (XAU/USD)**\n"
                f"💥 Signal: **{data['action']}**\n"
                f"💵 Entry: **${data['price']:.2f}**\n\n"
                f"🛑 SL: **${data['sl']:.2f}**\n"
                f"🎯 TP1: **${data['tp1']:.2f}**\n"
                f"🚀 TP2: **${data['tp2']:.2f}**\n\n"
                f"⚡ Exness App open karke immediate trade place kar sakte hain!"
            )
            await context.bot.send_message(chat_id=chat_id, text=alert_msg, parse_mode='Markdown')
            last_signal = data['action']

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    print("Bot is running smoothly...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
