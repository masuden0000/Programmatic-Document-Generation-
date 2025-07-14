# AI Document Template Generator 📄

Aplikasi otomatis untuk mengekstrak aturan format dari dokumen panduan dan membuat template Word menggunakan Gemini AI.

## 🚀 Features

- 📝 Upload dokumen panduan (.txt, .docx)
- 🤖 Ekstraksi aturan format otomatis dengan Gemini AI
- 📄 Generate template Word yang siap pakai
- ⚡ Caching untuk performa optimal

## ️ Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Setup API key:**
Buat file `.env` dan tambahkan:
```env
GOOGLE_API_KEY=your_api_key_here
```

3. **Jalankan aplikasi:**
```bash
streamlit run streamlit_app.py
```

## 📖 Cara Penggunaan

1. Upload dokumen panduan format (.txt/.docx)
2. Klik "Ekstrak Aturan Format"
3. Klik "Generate Template"
4. Download template Word yang sudah diformat

## 🔧 Tech Stack

- **AI**: Google Gemini 2.0 Flash
- **Backend**: Python + LangChain
- **Frontend**: Streamlit
- **Document**: python-docx
