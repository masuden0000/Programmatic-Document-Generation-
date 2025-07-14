# Sistem Otomasi Template Dokumen - Streamlit Version
# Tampilan sederhana mirip ui.html

import hashlib
import json
import os
import pickle
import re
import sys
import tempfile
import time
from io import BytesIO
from typing import Any, Dict, List

import streamlit as st

# Configure page FIRST before any other streamlit calls
st.set_page_config(
    page_title="Sistem Otomasi Template Dokumen",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH as WD_PARAGRAPH_ALIGNMENT
from docx.shared import Cm, Inches, Pt
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()


class FormatRulesExtractor:
    """Mengekstrak aturan format dari dokumen panduan"""

    def __init__(self):
        # Initialize Gemini model
        # Try Streamlit secrets first, fallback to .env
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
        except:
            api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            st.error(
                "⚠️ GOOGLE_API_KEY tidak ditemukan! Pastikan sudah setting di Streamlit Cloud secrets atau file .env"
            )
            st.info("📝 Untuk Streamlit Cloud: Tambahkan GOOGLE_API_KEY di app secrets")
            st.stop()

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=0.1,
            max_retries=3,
            timeout=60,
        )

        # Cache directory untuk menyimpan hasil
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key dari text content"""
        return hashlib.md5(text.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Dict[str, Any] | None:
        """Load hasil dari cache jika ada"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
            except:
                pass
        return None

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """Simpan hasil ke cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
        except:
            pass

    def extract_rules_with_ai(self, document_path: str) -> Dict[str, Any]:
        """Menggunakan AI untuk ekstrak aturan format"""

        # Load dokumen
        loader = Docx2txtLoader(document_path)
        documents = loader.load()

        # Gabungkan semua dokumen menjadi satu teks
        full_text = "\\n".join([doc.page_content for doc in documents])

        # Cek cache terlebih dahulu
        cache_key = self._get_cache_key(full_text)
        cached_result = self._load_from_cache(cache_key)
        if cached_result:
            st.info("📋 Menggunakan hasil dari cache...")
            return cached_result

        # Jika teks terlalu panjang, potong ke 12000 karakter pertama
        if len(full_text) > 12000:
            full_text = full_text[:12000] + "..."

        # Prompt yang lebih komprehensif dan detail
        prompt = f"""
        Analisis dokumen panduan berikut dan ekstrak SEMUA aturan format yang ada untuk membuat template dokumen yang LENGKAP dan DETAIL.

        DOKUMEN PANDUAN:
        {full_text}

        Ekstrak informasi berikut dalam format JSON yang SANGAT DETAIL:

        1. MARGIN (dalam cm): top, bottom, left, right
        2. FONT: family, size untuk berbagai elemen (body, heading, subheading)
        3. SPACING: line_spacing, paragraph_spacing, before_after_spacing
        4. PAPER: size (A4/Letter), orientation (portrait/landscape)
        5. HEADERS_FOOTERS: apakah ada, posisi, format
        6. NUMBERING: page_numbering, chapter_numbering, section_numbering
        7. DOCUMENT_STRUCTURE: urutan bagian dokumen (cover, toc, chapters, etc)
        8. SPECIAL_FORMATTING: indent, alignment, bullet_points, tables

        PENTING: Berikan nilai DEFAULT jika tidak disebutkan:
        - Margin: top=3, bottom=3, left=3, right=3
        - Font: family="Times New Roman", size=12
        - Spacing: line_spacing=1.5, paragraph_spacing=6
        - Paper: size="A4", orientation="portrait"

        Berikan response dalam format JSON yang valid dan lengkap.
        """

        try:
            # Buat messages untuk Gemini
            messages = [
                SystemMessage(
                    content="Anda adalah ahli analisis dokumen yang sangat detail dan teliti dalam mengekstrak aturan format."
                ),
                HumanMessage(content=prompt),
            ]

            # Kirim request ke Gemini dengan retry
            response = None
            for attempt in range(3):
                try:
                    response = self.llm.invoke(messages)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise e
                    time.sleep(2)  # Wait before retry

            if not response:
                raise Exception("No response from Gemini API")

            # Parse response
            response_text = response.content

            # Coba extract JSON dari response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start != -1 and json_end != -1:
                json_text = response_text[json_start:json_end]
                rules = json.loads(json_text)
            else:
                # Fallback: buat struktur default jika parsing gagal
                rules = self._create_fallback_rules()

            # Normalisasi dan validasi rules
            rules = self._normalize_rules(rules)

            # Simpan ke cache
            self._save_to_cache(cache_key, rules)

            return rules

        except Exception as e:
            st.warning(f"⚠️ AI extraction error: {str(e)}")
            # Return fallback rules
            return self._create_fallback_rules()

    def _create_fallback_rules(self) -> Dict[str, Any]:
        """Buat aturan format default jika AI gagal"""
        return {
            "margin": {"top": 3, "bottom": 3, "left": 3, "right": 3},
            "font": {
                "family": "Times New Roman",
                "body_size": 12,
                "heading_size": 14,
                "subheading_size": 12,
            },
            "spacing": {"line_spacing": 1.5, "paragraph_spacing": 6},
            "paper": {"size": "A4", "orientation": "portrait"},
            "headers_footers": {"enabled": True, "page_numbers": True},
            "numbering": {
                "page_numbering": "arabic",
                "chapter_numbering": "roman_upper",
                "section_numbering": "decimal",
            },
            "document_structure": [
                "Halaman Judul",
                "Daftar Isi",
                "BAB I PENDAHULUAN",
                "BAB II TINJAUAN PUSTAKA",
                "BAB III METODOLOGI",
                "BAB IV HASIL DAN PEMBAHASAN",
                "BAB V KESIMPULAN",
                "Daftar Pustaka",
            ],
        }

    def _normalize_rules(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Normalisasi dan validasi rules"""
        normalized = self._create_fallback_rules()

        # Update dengan rules yang diekstrak
        if isinstance(rules, dict):
            for key, value in rules.items():
                if key in normalized:
                    if isinstance(value, dict) and isinstance(normalized[key], dict):
                        normalized[key].update(value)
                    else:
                        normalized[key] = value

        return normalized


class TemplateGenerator:
    """Generate template dokumen berdasarkan aturan format"""

    def generate_template(self, rules: Dict[str, Any]) -> BytesIO:
        """Generate template Word document"""
        try:
            # Create new document
            doc = Document()

            # Set page margins
            margins = rules.get("margin", {})
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(margins.get("top", 3) / 2.54)
                section.bottom_margin = Inches(margins.get("bottom", 3) / 2.54)
                section.left_margin = Inches(margins.get("left", 3) / 2.54)
                section.right_margin = Inches(margins.get("right", 3) / 2.54)

            # Add title
            title = doc.add_heading("TEMPLATE DOKUMEN", level=1)
            title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            # Add document structure based on rules
            structure = rules.get("document_structure", [])
            for item in structure:
                if "BAB" in item.upper():
                    heading = doc.add_heading(item, level=1)
                    heading.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                    # Add sample content
                    p = doc.add_paragraph("\\n[Konten untuk bagian ini]\\n")

                else:
                    doc.add_heading(item, level=2)
                    doc.add_paragraph("\\n[Konten akan diisi di sini]\\n")

            # Set font for all paragraphs
            font_info = rules.get("font", {})
            for paragraph in doc.paragraphs:
                for run in paragraph.runs:
                    run.font.name = font_info.get("family", "Times New Roman")
                    run.font.size = Pt(font_info.get("body_size", 12))

            # Save to BytesIO
            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)

            return doc_io

        except Exception as e:
            st.error(f"Error generating template: {str(e)}")
            # Return minimal template
            doc = Document()
            doc.add_heading("Template Dokumen", level=1)
            doc.add_paragraph("Template minimal - error dalam generating.")

            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)
            return doc_io


def main():
    # Simple CSS - mirip ui.html
    st.markdown(
        """
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .block-container {
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        max-width: 800px;
        padding: 2rem;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    .header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .header h1 {
        color: #667eea;
        font-size: 2.5em;
        margin-bottom: 0.5rem;
    }
    .header p {
        color: #666;
        font-size: 1.1em;
    }
    .upload-section {
        border: 3px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
        margin: 2rem 0;
    }
    .file-info {
        background: #f8f9ff;
        border: 1px solid #e0e0ff;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        width: 100%;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header - sederhana seperti ui.html
    st.markdown(
        """
    <div class="header">
        <h1>📄 Sistem Otomasi Template Dokumen</h1>
        <p>Ekstrak aturan format dari dokumen panduan dan buat template otomatis</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Main upload area
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)

    # File upload
    st.subheader("📤 Upload Dokumen Panduan")
    uploaded_file = st.file_uploader(
        "Pilih file dokumen panduan",
        type=["txt", "docx"],
        help="Upload dokumen yang berisi aturan format untuk template",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        # File info
        st.markdown(
            f"""
            <div class="file-info">
                <strong>📁 File:</strong> {uploaded_file.name}<br>
                <strong>📏 Ukuran:</strong> {uploaded_file.size / 1024:.2f} KB
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, uploaded_file.name)

        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Initialize components
        extractor = FormatRulesExtractor()
        generator = TemplateGenerator()

        # Button columns
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Ekstrak Aturan Format"):
                with st.spinner("Menganalisis dokumen..."):
                    try:
                        rules = extractor.extract_rules_with_ai(temp_file_path)
                        st.session_state.extracted_rules = rules
                        st.success("✅ Aturan format berhasil diekstrak!")

                        # Display rules
                        with st.expander("📋 Lihat Aturan yang Diekstrak"):
                            st.json(rules)

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        with col2:
            if (
                st.button("📄 Generate Template")
                and "extracted_rules" in st.session_state
            ):
                with st.spinner("Membuat template..."):
                    try:
                        rules = st.session_state.extracted_rules
                        template_io = generator.generate_template(rules)

                        st.success("✅ Template berhasil dibuat!")

                        # Download button
                        st.download_button(
                            label="⬇️ Download Template",
                            data=template_io.getvalue(),
                            file_name="template_dokumen.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        # Cleanup
        try:
            os.remove(temp_file_path)
            os.rmdir(temp_dir)
        except:
            pass

    else:
        # Instructions when no file uploaded
        st.info("👆 Silakan upload dokumen panduan format untuk memulai")

        # Example download
        st.subheader("📥 Contoh Dokumen Panduan")
        example_content = """PANDUAN FORMAT DOKUMEN

1. MARGIN
   - Atas: 4 cm
   - Bawah: 3 cm
   - Kiri: 4 cm
   - Kanan: 3 cm

2. FONT
   - Jenis: Times New Roman
   - Ukuran: 12 pt untuk isi
   - Ukuran: 14 pt untuk judul bab

3. SPASI
   - Antar baris: 1,5 (satu setengah)
   - Antar paragraf: 6 pt setelah paragraf

4. STRUKTUR DOKUMEN
   - Halaman Judul
   - Daftar Isi
   - BAB I PENDAHULUAN
   - BAB II TINJAUAN PUSTAKA
   - BAB III METODOLOGI
   - BAB IV HASIL DAN PEMBAHASAN
   - BAB V KESIMPULAN
   - Daftar Pustaka"""

        st.download_button(
            label="📄 Download Contoh",
            data=example_content,
            file_name="contoh_panduan.txt",
            mime="text/plain",
        )


if __name__ == "__main__":
    main()
