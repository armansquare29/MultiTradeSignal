import logging
from groq import Groq
from config import GROQ_API_KEY

# Inisialisasi logger
logger = logging.getLogger(__name__)

# Inisialisasi client Groq dengan API Key dari config
client = Groq(api_key=GROQ_API_KEY)

def analyze_crypto_price(pair, price_data_text):
    """
    Mengirim data harga ke Groq AI untuk dianalisis dan mendapatkan rekomendasi.
    
    Args:
        pair (str): Nama pasangan aset (contoh: "BTC/IDR", "SOL/IDR").
        price_data_text (str): Teks yang sudah diformat berisi data harga.
        
    Returns:
        str: Respon analisis dari AI, atau pesan error jika gagal.
    """
    system_prompt = (
        "Anda adalah seorang analis pasar cryptocurrency yang ahli, ringkas, dan to the point. "
        f"Tugas Anda adalah memberikan analisis singkat dan rekomendasi (BELI, JUAL, atau TAHAN) " 
        f"untuk pasangan {pair} di Indodax berdasarkan data pasar saat ini. Strategi utama Anda adalah Swing Trading (Momentum). "
        "ATURAN KERAS: "
        "1. Rekomendasikan BELI HANYA JIKA ada indikasi kuat harga BARU MULAI NAIK dari titik bawah (reversal naik). "
        "2. Rekomendasikan JUAL HANYA JIKA harga terlihat berada di puncak dan bersiap turun. "
        "3. JANGAN PERNAH merekomendasikan BELI jika harga sedang dalam tren turun atau baru saja anjlok. Jika ragu, rekomendasikan TAHAN. "
        "Fokus pada data yang diberikan saja. Berikan jawaban dalam format berikut:\n\n"
        "**Rekomendasi:** [BELI/JUAL/TAHAN]\n"
        "**Target TP:** [Angka harga target profit (contoh: 1050000000). Wajib diisi jika BELI, isi 0 jika JUAL/TAHAN]\n"
        "**Analisis Singkat:** [Jelaskan alasan Anda dalam 1-2 kalimat singkat]"
    )
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": price_data_text}
            ],
            model="llama-3.1-8b-instant", # Model yang cepat dan efisien
            temperature=0.6,
            max_tokens=150,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Terjadi error saat menghubungi Groq API: {e}")
        return "Maaf, terjadi kesalahan saat mencoba menganalisis data dengan AI. Silakan coba lagi nanti."