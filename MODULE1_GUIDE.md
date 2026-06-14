# MODULE 1: INPUT HANDLER - LEARNING GUIDE

## 🎯 Mục tiêu Module

Validate và chuẩn hóa file upload để đảm bảo:
1. **Security**: Tránh malicious files (virus, fake extensions)
2. **Performance**: Giới hạn file size để control cost
3. **Standardization**: Convert sang format chuẩn (FileObject)

---

## 📚 Kiến thức cần nhớ (cho phỏng vấn)

### 1. Magic Bytes là gì?

**Definition:**
> Magic bytes = 4-8 bytes đầu tiên của file, giống như "chữ ký" unique cho mỗi format.

**Ví dụ:**
```
PDF:  25 50 44 46           (%PDF)
PNG:  89 50 4E 47           (\x89PNG)
JPEG: FF D8 FF E0           (\xff\xd8\xff)
ZIP:  50 4B 03 04           (PK\x03\x04) → DOCX cũng là ZIP!
```

**Tại sao quan trọng?**
- User có thể rename `virus.exe` → `contract.pdf`
- Extension không đáng tin cậy (dễ fake)
- Magic bytes không thể fake (binary signature)

**Interview Answer:**
> "I validate files by checking magic bytes, not just extensions. For example, a PDF must start with '%PDF' in binary. This prevents users from uploading malicious files disguised as documents."

---

### 2. Dataclass vs Dictionary

**Code so sánh:**
```python
# ❌ Dùng dict (không type-safe)
file = {
    "filename": "contract.pdf",
    "size": 1024,
    "type": "application/pdf"
}
# Vấn đề: Typo không bắt được
print(file["sizee"])  # KeyError chỉ khi runtime

# ✅ Dùng dataclass (type-safe)
@dataclass
class FileObject:
    filename: str
    file_size: int
    mime_type: str

file = FileObject("contract.pdf", 1024, "application/pdf")
# IDE sẽ autocomplete, type checker sẽ bắt lỗi
```

**Interview Answer:**
> "I use dataclasses instead of dictionaries because they provide type safety, auto-completion in IDEs, and clear structure for data objects."

---

### 3. Exception Hierarchy

**Design pattern:**
```
FileValidationError (base)
    ├── FileSizeError
    ├── FileTypeError
    └── SecurityError
```

**Tại sao phân tầng?**
```python
# Catch specific error
try:
    validate_file()
except FileSizeError:
    return "File quá lớn, vui lòng chọn file < 10MB"
except SecurityError:
    return "File không an toàn, bị từ chối"
except FileValidationError:
    return "Lỗi validation chung"
```

**Interview Answer:**
> "I use exception hierarchy to handle different error types appropriately. For example, a file size error shows a user-friendly message, while a security error might trigger logging and alerts."

---

## 🔍 Code Walkthrough

### Flow chính của `validate_and_process()`:

```
Input: file_path (string)
    ↓
[1] Check file exists → FileValidationError nếu không
    ↓
[2] Validate extension → FileTypeError nếu không support
    ↓
[3] Read file content → bytes
    ↓
[4] Validate size → FileSizeError nếu < 100 bytes hoặc > 10MB
    ↓
[5] Validate magic bytes → SecurityError nếu mismatch
    ↓
[6] Detect MIME type → "application/pdf", "image/png", etc.
    ↓
Output: FileObject (dataclass)
```

### Các constant quan trọng:

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
# Tại sao 10MB?
# - Azure Form Recognizer limit: 50MB
# - Nhưng file lớn = cost cao
# - 10MB đủ cho hầu hết documents

MIN_FILE_SIZE = 100  # 100 bytes
# Tại sao 100 bytes?
# - File < 100 bytes thường rỗng hoặc corrupt
# - PDF header tối thiểu ~200 bytes
```

---

## 🚀 Cách chạy test

### Bước 1: Mở terminal
```bash
cd C:\Users\Lenovo\Downloads\BotFollowIndicator2  (Copy)\BotFollowIndicator2  (Copy)\doAn\code\Project1_DocClassifier
```

### Bước 2: Chạy test
```bash
python test_module1.py
```

### Bước 3: Quan sát output

**Expected results:**
- ✅ Test 1, 2: PASS (valid PDF, DOCX)
- ❌ Test 3: FAIL với `FileTypeError` (.txt không support)
- ❌ Test 4: FAIL với `FileSizeError` (file > 10MB)
- ❌ Test 5: FAIL với `SecurityError` (magic bytes mismatch)

---

## 💬 Câu hỏi để tự test hiểu biết

**Sau khi chạy test xong, bạn phải trả lời được:**

1. **Tại sao cần validate magic bytes, không chỉ check extension?**
   <details>
   <summary>Đáp án</summary>
   Vì extension dễ fake (rename .exe → .pdf), nhưng magic bytes là binary signature không thể giả mạo.
   </details>

2. **DOCX có magic bytes là gì? Tại sao?**
   <details>
   <summary>Đáp án</summary>
   `PK\x03\x04` (ZIP magic bytes) vì DOCX thực chất là file ZIP chứa XML.
   </details>

3. **Nếu file 50MB, error gì sẽ raise?**
   <details>
   <summary>Đáp án</summary>
   `FileSizeError` với message "File quá lớn (50.00 MB). Maximum: 10.00 MB"
   </details>

4. **Tại sao dùng dataclass thay vì dict?**
   <details>
   <summary>Đáp án</summary>
   Type safety, IDE autocomplete, rõ ràng hơn về structure, dễ maintain.
   </details>

5. **Hàm `validate_and_process_bytes()` khác gì `validate_and_process()`?**
   <details>
   <summary>Đáp án</summary>
   `validate_and_process()` nhận file path, đọc từ disk. `validate_and_process_bytes()` nhận bytes trực tiếp (dùng cho web upload).
   </details>

---

## 🎤 Phỏng vấn 1 phút về Module 1

**Interviewer: "Tell me how you handle file uploads securely."**

**Your answer:**
> "I implement a three-layer validation system. First, I check the file extension against an allowlist to ensure we only accept supported formats. Second, I validate the file size to prevent resource exhaustion - I set a 10MB limit based on cost and performance considerations. 
>
> Most importantly, I verify the magic bytes - the binary signature at the start of the file. For example, a PDF must begin with '%PDF', a PNG with '\x89PNG'. This prevents users from simply renaming a malicious file to bypass extension checks.
>
> All validation logic is centralized in an input handler module that returns a standardized FileObject. This makes the system maintainable and testable."

---

## ✅ Checklist trước khi sang Module 2

- [ ] Đã chạy `test_module1.py` thành công
- [ ] Hiểu rõ magic bytes là gì
- [ ] Giải thích được tại sao dùng dataclass
- [ ] Nêu được 3 lý do validate file size
- [ ] Có thể vẽ được flow chart của `validate_and_process()`

---

## 🔜 Module 2 Preview: Text Extractor

**Mục tiêu:**
- Extract text từ PDF/DOCX/Image
- Azure Form Recognizer (cloud) + Fallback (local)
- Handle OCR errors

**Skills học được:**
- API integration (Azure)
- Error handling & retry logic
- Performance optimization

**Bạn sẵn sàng chưa?** 🚀
