# modules/entity_extractor.py
"""
ENTITY EXTRACTOR MODULE
========================
Nhiệm vụ:
- Nhận raw_text từ Module 2
- Trích xuất thông tin cụ thể: tên người, tổ chức, số tiền, ngày, email
- Dùng Regex patterns (fast, no model needed)

Ví dụ:
    Input:  "Invoice from AvePoint to John Doe, $1,500 due 2024-02-15"
    Output: {
        people: ["John Doe"],
        organizations: ["AvePoint"],
        amounts: ["$1,500"],
        dates: ["2024-02-15"],
        emails: []
    }
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict

sys.path.append(str(Path(__file__).parent.parent))


# ===== DATA CLASS =====
@dataclass
class EntityResult:
    """
    Kết quả trích xuất entities

    Attributes:
        people        : Tên người (regex: viết hoa 2 từ liên tiếp)
        organizations : Tên tổ chức (Inc, Ltd, Corp...)
        amounts       : Số tiền ($1,500.00)
        dates         : Ngày tháng (2024-01-15, Jan 15 2024...)
        emails        : Địa chỉ email
        invoice_numbers: Số hóa đơn (INV-001, #12345...)
        phone_numbers : Số điện thoại
    """
    people: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    amounts: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    invoice_numbers: List[str] = field(default_factory=list)
    phone_numbers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert sang dict để dễ hiển thị / serialize"""
        return {
            "people": self.people,
            "organizations": self.organizations,
            "amounts": self.amounts,
            "dates": self.dates,
            "emails": self.emails,
            "invoice_numbers": self.invoice_numbers,
            "phone_numbers": self.phone_numbers
        }

    def summary(self) -> str:
        """In tóm tắt đẹp"""
        lines = ["📋 EXTRACTED ENTITIES:"]
        for key, values in self.to_dict().items():
            if values:
                lines.append(f"  {key:20}: {', '.join(values)}")
        return "\n".join(lines) if len(lines) > 1 else "  (no entities found)"


# ===== REGEX PATTERNS =====
"""
Regex là gì?
    Regular Expression = pattern để tìm kiếm text
    Giống như "wildcard" nhưng mạnh hơn nhiều

Ví dụ đơn giản:
    Pattern: r'\d+'        → tìm 1 hoặc nhiều số liên tiếp
    Text: "Invoice $500"  → tìm thấy "500"

    Pattern: r'\$[\d,]+'   → tìm $ theo sau bởi số và dấu phẩy
    Text: "Amount $1,500"  → tìm thấy "$1,500"

Ký hiệu thường dùng:
    \d  = digit (số 0-9)
    \w  = word character (a-z, A-Z, 0-9, _)
    \s  = whitespace (space, tab)
    +   = 1 hoặc nhiều lần
    *   = 0 hoặc nhiều lần
    ?   = 0 hoặc 1 lần (optional)
    []  = character class (1 trong các ký tự)
    ()  = group
"""

PATTERNS = {

    # Tìm số tiền: $1,500  $500.00  $1,234,567.89
    "amounts": re.compile(
        r'\$[\d,]+(?:\.\d{2})?',
        re.IGNORECASE
    ),

    # Tìm ngày dạng YYYY-MM-DD: 2024-01-15
    "dates_iso": re.compile(
        r'\b\d{4}-\d{2}-\d{2}\b'
    ),

    # Tìm ngày dạng "January 15, 2024" hoặc "Jan 15 2024"
    "dates_text": re.compile(
        r'\b(?:January|February|March|April|May|June|July|August|'
        r'September|October|November|December|'
        r'Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        r'\s+\d{1,2}(?:,\s*\d{4}|\s+\d{4})\b',
        re.IGNORECASE
    ),

    # Tìm ngày dạng "15/01/2024" hoặc "01-15-2024"
    "dates_numeric": re.compile(
        r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b'
    ),

    # Tìm email: john.doe@company.com
    "emails": re.compile(
        r'\b[\w._%+\-]+@[\w.\-]+\.[a-zA-Z]{2,}\b'
    ),

    # Tìm số hóa đơn: INV-001, INV-2024-001, #12345, PO-001
    # Yêu cầu phải có số/ký tự theo sau (tránh bắt "INVOICE" đơn lẻ)
    "invoice_numbers": re.compile(
        r'\b(?:INV|PO|REF|ORDER)[#\-\s]*[\w\-]+\b|#\d+\b',
        re.IGNORECASE
    ),

    # Tìm số điện thoại: (84) 123-456-789, +84-123-456-789, 0123456789
    "phone_numbers": re.compile(
        r'(?:\+\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}'
    ),

    # Tìm tổ chức: "AvePoint Inc", "Google LLC", "Microsoft Corp"
    "organizations": re.compile(
        r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+'
        r'(?:Inc|LLC|Ltd|Corp|Corporation|Company|Co\.|Group|Technologies|Services|Solutions)\b'
    ),

    # Tìm tên người: 2 từ viết hoa, không phải đầu câu
    # Ví dụ: "John Doe", "Jane Smith"
    "people": re.compile(
        r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
    ),
}

# Từ cần loại bỏ khỏi danh sách người (false positives)
NON_PERSON_WORDS = {
    # Invoice terms
    "Invoice Number", "Due Date", "Payment Due", "Total Amount",
    "Amount Due", "Subtotal Tax", "Invoice Date",
    # Contract terms
    "Effective Date", "Termination Date", "Contract Value",
    "Service Agreement", "Terms Conditions",
    # Report terms
    "Executive Summary", "Annual Report", "Quarterly Report",
    # Email terms
    "Dear Jane", "Dear John", "Best Regards", "Kind Regards",
    "Please Find", "Subject Meeting", "Thank You", "Meeting Tomorrow",
    # Generic false positives
    "Reference Number", "Account Number", "Phone Number"
}


# ===== EXTRACTION FUNCTIONS =====

def extract_amounts(text: str) -> List[str]:
    """Tìm tất cả số tiền trong text"""
    matches = PATTERNS["amounts"].findall(text)
    # Loại bỏ trùng lặp, giữ thứ tự
    return list(dict.fromkeys(matches))


def extract_dates(text: str) -> List[str]:
    """Tìm tất cả ngày tháng (3 format)"""
    dates = []
    dates += PATTERNS["dates_iso"].findall(text)
    dates += PATTERNS["dates_text"].findall(text)
    dates += PATTERNS["dates_numeric"].findall(text)
    return list(dict.fromkeys(dates))  # Remove duplicates


def extract_emails(text: str) -> List[str]:
    """Tìm tất cả địa chỉ email"""
    return PATTERNS["emails"].findall(text)


def extract_invoice_numbers(text: str) -> List[str]:
    """Tìm số hóa đơn / mã tham chiếu"""
    return PATTERNS["invoice_numbers"].findall(text)


def extract_phone_numbers(text: str) -> List[str]:
    """Tìm số điện thoại"""
    return PATTERNS["phone_numbers"].findall(text)


def extract_organizations(text: str) -> List[str]:
    """Tìm tên tổ chức (có Inc, LLC, Corp...)"""
    return list(dict.fromkeys(PATTERNS["organizations"].findall(text)))


def extract_people(text: str, organizations: List[str]) -> List[str]:
    """
    Tìm tên người

    Logic:
        1. Tìm tất cả cụm 2 từ viết hoa (John Doe)
        2. Loại bỏ những cụm là tên tổ chức
        3. Loại bỏ false positives thường gặp
    """
    candidates = PATTERNS["people"].findall(text)

    # Loại bỏ organization names
    org_words = set()
    for org in organizations:
        org_words.update(org.split())

    people = []
    for name in candidates:
        # Kiểm tra không phải org và không phải false positive
        if (name not in NON_PERSON_WORDS and
                not any(word in name for word in ["Inc", "LLC", "Corp", "Ltd"])):
            people.append(name)

    return list(dict.fromkeys(people))  # Remove duplicates


# ===== MAIN ENTRY POINT =====

def extract_entities(text: str) -> EntityResult:
    """
    Main function: Trích xuất tất cả entities từ text

    Args:
        text: Raw text từ Module 2

    Returns:
        EntityResult với tất cả entities tìm được

    Example:
        >>> result = extract_entities("Invoice from AvePoint Inc to John Doe, $1,500 due 2024-02-15")
        >>> print(result.amounts)
        ['$1,500']
        >>> print(result.dates)
        ['2024-02-15']
    """
    if not text or not text.strip():
        return EntityResult()

    # Extract từng loại entity
    amounts = extract_amounts(text)
    dates = extract_dates(text)
    emails = extract_emails(text)
    invoice_numbers = extract_invoice_numbers(text)
    phone_numbers = extract_phone_numbers(text)
    organizations = extract_organizations(text)
    people = extract_people(text, organizations)

    return EntityResult(
        people=people,
        organizations=organizations,
        amounts=amounts,
        dates=dates,
        emails=emails,
        invoice_numbers=invoice_numbers,
        phone_numbers=phone_numbers
    )


if __name__ == "__main__":
    print("Entity Extractor Module")
    print("=" * 50)
    test = "Invoice INV-001 from AvePoint Inc to John Doe. Amount: $1,500.00 due 2024-02-15. Contact: john@avepoint.com"
    result = extract_entities(test)
    print(result.summary())
