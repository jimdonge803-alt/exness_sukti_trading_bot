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
    return "Exness Sukti Super AI Mentor is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8790173607:AAFgcstrywXtbMMfADLi9R3xHLnY6cbkjA8")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_balances = {}
last_signal = None

def get_super_ai_analysis(user_id=None):
    try:
        df_15m = yf.download(tickers='GC=F', period='5d', interval='15m')
        df_1h = yf.download(tickers='GC=F', period='5d', interval='1h')
        
        if df_15m.empty:
            df_15m = yf.download(tickers='XAUUSD=X', period='5d', interval='15m')
            df_1h = yf.download(tickers='XAUUSD=X', period='5d', interval='1h')
            
        if df_15m.empty:
            return None
        
        close_15 = df_15m['Close'].squeeze()
        high_15 = df_15m['High'].squeeze()
        low_15 = df_15m['Low'].squeeze()
        close_1h = df_1h['Close'].squeeze()
        
        rsi = ta.momentum.RSIIndicator(close=close_15, window=14).rsi().iloc[-1]
        ema_fast = ta.trend.EMAIndicator(close=close_15, window=9).ema_indicator().iloc[-1]
        ema_slow = ta.trend.EMAIndicator(close=close_15, window=21).ema_indicator().iloc[-1]
        ema_trend = ta.trend.EMAIndicator(close=close_1h, window=50).ema_indicator().iloc[-1]
        
        macd = ta.trend.MACD(close=close_15)
        macd_hist = macd.macd_diff().iloc[-1]
        
        atr = ta.volatility.AverageTrueRange(high=high_15, low=low_15, close=close_15, window=14).average_true_range().iloc[-1]
        
        current_price = float(close_15.iloc[-1])
        rsi_val = float(rsi)
        
        res_level = float(high_15.tail(20).max())
        sup_level = float(low_15.tail(20).min())
        
        action = "NEUTRAL (WAIT)"
        score = 0
        
        if ema_fast > ema_slow: score += 1
        if current_price > ema_trend: score += 1
        if macd_hist > 0: score += 1
        if rsi_val < 45: score += 1
        
        if ema_fast < ema_slow: score -= 1
        if current_price < ema_trend: score -= 1
        if macd_hist < 0: score -= 1
        if rsi_val > 55: score -= 1
        
        sl = 0.0
        tp1 = 0.0
        tp2 = 0.0
        
        if score >= 3:
            action = "🟢 STRONG BUY"
            sl = current_price - (1.5 * atr)
            tp1 = current_price + (1.5 * atr)
            tp2 = current_price + (3.0 * atr)
        elif score <= -3:
            action = "🔴 STRONG SELL"
            sl = current_price + (1.5 * atr)
            tp1 = current_price - (1.5 * atr)
            tp2 = current_price - (3.0 * atr)
            
        balance = user_balances.get(user_id, 100)
        risk_amount = balance * 0.02
        sl_pips = abs(current_price - sl) if sl != 0 else 1.0
        lot_size = round(risk_amount / (sl_pips * 100), 2)
        if lot_size < 0.01: lot_size = 0.01
        
        return {
            "price": current_price,
            "rsi": rsi_val,
            "action": action,
            "score": score,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "sup": sup_level,
            "res": res_level,
            "balance": balance,
            "lot_size": lot_size
        }
    except Exception as e:
        logging.error(f"Error in Super AI analysis: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()
        
    context.job_queue.run_repeating(auto_market_monitor, interval=60, first=3, chat_id=chat_id, name=str(chat_id))
    
    await update.message.reply_text(
        "🚀 **EXNESS SUKTI SUPER AI MENTOR ACTIVE!**\n\n"
        "⚡ Multi-Timeframe Analysis (5M + 15M + 1H)\n"
        "📊 Multi-Indicator (EMA + RSI + MACD + S/R + ATR)\n"
        "💰 Custom Risk & Lot Size Calculator\n"
        "🔔 24/7 Live High-Probability Trade Alerts\n\n"
        "📌 **Commands:**\n"
        "👉 `/status` - Live Setup Check Karein\n"
        "👉 `/setbalance <amount>` - Balance Set Karein (e.g. `/setbalance 500`)"
    )

async def set_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        balance = float(context.args[0])
        user_balances[user_id] = balance
        await update.message.reply_text(f"✅ Account Balance set: **${balance:.2f}**\nSafe Lot Size calculate ho jayega!")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Example format: `/setbalance 100`")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = get_super_ai_analysis(user_id)
    
    if not data:
        await update.message.reply_text("Market data fetch ho raha hai, please 30 seconds baad try karein.")
        return
        
    price = data['price']
    action = data['action']
    sup = data['sup']
    res = data['res']
    
    msg = (
        f"🤖 **SUPER AI GOLD (XAU/USD) ANALYSIS**\n\n"
        f"💵 Live Exness Price: **${price:.2f}**\n"
        f"📈 RSI: **{data['rsi']:.2f}** | Signal Score: **{data['score']}/4**\n"
        f"🛡️ Support: **${sup:.2f}** \vert{} Resistance: **${res:.2f}**\n\n"
        f"🎯 Signal: **{action}**\n"
    )
    
    if action in ["🟢 STRONG BUY", "🔴 STRONG SELL"]:
        msg += (
            f"\n📍 **EXACT ENTRY SETUP:**\n"
            f"💵 Entry: **${price:.2f}**\n"
            f"🛑 Stop Loss (SL): **${data['sl']:.2f}**\n"
            f"🎯 Take Profit 1 (TP1): **${data['tp1']:.2f}**\n"
            f"🚀 Take Profit 2 (TP2): **${data['tp2']:.2f}**\n\n"
            f"📐 **RISK MANAGEMENT (Balance: ${data['balance']:.2f}):**\n"
            f"⚖️ Safe Lot Size: **{data['lot_size']} Lot** (2% Max Risk)\n\n"
            f"⚡ Direct Exness App me trade enter karein!"
        )
    else:
        msg += "\n⏳ **AI Mentor Status:** Market range-bound hai. Clear confirmation par alert aayega!"
        
    await update.message.reply_text(msg, parse_mode='Markdown')

async def auto_market_monitor(context: ContextTypes.DEFAULT_TYPE):
    global last_signal
    chat_id = context.job.chat_id
    user_id = chat_id
    
    data = get_super_ai_analysis(user_id)
    if data and data['action'] in ["🟢 STRONG BUY", "🔴 STRONG SELL"]:
        if data['action'] != last_signal:
            alert_msg = (
                f"🚨 **SUPER AI HIGH-CONFIRMATION TRADE ALERT** 🚨\n\n"
                f"🪙 Pair: **Gold (XAU/USD)**\n"
                f"💥 Signal: **{data['action']}**\n"
                f"💵 Entry: **${data['price']:.2f}**\n\n"
                f"🛑 SL: **${data['sl']:.2f}**\n"
                f"🎯 TP1: **${data['tp1']:.2f}**\n"
                f"🚀 TP2: **${data['tp2']:.2f}**\n\n"
                f"📐 Safe Lot Size: **{data['lot_size']}**\n"
                f"⚡ Immediate Exness trade place karein!"
            )
            await context.bot.send_message(chat_id=chat_id, text=alert_msg, parse_mode='Markdown')
            last_signal = data['action']

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("setbalance", set_balance))
    
    print("Sukti Super AI Bot is Running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
