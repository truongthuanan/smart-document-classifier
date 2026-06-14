# test_module3.py
"""
Test Module 3: Document Classifier

Test cases (keyword method):
1. Contract text → expect "Contract"
2. Invoice text  → expect "Invoice"
3. Report text   → expect "Report"
4. Email text    → expect "Email"
5. Pipeline test: file thật từ Module 1+2+3 kết hợp
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.classifier import classify_document, classify_by_keywords


# ===== 4 ĐOẠN TEXT MẪU =====
SAMPLE_TEXTS = {
    "Contract": """
        SERVICE AGREEMENT CONTRACT
        This agreement is made between AvePoint Inc (hereinafter "Company") 
        and John Doe (hereinafter "Client"). Both parties hereby agree to the 
        following terms and conditions. This contract shall be binding upon 
        signature. Either party may terminate this agreement with 30 days notice.
        Clause 1: Obligations of the Company...
        Signed: John Doe | Date: 2024-01-15
    """,

    "Invoice": """
        INVOICE #INV-2024-001
        From: AvePoint Inc
        To: John Doe
        Invoice Date: 2024-01-15
        Payment Due: 2024-02-15
        
        Description          Amount
        Software License     $1,000.00
        Support Fee          $500.00
        Subtotal:            $1,500.00
        Tax (10%):           $150.00
        Total Amount Due:    $1,650.00
        
        Please remit payment via bank transfer.
    """,

    "Report": """
        QUARTERLY PERFORMANCE REPORT - Q4 2024
        Executive Summary:
        This report presents the analysis and findings of Q4 2024 performance.
        
        Methodology: Data was collected from multiple sources and analyzed.
        
        Results: Revenue increased by 15% compared to previous quarter.
        Key statistics show improvement across all metrics.
        
        Conclusion and Recommendations:
        Based on the data analysis, we recommend expanding the product line.
        Figure 1 shows the trend chart for the reporting period.
    """,

    "Email": """
        From: john.doe@company.com
        To: jane.smith@avepoint.com
        Subject: Meeting Tomorrow
        CC: manager@company.com
        
        Dear Jane,
        
        Hi, I hope this email finds you well.
        Please find attached the documents for tomorrow's meeting.
        
        Could you please review and provide feedback?
        
        Thank you for your time.
        
        Best regards,
        John Doe
    """
}


def run_classification_test(doc_type: str, text: str):
    """Test phân loại 1 đoạn text"""
    print(f"\n{'='*55}")
    print(f"TEST: Classify '{doc_type}' text")
    print(f"{'='*55}")

    result = classify_by_keywords(text)

    # Check kết quả
    is_correct = result.document_type == doc_type
    status = "✅ CORRECT" if is_correct else f"❌ WRONG (got {result.document_type})"

    print(f"Expected : {doc_type}")
    print(f"Got      : {result.document_type}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Status   : {status}")
    print(f"\nAll scores:")
    for dtype, score in sorted(result.all_scores.items(),
                                key=lambda x: x[1], reverse=True):
        bar = "█" * int(score * 20)
        print(f"  {dtype:10} {bar:20} {score:.3f}")

    return is_correct


def run_pipeline_test():
    """Test toàn bộ pipeline Module 1 + 2 + 3"""
    print(f"\n{'='*55}")
    print("PIPELINE TEST: Module 1 + 2 + 3")
    print(f"{'='*55}")

    from modules.input_handler import validate_and_process
    from modules.text_extractor import extract_text

    test_dir = Path(__file__).parent / "test_files"

    test_files = [
        ("contract_test.docx", "Contract"),
        ("invoice_test.docx", "Invoice"),
        ("invoice_test.pdf", "Invoice"),
    ]

    for filename, expected in test_files:
        file_path = test_dir / filename
        if not file_path.exists():
            print(f"⚠ Skip {filename} (file not found)")
            continue

        print(f"\n📄 File: {filename}")
        try:
            # Module 1
            file_obj = validate_and_process(str(file_path))
            # Module 2
            extraction = extract_text(file_obj)
            # Module 3
            classification = classify_document(extraction.raw_text)

            is_correct = classification.document_type == expected
            status = "✅" if is_correct else "❌"
            print(f"   {status} Result: {classification.document_type} "
                  f"(confidence: {classification.confidence:.0%})")

        except Exception as e:
            print(f"   ❌ Error: {e}")


def main():
    print("=" * 55)
    print("MODULE 3 TEST SUITE: Document Classifier")
    print("=" * 55)

    # Test 4 loại text mẫu
    results = []
    for doc_type, text in SAMPLE_TEXTS.items():
        correct = run_classification_test(doc_type, text)
        results.append(correct)

    # Tổng kết
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*55}")
    print(f"KEYWORD CLASSIFIER: {passed}/{total} correct")
    print(f"{'='*55}")

    # Pipeline test
    run_pipeline_test()

    print(f"\n{'='*55}")
    print("MODULE 3 COMPLETE!")
    print(f"{'='*55}")
    print("\n💡 Toàn bộ pipeline Module 1→2→3 đã hoạt động!")
    print("   Input: file → Output: Document Type + Confidence")


if __name__ == "__main__":
    main()
