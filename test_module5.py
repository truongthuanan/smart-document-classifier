# test_module5.py
"""Test Module 5: Compliance Checker + Full Pipeline 1→2→3→4→5"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.entity_extractor import EntityResult
from modules.compliance_checker import check_compliance


def test_scoring():
    """Test scoring logic với các scenario khác nhau"""
    print("=" * 55)
    print("MODULE 5 TEST: Compliance Checker")
    print("=" * 55)

    scenarios = [
        {
            "name": "Simple Public Report (expect LOW)",
            "entities": EntityResult(
                organizations=["AvePoint Inc"]
            ),
            "doc_type": "Report"
        },
        {
            "name": "Invoice with PII (expect MEDIUM)",
            "entities": EntityResult(
                people=["John Doe"],
                amounts=["$1,500.00"],
                emails=["john@company.com"],
                organizations=["AvePoint Inc"]
            ),
            "doc_type": "Invoice"
        },
        {
            "name": "Contract with Full PII (expect HIGH)",
            "entities": EntityResult(
                people=["Jane Smith", "John Doe"],
                organizations=["Microsoft Corp"],
                amounts=["$50,000.00"],
                emails=["jane@microsoft.com"],
                phone_numbers=["+84-123-456-789"]
            ),
            "doc_type": "Contract"
        },
    ]

    for scenario in scenarios:
        print(f"\n{'─'*55}")
        print(f"Scenario: {scenario['name']}")
        report = check_compliance(scenario["entities"], scenario["doc_type"])
        print(report.summary())


def test_full_pipeline():
    """Full pipeline: Module 1 → 2 → 3 → 4 → 5"""
    print(f"\n{'='*55}")
    print("FULL PIPELINE: Module 1 → 2 → 3 → 4 → 5")
    print(f"{'='*55}")

    from modules.input_handler import validate_and_process
    from modules.text_extractor import extract_text
    from modules.classifier import classify_document
    from modules.entity_extractor import extract_entities

    test_dir = Path(__file__).parent / "test_files"

    for filename in ["contract_test.docx", "invoice_test.docx"]:
        fpath = test_dir / filename
        if not fpath.exists():
            continue

        print(f"\n📄 Processing: {filename}")
        print("─" * 40)

        # Pipeline
        file_obj    = validate_and_process(str(fpath))        # M1
        extraction  = extract_text(file_obj)                   # M2
        classif     = classify_document(extraction.raw_text)   # M3
        entities    = extract_entities(extraction.raw_text)    # M4
        compliance  = check_compliance(entities, classif.document_type)  # M5

        # Final output
        print(f"✅ Type       : {classif.document_type} ({classif.confidence:.0%})")
        print(f"✅ People     : {entities.people}")
        print(f"✅ Amounts    : {entities.amounts}")
        print(f"✅ Dates      : {entities.dates}")
        print(compliance.summary())


if __name__ == "__main__":
    test_scoring()
    test_full_pipeline()
    print(f"\n{'='*55}")
    print("✅ MODULE 5 COMPLETE - Pipeline M1→M5 working!")
    print(f"{'='*55}")
