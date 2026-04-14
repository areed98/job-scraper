"""
PDF utilities:
- extract_text_from_pdf: uses pdfminer.six
- generate_pdf: renders resume text to PDF via reportlab
"""
from pdfminer.high_level import extract_text
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a PDF file."""
    try:
        return extract_text(pdf_path)
    except Exception as e:
        print(f"[pdf_service] extract error: {e}")
        return ""


def generate_pdf(resume_text: str, output_path: str) -> None:
    """
    Render resume_text as a styled PDF and save to output_path using reportlab.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "ResumeNormal",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        alignment=TA_LEFT,
    )

    story = []
    for line in resume_text.splitlines():
        stripped = line.strip()
        if stripped:
            # Escape ampersands/angle brackets for ReportLab XML parser
            safe = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, normal))
        else:
            story.append(Spacer(1, 6))

    doc.build(story)
