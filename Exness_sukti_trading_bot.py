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
    return "Exness Sukti Gold AI Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# Token from Environment or Fallback
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8790173607:AAFgcstrywXtbMMfADLi9R3xHLnY6cbkjA8")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_gold_status():
    try:
        df = yf.download(tickers='GC=F', period='2d', interval='5m')
        if df.empty:
            df = yf.download(tickers='XAUUSD=X', period='2d', interval='5m')
            
        if df.empty:
            return "Market price fetch nahi ho pa raha hai. Please try again."
            
        close = df['Close'].squeeze()
        high = df['High'].squeeze()
        low = df['Low'].squeeze()
        
        current_price = float(close.iloc[-1])
        rsi = float(ta.momentum.RSIIndicator(close=close, window=14).rsi().iloc[-1])
        atr = float(ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range().iloc[-1])
        
        signal = "NEUTRAL (WAIT)"
        sl = current_price
        tp = current_price
        
        if rsi < 35:
            signal = "🟢 BUY NOW"
            sl = current_price - (1.5 * atr)
            tp = current_price + (2.5 * atr)
        elif rsi > 65:
            signal = "🔴 SELL NOW"
            sl = current_price + (1.5 * atr)
            tp = current_price - (2.5 * atr)
            
        msg = (
            f"🎯 **EXNESS GOLD (XAU/USD) ANALYSIS**\n\n"
            f"💵 Live Price: **${current_price:.2f}**\n"
            f"📉 RSI: **{rsi:.2f}**\n"
            f"📊 Signal: **{signal}**\n\n"
        )
        if signal != "NEUTRAL (WAIT)":
            msg += f"🛑 Recommended SL: **${sl:.2f}**\n🎯 Recommended TP: **${tp:.2f}**\n"
        else:
            msg += "💡 Abhi clear entry nahi hai, market wait karne ka ishara kar rahi hai."
            
        return msg
    except Exception as e:
        return f"Error: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Namaste! Exness Sukti Gold AI Active Hai!**\n\n"
        "Main aapka Gold (XAUUSD) AI Trading Mentor hu.\n\n"
        "👉 Check Market & Trade Signal: /status"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_gold_status()
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    print("Bot started polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
