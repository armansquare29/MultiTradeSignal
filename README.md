# Bot Telegram Analisis Kripto (Indodax All Coins) dengan Groq AI

Bot Telegram berbasis Python ini mengambil data harga *real-time* berbagai pasangan aset kripto (seperti SOL/IDR, ETH/IDR, DOGE/IDR) langsung dari API publik Indodax, lalu menggunakan kecerdasan buatan dari Groq AI (model Llama 3.1) untuk memberikan analisis singkat beserta rekomendasi trading (Beli/Jual/Tahan).

## Fitur Utama
* **Integrasi Indodax API:** Mengambil metrik harga esensial seperti Last, High, Low, Buy (Bid), dan Sell (Ask) dalam 24 jam terakhir.
* **Analisis AI Cerdas:** Menggunakan *system prompt* khusus yang dirancang untuk strategi *Swing Trading* (menangkap momentum) di *spot market*.
* **Smart Alert:** Bot dapat berjalan di latar belakang dan otomatis memberi tahu Anda HANYA saat AI mendeteksi momentum BELI atau JUAL.
* **Respon Super Cepat:** Didukung oleh infrastruktur *inference* Groq yang sangat cepat.

## Prasyarat
* Python 3.8+
* Akun Telegram dan Bot Token dari [BotFather](https://t.me/botfather)
* API Key gratis dari [Groq Console](https://console.groq.com/)

## Instalasi & Persiapan

1. Pastikan Anda berada di direktori proyek ini.
2. Instal semua pustaka (dependencies) yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```
3. Buat sebuah file bernama `.env` (tanpa ekstensi) di folder utama.
4. Isi file `.env` tersebut dengan kredensial rahasia Anda (lihat file `.env.example` sebagai referensi):
   ```dotenv
   TELEGRAM_BOT_TOKEN=masukkan_token_bot_telegram_anda_disini
   GROQ_API_KEY=masukkan_api_key_groq_anda_disini
   ```

## Cara Menjalankan Bot

1. Buka terminal atau PowerShell, jalankan skrip utama:
   ```bash
   python bot.py
   ```
2. Pastikan muncul log `INFO:telegram.ext.Application:Application started`. *(Catatan: Gunakan VPN seperti Cloudflare WARP jika ISP Anda memblokir koneksi ke API Telegram).*
3. Buka aplikasi Telegram, cari nama bot Anda, dan mulai obrolan.
4. Ketik `/start` untuk melihat pesan sambutan.
5. Ketik `/analisa [koin]` (contoh: `/analisa sol`) untuk meminta bot menganalisis harga koin tertentu secara manual.
6. Ketik `/start_alert [koin]` (contoh: `/start_alert doge`) untuk mengaktifkan pemantauan sinyal otomatis pada koin tersebut.
7. Ketik `/stop_alert [koin]` (contoh: `/stop_alert doge`) untuk mematikan pemantauan.