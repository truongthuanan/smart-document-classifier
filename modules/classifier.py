# modules/classifier.py
"""
DOCUMENT CLASSIFIER MODULE
===========================
Nhiệm vụ:
- Nhận raw_text từ Module 2
- Phân loại tài liệu: Contract / Invoice / Report / Email
- Trả về loại + confidence score

2 phương pháp (dùng cái nào được cái đó):
    Method 1: Keyword-based  → Nhanh, không cần download gì
    Method 2: Hugging Face   → Chính xác hơn, cần internet lần đầu

Logic chọn phương pháp:
    → Thử Method 2 (HF) trước
    → Nếu lỗi (no internet, model lỗi...) → fallback Method 1
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List

sys.path.append(str(Path(__file__).parent.parent))


# ===== DATA CLASS: ClassificationResult =====
@dataclass
class ClassificationResult:
    """
    Kết quả phân loại tài liệu

    Attributes:
        document_type : Loại tài liệu ("Contract", "Invoice", "Report", "Email", "Unknown")
        confidence    : Độ chắc chắn (0.0 - 1.0)
        method        : Phương pháp dùng ("keyword" hoặc "huggingface")
        all_scores    : Điểm của tất cả 4 loại (để debug)
    """
    document_type: str
    confidence: float
    method: str
    all_scores: Dict[str, float] = field(default_factory=dict)

    def __repr__(self):
        return (f"ClassificationResult("
                f"type='{self.document_type}', "
                f"confidence={self.confidence:.2f}, "
                f"method='{self.method}')")


# ===== METHOD 1: KEYWORD-BASED CLASSIFIER =====
"""
Ý tưởng đơn giản:
- Mỗi loại tài liệu có TỪ KHÓA đặc trưng
- Đếm bao nhiêu từ khóa xuất hiện trong text
- Loại nào có nhiều từ khóa nhất → đó là loại tài liệu

Ví dụ:
    Text: "This invoice shows amount due of $500"
    Contract keywords found: 0
    Invoice keywords found:  3 (invoice, amount, due)
    Report keywords found:   0
    Email keywords found:    0
    → Kết luận: INVOICE (confidence = 3/(0+3+0+0) = 1.0)
"""

# Từ khóa đặc trưng cho từng loại
DOCUMENT_KEYWORDS = {
    "Contract": [
        "agreement", "contract", "hereby", "clause", "party", "parties",
        "terms", "conditions", "signed", "signature", "obligation",
        "whereas", "therefore", "shall", "binding", "legal",
        "effective date", "termination", "breach", "liability"
    ],
    "Invoice": [
        "invoice", "bill", "payment", "amount", "due", "total",
        "subtotal", "tax", "vat", "price", "cost", "fee",
        "invoice number", "inv-", "pay by", "bank transfer",
        "purchase order", "po number", "remittance"
    ],
    "Report": [
        "report", "summary", "analysis", "findings", "conclusion",
        "introduction", "methodology", "results", "recommendation",
        "executive summary", "quarterly", "annual", "performance",
        "statistics", "data", "chart", "table", "figure"
    ],
    "Email": [
        "subject", "from:", "to:", "cc:", "dear", "regards",
        "sincerely", "best regards", "kind regards", "hi ",
        "hello", "thank you", "please find", "attached",
        "forward", "reply", "inbox", "@"
    ]
}


def classify_by_keywords(text: str) -> ClassificationResult:
    """
    Phân loại tài liệu bằng cách đếm từ khóa

    Args:
        text: Raw text từ Module 2

    Returns:
        ClassificationResult

    Algorithm:
        1. Lowercase text (để tránh "Invoice" vs "invoice")
        2. Với mỗi loại, đếm bao nhiêu keyword xuất hiện
        3. Tính score = số keyword tìm thấy / tổng keyword của loại đó
        4. Loại có score cao nhất = kết quả
        5. Confidence = score_cao_nhất / tổng_tất_cả_scores
    """
    text_lower = text.lower()

    # Đếm keyword cho từng loại
    scores = {}
    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw.lower() in text_lower)
        # Normalize: chia cho tổng số keyword để công bằng
        scores[doc_type] = count / len(keywords)

    # Tìm loại có score cao nhất
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # Tính confidence: tỷ lệ giữa best score và tổng score
    total_score = sum(scores.values())
    if total_score == 0:
        # Không tìm thấy keyword nào → Unknown
        return ClassificationResult(
            document_type="Unknown",
            confidence=0.0,
            method="keyword",
            all_scores=scores
        )

    confidence = best_score / total_score

    # Nếu confidence quá thấp → không chắc chắn
    if confidence < 0.4:
        best_type = "Unknown"

    return ClassificationResult(
        document_type=best_type,
        confidence=round(confidence, 3),
        method="keyword",
        all_scores={k: round(v, 3) for k, v in scores.items()}
    )


# ===== METHOD 2: HUGGING FACE CLASSIFIER =====
"""
Ý tưởng:
- Dùng mô hình đã được train sẵn từ Hugging Face
- Zero-shot classification: không cần train lại
- Model đọc text và tự hiểu ngữ cảnh

Zero-shot là gì?
    "Zero" = không cần training data của chúng ta
    Model đã học từ hàng triệu tài liệu trên internet
    Ta chỉ cần nói "hãy phân loại vào 1 trong 4 nhóm này"

Model dùng: "facebook/bart-large-mnli"
    - Nhẹ hơn GPT, đủ mạnh cho classification
    - Download ~1.6GB lần đầu, cache lại dùng mãi
"""

def classify_by_huggingface(text: str) -> ClassificationResult:
    """
    Phân loại bằng Hugging Face zero-shot classification

    Args:
        text: Raw text từ Module 2 (dùng 512 ký tự đầu)

    Returns:
        ClassificationResult

    Raises:
        Exception: Nếu model không load được (sẽ fallback về keyword)
    """
    from transformers import pipeline

    # Load model (lần đầu sẽ download ~1.6GB)
    # Các lần sau load từ cache (nhanh)
    print("   🤖 Loading Hugging Face model (lần đầu có thể mất vài phút)...")

    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1  # -1 = CPU, 0 = GPU (nếu có)
    )

    # Candidate labels = 4 loại tài liệu
    candidate_labels = ["Contract", "Invoice", "Report", "Email"]

    # Chỉ dùng 512 ký tự đầu (model có giới hạn token)
    text_truncated = text[:512]

    # Chạy classification
    result = classifier(text_truncated, candidate_labels)

    # result trả về dạng:
    # {
    #   "labels": ["Invoice", "Contract", "Report", "Email"],
    #   "scores": [0.85, 0.10, 0.03, 0.02]
    # }

    best_label = result["labels"][0]
    best_score = result["scores"][0]

    # Tạo dict all_scores
    all_scores = dict(zip(result["labels"], result["scores"]))

    return ClassificationResult(
        document_type=best_label,
        confidence=round(best_score, 3),
        method="huggingface",
        all_scores={k: round(v, 3) for k, v in all_scores.items()}
    )


# ===== MAIN ENTRY POINT =====

def classify_document(text: str, use_huggingface: bool = False) -> ClassificationResult:
    """
    Main function: Phân loại tài liệu

    Strategy:
        - Mặc định dùng keyword-based (nhanh, không cần internet)
        - Nếu use_huggingface=True → thử HuggingFace trước
        - Nếu HF lỗi → tự động fallback về keyword

    Args:
        text           : Raw text từ Module 2
        use_huggingface: True để dùng HF model (chính xác hơn)

    Returns:
        ClassificationResult

    Example:
        >>> result = classify_document("This invoice shows $500 due...")
        >>> print(result)
        ClassificationResult(type='Invoice', confidence=0.87, method='keyword')
    """
    if not text or not text.strip():
        return ClassificationResult(
            document_type="Unknown",
            confidence=0.0,
            method="keyword",
            all_scores={}
        )

    if use_huggingface:
        try:
            return classify_by_huggingface(text)
        except Exception as e:
            print(f"   ⚠ HuggingFace failed: {e}")
            print(f"   → Fallback to keyword-based classifier")

    # Default: keyword-based
    return classify_by_keywords(text)


if __name__ == "__main__":
    print("Classifier Module")
    print("=" * 50)
    print("Supported types:", list(DOCUMENT_KEYWORDS.keys()))
