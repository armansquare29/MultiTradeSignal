# Menggunakan image Python versi ringan
FROM python:3.10-slim

# Menentukan direktori kerja di dalam container
WORKDIR /app

# Menyalin dan menginstal pustaka yang dibutuhkan
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh file proyek ke dalam container
COPY . .

# Menjalankan bot
CMD ["python", "bot.py"]