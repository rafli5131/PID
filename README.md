# 🫁 Central Java Air Quality & Health Risk Monitor

![SDG 3](https://img.shields.io/badge/SDG-3%20Good%20Health%20and%20Well--being-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

**Central Java Air Quality & Health Risk Monitor** adalah platform analisis data yang dirancang untuk memantau kualitas udara secara real-time dan menganalisis dampaknya terhadap kesehatan masyarakat, khususnya kasus Infeksi Saluran Pernapasan Akut (ISPA) di Jawa Tengah. Proyek ini mendukung **Sustainable Development Goal (SDG) 3: Good Health and Well-being**.

---

## 🌟 Fitur Utama

### 1. Real-Time Environment Monitor (Operasional)
Pantau kondisi lingkungan terkini di seluruh kota di Jawa Tengah.
- **KPI Cards**: Menampilkan rata-rata AQI, suhu, kelembaban, dan kota dengan polusi tertinggi saat ini.
- **Time Series Chart**: Grafik tren polusi udara dalam 24 jam terakhir.
- **Weather Distribution**: Visualisasi kondisi cuaca saat ini.

### 2. Geospatial Analysis (Peta Sebaran)
Peta interaktif untuk melihat sebaran polusi dan risiko kesehatan.
- **Bubble Map**:
  - **Warna**: Indikator AQI Real-time (🟢 Sehat, 🟡 Sedang, 🟠 Tidak Sehat, 🔴 Berbahaya).
  - **Ukuran**: Indikator jumlah kasus ISPA historis (Semakin besar = semakin banyak kasus).
- **Tooltip Interaktif**: Arahkan kursor ke kota untuk melihat detail suhu, status AQI, dan total kasus ISPA.

### 3. Health Risk Correlation (Analisis Strategis)
Analisis mendalam mengenai hubungan antara kualitas udara dan kesehatan.
- **Scatter Plot**: Korelasi antara Indeks Polusi vs Total Kasus ISPA.
- **Top 10 Cities**: Daftar kota dengan kasus ISPA tertinggi.
- **Risk Analysis**: Identifikasi area berisiko tinggi berdasarkan gabungan data polusi dan kesehatan.

### 4. Interaktivitas
- **Filter Kota**: Sidebar untuk memfilter tampilan dashboard berdasarkan kota tertentu.

---

## 🛠️ Teknologi yang Digunakan

- **Bahasa Pemrograman**: Python
- **Framework Dashboard**: Streamlit
- **Database**: PostgreSQL
- **Visualisasi**: Plotly, PyDeck
- **Containerization**: Docker & Docker Compose
- **Data Source**: OpenWeatherMap (Cuaca/Polusi) & Data Dinas Kesehatan (ISPA)

---

## 🚀 Cara Menjalankan

Pastikan Anda telah menginstal **Docker** dan **Docker Compose** di komputer Anda.

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd project-akhir
   ```

2. **Jalankan Aplikasi dengan Docker Compose**
   Perintah ini akan membangun image dan menjalankan container untuk Database, Scraper, dan Dashboard.
   ```bash
   docker compose up -d --build
   ```

3. **Akses Dashboard**
   Buka browser dan kunjungi:
   ```
   http://localhost:8501
   ```

4. **Menghentikan Aplikasi**
   ```bash
   docker compose down
   ```

---

## 📂 Struktur Proyek

```
project-akhir/
├── dashboard/              # Kode sumber aplikasi Streamlit
│   ├── app.py              # Main application file
│   └── requirements.txt    # Dependencies Python untuk dashboard
├── db/                     # Skema Database
│   └── init.sql            # Script inisialisasi tabel SQL
├── docker/                 # Konfigurasi Dockerfile
│   ├── streamlit/
│   └── weather_scraper/
├── scripts/                # Script Python untuk pengolahan data
│   ├── ingest_ispa.py      # Import data ISPA ke database
│   ├── ingest_weather.py   # Scraper data cuaca/polusi
│   └── run_scraper.py      # Scheduler untuk scraper
├── docker-compose.yml      # Konfigurasi layanan Docker
└── README.md               # Dokumentasi Proyek
```

---

## 📊 Metodologi Analisis Risiko

Dashboard ini menggunakan pendekatan **Dynamic Risk Index** untuk mengkategorikan risiko setiap kota:
1. **Normalisasi Data**: Data Polusi dan ISPA dinormalisasi (skala 0-1) menggunakan Min-Max Scaling.
2. **Composite Score**: Skor risiko dihitung dengan bobot 50% Polusi dan 50% ISPA.
   `Risk Score = (Norm. Pollution * 0.5) + (Norm. ISPA * 0.5)`
3. **Kategorisasi**: Kota dikelompokkan menjadi *High*, *Medium*, atau *Low Risk* berdasarkan distribusi statistik (kuantil).

---

## 📝 Catatan
- Data cuaca diperbarui setiap 5 menit oleh service `weather_scraper`.
- Data ISPA merupakan data agregat tahunan (2023).

---
*Dibuat untuk Tugas Akhir PID - 2025*
