# test_module1.py
"""
Test script cho Module 1: Input Handler

Test cases:
1. ✅ Valid PDF file
2. ✅ Valid DOCX file
3. ❌ Invalid extension (.txt)
4. ❌ File quá lớn (> 10MB)
5. ❌ Magic bytes mismatch (fake PDF)
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from modules.input_handler import (
    validate_and_process,
    validate_and_process_bytes,
    FileValidationError,
    FileSizeError,
    FileTypeError,
    SecurityError
)


def create_test_files():
    """Tạo sample files để test"""
    test_dir = Path(__file__).parent / "test_files"
    test_dir.mkdir(exist_ok=True)
    
    # Test 1: Valid PDF
    pdf_path = test_dir / "sample.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n%Sample PDF content here...' + b'x' * 1000)
    
    # Test 2: Valid DOCX (ZIP format)
    docx_path = test_dir / "sample.docx"
    with open(docx_path, 'wb') as f:
        f.write(b'PK\x03\x04' + b'x' * 1000)  # ZIP magic bytes
    
    # Test 3: Invalid extension
    txt_path = test_dir / "invalid.txt"
    with open(txt_path, 'w') as f:
        f.write("This is a text file")
    
    # Test 4: File quá lớn (11 MB)
    large_path = test_dir / "large.pdf"
    with open(large_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')
        f.write(b'x' * (11 * 1024 * 1024))  # 11 MB
    
    # Test 5: Fake PDF (wrong magic bytes)
    fake_path = test_dir / "fake.pdf"
    with open(fake_path, 'wb') as f:
        f.write(b'FAKE' + b'x' * 1000)  # Wrong magic bytes
    
    return test_dir


def run_test(test_name: str, file_path: Path, should_pass: bool):
    """
    Helper function để chạy 1 test case
    
    Args:
        test_name (str): Tên test
        file_path (Path): Đường dẫn file test
        should_pass (bool): True nếu expect pass, False nếu expect fail
    """
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"File: {file_path.name}")
    
    try:
        file_obj = validate_and_process(str(file_path))
        
        if should_pass:
            print("✅ PASS - File validated successfully")
            print(f"   {file_obj}")
        else:
            print("❌ FAIL - Expected validation error but passed")
    
    except FileValidationError as e:
        if not should_pass:
            print(f"✅ PASS - Caught expected error")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Message: {str(e)}")
        else:
            print(f"❌ FAIL - Unexpected validation error")
            print(f"   {type(e).__name__}: {str(e)}")
    
    except Exception as e:
        print(f"❌ FAIL - Unexpected exception")
        print(f"   {type(e).__name__}: {str(e)}")


def main():
    """Main test runner"""
    print("=" * 60)
    print("MODULE 1 TEST SUITE: Input Handler")
    print("=" * 60)
    
    # Tạo test files
    print("\n📁 Creating test files...")
    test_dir = create_test_files()
    print(f"✓ Test files created in: {test_dir}")
    
    # Run tests
    run_test(
        "Test 1: Valid PDF File",
        test_dir / "sample.pdf",
        should_pass=True
    )
    
    run_test(
        "Test 2: Valid DOCX File",
        test_dir / "sample.docx",
        should_pass=True
    )
    
    run_test(
        "Test 3: Invalid Extension (.txt)",
        test_dir / "invalid.txt",
        should_pass=False
    )
    
    run_test(
        "Test 4: File Too Large (> 10MB)",
        test_dir / "large.pdf",
        should_pass=False
    )
    
    run_test(
        "Test 5: Security Check - Fake PDF (Wrong Magic Bytes)",
        test_dir / "fake.pdf",
        should_pass=False
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUITE COMPLETED")
    print(f"{'='*60}")
    print("\n📊 Expected Results:")
    print("   - Test 1, 2: Should PASS ✅")
    print("   - Test 3, 4, 5: Should FAIL with specific errors ❌")
    print("\n💡 Next step: Giải thích lại logic của module cho Study Agent!")


if __name__ == "__main__":
    main()
