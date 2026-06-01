"""
TradeMind — PDF Export
Generates a professional PDF from the report data using ReportLab.
"""

import logging
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logger = logging.getLogger("trademind.report.pdf")


def export_pdf(ticker: str, context: dict) -> bytes:
    """
    Generate a professional PDF report.

    Args:
        ticker: Stock symbol
        context: Full pipeline context with all agent outputs

    Returns:
        PDF file as bytes
    """
    logger.info(f"Generating PDF report for {ticker}...")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    # Build custom styles
    styles = _build_styles()

    # Build story (list of flowable elements)
    story = []

    report = context.get("report", {})
    company = context.get("company_info", {})
    news = context.get("news_analysis", {})
    quant = context.get("quant_analysis", {})
    fundamental = context.get("fundamental_analysis", {})
    risk = context.get("risk_analysis", {})

    company_name = company.get("name", ticker)
    rating = report.get("investment_rating", "N/A")
    confidence = report.get("confidence_level", "N/A")
    date_str = datetime.now().strftime("%B %d, %Y")

    # --- HEADER ---
    story.append(Paragraph("TradeMind", styles["CustomTitle"]))
    story.append(Paragraph("AI-Powered Equity Research Report", styles["CustomSubtitle"]))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB")))
    story.append(Spacer(1, 15))

    # --- COMPANY INFO ---
    story.append(Paragraph(f"{company_name} ({ticker})", styles["CompanyName"]))
    story.append(Paragraph(f"Report Date: {date_str}", styles["Date"]))
    story.append(Spacer(1, 15))

    # --- RATING TABLE ---
    rating_color = {"BUY": colors.HexColor("#16A34A"),
                    "HOLD": colors.HexColor("#EAB308"),
                    "SELL": colors.HexColor("#DC2626")}.get(rating, colors.grey)

    rating_data = [
        ["Investment Rating", "Confidence", "Current Price", "Price Target", "Risk Level"],
        [
            rating,
            f"{confidence}/100",
            f"${company.get('current_price', 'N/A')}",
            f"${report.get('price_target', 'N/A')}",
            risk.get("overall_risk_score", "N/A"),
        ],
    ]

    rating_table = Table(rating_data, colWidths=[90, 80, 90, 90, 80])
    rating_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, 1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 1), (0, 1), rating_color),
        ("TEXTCOLOR", (0, 1), (0, 1), colors.white),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(rating_table)
    story.append(Spacer(1, 20))

    # --- EXECUTIVE SUMMARY ---
    story.append(Paragraph("Executive Summary", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB")))
    story.append(Spacer(1, 8))
    exec_summary = report.get("executive_summary", "No executive summary available.")
    story.append(Paragraph(exec_summary, styles["Body"]))
    story.append(Spacer(1, 15))

    # --- SECTIONS ---
    sections = report.get("sections", {})

    # News & Sentiment
    story.append(Paragraph("News & Market Sentiment", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB")))
    story.append(Spacer(1, 8))
    news_text = sections.get("news_and_sentiment", news.get("sentiment_summary", "N/A"))
    story.append(Paragraph(_sanitize(news_text), styles["Body"]))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        f"Sentiment Score: {news.get('sentiment_score', 'N/A')}/100 "
        f"({news.get('overall_sentiment', 'N/A')})",
        styles["Metric"]
    ))
    story.append(Spacer(1, 15))

    # Technical Analysis
    story.append(Paragraph("Technical Analysis", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB")))
    story.append(Spacer(1, 8))
    tech_text = sections.get("technical_analysis", quant.get("technical_summary", "N/A"))
    story.append(Paragraph(_sanitize(tech_text), styles["Body"]))
    story.append(Spacer(1, 8))

    # Technical indicators table
    raw = quant.get("raw_indicators", {})
    if raw:
        ta_data = [
            ["Indicator", "Value", "Signal"],
            ["RSI (14)", str(raw.get("rsi", {}).get("value", "N/A")), raw.get("rsi", {}).get("signal", "N/A")],
            ["MACD", str(raw.get("macd", {}).get("macd_line", "N/A")), raw.get("macd", {}).get("signal", "N/A")],
            ["Bollinger", "—", raw.get("bollinger", {}).get("signal", "N/A")],
            ["50 SMA", f"${raw.get('sma', {}).get('sma_50', 'N/A')}", "—"],
            ["200 SMA", f"${raw.get('sma', {}).get('sma_200', 'N/A')}", raw.get("sma", {}).get("golden_cross", "N/A")],
            ["Volatility", f"{raw.get('volatility', {}).get('annualized_30d', 'N/A')}%", raw.get("volatility", {}).get("signal", "N/A")],
        ]

        ta_table = Table(ta_data, colWidths=[120, 120, 200])
        ta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(ta_table)
    story.append(Spacer(1, 15))

    # Fundamental Analysis
    story.append(Paragraph("Fundamental Analysis", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB")))
    story.append(Spacer(1, 8))
    fund_text = sections.get("fundamental_analysis", fundamental.get("fundamental_summary", "N/A"))
    story.append(Paragraph(_sanitize(fund_text), styles["Body"]))
    story.append(Spacer(1, 15))

    # Risk Assessment
    story.append(Paragraph("Risk Assessment", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB")))
    story.append(Spacer(1, 8))
    risk_text = sections.get("risk_factors", risk.get("risk_summary", "N/A"))
    story.append(Paragraph(_sanitize(risk_text), styles["Body"]))
    story.append(Spacer(1, 15))

    # Investment Thesis
    story.append(Paragraph("Investment Thesis", styles["SectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB")))
    story.append(Spacer(1, 8))

    thesis = sections.get("investment_thesis", {})
    if isinstance(thesis, dict):
        story.append(Paragraph("Bull Case", styles["SubHeader"]))
        story.append(Paragraph(_sanitize(thesis.get("bull_case", "N/A")), styles["Body"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Bear Case", styles["SubHeader"]))
        story.append(Paragraph(_sanitize(thesis.get("bear_case", "N/A")), styles["Body"]))
    story.append(Spacer(1, 20))

    # Disclaimer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 8))
    disclaimer = report.get("disclaimer",
                            "This report is for informational purposes only and does not constitute investment advice.")
    story.append(Paragraph(disclaimer, styles["Disclaimer"]))
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"Generated by TradeMind AI — {date_str}", styles["Disclaimer"]))

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(f"PDF generated for {ticker}: {len(pdf_bytes)} bytes")
    return pdf_bytes


def _build_styles():
    """Build custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=28, textColor=colors.HexColor("#1E3A5F"),
        spaceAfter=2, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "CustomSubtitle",
        fontSize=12, textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        "CompanyName",
        fontSize=20, textColor=colors.HexColor("#0F172A"),
        fontName="Helvetica-Bold", spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "Date",
        fontSize=10, textColor=colors.HexColor("#94A3B8"),
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        fontSize=14, textColor=colors.HexColor("#1E3A5F"),
        fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "SubHeader",
        fontSize=11, textColor=colors.HexColor("#334155"),
        fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        "Body",
        fontSize=10, textColor=colors.HexColor("#334155"),
        leading=14, alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "Metric",
        fontSize=10, textColor=colors.HexColor("#2563EB"),
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "Disclaimer",
        fontSize=8, textColor=colors.HexColor("#94A3B8"),
        leading=10, alignment=TA_CENTER,
    ))

    return styles


def _sanitize(text: str) -> str:
    """Sanitize text for ReportLab (escape XML special chars)."""
    if not text:
        return "N/A"
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # Replace common markdown
    text = text.replace("**", "")
    text = text.replace("##", "")
    text = text.replace("# ", "")
    return text
