import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_crypto_ticker(coin, broker="indodax"):
    """
    Mengambil data ticker dari API publik (Indodax atau Binance).
    Menerapkan 'Adapter Pattern' agar format datanya seragam.
    """
    coin = coin.lower()
    if broker == "indodax":
        url = f"https://indodax.com/api/ticker/{coin}idr"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get("ticker", {})
            if not data: return None
            return {
                "last": data.get("last"), "high": data.get("high"), "low": data.get("low"),
                "buy": data.get("buy"), "sell": data.get("sell"), "currency": "IDR"
            }
        except Exception as e:
            logger.error(f"Gagal mengambil data Indodax API: {e}")
            return None
            
    elif broker == "binance":
        url = f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={coin.upper()}USDT"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "last": data.get("lastPrice"), "high": data.get("highPrice"), "low": data.get("lowPrice"),
                "buy": data.get("bidPrice"), "sell": data.get("askPrice"), "currency": "USDT"
            }
        except Exception as e:
            logger.error(f"Gagal mengambil data Binance API. Jika Anda di Indonesia, nyalakan VPN/WARP. Error: {e}")
            return None
            
    elif broker == "tokocrypto":
        # Tokocrypto sebagian besar menggunakan arsitektur Binance Cloud
        url = f"https://api.tokocrypto.com/api/v1/ticker/24hr?symbol={coin.upper()}USDT"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "last": data.get("lastPrice"), "high": data.get("highPrice"), "low": data.get("lowPrice"),
                "buy": data.get("bidPrice"), "sell": data.get("askPrice"), "currency": "USDT"
            }
        except Exception as e:
            logger.error(f"Gagal mengambil data Tokocrypto API. Error: {e}")
            return None
            
    elif broker == "bybit":
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={coin.upper()}USDT"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json().get("result", {}).get("list", [])
            if not result: return None
            data = result[0]
            return {
                "last": data.get("lastPrice"), "high": data.get("highPrice24h"), "low": data.get("lowPrice24h"),
                "buy": data.get("bid1Price"), "sell": data.get("ask1Price"), "currency": "USDT"
            }
        except Exception as e:
            logger.error(f"Gagal mengambil data Bybit API. Jika Anda di Indonesia, nyalakan VPN/WARP. Error: {e}")
            return None
            
    elif broker == "pintu":
        # Placeholder: API Pintu memiliki struktur GraphQL/Mobile yang berbeda, kita kosongkan dulu
        logger.error("API Pintu masih dalam tahap pengembangan (Placeholder).")
        return None
            
    return None

def format_ticker_for_ai(pair_display, ticker_data):
    """
    Memformat data ticker mentah menjadi teks deskriptif untuk dianalisa oleh AI.
    """
    if not ticker_data:
        return "Data harga tidak tersedia saat ini karena gangguan koneksi ke Exchange."
    
    curr = ticker_data.get("currency", "IDR")
    formatted_text = (
        f"Data Pasar {pair_display} Saat Ini:\n"
        f"- Harga Terakhir (Last): {curr} {ticker_data.get('last')}\n"
        f"- Harga Tertinggi 24j (High): {curr} {ticker_data.get('high')}\n"
        f"- Harga Terendah 24j (Low): {curr} {ticker_data.get('low')}\n"
        f"- Harga Beli Tertinggi (Buy/Bid): {curr} {ticker_data.get('buy')}\n"
        f"- Harga Jual Terendah (Sell/Ask): {curr} {ticker_data.get('sell')}\n"
    )
    
    return formatted_text