# modules/text_extractor.py
"""
TEXT EXTRACTOR MODULE
=====================
Nhiệm vụ:
- Nhận FileObject từ Module 1
- Đọc nội dung text từ PDF / DOCX / Image
- Trả về text thuần (string) để Module 3 phân loại

3 loại file → 3 cách đọc khác nhau:
    PDF   → pdfplumber (chính xác hơn PyPDF2)
    DOCX  → python-docx
    Image → pytesseract (OCR: đọc chữ trong ảnh)
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from modules.input_handler import FileObject


# ===== DATA CLASS: ExtractionResult =====
@dataclass
class ExtractionResult:
    """
    Kết quả sau khi extract text

    Attributes:
        raw_text   : Toàn bộ text đọc được (string)
        method     : Phương pháp đã dùng ("pdfplumber", "docx", "ocr")
        page_count : Số trang (nếu có)
        confidence : Độ tin cậy (0.0 - 1.0)
                     PDF/DOCX = 1.0 (chắc chắn đúng)
                     OCR      = 0.7 (có thể nhận sai chữ)
        error      : Thông báo lỗi nếu extract thất bại
    """
    raw_text: str
    method: str
    page_count: int = 1
    confidence: float = 1.0
    error: Optional[str] = None

    def __repr__(self):
        preview = self.raw_text[:80].replace('\n', ' ')
        return (f"ExtractionResult("
                f"method='{self.method}', "
                f"pages={self.page_count}, "
                f"confidence={self.confidence}, "
                f"chars={len(self.raw_text)}, "
                f"preview='{preview}...')")


# ===== EXCEPTION =====
class ExtractionError(Exception):
    """Lỗi khi không thể extract text từ file"""
    pass


# ===== EXTRACTOR FUNCTIONS =====

def extract_from_pdf(file_obj: FileObject) -> ExtractionResult:
    """
    Đọc text từ file PDF dùng pdfplumber

    Tại sao dùng pdfplumber thay vì PyPDF2?
    - pdfplumber xử lý tốt hơn với PDF có bảng biểu
    - Giữ nguyên layout tốt hơn
    - Hỗ trợ tốt hơn với PDF tiếng Việt/có font đặc biệt

    Args:
        file_obj: FileObject từ Module 1

    Returns:
        ExtractionResult với text và số trang
    """
    try:
        import pdfplumber
        import io

        # Đọc PDF từ bytes (không cần save ra file)
        # io.BytesIO: giả lập file trong RAM
        pdf_bytes = io.BytesIO(file_obj.content_bytes)

        all_text = []
        page_count = 0

        with pdfplumber.open(pdf_bytes) as pdf:
            page_count = len(pdf.pages)

            for page in pdf.pages:
                # extract_text() đọc toàn bộ text trên 1 trang
                text = page.extract_text()
                if text:
                    all_text.append(text)

        # Ghép tất cả trang lại, ngăn cách bằng newline
        combined_text = "\n\n".join(all_text)

        if not combined_text.strip():
            # PDF không có text (có thể là PDF scan/ảnh)
            return ExtractionResult(
                raw_text="",
                method="pdfplumber",
                page_count=page_count,
                confidence=0.0,
                error="PDF không có text. Có thể là PDF dạng ảnh scan."
            )

        return ExtractionResult(
            raw_text=combined_text,
            method="pdfplumber",
            page_count=page_count,
            confidence=1.0
        )

    except Exception as e:
        raise ExtractionError(f"Không thể đọc PDF: {str(e)}")


def extract_from_docx(file_obj: FileObject) -> ExtractionResult:
    """
    Đọc text từ file DOCX dùng python-docx

    Cấu trúc DOCX:
    - Document gồm nhiều Paragraph
    - Mỗi Paragraph gồm nhiều Run (đoạn text cùng format)
    - Ta lấy text từng Paragraph rồi ghép lại

    Args:
        file_obj: FileObject từ Module 1

    Returns:
        ExtractionResult với text
    """
    try:
        from docx import Document
        import io

        # Đọc DOCX từ bytes
        docx_bytes = io.BytesIO(file_obj.content_bytes)
        doc = Document(docx_bytes)

        # Lấy text từng paragraph
        # paragraph.text tự động ghép các Run lại
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:  # Bỏ qua paragraph rỗng
                paragraphs.append(text)

        combined_text = "\n".join(paragraphs)

        if not combined_text.strip():
            return ExtractionResult(
                raw_text="",
                method="python-docx",
                confidence=0.0,
                error="File DOCX không có text."
            )

        return ExtractionResult(
            raw_text=combined_text,
            method="python-docx",
            page_count=1,  # DOCX không có khái niệm "trang" rõ ràng
            confidence=1.0
        )

    except Exception as e:
        raise ExtractionError(f"Không thể đọc DOCX: {str(e)}")


def extract_from_image(file_obj: FileObject) -> ExtractionResult:
    """
    Đọc text từ ảnh dùng pytesseract (OCR)

    OCR là gì?
    - OCR = Optical Character Recognition
    - Dùng AI để "nhìn" vào ảnh và nhận ra chữ
    - Ví dụ: chụp ảnh hóa đơn → OCR đọc ra số tiền, ngày tháng

    pytesseract = Python wrapper cho Tesseract OCR (open-source của Google)

    Args:
        file_obj: FileObject từ Module 1

    Returns:
        ExtractionResult với text và confidence thấp hơn (0.7)
    """
    try:
        import pytesseract
        from PIL import Image
        import io

        # Mở ảnh từ bytes
        image_bytes = io.BytesIO(file_obj.content_bytes)
        image = Image.open(image_bytes)

        # OCR: đọc text từ ảnh
        # lang='eng' = ngôn ngữ tiếng Anh
        # Nếu muốn tiếng Việt: lang='vie' (cần cài thêm language pack)
        extracted_text = pytesseract.image_to_string(
            image,
            lang='eng',
            config='--psm 3'  # psm 3 = tự động detect layout
        )

        if not extracted_text.strip():
            return ExtractionResult(
                raw_text="",
                method="ocr-tesseract",
                confidence=0.0,
                error="OCR không đọc được chữ trong ảnh."
            )

        return ExtractionResult(
            raw_text=extracted_text,
            method="ocr-tesseract",
            page_count=1,
            confidence=0.7  # OCR có thể nhận sai ~30% ký tự
        )

    except Exception as e:
        raise ExtractionError(f"Không thể OCR ảnh: {str(e)}")


# ===== MAIN ENTRY POINT =====

def extract_text(file_obj: FileObject) -> ExtractionResult:
    """
    Main function: Tự động chọn phương pháp extract phù hợp

    Logic:
        Nhìn vào extension của FileObject → gọi đúng hàm

        .pdf  → extract_from_pdf()
        .docx → extract_from_docx()
        .png/.jpg/.jpeg → extract_from_image()

    Args:
        file_obj: FileObject đã validate từ Module 1

    Returns:
        ExtractionResult chứa text đã extract

    Example:
        >>> file_obj = validate_and_process("contract.pdf")
        >>> result = extract_text(file_obj)
        >>> print(result.raw_text[:100])
        "This agreement is made between..."
    """
    ext = file_obj.extension.lower()

    # Route đến đúng extractor dựa vào extension
    if ext == '.pdf':
        return extract_from_pdf(file_obj)

    elif ext == '.docx':
        return extract_from_docx(file_obj)

    elif ext in ('.png', '.jpg', '.jpeg'):
        return extract_from_image(file_obj)

    else:
        # Không nên xảy ra vì Module 1 đã validate
        raise ExtractionError(f"Không hỗ trợ extension: {ext}")


if __name__ == "__main__":
    print("Text Extractor Module")
    print("=" * 50)
    print("Supported: PDF (pdfplumber), DOCX (python-docx), Image (pytesseract)")
