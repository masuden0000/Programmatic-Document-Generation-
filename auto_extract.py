#!/usr/bin/env python3
"""
Auto Document Extractor
File untuk otomatis mengekstrak informasi format dari dokumen .docx di folder Documents

Usage: python auto_extract.py [path_to_docx_file]
Jika tidak ada path, akan mencari file .docx di folder Documents user
"""

import hashlib
import json
import os
import pickle
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Import untuk document processing
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.document_loaders import Docx2txtLoader
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()


class FormatRulesExtractor:
    """Mengekstrak aturan format dari dokumen panduan"""

    def __init__(self):
        # Initialize Gemini model
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            print(
                "❌ GOOGLE_API_KEY tidak ditemukan! Pastikan sudah setting di file .env"
            )
            print("📝 Buat file .env dan tambahkan: GOOGLE_API_KEY=your_api_key_here")
            sys.exit(1)

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

        print(f"📄 Memproses dokumen: {document_path}")

        # Load dokumen
        try:
            if document_path.lower().endswith(".txt"):
                # Handle .txt files
                with open(document_path, "r", encoding="utf-8") as f:
                    full_text = f.read()
                print(f"📄 Loaded .txt file directly")
            else:
                # Handle .docx files
                loader = Docx2txtLoader(document_path)
                documents = loader.load()
                full_text = "\\n".join([doc.page_content for doc in documents])
                print(f"📄 Loaded .docx file via langchain")
        except Exception as e:
            print(f"❌ Error loading document: {str(e)}")
            return self._create_fallback_rules()

        # Remove the duplicate line
        # full_text = "\\n".join([doc.page_content for doc in documents])

        # Cek cache terlebih dahulu
        cache_key = self._get_cache_key(full_text)
        cached_result = self._load_from_cache(cache_key)
        if cached_result:
            print("📋 Menggunakan hasil dari cache...")
            return cached_result

        # Jika teks terlalu panjang, potong ke 12000 karakter pertama
        if len(full_text) > 12000:
            full_text = full_text[:12000] + "..."
            print(f"📏 Teks dipotong ke {len(full_text)} karakter")

        print(f"📊 Ukuran teks: {len(full_text)} karakter")
        print("🤖 Mengirim ke Gemini AI untuk analisis...")

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
                    print(f"🔄 Percobaan {attempt + 1}/3 ke Gemini API...")
                    response = self.llm.invoke(messages)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise e
                    print(f"⚠️ Percobaan {attempt + 1} gagal: {str(e)}")
                    time.sleep(2)  # Wait before retry

            if not response:
                raise Exception("No response from Gemini API")

            print("✅ Response diterima dari Gemini AI")

            # Parse response
            response_text = response.content

            # Ensure response_text is string
            if not isinstance(response_text, str):
                response_text = str(response_text)

            # Coba extract JSON dari response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start != -1 and json_end != -1:
                json_text = response_text[json_start:json_end]
                rules = json.loads(json_text)
                print("✅ JSON berhasil di-parse")
            else:
                print(
                    "⚠️ JSON tidak ditemukan dalam response, menggunakan fallback rules"
                )
                rules = self._create_fallback_rules()

            # Normalisasi dan validasi rules
            rules = self._normalize_rules(rules)

            # Simpan ke cache
            self._save_to_cache(cache_key, rules)
            print("💾 Hasil disimpan ke cache")

            return rules

        except Exception as e:
            print(f"❌ AI extraction error: {str(e)}")
            print("🔄 Menggunakan fallback rules...")
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


def find_docx_files(directory: str) -> List[str]:
    """Cari semua file .docx dan .txt di directory"""
    files = []
    for ext in ["*.docx", "*.txt"]:
        for file in Path(directory).glob(f"**/{ext}"):
            # Skip temporary files yang dimulai dengan ~$
            if not file.name.startswith("~$"):
                files.append(str(file))
    return files


def print_results(rules: Dict[str, Any], filename: str):
    """Print hasil ekstraksi dengan format yang rapi"""
    print("\\n" + "=" * 80)
    print(f"📋 HASIL EKSTRAKSI AI - {filename}")
    print("=" * 80)

    # Print setiap kategori
    for category, data in rules.items():
        print(f"\\n📌 {category.upper().replace('_', ' ')}:")
        print("-" * 40)

        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  • {key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data, 1):
                print(f"  {i}. {item}")
        else:
            print(f"  {data}")

    print("\\n" + "=" * 80)


def save_to_json(rules: Dict[str, Any], filename: str):
    """Simpan hasil ke file JSON"""
    output_file = f"extracted_rules_{Path(filename).stem}.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2, ensure_ascii=False)
        print(f"💾 Hasil disimpan ke: {output_file}")
    except Exception as e:
        print(f"❌ Error saving to JSON: {str(e)}")


def main():
    print("🚀 Auto Document Extractor")
    print("=" * 50)

    # Check if file path provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"❌ File tidak ditemukan: {file_path}")
            sys.exit(1)

        if not (
            file_path.lower().endswith(".docx") or file_path.lower().endswith(".txt")
        ):
            print("❌ File harus berformat .docx atau .txt")
            sys.exit(1)

        files_to_process = [file_path]
    else:
        # Auto-detect documents in Documents folder
        documents_folder = str(Path.home() / "Documents")
        print(f"🔍 Mencari file .docx dan .txt di: {documents_folder}")

        files_to_process = find_docx_files(documents_folder)

        if not files_to_process:
            print("❌ Tidak ada file .docx atau .txt ditemukan di folder Documents")
            print("💡 Usage: python auto_extract.py [path_to_file]")
            sys.exit(1)

        print(f"📄 Ditemukan {len(files_to_process)} file:")
        for i, file in enumerate(files_to_process, 1):
            print(f"  {i}. {Path(file).name}")

        # Pilih file pertama atau biarkan user memilih
        if len(files_to_process) > 1:
            print(
                "\\n📌 Memproses file pertama. Untuk memproses file lain, jalankan dengan path spesifik."
            )

        files_to_process = [files_to_process[0]]

    # Initialize extractor
    try:
        extractor = FormatRulesExtractor()
    except Exception as e:
        print(f"❌ Error initializing extractor: {str(e)}")
        sys.exit(1)

    # Process each file
    for file_path in files_to_process:
        print(f"\\n🔄 Processing: {Path(file_path).name}")

        try:
            # Extract rules
            rules = extractor.extract_rules_with_ai(file_path)

            # Print results
            print_results(rules, Path(file_path).name)

            # Save to JSON
            save_to_json(rules, file_path)

            print(f"✅ Selesai memproses: {Path(file_path).name}")

        except Exception as e:
            print(f"❌ Error processing {file_path}: {str(e)}")

    print("\\n🎉 Auto extraction completed!")


if __name__ == "__main__":
    main()
