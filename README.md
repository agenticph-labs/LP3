# 📄 RFP / RFQ Analyzer

[![Status: Live](https://img.shields.io/badge/status-live-22c55e.svg)](https://github.com/agenticph-labs/p3-rfp-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/agenticph-labs/p3-rfp-analyzer/actions/workflows/test.yml/badge.svg)](https://github.com/agenticph-labs/p3-rfp-analyzer/actions/workflows/test.yml)
[![Security](https://github.com/agenticph-labs/p3-rfp-analyzer/actions/workflows/security.yml/badge.svg)](https://github.com/agenticph-labs/p3-rfp-analyzer/actions/workflows/security.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

A Python-based system that extracts structured information from procurement documents (RFPs, RFQs, tenders). Upload a PDF → AI extracts deadlines, eligibility criteria, deliverables, evaluation criteria, and risks — all as structured, validated data.

> **Portfolio Project 3 — [AgenticPH Labs](https://agenticph-labs.github.io/portfolio)** — Focused on demonstrating clean architecture, not a polished SaaS product.

---

## Table of Contents

- [PH Use Case](#ph-use-case)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Using Your Own Documents](#using-your-own-documents)
- [Model Support](#model-support)
- [Architecture Notes](#architecture-notes)
- [Contributing](#contributing)
- [License](#license)

---

## PH Use Case

### Why This Matters for Philippine Procurement

The Philippine government procures over **₱500 billion** annually in goods and services through the Procurement Law (RA 9184). Construction firms, IT vendors, suppliers, and consulting firms regularly bid on RFPs from DPWH, DOST, DICT, LGUs, and GOCCs — but manually analyzing 50+ page tender documents is slow, error-prone, and expensive.

| Stakeholder | How They Use This |
|-------------|-------------------|
| **Construction Companies** | Extract deadlines, eligibility docs, and evaluation criteria from DPWH/DOTr infrastructure bids |
| **IT / Software Vendors** | Parse DICT and LGU RFPs for technical requirements, submission deadlines, and compliance docs |
| **Consulting Firms** | Analyze consulting RFQs for scope, deliverables, and evaluation weightings |
| **Government Procurement Offices** | Validate bid submissions against requirements, standardize tender reviews |
| **SME Suppliers** | Quickly assess whether they qualify to bid without reading 100-page documents |

### Key Benefits for PH Bidders

- **Save hours per RFP** — 50+ page PDFs analyzed in seconds
- **Never miss a deadline** — all dates extracted and surfaced prominently
- **Understand evaluation weights** — know what actually gets scored (technical vs. financial)
- **Identify risks early** — hidden requirements, compliance gotchas, disqualification traps
- **Compare multiple bids** — structured data lets you compare across opportunities

Extraction works best with text-based PDFs (standard for PH government RFPs). No OCR required for digital documents.

---

## How It Works

```
PDF Upload  ──▶  PyMuPDF Text Extraction  ──▶  LLM Structured Output  ──▶  Pydantic Validation  ──▶  Streamlit UI
```

Three layers, each independently testable:

### 1. PDF Parsing (`src/pdf_parser.py`)

Uses **PyMuPDF** (fitz) to extract all text from a PDF document. Returns raw text and page count. Chunking logic is available for long documents that exceed LLM context windows.

### 2. LLM Extraction (`src/analyzer.py` + `src/prompt.py`)

Sends extracted text to an OpenAI-compatible LLM with a **structured output** schema defined as a Pydantic model. The prompt instructs the model to extract:

- Document metadata (title, type, org, solicitation number)
- Key deadlines and important dates
- Eligibility / qualification requirements
- Deliverables with descriptions and due dates
- Evaluation criteria with percentage weights
- Budget range
- Risks and potential gotchas

The LLM returns JSON, which is validated against `RFPParseResult` (Pydantic) — fields missing from the document are gracefully omitted rather than hallucinated.

### 3. UI (`src/app.py`)

A **Streamlit** single-page app:
- Sidebar: API key, model selection, sample/browse toggle
- Upload or use the bundled sample RFP
- Results displayed in collapsible cards: summary, dates, deliverables, eligibility, evaluation criteria, budget, risks
- Raw JSON expandable for debugging

---

## Project Structure

```
p3-rfp-analyzer/
├── .github/workflows/
│   ├── test.yml              # CI — lint + pytest (matrix: 3.11-3.13)
│   └── security.yml           # bandit + safety scans
├── scripts/
│   └── start.bat             # Windows startup script (venv + install + launch)
├── src/
│   ├── __init__.py
│   ├── app.py              # Streamlit UI
│   ├── analyzer.py          # Orchestrator: PDF → LLM → validated model
│   ├── models.py            # Pydantic schemas for extracted data
│   ├── pdf_parser.py        # PyMuPDF text extraction
│   └── prompt.py            # LLM system + user prompts
├── sample_docs/
│   ├── rfp_sample.pdf       # Bundled 5-page sample RFP
│   └── generate_sample_pdf.py
├── tests/
│   ├── __init__.py
│   └── test_analyzer.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- An OpenAI API key (or compatible endpoint)

### Setup

```bash
# Clone
git clone https://github.com/agenticph-labs/p3-rfp-analyzer.git
cd p3-rfp-analyzer

# Virtual env
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

### Run

```bash
streamlit run src/app.py
```

Open the URL shown in the terminal (default: `http://localhost:8501`). The sample RFP is pre-selected — just click **Analyze Document**.

### Windows Quick Start

Double-click `scripts/start.bat` — it handles venv creation, dependency installation, dashboard launch, and opens your browser automatically. First run will prompt you to configure your API key via the `.env` file.

---

## Using Your Own Documents

1. Uncheck **"Use sample RFP document"** in the sidebar
2. Upload any procurement PDF
3. Click **Analyze Document**

The analyzer works best with text-based PDFs (not scanned images). For scanned documents, add OCR preprocessing (e.g., Tesseract + `pytesseract`) before the extraction step.

---

## Model Support

Default model: **`gpt-4o-mini`** (fast and cost-effective for extraction tasks). Supports any OpenAI-compatible chat model with JSON mode. Switch models in the sidebar dropdown or via the `LLM_MODEL` env var.

---

## Architecture Notes

| Concern | Implementation | Why |
|---------|---------------|-----|
| PDF parsing | PyMuPDF | Fast, pure-Python, no system deps |
| Structured extraction | OpenAI JSON mode | Reliable schema adherence |
| Validation | Pydantic v2 | Type-safe, serializable, documented |
| UI | Streamlit | Minimal boilerplate, reactive |
| Prompts | Separate module | Version-controlled, tweakable without touching code |

The design deliberately separates parsing, prompting, and validation so any layer can be swapped (e.g., replace OpenAI with a local model via vLLM, replace Streamlit with FastAPI, add OCR as a preprocessing step).

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Lint with ruff: `ruff check src/ tests/`
5. Run tests: `pytest tests/ -v --cov=src`
6. Push and open a pull request

---

## License

MIT — see [LICENSE](LICENSE).

---

*Portfolio Project 3 — [AgenticPH Labs](https://agenticph-labs.github.io/portfolio)*  
*Built by [AgenticPH Labs](https://agenticph-labs.github.io/portfolio) — intelligent tools for Philippine business decisions*
