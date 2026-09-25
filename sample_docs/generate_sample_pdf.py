"""Generate a sample RFP PDF for the analyzer demo."""
import pymupdf
from pathlib import Path

SAMPLE_PATH = Path("/opt/data/portfolio/p3-rfp-analyzer/sample_docs/rfp_sample.pdf")
SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)

doc = pymupdf.open()

# Helper to insert bold-like text by using helv with larger size where bold is desired
def add_text(page, point, text, fontsize=10, bold=False):
    font = "helv" if not bold else "helv"
    # Fake bold by inserting text twice with slight offset
    if bold:
        page.insert_text(pymupdf.Point(point.x - 0.3, point.y), text, fontsize=fontsize, fontname=font)
        page.insert_text(pymupdf.Point(point.x + 0.3, point.y), text, fontsize=fontsize, fontname=font)
    page.insert_text(point, text, fontsize=fontsize, fontname=font)

def write_text(page, x, y, text, fontsize=10, width=0, bold=False):
    font = "helv"
    page.insert_text(pymupdf.Point(x, y), text, fontsize=fontsize, fontname=font)

# ── Page 1: Cover / Title ──────────────────────────────────────────────────
p = doc.new_page()

write_text(p, 72, 80, "REQUEST FOR PROPOSAL", fontsize=20)
write_text(p, 72, 110, "RFP No: IT-2026-0042", fontsize=13)
write_text(p, 72, 130, "Issue Date: April 15, 2026", fontsize=11)

p.draw_line(pymupdf.Point(72, 150), pymupdf.Point(540, 150))

write_text(p, 72, 180, "Issuing Organization", fontsize=12)
write_text(p, 72, 200, "State Department of Technology Services", fontsize=11)
write_text(p, 72, 220, "450 Capitol Avenue, Suite 300", fontsize=11)
write_text(p, 72, 240, "Hartford, CT 06103", fontsize=11)

p.draw_line(pymupdf.Point(72, 260), pymupdf.Point(540, 260))

write_text(p, 72, 290, "Title:", fontsize=12)
write_text(p, 72, 310, "Enterprise Data Analytics Platform", fontsize=11)

write_text(p, 72, 340, "Procurement Type:", fontsize=12)
write_text(p, 72, 360, "Request for Proposal (RFP)", fontsize=11)

write_text(p, 72, 390, "Contract Value:", fontsize=12)
write_text(p, 72, 410, "Estimated $750,000 - $1,200,000 (five-year term)", fontsize=11)

write_text(p, 72, 440, "Important Dates:", fontsize=12)
dates = [
    "Pre-Proposal Conference:  May 5, 2026 at 10:00 AM ET",
    "Questions Due:            May 12, 2026 at 5:00 PM ET",
    "Proposals Due:            June 1, 2026 at 2:00 PM ET",
    "Anticipated Award:        July 15, 2026",
    "Contract Start:           September 1, 2026",
]
for i, d in enumerate(dates):
    write_text(p, 72, 465 + i * 22, d, fontsize=10)

# ── Page 2: Background & Scope ─────────────────────────────────────────────
p = doc.new_page()
write_text(p, 72, 60, "1. BACKGROUND", fontsize=14)
bg_text = (
    "The State Department of Technology Services (SDTS) is seeking proposals from qualified "
    "vendors to design, develop, deploy, and maintain an Enterprise Data Analytics Platform "
    "(EDAP). The platform will consolidate data from 15+ agency systems, provide real-time "
    "dashboarding, support ad-hoc querying, and enable predictive analytics for resource "
    "allocation and service delivery optimization."
)
write_text(p, 72, 90, bg_text, fontsize=10)
write_text(p, 72, 200, "2. SCOPE OF WORK", fontsize=14)

scope_items = [
    "2.1 Data ingestion pipelines for 15+ source systems (structured and unstructured)",
    "2.2 Data warehouse / data lake architecture design and implementation",
    "2.3 Real-time dashboard and reporting interface (role-based access)",
    "2.4 Ad-hoc query engine with natural-language interface (NLP-based)",
    "2.5 Predictive analytics modules for resource forecasting and anomaly detection",
    "2.6 API layer for third-party integration",
    "2.7 User training (train-the-trainer) and comprehensive documentation",
    "2.8 24/7 production support with SLA guarantees (99.5% uptime)",
]
for i, item in enumerate(scope_items):
    write_text(p, 72, 230 + i * 22, item, fontsize=10)

# ── Page 3: Deliverables ───────────────────────────────────────────────────
p = doc.new_page()
write_text(p, 72, 60, "3. DELIVERABLES", fontsize=14)

deliverables = [
    ("D1 - Requirements Specification", "Complete SRS document approved by SDTS program manager.", "June 30, 2026"),
    ("D2 - Architecture Blueprint", "Detailed architecture document covering data flow, security, scalability.", "July 31, 2026"),
    ("D3 - MVP Release (Phase 1)", "Ingestion pipelines and dashboards for first 5 source systems.", "September 30, 2026"),
    ("D4 - Full Platform Release", "All 15+ source systems, analytics modules, and API layer.", "December 15, 2026"),
    ("D5 - Training and Handover", "Training sessions, user manuals, admin guides, and source code repository.", "January 15, 2027"),
    ("D6 - Warranty and Support", "6-month production support post-handover with SLA monitoring.", "July 15, 2027"),
]

write_text(p, 72, 90, "Deliverable", fontsize=10)
write_text(p, 400, 90, "Due Date", fontsize=10)
p.draw_line(pymupdf.Point(72, 95), pymupdf.Point(540, 95))

for i, (name, desc, due) in enumerate(deliverables):
    y = 110 + i * 50
    write_text(p, 72, y, name, fontsize=10)
    write_text(p, 72, y + 14, desc, fontsize=9)
    write_text(p, 400, y + 4, due, fontsize=10)
    p.draw_line(pymupdf.Point(72, y + 35), pymupdf.Point(540, y + 35))

# ── Page 4: Eligibility & Evaluation ──────────────────────────────────────
p = doc.new_page()
write_text(p, 72, 60, "4. ELIGIBILITY REQUIREMENTS", fontsize=14)

eligibility = [
    ("Experience", "Minimum 5 years of experience building enterprise-scale data platforms (reference required)"),
    ("Team Qualification", "Proposed team must include at least one certified AWS Solutions Architect and one CDMP-certified data professional"),
    ("Financial Stability", "Minimum $2M annual revenue for the past 2 fiscal years; audited financial statements required"),
    ("Security Clearance", "All team members must pass state-level background check (fingerprinting)"),
    ("Insurance", "Must hold $5M general liability and $2M professional liability insurance"),
]
for i, (cat, req) in enumerate(eligibility):
    write_text(p, 72, 90 + i * 30, f"[Mandatory] {cat}:", fontsize=10)
    write_text(p, 72, 90 + i * 30 + 14, req, fontsize=9)

write_text(p, 72, 280, "5. EVALUATION CRITERIA", fontsize=14)
write_text(p, 72, 305, "Proposals will be evaluated on a 100-point scale:", fontsize=10)

criteria = [
    ("Technical Approach and Solution Design", 30),
    ("Past Performance and References", 20),
    ("Project Management and Staffing Plan", 15),
    ("Cost / Price Proposal", 20),
    ("Small Business / MWBE Participation", 10),
    ("Compliance with RFP Requirements", 5),
]
for i, (criterion, weight) in enumerate(criteria):
    y = 330 + i * 25
    write_text(p, 72, y, criterion, fontsize=10)
    write_text(p, 450, y, f"{weight}%", fontsize=10)

total_y = 330 + len(criteria) * 25
p.draw_line(pymupdf.Point(72, total_y), pymupdf.Point(540, total_y))
write_text(p, 72, total_y + 10, "TOTAL", fontsize=10)
write_text(p, 450, total_y + 10, "100%", fontsize=10)

# ── Page 5: Terms, Conditions & Risks ─────────────────────────────────────
p = doc.new_page()
write_text(p, 72, 60, "6. TERMS AND CONDITIONS", fontsize=14)

terms = [
    "6.1 Contract Term: Five (5) years from the effective date, with two (2) optional one-year renewals.",
    "6.2 Payment Terms: Net 45. 10% retention held on each milestone payment until final acceptance.",
    "6.3 Warranty: Vendor warrants the platform will be free from defects for 12 months post-acceptance.",
    "6.4 Liquidated Damages: $500 per day for each deliverable past due, up to 10% of contract value.",
    "6.5 Data Ownership: All data, code, and intellectual property produced under this contract shall be owned exclusively by the State.",
    "6.6 Non-Disclosure: Vendor and its personnel shall sign state-standard NDAs. Breach results in immediate termination and liability for damages.",
    "6.7 Auditing: State reserves the right to audit vendor's security controls, financial records, and subcontractor compliance at any time.",
    "6.8 Termination for Convenience: State may terminate without cause with 30 days written notice.",
    "6.9 Debarment: Vendor certifies it is not debarred, suspended, or otherwise excluded from federal or state procurement programs.",
]
for i, t in enumerate(terms):
    write_text(p, 72, 90 + i * 24, t, fontsize=9)

write_text(p, 72, 340, "7. IMPORTANT NOTES / POTENTIAL RISKS", fontsize=14)
risks = [
    "10% retention on milestone payments creates cash-flow pressure - factor into pricing.",
    "Liquidated damages clause ($500/day) applies per deliverable - aggressive schedule risk.",
    "Fingerprint-based background checks for ALL team members may delay onboarding by 4-6 weeks.",
    "Net 45 payment terms with 10% retention means final payment may be 60+ days post-delivery.",
    "State reserves audit rights - ensure SOC 2 Type II or equivalent certification is current.",
]
for i, r in enumerate(risks):
    write_text(p, 72, 370 + i * 22, r, fontsize=9)

# ── Save ──────────────────────────────────────────────────────────────────
doc.save(str(SAMPLE_PATH))
doc.close()

print(f"Sample RFP PDF created: {SAMPLE_PATH} ({SAMPLE_PATH.stat().st_size} bytes)")
