# test_module4.py
"""Test Module 4: Entity Extractor"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.entity_extractor import extract_entities


SAMPLE_TEXTS = {
    "Invoice": """
        INVOICE #INV-2024-001
        From: AvePoint Inc
        To: John Doe
        Date: 2024-01-15
        Payment Due: 2024-02-15
        Amount Due: $1,500.00
        Contact: john.doe@company.com
        Phone: +84-123-456-789
    """,

    "Contract": """
        SERVICE CONTRACT
        This agreement is between Microsoft Corp and Jane Smith.
        Effective Date: January 15, 2024
        Termination Date: 2024-12-31
        Contract Value: $50,000.00
        Reference: REF-2024-CONTRACT-001
        Contact: jane.smith@microsoft.com
    """,

    "Email": """
        From: john.doe@company.com
        To: jane.smith@avepoint.com
        Subject: Meeting Tomorrow
        Date: 15/01/2024

        Dear Jane Smith,
        Please find attached invoice INV-001 for $500.
        Best regards,
        John Doe
    """
}


def main():
    print("=" * 55)
    print("MODULE 4 TEST SUITE: Entity Extractor")
    print("=" * 55)

    for doc_type, text in SAMPLE_TEXTS.items():
        print(f"\n{'='*55}")
        print(f"TEST: Extract entities from {doc_type}")
        print(f"{'='*55}")
        result = extract_entities(text)
        print(result.summary())

    # Pipeline test: Module 1+2+3+4
    print(f"\n{'='*55}")
    print("FULL PIPELINE TEST: Module 1 → 2 → 3 → 4")
    print(f"{'='*55}")

    from modules.input_handler import validate_and_process
    from modules.text_extractor import extract_text
    from modules.classifier import classify_document

    test_dir = Path(__file__).parent / "test_files"
    for filename in ["contract_test.docx", "invoice_test.docx"]:
        fpath = test_dir / filename
        if not fpath.exists():
            continue
        print(f"\n📄 {filename}")
        file_obj = validate_and_process(str(fpath))
        extraction = extract_text(file_obj)
        classification = classify_document(extraction.raw_text)
        entities = extract_entities(extraction.raw_text)

        print(f"  Type      : {classification.document_type} ({classification.confidence:.0%})")
        print(entities.summary())

    print(f"\n{'='*55}")
    print("MODULE 4 COMPLETE!")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
