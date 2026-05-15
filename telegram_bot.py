from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from screener import scan_symbol, screen_all, calculate_harga_wajar
import asyncio
import logging

# =======================
# Logging setup
# =======================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8844221894:AAHUFcRtCj2a8Mt11QVSG-RS8ryMWqFwjfY"

# ======================================================
# /start
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "🤖 Screener ALPHA Aktif!\n\n"
            "Perintah:\n"
            "- /rekomendasi — Top 15 Day trade\n"
            "- /swing — Top swing (hold 5-10 hari)\n"
            "- /harga_wajar SYMBOL — Hitung harga wajar saham\n"
            "- /scan SYMBOL — Scan analisa per saham\n\n"
            "Contoh: /scan BBNI"
        )
    except Exception as e:
        logger.error(f"Error di /start: {e}")

# =====================================================
# /scan — tetap format lama (full data)
# =====================================================
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Gunakan: /scan BBRI.JK")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"⏳ Scanning {symbol} di 3 timeframe...")

    for tf in ["1d", "1h", "30m"]:
        data = scan_symbol(symbol, tf)
        if not data:
            await update.message.reply_text(f"⚠️ {symbol} tidak ada data di TF {tf}")
            continue

        msg = (
            f"📊 {symbol} - TF {tf}\n"
            f"Harga : {data['price']}\n"
            f"MA60  : {data['ma60']} ({'🟢' if data['ma_status']=='Above MA60' else '🔴'})\n"
            f"RSI   : {data['rsi']}\n"
            f"Volume: {data['vol_last']} ({data['vol_status']})\n"
            f"Value : {data['value_last']:,} ({data['value_status']})\n\n"
            f"📌 Fibonacci:\n"
            f"50%   : {data['fib_50']}\n"
            f"61.8% : {data['fib_618']}\n"
            f"78.6% : {data['fib_786']}\n"
            f"TP -21% : {data['tp_21']}\n"
        )
        await update.message.reply_text(msg)
        await asyncio.sleep(1)

# =====================================================
# /rekomendasi — Top 15 (RSI 60–75 + MA 🟢)
# =====================================================
async def rekomendasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Mengambil rekomendasi terbaik 🚀⚡...")
    data = screen_all()
    if not data:
        await update.message.reply_text("❌ Tidak ada data.")
        return

    filtered = [
        s for s in data
        if 60 <= s["rsi"] <= 75 and s["ma_status"] == "Above MA60"
    ]
    top = filtered[:15]

    if not top:
        await update.message.reply_text("❌ Tidak ada yang memenuhi filter RSI 60–75 + MA🟢")
        return

    for s in top:
        msg = (
            f"📊 {s['symbol']}.JK - REKOMENDASI\n"
            f"Harga : {s['price']}\n"
            f"MA60  : {s['ma60']} (🟢)\n"
            f"RSI   : {s['rsi']}\n"
        )
        await update.message.reply_text(msg)
        await asyncio.sleep(0.5)

# =====================================================
# /swing — RSI 35–50 + MA 🔴
# =====================================================
async def swing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Mencari saham swing setup 📈...")
    data = screen_all()
    if not data:
        await update.message.reply_text("❌ Tidak ada data.")
        return

    filtered = [
        s for s in data
        if 35 <= s["rsi"] <= 50 and s["ma_status"] == "Below MA60"
    ]
    if not filtered:
        await update.message.reply_text("❌ Tidak ada yang memenuhi filter Swing (RSI 35–50 + MA🔴)")
        return

    top = filtered[:10]
    for s in top:
        msg = (
            f"📊 {s['symbol']}.JK - SWING\n"
            f"Harga : {s['price']}\n"
            f"MA60  : {s['ma60']} (🔴)\n"
            f"RSI   : {s['rsi']}\n"
        )
        await update.message.reply_text(msg)
        await asyncio.sleep(0.5)

# =====================================================
# /harga_wajar — Hitung harga wajar saham
# =====================================================
async def harga_wajar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Gunakan: /harga_wajar <symbol>")
        return

    symbol = context.args[0].upper()
    data = calculate_harga_wajar(symbol)
    if not data:
        await update.message.reply_text(f"⚠️ Gagal mengambil data saham {symbol}.")
        return

    msg = f"💹 Harga Wajar Saham {symbol}\n"
    msg += f"Harga Sekarang: Rp {data['harga_saham']:,}\n"
    msg += f"EPS (TTM): {data['eps']}\n"
    msg += f"PBV: {data['pbv']}\n"
    msg += f"PER (TTM): {data['per']}\n\n"
    msg += f"🔹 Harga Wajar PER: Rp {data['wajar']['PER'][0]:,.2f} - Rp {data['wajar']['PER'][1]:,.2f}\n"
    msg += f"🔹 Harga Wajar PBV: Rp {data['wajar']['PBV'][0]:,.2f} - Rp {data['wajar']['PBV'][1]:,.2f}\n"
    msg += f"🔹 Harga Wajar Gabungan: Rp {data['wajar']['Gabungan'][0]:,.2f} - Rp {data['wajar']['Gabungan'][1]:,.2f}\n\n"
    msg += f"Status: {data['status']}"

    await update.message.reply_text(msg)

# =====================================================
# Global error handler
# =====================================================
async def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# =====================================================
# Run Bot
# =====================================================
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("rekomendasi", rekomendasi))
    app.add_handler(CommandHandler("swing", swing))
    app.add_handler(CommandHandler("harga_wajar", harga_wajar))

    # Global error handler
    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()
