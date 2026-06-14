# app/streamlit_app.py
"""
STREAMLIT UI - Smart Document Classifier
=========================================
Giao diện web để demo project cho phỏng vấn

Cách chạy:
    streamlit run app/streamlit_app.py

Streamlit là gì?
    - Library Python để tạo web app CHỈ bằng Python
    - Không cần HTML/CSS/JavaScript
    - Mỗi lần user tương tác → Python script chạy lại từ đầu
    - Perfect cho AI/ML demo
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from services.document_processor import process_document_bytes


# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Smart Document Classifier",
    page_icon="📄",
    layout="wide"
)


# ===== HELPER FUNCTIONS =====

def get_risk_color(risk_level: str) -> str:
    """Map risk level to color"""
    return {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}.get(risk_level, "gray")

def get_risk_emoji(risk_level: str) -> str:
    return {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk_level, "⚪")

def get_doc_emoji(doc_type: str) -> str:
    return {
        "Contract": "📝", "Invoice": "🧾",
        "Report": "📊", "Email": "📧", "Unknown": "❓"
    }.get(doc_type, "📄")


# ===== MAIN UI =====

def main():
    # ── Header ──
    st.title("📄 Smart Document Classifier")
    st.caption("Upload a document to classify, extract key information, and check compliance")
    st.divider()

    # ── Layout: 2 columns ──
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("📤 Upload Document")

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "png", "jpg", "jpeg"],
            help="Supported: PDF, DOCX, PNG, JPG (max 10MB)"
        )

        if uploaded_file:
            st.success(f"✅ File loaded: **{uploaded_file.name}**")
            st.caption(f"Size: {uploaded_file.size / 1024:.1f} KB")

            process_btn = st.button(
                "🔍 Analyze Document",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("👆 Upload a file to begin")
            process_btn = False

        # ── Sample files hint ──
        with st.expander("💡 Don't have a file? Try these"):
            st.markdown("""
            **Sample texts to test with:**
            - Create a `.docx` file with: *"This invoice shows $500 due from John Doe"*
            - Create a `.docx` file with: *"This agreement between AvePoint and Jane Smith..."*
            """)

    with col_right:
        if uploaded_file and process_btn:
            # ── Processing ──
            with st.spinner("🤖 Analyzing document..."):
                file_bytes = uploaded_file.read()
                result = process_document_bytes(uploaded_file.name, file_bytes)

            if not result.success:
                st.error(f"❌ **Error at stage '{result.error_stage}':** {result.error_message}")
                return

            # ── Results ──
            st.subheader("📊 Analysis Results")
            st.caption(f"⏱️ Processed in {result.processing_time_ms:.0f}ms")

            # Row 1: Classification + Compliance summary
            r1_col1, r1_col2, r1_col3 = st.columns(3)

            with r1_col1:
                doc_type = result.classification.document_type if result.classification else "Unknown"
                emoji = get_doc_emoji(doc_type)
                confidence = result.classification.confidence if result.classification else 0
                st.metric(
                    label="Document Type",
                    value=f"{emoji} {doc_type}",
                    delta=f"{confidence:.0%} confidence"
                )

            with r1_col2:
                score = result.compliance.sensitivity_score if result.compliance else 0
                st.metric(
                    label="Sensitivity Score",
                    value=f"{score}/100",
                )

            with r1_col3:
                risk = result.compliance.risk_level if result.compliance else "UNKNOWN"
                risk_emoji = get_risk_emoji(risk)
                st.metric(
                    label="Risk Level",
                    value=f"{risk_emoji} {risk}"
                )

            st.divider()

            # Row 2: Entities + Compliance Details
            r2_col1, r2_col2 = st.columns(2)

            with r2_col1:
                st.subheader("🔍 Extracted Information")
                entities = result.entities

                if entities:
                    if entities.people:
                        st.markdown(f"**👤 People:** {', '.join(entities.people)}")
                    if entities.organizations:
                        st.markdown(f"**🏢 Organizations:** {', '.join(entities.organizations)}")
                    if entities.amounts:
                        st.markdown(f"**💰 Amounts:** {', '.join(entities.amounts)}")
                    if entities.dates:
                        st.markdown(f"**📅 Dates:** {', '.join(entities.dates)}")
                    if entities.emails:
                        st.markdown(f"**📧 Emails:** {', '.join(entities.emails)}")
                    if entities.phone_numbers:
                        st.markdown(f"**📱 Phones:** {', '.join(entities.phone_numbers)}")
                    if entities.invoice_numbers:
                        st.markdown(f"**🔢 Invoice#:** {', '.join(entities.invoice_numbers)}")

                    if not any([entities.people, entities.organizations,
                               entities.amounts, entities.dates,
                               entities.emails, entities.phone_numbers]):
                        st.info("No key entities found")
                else:
                    st.info("No entities extracted")

            with r2_col2:
                st.subheader("🛡️ Compliance Report")

                if result.compliance:
                    compliance = result.compliance

                    # Score breakdown
                    if compliance.score_breakdown:
                        st.markdown("**Score Breakdown:**")
                        for reason, points in compliance.score_breakdown.items():
                            if points > 0:
                                color = "red" if points >= 20 else "orange" if points >= 10 else "gray"
                                st.markdown(f":{color}[+{points}] {reason}")

                    # PII found
                    if compliance.pii_found:
                        st.markdown(f"**PII Detected:** `{'`, `'.join(compliance.pii_found)}`")

                    # Recommendations
                    if compliance.recommendations:
                        st.markdown("**Recommendations:**")
                        for rec in compliance.recommendations:
                            st.markdown(f"• {rec}")

            st.divider()

            # Row 3: Raw JSON (for developers)
            with st.expander("🔧 Raw JSON Output (for API integration)"):
                st.json(result.to_dict())

        elif not uploaded_file:
            # ── Welcome screen ──
            st.subheader("👋 Welcome!")
            st.markdown("""
            This system automatically:

            | Step | What it does |
            |------|-------------|
            | 1️⃣ **Validate** | Check file type, size, security |
            | 2️⃣ **Extract** | Read text from PDF/DOCX/Image |
            | 3️⃣ **Classify** | Identify: Contract / Invoice / Report / Email |
            | 4️⃣ **Extract Entities** | Find people, amounts, dates, emails |
            | 5️⃣ **Compliance Check** | Calculate sensitivity score & risk level |

            ---
            **Tech Stack:** Python · pdfplumber · python-docx · scikit-learn · Streamlit

            **Use case:** Automated document governance for Microsoft 365 environments
            """)


if __name__ == "__main__":
    main()
