# config/settings.py
"""
Configuration file cho Document Classifier Project
Chứa constants, file size limits, allowed extensions
"""

import os
from pathlib import Path

# ===== PROJECT PATHS =====
PROJECT_ROOT = Path(__file__).parent.parent
TEMP_DIR = PROJECT_ROOT / "temp"
LOGS_DIR = PROJECT_ROOT / "logs"

# Tạo folder nếu chưa có
TEMP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


# ===== FILE VALIDATION SETTINGS =====
# Các định dạng file được phép upload
ALLOWED_EXTENSIONS = {
    '.pdf',   # PDF documents
    '.docx',  # Word documents
    '.png',   # Images (for OCR)
    '.jpg',
    '.jpeg'
}

# Kích thước file tối đa (bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MIN_FILE_SIZE = 100  # 100 bytes (tránh file rỗng)

# Magic bytes để detect file type thật (security check)
# Tránh trường hợp user đổi .exe → .pdf để bypass
MAGIC_BYTES = {
    'pdf': b'%PDF',
    'docx': b'PK\x03\x04',  # DOCX là ZIP file
    'png': b'\x89PNG',
    'jpg': b'\xff\xd8\xff',
    'jpeg': b'\xff\xd8\xff'
}


# ===== AZURE SETTINGS (sẽ dùng ở module sau) =====
AZURE_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT", "")
AZURE_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY", "")

# Flag để bật/tắt Azure (nếu chưa có account, dùng local fallback)
USE_AZURE = bool(AZURE_ENDPOINT and AZURE_KEY)


# ===== LOGGING SETTINGS =====
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# ===== CLASSIFICATION SETTINGS (cho module sau) =====
DOCUMENT_TYPES = ["Contract", "Invoice", "Report", "Email"]
CONFIDENCE_THRESHOLD = 0.6  # Dưới 60% → "Unknown"


# ===== COMPLIANCE SETTINGS (cho module sau) =====
SENSITIVITY_THRESHOLDS = {
    "LOW": (0, 30),
    "MEDIUM": (30, 60),
    "HIGH": (60, 100)
}
