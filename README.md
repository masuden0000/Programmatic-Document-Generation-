# AI Document Template Generator 📄✨

Aplikasi otomatis untuk mengekstrak aturan format dari dokumen panduan dan membuat template Word secara otomatis menggunakan AI.

## 🌟 Features

- 📝 Upload dokumen panduan (.txt, .docx)
- 🤖 Ekstraksi aturan format otomatis dengan Gemini AI
- 📄 Generate template Word yang siap pakai
- ⚡ Caching untuk performa optimal
- � Interface yang user-friendly

## 🚀 Live Demo

**[Akses Aplikasi di Streamlit Cloud](YOUR_STREAMLIT_URL_HERE)**

## 🛠️ Tech Stack

- **AI**: Google Gemini 2.0 Flash
- **Backend**: LangChain + Python
- **Frontend**: Streamlit
- **Document Processing**: python-docx
- **Deployment**: Streamlit Cloud

## Setup Instructions

### Metode 1: Otomatis (Recommended)

**Windows:**

```bash
setup.bat
```

**Linux/Mac:**

```bash
chmod +x setup.sh
./setup.sh
```

### Metode 2: Manual

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Setup environment variables:**

   - Edit file `.env` dan tambahkan Google API key Anda
   - Dapatkan API key dari: https://makersuite.google.com/app/apikey

   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

3. **Jalankan aplikasi:**

```bash
python generated.py
```

4. **Buka browser ke:** http://localhost:5000

## Environment Variables

- `GOOGLE_API_KEY`: API key Google Gemini (required)

## Struktur File

```
├── generated.py          # Main application file
├── ui.html              # Web interface
├── requirements.txt     # Python dependencies
├── .env                # Environment variables
├── setup.sh            # Setup script (Linux/Mac)
├── setup.bat           # Setup script (Windows)
├── README.md           # Documentation
└── uploads/            # Temporary upload folder
```

## API Endpoints

- `GET /`: Serve web interface
- `POST /api/extract-rules`: Extract formatting rules from a document
- `POST /api/generate-template`: Generate a template document
- `POST /api/process`: Complete process (extract + generate)

## Cara Penggunaan

1. **Upload Dokumen**: Upload file .doc atau .docx yang berisi aturan format
2. **AI Processing**: Sistem akan menganalisis dokumen menggunakan Gemini AI
3. **Template Generation**: Template baru akan dibuat sesuai aturan yang terdeteksi
4. **Download**: File template akan otomatis terdownload

## Format Dokumen yang Didukung

- **Input**: .doc, .docx (dokumen panduan format)
- **Output**: .docx (template dokumen)

## Teknologi yang Digunakan

- **Backend**: Python Flask
- **AI**: Google Gemini 2.0 Flash (via LangChain)
- **Document Processing**: python-docx, docx2txt
- **Frontend**: HTML, CSS, JavaScript
- **Environment**: python-dotenv

## Troubleshooting

### Error: Google API Key tidak ditemukan

- Pastikan file `.env` ada dan berisi `GOOGLE_API_KEY`
- Pastikan API key valid dari Google AI Studio

### Error: Module tidak ditemukan

- Jalankan: `pip install -r requirements.txt`

### Error: File upload gagal

- Pastikan file berformat .doc atau .docx
- Maksimal ukuran file: 16MB

## Kontribusi

1. Fork repository
2. Buat feature branch
3. Commit changes
4. Push ke branch
5. Create Pull Request

## Lisensi

MIT License

## Usage

1. Upload a document with formatting rules
2. The system will extract rules using Gemini 2.0 Flash
3. Generate a formatted Word document template

## Solusi Rate Limit dan Optimasi

### 1. **Mengatasi Rate Limit**

Jika Anda mengalami masalah dengan rate limit saat menggunakan Google Gemini API, berikut adalah beberapa solusi yang dapat diterapkan:

- **Tunggu Beberapa Saat**: Rate limit biasanya direset setelah periode tertentu. Tunggu beberapa menit dan coba lagi.
- **Optimalkan Penggunaan API**: Kurangi frekuensi dan jumlah permintaan yang dikirim ke API. Gabungkan beberapa permintaan menjadi satu jika memungkinkan.
- **Gunakan Akun Berbeda**: Jika Anda memiliki akses ke beberapa akun Google, coba gunakan akun lain untuk menghindari rate limit pada akun utama Anda.

### 2. **Alternatif AI Models (Jika diperlukan)**

Saya akan menambahkan opsi untuk menggunakan model alternatif jika rate limit tercapai:

```python
# Alternatif 1: Gunakan Gemini 1.5 Flash (rate limit lebih rendah)
# Alternatif 2: Tambahkan fallback ke model lokal
# Alternatif 3: Implementasi caching untuk mengurangi request
```

## 🔄 Optimasi yang Sudah Diterapkan:

1. **Single Request**: Menggabungkan semua chunks menjadi satu request
2. **Text Truncation**: Memotong teks panjang untuk menghemat token
3. **Better Prompt**: Prompt yang lebih spesifik untuk hasil lebih akurat
4. **Error Handling**: Fallback jika parsing JSON gagal

## 💰 **Rekomendasi Upgrade:**

### Google AI Studio Paid Plan:

- **Harga**: ~$0.075 per 1K input tokens
- **Rate Limit**: 1000+ requests/menit
- **Token Limit**: 2M tokens/menit
- **Lebih stabil** untuk production

### Cara Upgrade:

1. Buka https://aistudio.google.com/
2. Klik "Upgrade" atau "Billing"
3. Setup payment method
4. Otomatis rate limit meningkat

## 🚀 Optimasi Lain yang Bisa Ditambahkan:
