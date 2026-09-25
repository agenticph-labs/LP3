"""Streamlit UI for the RFP/RFQ Analyzer."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

from src.analyzer import RPFAnalyzer
from src.models import RFPParseResult

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="RFP/RFQ Analyzer",
    page_icon="📄",
    layout="wide",
)

# ── Title ────────────────────────────────────────────────────────────────────

st.title("📄 RFP / RFQ Analyzer")
st.markdown(
    "Upload a procurement document (PDF) and the AI extracts deadlines, "
    "eligibility, deliverables, evaluation criteria, and risks — all in "
    "structured form."
)
st.divider()

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Leave blank to use OPENAI_API_KEY env var",
    )
    model = st.selectbox(
        "Model",
        options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        index=0,
    )
    use_sample = st.checkbox("🔬 Use sample RFP document (no upload needed)", value=True)

    st.divider()
    st.markdown("**How it works**")
    st.markdown(
        "1. PDF is parsed with PyMuPDF\n"
        "2. Extracted text is sent to an LLM\n"
        "3. LLM returns structured JSON (Pydantic validated)\n"
        "4. Results are displayed in cards & tables"
    )

# ── Determine PDF source ────────────────────────────────────────────────────

pdf_path: Path | None = None

SAMPLE_PDF = Path(__file__).resolve().parent.parent / "sample_docs" / "rfp_sample.pdf"

if use_sample:
    if SAMPLE_PDF.exists():
        pdf_path = SAMPLE_PDF
        st.info(f"📎 Using sample: **{SAMPLE_PDF.name}**")
    else:
        st.warning("Sample PDF not found — uncheck 'Use sample' and upload one.")
        pdf_path = None
else:
    uploaded = st.file_uploader("Choose a PDF", type=["pdf"])
    if uploaded:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(uploaded.read())
        pdf_path = Path(tmp.name)

# ── Analyze ──────────────────────────────────────────────────────────────────

def display_result(result: RFPParseResult) -> None:
    """Render the parsed result in Streamlit components."""

    # Summary row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📄 Pages", result.raw_pages)
    col2.metric("📝 Words", f"{result.raw_word_count:,}")
    col3.metric("🏷️ Type", result.document_type.value)
    col4.metric("📋 Criteria", len(result.evaluation_criteria))

    # Title & org
    st.subheader(result.title)
    cols = st.columns(2)
    with cols[0]:
        if result.issuing_organization:
            st.caption(f"**Issuing org:** {result.issuing_organization}")
    with cols[1]:
        if result.solicitation_number:
            st.caption(f"**Solicitation #:** {result.solicitation_number}")

    # Summary
    with st.expander("📖 Summary", expanded=True):
        st.write(result.summary)

    # Deadlines
    if result.deadlines:
        with st.expander("📅 Key Dates", expanded=True):
            rows = [{"Label": d.label, "Date": d.date_value} for d in result.deadlines]
            st.table(rows)

    # Deliverables
    if result.deliverables:
        with st.expander("📦 Deliverables", expanded=True):
            rows = [
                {"Name": d.name, "Description": d.description, "Due": d.due_date or "—"}
                for d in result.deliverables
            ]
            st.table(rows)

    # Eligibility
    if result.eligibility_criteria:
        with st.expander("✅ Eligibility Criteria", expanded=True):
            for c in result.eligibility_criteria:
                badge = "🔴 Mandatory" if c.mandatory else "🟡 Recommended"
                st.markdown(f"- **{c.category}** ({badge}): {c.requirement}")

    # Evaluation criteria
    if result.evaluation_criteria:
        with st.expander("⚖️ Evaluation Criteria", expanded=True):
            rows = []
            for c in result.evaluation_criteria:
                w = f"{c.weight:.0f}%" if c.weight is not None else "—"
                rows.append({"Criterion": c.criterion, "Weight": w})
            st.table(rows)

    # Budget
    if result.budget_range:
        with st.expander("💰 Budget", expanded=False):
            st.write(result.budget_range)

    # Risks
    if result.risks:
        with st.expander("⚠️ Risks & Gotchas", expanded=True):
            for r in result.risks:
                sev_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    r.severity, "⚪"
                )
                st.markdown(f"- {sev_emoji} **{r.risk}**: {r.detail}")

    # Raw JSON
    with st.expander("📋 Raw JSON Output", expanded=False):
        st.code(result.model_dump_json(indent=2), language="json")


if pdf_path is not None and st.button("🚀 Analyze Document", type="primary"):
    with st.spinner("Parsing PDF and extracting text with PyMuPDF…"):
        pass  # progress bar below

    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        st.error("OpenAI API key required — set OPENAI_API_KEY env var or enter in sidebar.")
        st.stop()

    analyzer = RPFAnalyzer(api_key=key, model=model)

    progress = st.progress(0, text="Extracting text…")
    try:
        result = analyzer.analyze(pdf_path)
        progress.progress(100, text="✅ Analysis complete")

        st.success("Analysis complete — see results below")
        display_result(result)

    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        raise
    finally:
        # Clean up uploaded temp file
        if not use_sample and pdf_path is not None and pdf_path.exists():
            pdf_path.unlink(missing_ok=True)
else:
    st.info("👈 Configure settings in the sidebar, then click **Analyze Document**.")
