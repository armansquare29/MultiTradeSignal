import logging
import json
from telegram import Update, BotCommand, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.request import HTTPXRequest
from datetime import datetime, timedelta # <-- Ubah ini untuk menghitung jam

# Impor konfigurasi dan modul lain yang sudah kita buat
from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID
from price_fetcher import get_crypto_ticker, format_ticker_for_ai
from groq_analyzer import analyze_crypto_price
import database # <-- Impor database SQLite

# --- KONFIGURASI UTAMA TIMEFRAME ---
# Ubah nilai ini untuk mengganti timeframe (dalam jam). Contoh: 1 untuk 1H, 4 untuk 4H.
TIMEFRAME_HOURS = 4
# ------------------------------------

ALL_COINS_LIST = ["btc", "eth", "sol", "doge", "pepe", "shib", "sui", "avax", "near", "rndr", "fet", "ada"]

# Konfigurasi logging untuk memantau aktivitas bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan sambutan saat perintah /start dijalankan."""
    user = update.effective_user
    
    # Simpan user ke database agar bisa menerima pesan broadcast di kemudian hari
    database.add_user_if_not_exists(user.id)

    welcome_text = (
        "🚀 <b>PRO CRYPTO AI SIGNAL</b> 🚀\n\n"
        f"Selamat datang, Trader {user.mention_html()}!\n"
        "Bot ini memindai pasar kripto secara <i>real-time</i> menggunakan teknologi AI untuk mendeteksi momentum dan memberikan sinyal <b>Beli/Jual/Tahan</b> dengan tingkat akurasi tinggi.\n\n"
        "⚙️ <b>FITUR UNGGULAN:</b>\n"
        "• 📊 <b>Analisis Instan:</b> Deteksi arah tren pasar saat ini.\n"
        "• 🔔 <b>Smart Alert:</b> Notifikasi sinyal trading otomatis 24/7.\n"
        "• 🌐 <b>Multi-Broker:</b> Indodax, Binance, Tokocrypto, Bybit, dll.\n\n"
        "<i>Pilih menu di bawah ini untuk memulai perjalanan trading Anda!</i>"
    )
    
    # Tombol raksasa untuk membuka Web App
    web_app_url = "https://armansquare29.github.io/MultiTradeSignal/" # Sesuaikan jika index.html Anda ada di dalam sub-folder
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("📱 Buka Aplikasi Pro Kripto", web_app=WebAppInfo(url=web_app_url))]], resize_keyboard=True)
    await update.message.reply_html(welcome_text, reply_markup=reply_markup)


async def proses_analisa(message, coin: str, context: ContextTypes.DEFAULT_TYPE, is_callback=False) -> None:
    """Fungsi pembantu untuk memproses analisa agar bisa dipanggil dari command atau tombol."""
    chat_id = message.chat_id
    broker = database.get_broker(chat_id)
    
    if broker in ["indodax", "pintu", "reku"]:
        pair_display = f"{coin.upper()}/IDR"
    else:
        pair_display = f"{coin.upper()}/USDT"

    # Kirim pesan awal
    if is_callback:
        proses_msg = message
        await proses_msg.edit_text(f"Sedang mengambil data {pair_display} dari {broker.upper()} dan menganalisis, mohon tunggu...")
    else:
        proses_msg = await message.reply_text(f"Sedang mengambil data {pair_display} dari {broker.upper()} dan menganalisis, mohon tunggu...")

    ticker_data = get_crypto_ticker(coin, broker)
    if not ticker_data:
        await proses_msg.edit_text(f"Gagal mengambil data untuk {pair_display}. Pastikan koin valid di {broker.upper()}.")
        return

    formatted_data = format_ticker_for_ai(pair_display, ticker_data)
    ai_response = analyze_crypto_price(pair_display, formatted_data)

    # Siapkan pesan final beserta judul koinnya
    final_message = f"📊 *ANALISIS {pair_display} ({broker.upper()})*\n\n{ai_response}"

    try:
        await proses_msg.edit_text(final_message, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await proses_msg.edit_text(f"📊 ANALISIS {pair_display} ({broker.upper()})\n\n{ai_response}")

async def analisa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengambil data, menganalisis dengan AI, dan mengirim hasilnya."""
    await update.message.reply_text("📱 Silakan klik tombol **'Buka Aplikasi Pro Kripto'** di bawah untuk melakukan Analisa Koin.")

async def smart_alert(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fungsi latar belakang untuk mengecek harga dan mengirim alert jika BELI/JUAL."""
    job = context.job
    chat_id = job.chat_id
    coin = job.data["coin"]
    broker = job.data["broker"]
    pair_display = job.data["pair_display"]
 
    ticker_data = get_crypto_ticker(coin, broker)
    if not ticker_data:
        logger.warning("Smart Alert: Gagal mengambil data ticker, skipping check.")
        return
 
    # Ekstrak harga sekarang dalam format integer
    harga_sekarang_raw = ticker_data.get('last', 0)
    try:
        harga_sekarang = int(harga_sekarang_raw)
    except (ValueError, TypeError):
        harga_sekarang = 0

    # 1. CEK TRANSAKSI AKTIF (MEMORI BOT) UNTUK TAKE PROFIT LOKAL
    trade = database.get_trade(chat_id, coin, broker)
    if trade and harga_sekarang > 0:
        if harga_sekarang >= trade["tp_price"]:
            profit = harga_sekarang - trade["buy_price"]
            harga_sekarang_formatted = f"Rp {harga_sekarang:,}".replace(',', '.')
            buy_formatted = f"Rp {trade['buy_price']:,}".replace(',', '.')
            tp_formatted = f"Rp {trade['tp_price']:,}".replace(',', '.')
            
            new_message = (
                "🎉 **TAKE PROFIT TERCAPAI!** 🎉\n"
                f"> Pair/TF: {pair_display} / {TIMEFRAME_HOURS} Jam\n"
                f"> Broker: {broker.upper()}\n"
                f"> Harga Beli Awal: {buy_formatted}\n"
                f"> Target TP: {tp_formatted}\n"
                f"> Harga Sekarang: {harga_sekarang_formatted}\n"
                f"> Rekomendasi: **CLOSE POSITION (JUAL SEKARANG)**\n"
                f"> Estimasi Profit: Rp {profit:,}".replace(',', '.')
            )
            await context.bot.send_message(chat_id=chat_id, text=new_message, parse_mode=ParseMode.MARKDOWN)
            # Hapus dari memori karena sudah take profit
            database.remove_trade(chat_id, coin, broker)
            return  # Berhenti di sini, tidak perlu analisa AI untuk siklus ini

    formatted_data = format_ticker_for_ai(pair_display, ticker_data)
    ai_response = analyze_crypto_price(pair_display, formatted_data)
 
    # Log aktivitas ke terminal laptop agar Anda tahu bot bekerja
    if "**Rekomendasi:** TAHAN" in ai_response:
        logger.info("Smart Alert: AI menyarankan TAHAN. Pesan tidak dikirim ke Telegram (Mode Senyap).")
    elif "**Rekomendasi:** BELI" not in ai_response and "**Rekomendasi:** JUAL" not in ai_response:
        logger.warning("Smart Alert: AI tidak memberikan rekomendasi yang jelas. Pesan diabaikan.")

    # Hanya kirim pesan jika rekomendasinya BELI atau JUAL
    if "**Rekomendasi:** BELI" in ai_response or "**Rekomendasi:** JUAL" in ai_response:
        rekomendasi = "N/A"
        analisa = "N/A"
        target_tp = 0
        try:
            lines = [line.strip() for line in ai_response.strip().split('\n') if line.strip()]
            for line in lines:
                if "**Rekomendasi:**" in line:
                    rekomendasi = line.replace("**Rekomendasi:**", "").strip()
                elif "**Target TP:**" in line:
                    tp_str = line.replace("**Target TP:**", "").strip()
                    # Bersihkan jika AI memasukkan titik/koma ke dalam angka
                    tp_clean = ''.join(filter(str.isdigit, tp_str))
                    target_tp = int(tp_clean) if tp_clean else 0
                elif "**Analisis Singkat:**" in line:
                    analisa = line.replace("**Analisis Singkat:**", "").strip()
        except (IndexError, Exception) as e:
            logger.error(f"Gagal mem-parsing respon AI: {e}. Menggunakan format mentah.")
            # Fallback jika parsing gagal
            await context.bot.send_message(
                chat_id=chat_id, 
                text=f"🚨 **SMART ALERT (Parse Error)** 🚨\n\n{ai_response}"
            )
            return

        harga_sekarang_formatted = f"Rp {harga_sekarang:,}".replace(',', '.') if harga_sekarang > 0 else "Tidak tersedia"

        if "BELI" in rekomendasi:
            # Jika AI lupa memberi target TP atau targetnya lebih rendah dari harga saat ini, 
            # bot akan otomatis membuat default target TP naik 2% dari harga saat ini.
            if target_tp <= harga_sekarang:
                target_tp = int(harga_sekarang * 1.02)
                
            # Simpan transaksi ke memori bot
            database.save_trade(chat_id, coin, broker, harga_sekarang, target_tp)
            
            tp_formatted = f"Rp {target_tp:,}".replace(',', '.')
            new_message = (
                "🟢 **Smart Alert (Sinyal BELI)** 🟢\n"
                f"> Pair/TF: {pair_display} / {TIMEFRAME_HOURS} Jam\n"
                f"> Broker: {broker.upper()}\n"
                f"> Harga Sekarang: {harga_sekarang_formatted}\n"
                f"> Rekomendasi: **{rekomendasi}**\n"
                f"> 🎯 Target TP: {tp_formatted}\n"
                f"> Analisa Singkat: {analisa}"
            )
        elif "JUAL" in rekomendasi and trade:
            # AI menyuruh JUAL (misal memotong kerugian / Cut Loss), dan kita sedang punya posisi terbuka
            buy_price = trade["buy_price"]
            profit = harga_sekarang - buy_price
            status = "Profit" if profit > 0 else "Loss"
            
            new_message = (
                f"🔴 **Smart Alert (Tutup Posisi / {status})** 🔴\n"
                f"> Pair/TF: {pair_display} / {TIMEFRAME_HOURS} Jam\n"
                f"> Broker: {broker.upper()}\n"
                f"> Harga Sekarang: {harga_sekarang_formatted}\n"
                f"> Rekomendasi: **{rekomendasi}**\n"
                f"> Hasil Trading: {status} (Rp {abs(profit):,}".replace(',', '.') + ")\n"
                f"> Analisa Singkat: {analisa}"
            )
            # Hapus transaksi dari memori
            database.remove_trade(chat_id, coin, broker)
        else:
            # Sinyal JUAL biasa dari AI tapi kita tidak punya posisi buy sebelumnya
            new_message = (
                "🔴 **Smart Alert (Sinyal JUAL)** 🔴\n"
                f"> Pair/TF: {pair_display} / {TIMEFRAME_HOURS} Jam\n"
                f"> Broker: {broker.upper()}\n"
                f"> Harga Sekarang: {harga_sekarang_formatted}\n"
                f"> Rekomendasi: **{rekomendasi}**\n"
                f"> Analisa Singkat: {analisa}"
            )

        # Kirim pesan dengan format Markdown
        await context.bot.send_message(
            chat_id=chat_id, 
            text=new_message,
            parse_mode=ParseMode.MARKDOWN
        )

async def proses_start_alert(message, coin: str, context: ContextTypes.DEFAULT_TYPE, is_callback=False) -> None:
    """Fungsi pembantu untuk memproses aktivasi alert 1 koin."""
    chat_id = message.chat_id
    broker = database.get_broker(chat_id)
    pair_display = f"{coin.upper()}/IDR" if broker in ["indodax", "pintu", "reku"] else f"{coin.upper()}/USDT"
    job_name = f"{chat_id}_{coin}_{broker}"
    
    if context.job_queue.get_jobs_by_name(job_name):
        msg = f"Smart Alert untuk {pair_display} sudah aktif!"
        await message.reply_text(msg)
        return

    interval_seconds = TIMEFRAME_HOURS * 3600
    now = datetime.now()
    next_candle_hour = ((now.hour // TIMEFRAME_HOURS) + 1) * TIMEFRAME_HOURS
    next_run_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0) if next_candle_hour >= 24 else now.replace(hour=next_candle_hour, minute=0, second=0, microsecond=0)
    delay_seconds = (next_run_time - now).total_seconds()

    context.job_queue.run_repeating(smart_alert, interval=interval_seconds, first=delay_seconds, chat_id=chat_id, name=job_name, data={"coin": coin, "broker": broker, "pair_display": pair_display})
    database.add_alert(chat_id, coin, broker)
    wita_time = next_run_time + timedelta(hours=8)
    msg = f"🔔 Smart Alert {pair_display} ({broker.upper()}) diaktifkan untuk timeframe {TIMEFRAME_HOURS} Jam!\n\nPengecekan pertama: pukul {wita_time.strftime('%H:%M')} WITA."
    await message.reply_text(msg)

async def proses_start_alert_all(message, context: ContextTypes.DEFAULT_TYPE, is_callback=False) -> None:
    """Fungsi pembantu untuk memproses aktivasi alert semua koin sekaligus."""
    chat_id = message.chat_id
    broker = database.get_broker(chat_id)
    activated, already = [], []
    
    interval_seconds = TIMEFRAME_HOURS * 3600
    now = datetime.now()
    next_candle_hour = ((now.hour // TIMEFRAME_HOURS) + 1) * TIMEFRAME_HOURS
    next_run_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0) if next_candle_hour >= 24 else now.replace(hour=next_candle_hour, minute=0, second=0, microsecond=0)
    delay_seconds = (next_run_time - now).total_seconds()

    for coin in ALL_COINS_LIST:
        pair_display = f"{coin.upper()}/IDR" if broker in ["indodax", "pintu", "reku"] else f"{coin.upper()}/USDT"
        job_name = f"{chat_id}_{coin}_{broker}"
        if context.job_queue.get_jobs_by_name(job_name):
            already.append(coin.upper())
            continue
        context.job_queue.run_repeating(smart_alert, interval=interval_seconds, first=delay_seconds, chat_id=chat_id, name=job_name, data={"coin": coin, "broker": broker, "pair_display": pair_display})
        database.add_alert(chat_id, coin, broker)
        activated.append(coin.upper())
        
    msg = f"🔔 **Smart Alert (ALL COINS - {broker.upper()}) Diproses!** 🔔\n\n"
    if activated: msg += f"✅ **Berhasil Aktif:** {', '.join(activated)}\n"
    if already: msg += f"⚠️ **Sudah Aktif Sebelumnya:** {', '.join(already)}\n"
    wita_time = next_run_time + timedelta(hours=8)
    msg += f"\nPengecekan perdana: pukul {wita_time.strftime('%H:%M')} WITA."
    
    await message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def start_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command untuk mengaktifkan pengecekan otomatis."""
    await update.message.reply_text("📱 Silakan klik tombol **'Buka Aplikasi Pro Kripto'** di bawah untuk mengelola Smart Alert.")

async def proses_stop_alert(message, coin: str, context: ContextTypes.DEFAULT_TYPE, is_callback=False) -> None:
    """Fungsi pembantu untuk mematikan alert 1 koin."""
    chat_id = message.chat_id
    broker = database.get_broker(chat_id)
    pair_display = f"{coin.upper()}/IDR" if broker in ["indodax", "pintu", "reku"] else f"{coin.upper()}/USDT"
    job_name = f"{chat_id}_{coin}_{broker}"
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    
    if not current_jobs:
        msg = f"Smart Alert untuk {pair_display} ({broker.upper()}) belum aktif."
        await message.reply_text(msg)
        return
        
    for job in current_jobs: job.schedule_removal()
    database.remove_alert(chat_id, coin, broker)
    msg = f"🔕 Smart Alert untuk {pair_display} ({broker.upper()}) telah dimatikan."
    await message.reply_text(msg)

async def proses_stop_alert_all(message, context: ContextTypes.DEFAULT_TYPE, is_callback=False) -> None:
    """Fungsi pembantu untuk mematikan alert semua koin sekaligus."""
    chat_id = message.chat_id
    broker = database.get_broker(chat_id)
    stopped, not_active = [], []

    for coin in ALL_COINS_LIST:
        job_name = f"{chat_id}_{coin}_{broker}"
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        if not current_jobs:
            not_active.append(coin.upper())
            continue
        for job in current_jobs: job.schedule_removal()
        database.remove_alert(chat_id, coin, broker)
        stopped.append(coin.upper())
        
    msg = f"🔕 **Smart Alert (ALL COINS - {broker.upper()}) Dimatikan!** 🔕\n\n"
    if stopped: msg += f"✅ **Berhasil Dimatikan:** {', '.join(stopped)}\n"
    if not_active: msg += f"⚠️ **Tidak Ada Alarm Aktif:** {', '.join(not_active)}\n"
    
    await message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def stop_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command untuk mematikan pengecekan otomatis."""
    await update.message.reply_text("📱 Silakan klik tombol **'Buka Aplikasi Pro Kripto'** di bawah untuk mengelola Smart Alert.")

async def set_broker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Perintah untuk memilih broker/exchange."""
    await update.message.reply_text("📱 Silakan klik tombol **'Buka Aplikasi Pro Kripto'** di bawah untuk mengganti Broker.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Perintah khusus Admin untuk mengirim pesan massal."""
    user_id = str(update.effective_user.id)
    
    # Cek apakah user adalah admin
    if not ADMIN_CHAT_ID or user_id != str(ADMIN_CHAT_ID):
        await update.message.reply_text(f"⛔ Anda tidak memiliki izin untuk menggunakan perintah ini.\n\n*Info Debug:* ID Telegram Anda adalah `{user_id}`.\nPastikan angka ini yang tertulis di file `.env` Anda.", parse_mode=ParseMode.MARKDOWN)
        return
        
    # Cek apakah ada pesan yang ingin di-broadcast
    if not context.args:
        await update.message.reply_text("⚠️ Format salah!\nGunakan: `/broadcast [pesan Anda]`", parse_mode=ParseMode.MARKDOWN)
        return
        
    pesan = " ".join(context.args)
    users = database.get_all_users()
    
    if not users:
        await update.message.reply_text("⚠️ Belum ada pengguna di database.")
        return
        
    await update.message.reply_text(f"⏳ Mulai mengirim pesan broadcast ke {len(users)} pengguna...")
    
    berhasil, gagal = 0, 0
    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"📢 **PENGUMUMAN ADMIN** 📢\n\n{pesan}", parse_mode=ParseMode.MARKDOWN)
            berhasil += 1
        except Exception as e:
            logger.error(f"Gagal mengirim broadcast ke {chat_id}: {e}")
            gagal += 1
            
    await update.message.reply_text(f"✅ **Broadcast Selesai!**\nBerhasil dikirim: {berhasil}\nGagal (Bot diblokir user): {gagal}", parse_mode=ParseMode.MARKDOWN)

async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menerima dan memproses data aksi yang dikirim dari Web App (HTML)."""
    try:
        # Data dari Web App selalu dikirim dalam bentuk string JSON
        data = json.loads(update.effective_message.web_app_data.data)
        action = data.get("action")
        broker = data.get("broker")
        coins = data.get("coins", [])
        
        chat_id = update.effective_message.chat_id
        
        # Simpan broker pilihan user ke Database
        if broker:
            database.set_broker(chat_id, broker)
            
        if action == "status":
            alerts = database.get_all_alerts()
            user_alerts = [a for a in alerts if a[0] == chat_id]
            
            msg = f"📊 **INFO STATUS ANDA** 📊\n\n"
            msg += f"🌐 **Broker Aktif:** {broker.upper()}\n"
            msg += f"🔔 **Total Alarm Aktif:** {len(user_alerts)}\n\n"
            
            if user_alerts:
                msg += "**Daftar Koin Dipantau:**\n"
                for alert in user_alerts:
                    msg += f"• {alert[1].upper()} ({alert[2].upper()})\n"
            else:
                msg += "Anda tidak memiliki alarm yang sedang berjalan saat ini.\n"
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return
            
        if not coins:
            await update.message.reply_text("⚠️ Anda tidak memilih koin apapun di Web App.")
            return
            
        coins_display = ', '.join([c.upper() for c in coins])
        
        # Eksekusi perintah berdasarkan aksi dari Web App
        if action == "analisa":
            await update.message.reply_text(f"Menerima perintah dari Web App.\nSedang memproses analisa untuk: **{coins_display}**...", parse_mode=ParseMode.MARKDOWN)
            for coin in coins:
                await proses_analisa(update.message, coin, context, is_callback=False)
        elif action == "startalert":
            await update.message.reply_text(f"Menerima perintah dari Web App.\nSedang memproses aktivasi Smart Alert untuk: **{coins_display}**...", parse_mode=ParseMode.MARKDOWN)
            for coin in coins:
                await proses_start_alert(update.message, coin, context, is_callback=False)
        elif action == "stopalert":
            await update.message.reply_text(f"Menerima perintah dari Web App.\nSedang memproses penonaktifan Smart Alert untuk: **{coins_display}**...", parse_mode=ParseMode.MARKDOWN)
            for coin in coins:
                await proses_stop_alert(update.message, coin, context, is_callback=False)
                
    except Exception as e:
        logger.error(f"Error memproses Web App Data: {e}")

async def post_init(application: Application) -> None:
    """Menyiapkan tombol menu (command) di Telegram."""
    await application.bot.set_my_commands([
        BotCommand("start", "Mulai bot dan lihat panduan"),
        BotCommand("broker", "Pilih Broker (Indodax / Binance)"),
        BotCommand("analisa", "Analisis instan koin (contoh: /analisa sol)"),
        BotCommand("start_alert", "Aktifkan sinyal (contoh: /start_alert btc)"),
        BotCommand("stop_alert", "Matikan sinyal (contoh: /stop_alert doge)"),
        BotCommand("broadcast", "Kirim pesan massal (Hanya Admin)")
    ])
    
    # RE-LOAD SEMUA ALARM DARI DATABASE SAAT BOT RESTART
    alerts = database.get_all_alerts()
    if alerts:
        logger.info(f"Memuat {len(alerts)} alarm aktif dari Database...")
        interval_seconds = TIMEFRAME_HOURS * 3600
        now = datetime.now()
        next_candle_hour = ((now.hour // TIMEFRAME_HOURS) + 1) * TIMEFRAME_HOURS
        next_run_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0) if next_candle_hour >= 24 else now.replace(hour=next_candle_hour, minute=0, second=0, microsecond=0)
        delay_seconds = (next_run_time - now).total_seconds()
        
        for alert in alerts:
            chat_id, coin, broker = alert
            pair_display = f"{coin.upper()}/IDR" if broker in ["indodax", "pintu", "reku"] else f"{coin.upper()}/USDT"
            job_name = f"{chat_id}_{coin}_{broker}"
            application.job_queue.run_repeating(
                smart_alert, 
                interval=interval_seconds, 
                first=delay_seconds, 
                chat_id=chat_id, 
                name=job_name, 
                data={"coin": coin, "broker": broker, "pair_display": pair_display}
            )

def main() -> None:
    """Jalankan bot."""
    # Inisialisasi Database
    database.init_db()

    # Gunakan HTTPXRequest untuk kestabilan ekstra di lingkungan server Cloud (Hugging Face)
    req = HTTPXRequest(connection_pool_size=8, connect_timeout=60.0, read_timeout=60.0)

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(req)
        .get_updates_request(req)
        .post_init(post_init)
        .build()
    )

    # Daftarkan command handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broker", set_broker))
    application.add_handler(CommandHandler("analisa", analisa))
    application.add_handler(CommandHandler("start_alert", start_alert))
    application.add_handler(CommandHandler("stop_alert", stop_alert))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))

    # Mulai polling untuk menerima update dari Telegram
    # bootstrap_retries=-1 memaksa bot mengulang koneksi jika server Cloud sedang lambat saat proses booting
    application.run_polling(drop_pending_updates=True, bootstrap_retries=-1)

if __name__ == "__main__":
    main()