# modules/input_handler.py
"""
INPUT HANDLER MODULE
====================
Nhiệm vụ:
1. Validate file upload (size, extension, magic bytes)
2. Normalize file object thành format chuẩn
3. Security check để tránh malicious files

Class chính: FileObject - đại diện cho 1 file đã validate
Function chính: validate_and_process() - entry point
"""

import os
import mimetypes
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple

# Import config
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import (
    ALLOWED_EXTENSIONS, 
    MAX_FILE_SIZE, 
    MIN_FILE_SIZE, 
    MAGIC_BYTES
)


# ===== DATA CLASS: FileObject =====
@dataclass
class FileObject:
    """
    Data class đại diện cho 1 file đã được validate
    
    Attributes:
        filename (str): Tên file gốc (ví dụ: "contract.pdf")
        content_bytes (bytes): Nội dung file dạng binary
        mime_type (str): MIME type (ví dụ: "application/pdf")
        file_size (int): Kích thước file (bytes)
        extension (str): Extension (ví dụ: ".pdf")
    """
    filename: str
    content_bytes: bytes
    mime_type: str
    file_size: int
    extension: str
    
    def __repr__(self):
        """Custom representation để dễ debug"""
        size_kb = self.file_size / 1024
        return (f"FileObject(filename='{self.filename}', "
                f"type='{self.mime_type}', "
                f"size={size_kb:.2f}KB)")


# ===== EXCEPTION CLASSES =====
class FileValidationError(Exception):
    """Base exception cho mọi lỗi validation"""
    pass

class FileSizeError(FileValidationError):
    """File quá lớn hoặc quá nhỏ"""
    pass

class FileTypeError(FileValidationError):
    """File type không được support"""
    pass

class SecurityError(FileValidationError):
    """File có vấn đề về security (magic bytes mismatch)"""
    pass


# ===== CORE FUNCTIONS =====

def validate_file_size(file_size: int) -> None:
    """
    Kiểm tra kích thước file có hợp lệ không
    
    Args:
        file_size (int): Kích thước file (bytes)
    
    Raises:
        FileSizeError: Nếu file quá lớn hoặc quá nhỏ
    
    Logic:
        - File < 100 bytes → có thể là file rỗng hoặc corrupt
        - File > 10 MB → tốn cost khi xử lý (Azure pricing)
    """
    if file_size < MIN_FILE_SIZE:
        raise FileSizeError(
            f"File quá nhỏ ({file_size} bytes). "
            f"Minimum: {MIN_FILE_SIZE} bytes"
        )
    
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise FileSizeError(
            f"File quá lớn ({size_mb:.2f} MB). "
            f"Maximum: {max_mb:.2f} MB"
        )


def validate_file_extension(filename: str) -> str:
    """
    Kiểm tra extension có được phép không
    
    Args:
        filename (str): Tên file (ví dụ: "document.pdf")
    
    Returns:
        str: Extension lowercase (ví dụ: ".pdf")
    
    Raises:
        FileTypeError: Nếu extension không được support
    
    Logic:
        - Extract extension từ filename
        - Normalize về lowercase (tránh .PDF vs .pdf)
        - Check trong ALLOWED_EXTENSIONS
    """
    extension = Path(filename).suffix.lower()
    
    if not extension:
        raise FileTypeError(
            f"File '{filename}' không có extension. "
            f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if extension not in ALLOWED_EXTENSIONS:
        raise FileTypeError(
            f"Extension '{extension}' không được support. "
            f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    return extension


def validate_magic_bytes(content_bytes: bytes, extension: str) -> bool:
    """
    Security check: Verify magic bytes match extension
    
    Args:
        content_bytes (bytes): Nội dung file
        extension (str): Extension claimed (ví dụ: ".pdf")
    
    Returns:
        bool: True nếu magic bytes match
    
    Raises:
        SecurityError: Nếu magic bytes không match
    
    Logic:
        Magic bytes = 4-8 bytes đầu tiên của file, unique cho mỗi format
        Ví dụ:
            - PDF:  %PDF (25 50 44 46)
            - PNG:  \x89PNG (89 50 4E 47)
            - JPEG: \xff\xd8\xff (FF D8 FF)
        
        Tại sao quan trọng?
        - User có thể rename virus.exe → contract.pdf
        - Extension không đáng tin, phải check binary signature
    """
    # Normalize extension (remove dot)
    ext_key = extension.lstrip('.').lower()
    
    # Get expected magic bytes
    if ext_key not in MAGIC_BYTES:
        # Nếu không có magic bytes defined, skip check (trust extension)
        return True
    
    expected_magic = MAGIC_BYTES[ext_key]
    actual_magic = content_bytes[:len(expected_magic)]
    
    if actual_magic != expected_magic:
        raise SecurityError(
            f"Magic bytes mismatch! File claims to be '{extension}' "
            f"but binary signature is different. Possible malicious file."
        )
    
    return True


def detect_mime_type(filename: str, extension: str) -> str:
    """
    Detect MIME type của file
    
    Args:
        filename (str): Tên file
        extension (str): Extension (ví dụ: ".pdf")
    
    Returns:
        str: MIME type (ví dụ: "application/pdf")
    
    Logic:
        Sử dụng Python's mimetypes module để map extension → MIME type
        Fallback: application/octet-stream (generic binary)
    """
    mime_type, _ = mimetypes.guess_type(filename)
    
    if not mime_type:
        # Fallback mapping
        mime_mapping = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
        mime_type = mime_mapping.get(extension, 'application/octet-stream')
    
    return mime_type


# ===== MAIN ENTRY POINT =====

def validate_and_process(file_path: str) -> FileObject:
    """
    Main function: Validate và process file upload
    
    Args:
        file_path (str): Đường dẫn tới file cần validate
    
    Returns:
        FileObject: Object chứa file đã được validate
    
    Raises:
        FileValidationError: Nếu file không hợp lệ (các subclass)
    
    Workflow:
        1. Check file tồn tại
        2. Validate extension
        3. Read file content
        4. Validate size
        5. Validate magic bytes (security)
        6. Detect MIME type
        7. Return FileObject
    
    Example:
        >>> file_obj = validate_and_process("documents/contract.pdf")
        >>> print(file_obj)
        FileObject(filename='contract.pdf', type='application/pdf', size=250.50KB)
    """
    # Step 1: Check file existence
    if not os.path.exists(file_path):
        raise FileValidationError(f"File không tồn tại: {file_path}")
    
    # Step 2: Validate extension
    filename = os.path.basename(file_path)
    extension = validate_file_extension(filename)
    
    # Step 3: Read file content
    try:
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
    except Exception as e:
        raise FileValidationError(f"Không thể đọc file: {str(e)}")
    
    # Step 4: Validate size
    file_size = len(content_bytes)
    validate_file_size(file_size)
    
    # Step 5: Security check - magic bytes
    validate_magic_bytes(content_bytes, extension)
    
    # Step 6: Detect MIME type
    mime_type = detect_mime_type(filename, extension)
    
    # Step 7: Create and return FileObject
    file_obj = FileObject(
        filename=filename,
        content_bytes=content_bytes,
        mime_type=mime_type,
        file_size=file_size,
        extension=extension
    )
    
    return file_obj


# ===== UTILITY FUNCTION =====

def validate_and_process_bytes(filename: str, content_bytes: bytes) -> FileObject:
    """
    Variant: Validate file từ bytes thay vì file path
    Hữu ích khi file được upload qua web (FastAPI/Streamlit)
    
    Args:
        filename (str): Tên file (ví dụ: "contract.pdf")
        content_bytes (bytes): Nội dung file
    
    Returns:
        FileObject: Object đã validate
    
    Logic:
        Tương tự validate_and_process() nhưng skip bước read file
    """
    # Validate extension
    extension = validate_file_extension(filename)
    
    # Validate size
    file_size = len(content_bytes)
    validate_file_size(file_size)
    
    # Security check
    validate_magic_bytes(content_bytes, extension)
    
    # Detect MIME type
    mime_type = detect_mime_type(filename, extension)
    
    # Create FileObject
    file_obj = FileObject(
        filename=filename,
        content_bytes=content_bytes,
        mime_type=mime_type,
        file_size=file_size,
        extension=extension
    )
    
    return file_obj


if __name__ == "__main__":
    """
    Quick test khi chạy module trực tiếp
    """
    print("Input Handler Module")
    print("=" * 50)
    print("Supported extensions:", ALLOWED_EXTENSIONS)
    print(f"Max file size: {MAX_FILE_SIZE / (1024*1024):.1f} MB")
    print(f"Min file size: {MIN_FILE_SIZE} bytes")
