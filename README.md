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

*Built as a portfolio project demonstrating NLP pipeline design,
modular architecture, and practical AI engineering skills.*
