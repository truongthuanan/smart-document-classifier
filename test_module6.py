# test_module6.py
"""Test Module 6: Orchestrator - Full Pipeline via single function call"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from services.document_processor import process_document


def main():
    print("=" * 55)
    print("MODULE 6 TEST: Orchestrator")
    print("Gọi process_document() 1 lần → nhận kết quả đầy đủ")
    print("=" * 55)

    test_dir = Path(__file__).parent / "test_files"

    # Test valid files
    for filename in ["contract_test.docx", "invoice_test.docx", "invoice_test.pdf"]:
        fpath = test_dir / filename
        if not fpath.exists():
            continue
        result = process_document(str(fpath))
        result.print_summary()

    # Test error handling: invalid file
    print(f"\n{'='*55}")
    print("TEST: Error handling với file không tồn tại")
    result = process_document("nonexistent.pdf")
    result.print_summary()

    # Test JSON output
    print(f"\n{'='*55}")
    print("TEST: JSON output (cho FastAPI)")
    result = process_document(str(test_dir / "contract_test.docx"))
    import json
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
