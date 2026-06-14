# 📄 Smart Document Classifier

A document intelligence system that automatically classifies business documents,
extracts key information, and performs GDPR compliance risk assessment.

## 🎯 Problem Statement

Organizations managing large volumes of documents (contracts, invoices, reports, emails)
face challenges in:
- Manual classification consuming significant time
- Identifying sensitive PII data before sharing
- Maintaining GDPR compliance across document repositories

This system automates the entire pipeline from document upload to compliance reporting.

---

## 🏗️ Architecture

```
Input Document (PDF / DOCX / Image)
        │
        ▼
┌───────────────────┐
│ Module 1          │  Validate file type, size, security (magic bytes)
│ Input Handler     │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Module 2          │  Extract text:
│ Text Extractor    │  PDF → pdfplumber | DOCX → python-docx | Image → pytesseract
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Module 3          │  Keyword-based classification
│ Classifier        │  → Contract / Invoice / Report / Email
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Module 4          │  Regex-based Named Entity Recognition
│ Entity Extractor  │  → People, Organizations, Amounts, Dates, Emails
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Module 5          │  Rule-based PII scoring
│ Compliance Check  │  → Sensitivity Score (0-100) + Risk Level
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Module 6          │  Single entry point
│ Orchestrator      │  → Coordinates all modules + error handling
└────────┬──────────┘
         │
         ▼
┌─────────┴─────────┐
│   Streamlit UI    │  Web demo interface
└───────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| PDF Extraction | `pdfplumber` | Better table/layout handling than PyPDF2 |
| DOCX Extraction | `python-docx` | Native DOCX parsing |
| OCR | `pytesseract` | Google Tesseract, open-source |
| Classification | Keyword-based + TF-IDF | Fast, interpretable, no training data needed |
| NER | Regex patterns | Deterministic, explainable |
| UI | `Streamlit` | Rapid ML demo prototyping |
| API-ready | `dataclasses` + JSON | Clean serialization for FastAPI integration |

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install pdfplumber python-docx pytesseract pillow streamlit scikit-learn
```

### 2. Run the web UI
```bash
streamlit run app/streamlit_app.py
```

### 3. Or use Python API directly
```python
from services.document_processor import process_document

result = process_document("path/to/your/document.pdf")
print(result.classification.document_type)   # "Invoice"
print(result.compliance.sensitivity_score)   # 65
print(result.compliance.risk_level)          # "HIGH"
```

---

## 📊 Sample Output

```json
{
  "filename": "contract.docx",
  "processing_time_ms": 159,
  "classification": {
    "document_type": "Contract",
    "confidence": 0.77,
    "method": "keyword"
  },
  "entities": {
    "people": ["John Doe"],
    "organizations": ["AvePoint Inc"],
    "amounts": ["$5,000"],
    "dates": ["2024-01-15", "January 1, 2024"]
  },
  "compliance": {
    "sensitivity_score": 55,
    "risk_level": "MEDIUM",
    "pii_found": ["Personal Name", "Financial Amount"],
    "recommendations": [
      "Restrict access to authorized personnel only",
      "Log all access and modifications"
    ]
  }
}
```

---

## 🧩 Module Details

### Module 1: Input Handler
- Validates file extension against allowlist
- Checks magic bytes (binary signature) to prevent fake extensions
- Enforces file size limits (100 bytes - 10 MB)
- Returns standardized `FileObject` dataclass

### Module 2: Text Extractor
- Routes to appropriate extractor based on file type
- PDF: `pdfplumber` (handles multi-page, preserves layout)
- DOCX: `python-docx` (paragraph-level extraction)
- Images: `pytesseract` OCR (confidence: 0.7 vs 1.0 for text files)
- Returns `ExtractionResult` with `confidence` score

### Module 3: Document Classifier
- **Keyword-based**: TF-IDF style keyword scoring per document type
- **Hugging Face** (optional): zero-shot classification with `facebook/bart-large-mnli`
- Auto-fallback: HuggingFace → keyword if model unavailable
- Limitation: keyword approach lacks contextual understanding

### Module 4: Entity Extractor
- Regex patterns for structured data (emails, amounts, dates, phone numbers)
- Heuristic NER for people names (capitalized bigrams + blacklist)
- Organization detection (company suffixes: Inc, LLC, Corp, Ltd)

### Module 5: Compliance Checker
- Additive scoring model based on PII types detected
- Bonus points for multiple PII combinations (GDPR aggregation risk)
- Three risk tiers: LOW (0-30), MEDIUM (30-60), HIGH (60-100)
- Actionable recommendations per risk level

### Module 6: Orchestrator
- Single `process_document()` entry point
- Graceful degradation: text extraction failure → stop; classification failure → continue
- Returns `ProcessingResult` with full JSON serialization support

---

## 🎤 Interview Defense (5 minutes)

**Q: Tell me about this project.**

> "I built a document intelligence system that automates document classification and GDPR compliance assessment.
> The pipeline has 6 modules: input validation, text extraction, classification, entity recognition, compliance scoring, and an orchestrator that ties everything together.
> I chose a modular architecture so each component is independently testable and replaceable."

**Q: Why keyword-based classification instead of a neural network?**

> "For 4 document classes with no labeled training data, a simple keyword-based approach achieves 77-83% confidence and is fully interpretable.
> A neural network would require hundreds of labeled examples and be harder to explain.
> I designed the classifier to support Hugging Face zero-shot classification as an optional upgrade, so the architecture is extensible."

**Q: How does the compliance checker work?**

> "It uses an additive scoring model inspired by GDPR risk assessment.
> Each PII type found adds points: email adds 10, personal names add 15, financial amounts add 15.
> There's also a bonus 30 points when multiple PII types are combined, because aggregate data enables individual identification—which is the core GDPR concern.
> The score maps to LOW/MEDIUM/HIGH risk tiers with specific remediation recommendations."

**Q: How is this relevant to AvePoint?**

> "AvePoint's core business is data governance for Microsoft 365.
> This system directly addresses that use case: automatically classifying documents, identifying sensitive data before it's shared, and providing compliance teams with actionable risk scores.
> The modular architecture means it could be integrated into an existing M365 workflow as a processing pipeline."

---

## 📁 Project Structure

```
Project1_DocClassifier/
├── config/
│   └── settings.py              # File limits, magic bytes, constants
├── modules/
│   ├── input_handler.py         # Module 1: File validation
│   ├── text_extractor.py        # Module 2: Text extraction
│   ├── classifier.py            # Module 3: Document classification
│   ├── entity_extractor.py      # Module 4: NER
│   └── compliance_checker.py    # Module 5: Risk scoring
├── services/
│   └── document_processor.py   # Module 6: Orchestrator
├── app/
│   └── streamlit_app.py         # Web UI
├── test_files/                  # Sample documents
├── test_module1.py              # Unit tests per module
├── test_module2.py
├── test_module3.py
├── test_module4.py
├── test_module5.py
├── test_module6.py
└── requirements.txt
```

---

## 🔮 Future Improvements

- [ ] Fine-tune DistilBERT classifier on labeled document dataset
- [ ] Add Azure Document Intelligence as cloud backend option
- [ ] Implement document anonymization (mask PII in output)
- [ ] Add batch processing for multiple files
- [ ] Build FastAPI REST endpoint for production integration
- [ ] Add support for Vietnamese language documents

---

*Built as a portfolio project demonstrating NLP pipeline design,
modular architecture, and practical AI engineering skills.*
