import sqlite3
import logging

logger = logging.getLogger(__name__)
DB_FILE = "bot_data.db"

def init_db():
    """Membuat tabel database jika belum ada."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Tabel User (menyimpan preferensi broker)
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY, broker TEXT DEFAULT 'indodax')''')
        # Tabel Alerts (menyimpan alarm yang aktif)
        cursor.execute('''CREATE TABLE IF NOT EXISTS alerts (chat_id INTEGER, coin TEXT, broker TEXT, PRIMARY KEY (chat_id, coin, broker))''')
        # Tabel Trades (menyimpan posisi trading)
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades (chat_id INTEGER, coin TEXT, broker TEXT, buy_price REAL, tp_price REAL, PRIMARY KEY (chat_id, coin, broker))''')
        conn.commit()
        logger.info("Database SQLite berhasil disiapkan.")

def set_broker(chat_id, broker):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO users (chat_id, broker) VALUES (?, ?)", (chat_id, broker))

def get_broker(chat_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT broker FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        return row[0] if row else "indodax"

def add_alert(chat_id, coin, broker):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO alerts (chat_id, coin, broker) VALUES (?, ?, ?)", (chat_id, coin, broker))

def remove_alert(chat_id, coin, broker):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM alerts WHERE chat_id = ? AND coin = ? AND broker = ?", (chat_id, coin, broker))

def get_all_alerts():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT chat_id, coin, broker FROM alerts")
        return cursor.fetchall()

def save_trade(chat_id, coin, broker, buy_price, tp_price):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO trades (chat_id, coin, broker, buy_price, tp_price) VALUES (?, ?, ?, ?, ?)", (chat_id, coin, broker, buy_price, tp_price))

def remove_trade(chat_id, coin, broker):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM trades WHERE chat_id = ? AND coin = ? AND broker = ?", (chat_id, coin, broker))

def get_trade(chat_id, coin, broker):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT buy_price, tp_price FROM trades WHERE chat_id = ? AND coin = ? AND broker = ?", (chat_id, coin, broker))
        row = cursor.fetchone()
        return {"buy_price": row[0], "tp_price": row[1]} if row else None