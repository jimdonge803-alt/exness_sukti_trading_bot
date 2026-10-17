import logging
import yfinance as yf
import pandas as pd
import ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Yaha apna naya Bot Token daalein
TELEGRAM_TOKEN = "8969292356:AAFovvKTKKf1nUG1l5IYBDZtutwPsJMalJE"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Gold Data Fetch & Signal Calculation
def get_gold_signal():
    # Fetch XAU/USD data (GC=F / Gold Futures)
    df = yf.download(tickers='GC=F', period='1d', interval='15m')
    if df.empty:
        return "Market Data nahi mil raha hai."
    
    # Calculate RSI
    rsi_series = ta.momentum.RSIIndicator(close=df['Close'].squeeze(), window=14).rsi()
    current_rsi = rsi_series.iloc[-1]
    current_price = df['Close'].iloc[-1].item()
    
    # Simple Strategy Logic
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

# Telegram Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! Mai aapka Gold Trading AI Assistant hu. Commands:\n/status - Live Gold Analysis")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analysis = get_gold_signal()
    await update.message.reply_text(analysis, parse_mode='Markdown')

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    print("Bot chalu ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()