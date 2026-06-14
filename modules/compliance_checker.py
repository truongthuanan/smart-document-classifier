# modules/compliance_checker.py
"""
COMPLIANCE CHECKER MODULE
==========================
Nhiệm vụ:
- Nhận EntityResult từ Module 4 + document_type từ Module 3
- Tính sensitivity score (0-100)
- Xác định risk level: LOW / MEDIUM / HIGH
- Đưa ra recommendations

Tại sao cần module này?
- GDPR (General Data Protection Regulation) yêu cầu doanh nghiệp
  biết tài liệu nào chứa thông tin cá nhân (PII)
- AvePoint làm về data governance → đây là core business value
- Giúp compliance team ưu tiên audit tài liệu nào trước
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict

sys.path.append(str(Path(__file__).parent.parent))
from modules.entity_extractor import EntityResult


# ===== DATA CLASS =====
@dataclass
class ComplianceReport:
    """
    Kết quả compliance check

    Attributes:
        sensitivity_score : Điểm nhạy cảm (0-100)
        risk_level        : "LOW" / "MEDIUM" / "HIGH"
        pii_found         : Danh sách loại PII tìm thấy
        score_breakdown   : Chi tiết điểm từng mục
        recommendations   : Gợi ý xử lý tài liệu
    """
    sensitivity_score: int
    risk_level: str
    pii_found: List[str] = field(default_factory=list)
    score_breakdown: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """In báo cáo compliance đẹp"""
        risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
        emoji = risk_emoji.get(self.risk_level, "⚪")

        lines = [
            f"\n🛡️  COMPLIANCE REPORT",
            f"{'─'*40}",
            f"Sensitivity Score : {self.sensitivity_score}/100",
            f"Risk Level        : {emoji} {self.risk_level}",
        ]

        if self.pii_found:
            lines.append(f"PII Detected      : {', '.join(self.pii_found)}")

        if self.score_breakdown:
            lines.append(f"\n📊 Score Breakdown:")
            for reason, points in self.score_breakdown.items():
                if points > 0:
                    lines.append(f"   +{points:2d}  {reason}")

        if self.recommendations:
            lines.append(f"\n💡 Recommendations:")
            for rec in self.recommendations:
                lines.append(f"   • {rec}")

        return "\n".join(lines)


# ===== SCORING RULES =====
"""
Scoring logic:
    Mỗi loại PII/thông tin nhạy cảm có điểm riêng
    Cộng tất cả lại → sensitivity score

Tại sao điểm khác nhau?
    Email (10pt)  → phổ biến, ít nhạy cảm hơn
    Phone (10pt)  → tương tự email
    Người (15pt)  → thông tin định danh cá nhân
    Tiền (15pt)   → thông tin tài chính nhạy cảm
    Contract (20pt) → tài liệu pháp lý, rủi ro cao nhất
    Nhiều PII (30pt bonus) → nhiều loại kết hợp = rất nguy hiểm
"""

SCORING_RULES = {
    "has_emails":         {"points": 10, "pii": "Email Address"},
    "has_phone_numbers":  {"points": 10, "pii": "Phone Number"},
    "has_people":         {"points": 15, "pii": "Personal Name"},
    "has_amounts":        {"points": 15, "pii": "Financial Amount"},
    "has_organizations":  {"points": 5,  "pii": None},  # Less sensitive
    "is_contract":        {"points": 20, "pii": None},  # Document type risk
    "is_invoice":         {"points": 15, "pii": None},
    "multiple_pii_types": {"points": 30, "pii": "Multiple PII Combined"},
}

RISK_THRESHOLDS = {
    "LOW":    (0, 30),
    "MEDIUM": (30, 60),
    "HIGH":   (60, 101),
}

RECOMMENDATIONS = {
    "LOW": [
        "Document is safe to share internally",
        "No special handling required"
    ],
    "MEDIUM": [
        "Restrict access to authorized personnel only",
        "Log all access and modifications",
        "Consider redacting personal information before sharing externally"
    ],
    "HIGH": [
        "RESTRICTED: Do not share without authorization",
        "Encrypt document before storage or transmission",
        "Audit trail required for all access",
        "Consider anonymizing PII before processing",
        "Review GDPR compliance requirements"
    ]
}


# ===== MAIN FUNCTION =====

def check_compliance(
    entities: EntityResult,
    document_type: str
) -> ComplianceReport:
    """
    Main function: Tính sensitivity score và risk level

    Args:
        entities      : EntityResult từ Module 4
        document_type : Loại tài liệu từ Module 3 ("Contract", "Invoice", etc.)

    Returns:
        ComplianceReport

    Algorithm:
        1. Kiểm tra từng loại entity
        2. Cộng điểm theo SCORING_RULES
        3. Nếu có nhiều loại PII → cộng thêm bonus
        4. Cap điểm tối đa là 100
        5. Xác định risk level từ tổng điểm
        6. Tạo recommendations phù hợp

    Example:
        Contract + tên người + số tiền + email
        = 20 + 15 + 15 + 10 = 60 → HIGH risk
    """
    score = 0
    score_breakdown = {}
    pii_found = []
    pii_count = 0  # Đếm số loại PII

    # ── Check từng loại entity ──

    if entities.emails:
        points = SCORING_RULES["has_emails"]["points"]
        score += points
        score_breakdown["Email addresses found"] = points
        pii_found.append(SCORING_RULES["has_emails"]["pii"])
        pii_count += 1

    if entities.phone_numbers:
        points = SCORING_RULES["has_phone_numbers"]["points"]
        score += points
        score_breakdown["Phone numbers found"] = points
        pii_found.append(SCORING_RULES["has_phone_numbers"]["pii"])
        pii_count += 1

    if entities.people:
        points = SCORING_RULES["has_people"]["points"]
        score += points
        score_breakdown[f"Personal names found ({len(entities.people)})"] = points
        pii_found.append(SCORING_RULES["has_people"]["pii"])
        pii_count += 1

    if entities.amounts:
        points = SCORING_RULES["has_amounts"]["points"]
        score += points
        score_breakdown[f"Financial amounts found ({len(entities.amounts)})"] = points
        pii_found.append(SCORING_RULES["has_amounts"]["pii"])
        pii_count += 1

    if entities.organizations:
        points = SCORING_RULES["has_organizations"]["points"]
        score += points
        score_breakdown[f"Organizations found ({len(entities.organizations)})"] = points

    # ── Document type risk ──
    doc_type_lower = document_type.lower()
    if doc_type_lower == "contract":
        points = SCORING_RULES["is_contract"]["points"]
        score += points
        score_breakdown["Document type: Contract (legal risk)"] = points
    elif doc_type_lower == "invoice":
        points = SCORING_RULES["is_invoice"]["points"]
        score += points
        score_breakdown["Document type: Invoice (financial risk)"] = points

    # ── Bonus: nhiều loại PII kết hợp ──
    if pii_count >= 3:
        points = SCORING_RULES["multiple_pii_types"]["points"]
        score += points
        score_breakdown[f"Multiple PII types combined ({pii_count} types)"] = points
        pii_found.append(SCORING_RULES["multiple_pii_types"]["pii"])

    # ── Cap score ở 100 ──
    score = min(score, 100)

    # ── Xác định risk level ──
    risk_level = "LOW"
    for level, (low, high) in RISK_THRESHOLDS.items():
        if low <= score < high:
            risk_level = level
            break

    # ── Lấy recommendations ──
    recommendations = RECOMMENDATIONS[risk_level].copy()

    # Thêm recommendation cụ thể
    if entities.emails and risk_level != "LOW":
        recommendations.append("Mask email addresses: j***@company.com")
    if entities.amounts and risk_level == "HIGH":
        recommendations.append("Redact financial figures before external sharing")

    return ComplianceReport(
        sensitivity_score=score,
        risk_level=risk_level,
        pii_found=list(dict.fromkeys(pii_found)),  # Remove duplicates
        score_breakdown=score_breakdown,
        recommendations=recommendations
    )


if __name__ == "__main__":
    # Quick test
    from modules.entity_extractor import EntityResult
    test_entities = EntityResult(
        people=["John Doe"],
        organizations=["AvePoint Inc"],
        amounts=["$1,500.00"],
        emails=["john@company.com"],
        dates=["2024-01-15"],
        invoice_numbers=["INV-001"]
    )
    report = check_compliance(test_entities, "Invoice")
    print(report.summary())
