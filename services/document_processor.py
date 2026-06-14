# services/document_processor.py
"""
ORCHESTRATOR / DOCUMENT PROCESSOR
===================================
Nhiệm vụ:
- Kết nối tất cả 5 modules thành 1 pipeline hoàn chỉnh
- Cung cấp 1 hàm duy nhất: process_document()
- Xử lý lỗi và partial results

Pattern: Orchestrator Pattern
    Thay vì caller phải gọi M1→M2→M3→M4→M5 riêng lẻ,
    Orchestrator làm hết và trả về kết quả tổng hợp.

Tại sao cần Orchestrator?
    → Separation of concerns: UI/API chỉ cần gọi 1 hàm
    → Error handling tập trung
    → Dễ thêm/bớt module sau này
    → Testable independently
"""

import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.append(str(Path(__file__).parent.parent))

from modules.input_handler import validate_and_process, validate_and_process_bytes, FileValidationError
from modules.text_extractor import extract_text, ExtractionResult
from modules.classifier import classify_document, ClassificationResult
from modules.entity_extractor import extract_entities, EntityResult
from modules.compliance_checker import check_compliance, ComplianceReport


# ===== DATA CLASS: ProcessingResult =====
@dataclass
class ProcessingResult:
    """
    Kết quả tổng hợp của toàn bộ pipeline

    Đây là object duy nhất mà UI/API nhận được.
    Chứa tất cả thông tin từ 5 modules.
    """
    # Metadata
    filename: str
    processing_time_ms: float
    success: bool

    # Module results (None nếu module đó fail)
    classification: Optional[ClassificationResult] = None
    entities: Optional[EntityResult] = None
    compliance: Optional[ComplianceReport] = None
    extraction: Optional[ExtractionResult] = None

    # Error info
    error_message: Optional[str] = None
    error_stage: Optional[str] = None  # "validation", "extraction", "classification", etc.

    def to_dict(self) -> dict:
        """Convert sang dict để serialize thành JSON (cho FastAPI)"""
        if not self.success:
            return {
                "success": False,
                "filename": self.filename,
                "error": self.error_message,
                "stage": self.error_stage
            }

        return {
            "success": True,
            "filename": self.filename,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "classification": {
                "document_type": self.classification.document_type,
                "confidence": self.classification.confidence,
                "method": self.classification.method
            } if self.classification else None,
            "entities": self.entities.to_dict() if self.entities else None,
            "compliance": {
                "sensitivity_score": self.compliance.sensitivity_score,
                "risk_level": self.compliance.risk_level,
                "pii_found": self.compliance.pii_found,
                "recommendations": self.compliance.recommendations
            } if self.compliance else None
        }

    def print_summary(self):
        """In tóm tắt kết quả ra console"""
        if not self.success:
            print(f"❌ FAILED at stage '{self.error_stage}': {self.error_message}")
            return

        risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(
            self.compliance.risk_level if self.compliance else "", "⚪"
        )

        print(f"\n{'='*55}")
        print(f"📄 DOCUMENT ANALYSIS COMPLETE")
        print(f"{'='*55}")
        print(f"File     : {self.filename}")
        print(f"Time     : {self.processing_time_ms:.0f}ms")

        if self.classification:
            print(f"\n📋 Classification:")
            print(f"   Type       : {self.classification.document_type}")
            print(f"   Confidence : {self.classification.confidence:.0%}")

        if self.entities:
            print(f"\n🔍 Key Information:")
            if self.entities.people:
                print(f"   People     : {', '.join(self.entities.people)}")
            if self.entities.organizations:
                print(f"   Orgs       : {', '.join(self.entities.organizations)}")
            if self.entities.amounts:
                print(f"   Amounts    : {', '.join(self.entities.amounts)}")
            if self.entities.dates:
                print(f"   Dates      : {', '.join(self.entities.dates)}")

        if self.compliance:
            print(f"\n🛡️  Compliance:")
            print(f"   Score      : {self.compliance.sensitivity_score}/100")
            print(f"   Risk       : {risk_emoji} {self.compliance.risk_level}")

        print(f"{'='*55}")


# ===== MAIN ORCHESTRATOR FUNCTION =====

def process_document(file_path: str) -> ProcessingResult:
    """
    Main pipeline function: Xử lý 1 file từ đầu đến cuối

    Args:
        file_path: Đường dẫn tới file cần xử lý

    Returns:
        ProcessingResult chứa tất cả kết quả

    Flow:
        Stage 1: Validate input      (Module 1)
        Stage 2: Extract text        (Module 2)
        Stage 3: Classify document   (Module 3)
        Stage 4: Extract entities    (Module 4)
        Stage 5: Check compliance    (Module 5)
        Return: ProcessingResult

    Error handling:
        Nếu 1 stage fail → trả về ProcessingResult với success=False
        Không crash toàn bộ pipeline
    """
    start_time = time.time()
    filename = Path(file_path).name

    # ── STAGE 1: Validate input ──
    try:
        file_obj = validate_and_process(file_path)
    except FileValidationError as e:
        return ProcessingResult(
            filename=filename,
            processing_time_ms=(time.time() - start_time) * 1000,
            success=False,
            error_message=str(e),
            error_stage="validation"
        )

    # ── STAGE 2: Extract text ──
    try:
        extraction = extract_text(file_obj)
        if not extraction.raw_text:
            return ProcessingResult(
                filename=filename,
                processing_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message="No text could be extracted from document",
                error_stage="extraction"
            )
    except Exception as e:
        return ProcessingResult(
            filename=filename,
            processing_time_ms=(time.time() - start_time) * 1000,
            success=False,
            error_message=str(e),
            error_stage="extraction"
        )

    # ── STAGE 3: Classify ──
    try:
        classification = classify_document(extraction.raw_text)
    except Exception as e:
        classification = None  # Non-critical, continue pipeline

    # ── STAGE 4: Extract entities ──
    try:
        entities = extract_entities(extraction.raw_text)
    except Exception as e:
        entities = EntityResult()  # Empty result, continue

    # ── STAGE 5: Compliance check ──
    try:
        doc_type = classification.document_type if classification else "Unknown"
        compliance = check_compliance(entities, doc_type)
    except Exception as e:
        compliance = None

    # ── Return final result ──
    elapsed_ms = (time.time() - start_time) * 1000

    return ProcessingResult(
        filename=filename,
        processing_time_ms=elapsed_ms,
        success=True,
        classification=classification,
        entities=entities,
        compliance=compliance,
        extraction=extraction
    )


def process_document_bytes(filename: str, content_bytes: bytes) -> ProcessingResult:
    """
    Variant: Xử lý file từ bytes (dùng cho web upload - FastAPI/Streamlit)

    Args:
        filename     : Tên file
        content_bytes: Nội dung file dạng bytes

    Returns:
        ProcessingResult
    """
    start_time = time.time()

    # Stage 1: Validate
    try:
        file_obj = validate_and_process_bytes(filename, content_bytes)
    except FileValidationError as e:
        return ProcessingResult(
            filename=filename,
            processing_time_ms=(time.time() - start_time) * 1000,
            success=False,
            error_message=str(e),
            error_stage="validation"
        )

    # Stages 2-5: Tương tự process_document()
    try:
        extraction = extract_text(file_obj)
    except Exception as e:
        return ProcessingResult(
            filename=filename,
            processing_time_ms=(time.time() - start_time) * 1000,
            success=False,
            error_message=str(e),
            error_stage="extraction"
        )

    classification = classify_document(extraction.raw_text) if extraction.raw_text else None
    entities = extract_entities(extraction.raw_text) if extraction.raw_text else EntityResult()
    doc_type = classification.document_type if classification else "Unknown"
    compliance = check_compliance(entities, doc_type)

    return ProcessingResult(
        filename=filename,
        processing_time_ms=(time.time() - start_time) * 1000,
        success=True,
        classification=classification,
        entities=entities,
        compliance=compliance,
        extraction=extraction
    )
