import io
import logging
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, KeepTogether,
)

logger = logging.getLogger(__name__)

# ── Colour palette ────────────────────────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#15803d")
GREEN_LIGHT = colors.HexColor("#86efac")
GREEN_BG    = colors.HexColor("#f0fdf4")
AMBER       = colors.HexColor("#f59e0b")
RED_COLOR   = colors.HexColor("#ef4444")
GRAY_DARK   = colors.HexColor("#1f2937")
GRAY_MID    = colors.HexColor("#6b7280")
GRAY_LIGHT  = colors.HexColor("#f3f4f6")
WHITE       = colors.white


def _build_styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle(
            'Title',
            parent=base['Title'],
            fontSize=22,
            textColor=GREEN_DARK,
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ),
        'subtitle': ParagraphStyle(
            'Subtitle',
            parent=base['Normal'],
            fontSize=10,
            textColor=GRAY_MID,
            spaceAfter=12,
            alignment=TA_CENTER,
        ),
        'section': ParagraphStyle(
            'Section',
            parent=base['Heading2'],
            fontSize=13,
            textColor=GREEN_DARK,
            spaceBefore=14,
            spaceAfter=6,
            fontName='Helvetica-Bold',
        ),
        'body': ParagraphStyle(
            'Body',
            parent=base['Normal'],
            fontSize=10,
            textColor=GRAY_DARK,
            spaceAfter=4,
            leading=14,
        ),
        'label': ParagraphStyle(
            'Label',
            parent=base['Normal'],
            fontSize=9,
            textColor=GRAY_MID,
            spaceAfter=2,
        ),
        'value': ParagraphStyle(
            'Value',
            parent=base['Normal'],
            fontSize=10,
            textColor=GRAY_DARK,
            fontName='Helvetica-Bold',
            spaceAfter=4,
        ),
        'badge_green': ParagraphStyle(
            'BadgeGreen',
            parent=base['Normal'],
            fontSize=10,
            textColor=GREEN_DARK,
            fontName='Helvetica-Bold',
        ),
        'badge_red': ParagraphStyle(
            'BadgeRed',
            parent=base['Normal'],
            fontSize=10,
            textColor=RED_COLOR,
            fontName='Helvetica-Bold',
        ),
        'tip': ParagraphStyle(
            'Tip',
            parent=base['Normal'],
            fontSize=9,
            textColor=GRAY_DARK,
            leftIndent=12,
            spaceAfter=3,
            leading=13,
        ),
    }


def _divider(width=None):
    return HRFlowable(
        width=width or "100%",
        thickness=1,
        color=GREEN_LIGHT,
        spaceAfter=8,
        spaceBefore=4,
    )


def _kv_table(rows, styles):
    """Builds a two-column key-value table."""
    data = []
    for label, value in rows:
        data.append([
            Paragraph(label, styles['label']),
            Paragraph(str(value), styles['value']),
        ])
    table = Table(data, colWidths=[5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, GRAY_LIGHT]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def generate_scan_report(scan, user):
    """
    Generates a PDF report for a single plant scan result.
    Returns bytes of the PDF file.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = _build_styles()
    story  = []
    result = scan.result_data or {}

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("🌱 CropGuard AI", styles['title']))
    story.append(Paragraph("Plant Disease Detection Report", styles['subtitle']))
    story.append(_divider())

    # ── Report metadata ───────────────────────────────────────────────────────
    story.append(Paragraph("Report Details", styles['section']))
    meta_rows = [
        ("Farmer Name",   f"{user.first_name} {user.last_name}".strip() or user.username),
        ("Username",      user.username),
        ("Report Date",   datetime.now().strftime("%d %B %Y, %I:%M %p")),
        ("Scan ID",       f"#{scan.id}"),
        ("Scan Date",     scan.created_at.strftime("%d %B %Y, %I:%M %p")),
        ("Data Source",   "Kindwise AI" if scan.source == "kindwise" else "Offline Model (Fallback)"),
    ]
    story.append(_kv_table(meta_rows, styles))
    story.append(Spacer(1, 0.4 * cm))

    # ── Plant identification ──────────────────────────────────────────────────
    story.append(_divider())
    story.append(Paragraph("Plant Identification", styles['section']))

    diseases_list  = result.get('diseases', [])
    first_disease  = diseases_list[0].get('name', '') if diseases_list else ''
    plant_name = (
        scan.plant_name
        or result.get('plant_name', '')
        or (f"Plant with {first_disease}" if first_disease else 'Unknown Plant')
    )
    
    is_healthy   = scan.is_healthy
    confidence   = scan.confidence or result.get('plant_probability', 0)

    health_style = styles['badge_green'] if is_healthy else styles['badge_red']
    health_text  = "✓ Healthy" if is_healthy else "✗ Disease Detected"

    id_rows = [
        ("Plant Name",   plant_name),
        ("Health Status", ""),
        ("Confidence",   f"{confidence:.1f}%"),
    ]
    story.append(_kv_table(id_rows, styles))
    story.append(Paragraph(f"  {health_text}", health_style))
    story.append(Spacer(1, 0.3 * cm))

    # Unsupported crop warning
    if scan.unsupported_crop:
        story.append(Paragraph(
            "⚠ Warning: This plant is outside the supported dataset. "
            "Results from the offline model may have limited accuracy.",
            styles['tip'],
        ))

    # ── Diseases ──────────────────────────────────────────────────────────────
    diseases = result.get('diseases', [])
    if diseases:
        story.append(_divider())
        story.append(Paragraph(f"Diseases Detected ({len(diseases)})", styles['section']))

        for disease in diseases:
            name        = disease.get('name', 'Unknown')
            probability = disease.get('probability', 0)
            description = disease.get('description', '')
            treatment   = disease.get('treatment', {})

            story.append(KeepTogether([
                Paragraph(f"{name} — {probability:.1f}% confidence", styles['value']),
            ]))

            if description:
                story.append(Paragraph(description, styles['body']))

            # Biological treatment
            bio = treatment.get('biological', [])
            if bio:
                story.append(Paragraph("Biological Treatment:", styles['label']))
                for item in bio[:4]:
                    story.append(Paragraph(f"• {item}", styles['tip']))

            # Chemical treatment
            chem = treatment.get('chemical', [])
            if chem:
                story.append(Paragraph("Chemical Treatment:", styles['label']))
                for item in chem[:4]:
                    story.append(Paragraph(f"• {item}", styles['tip']))

            # Prevention
            prev = treatment.get('prevention', [])
            if prev:
                story.append(Paragraph("Prevention:", styles['label']))
                for item in prev[:4]:
                    story.append(Paragraph(f"• {item}", styles['tip']))

            story.append(Spacer(1, 0.3 * cm))

    # ── No disease ────────────────────────────────────────────────────────────
    elif is_healthy:
        story.append(_divider())
        story.append(Paragraph("Disease Status", styles['section']))
        story.append(Paragraph(
            "No diseases detected. Your plant appears healthy. "
            "Continue your current farming practices.",
            styles['body'],
        ))

    # ── General recommendations ───────────────────────────────────────────────
    story.append(_divider())
    story.append(Paragraph("General Recommendations", styles['section']))
    general_tips = [
        "Inspect crops regularly — early detection prevents spread.",
        "Maintain proper spacing between plants for airflow.",
        "Use certified disease-free seeds for the next season.",
        "Consult your local agricultural officer for persistent issues.",
        "Keep records of all treatments applied for future reference.",
    ]
    for tip in general_tips:
        story.append(Paragraph(f"• {tip}", styles['tip']))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(_divider())
    story.append(Paragraph(
        "Generated by CropGuard AI — Smart Farming Assistant | "
        f"Report generated on {datetime.now().strftime('%d/%m/%Y at %I:%M %p')}",
        styles['subtitle'],
    ))
    story.append(Paragraph(
        "This report is for informational purposes only. "
        "Always consult a certified agronomist for critical decisions.",
        styles['label'],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_summary_report(user, scans, crop_recs, fertilizer_recs, irrigation_recs):
    """
    Generates a comprehensive summary PDF for all user activity.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = _build_styles()
    story  = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("🌱 CropGuard AI", styles['title']))
    story.append(Paragraph("Farming Activity Summary Report", styles['subtitle']))
    story.append(_divider())

    # ── Farmer info ───────────────────────────────────────────────────────────
    story.append(Paragraph("Farmer Profile", styles['section']))
    farmer_rows = [
        ("Name",         f"{user.first_name} {user.last_name}".strip() or user.username),
        ("Username",     user.username),
        ("Email",        user.email),
        ("Report Date",  datetime.now().strftime("%d %B %Y")),
    ]
    try:
        profile = user.profile
        if profile.location:
            farmer_rows.append(("Location", profile.location))
        if profile.farm_size:
            farmer_rows.append(("Farm Size", profile.farm_size))
    except Exception:
        pass

    story.append(_kv_table(farmer_rows, styles))
    story.append(Spacer(1, 0.3 * cm))

    # ── Activity summary ──────────────────────────────────────────────────────
    story.append(_divider())
    story.append(Paragraph("Activity Summary", styles['section']))

    summary_data = [
        ["Activity",              "Count"],
        ["Plant Scans",           str(len(scans))],
        ["Diseases Detected",     str(sum(1 for s in scans if not s.is_healthy))],
        ["Crop Recommendations",  str(len(crop_recs))],
        ["Fertilizer Advice",     str(len(fertilizer_recs))],
        ["Irrigation Plans",      str(len(irrigation_recs))],
    ]

    summary_table = Table(summary_data, colWidths=[10 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, 0), GREEN_DARK),
        ('TEXTCOLOR',    (0, 0), (-1, 0), WHITE),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 10),
        ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ('FONTSIZE',     (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING',   (0, 0), (-1, -1), 7),
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor("#d1fae5")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Recent scans ──────────────────────────────────────────────────────────
    if scans:
        story.append(_divider())
        story.append(Paragraph("Recent Plant Scans", styles['section']))

        scan_data = [["Plant", "Status", "Confidence", "Source", "Date"]]
        for scan in scans[:10]:
            scan_data.append([
                scan.plant_name or "Unknown",
                "Healthy" if scan.is_healthy else "Diseased",
                f"{scan.confidence:.1f}%",
                "Kindwise" if scan.source == "kindwise" else "Offline",
                scan.created_at.strftime("%d/%m/%Y"),
            ])

        scan_table = Table(
            scan_data,
            colWidths=[4.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4*cm]
        )
        scan_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), GREEN_DARK),
            ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING',    (0, 0), (-1, -1), 5),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor("#d1fae5")),
        ]))
        story.append(scan_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── Recent crop recommendations ───────────────────────────────────────────
    if crop_recs:
        story.append(_divider())
        story.append(Paragraph("Recent Crop Recommendations", styles['section']))

        crop_data = [["Recommended Crop", "Confidence", "Date"]]
        for rec in crop_recs[:8]:
            crop_data.append([
                rec.recommended_crop.capitalize(),
                f"{rec.confidence:.1f}%",
                rec.created_at.strftime("%d/%m/%Y"),
            ])

        crop_table = Table(crop_data, colWidths=[8*cm, 4*cm, 4*cm])
        crop_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), GREEN_DARK),
            ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor("#d1fae5")),
        ]))
        story.append(crop_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── Recent fertilizer recommendations ─────────────────────────────────────
    if fertilizer_recs:
        story.append(_divider())
        story.append(Paragraph("Recent Fertilizer Recommendations", styles['section']))

        fert_data = [["Crop", "Fertilizer", "Confidence", "Date"]]
        for rec in fertilizer_recs[:8]:
            fert_data.append([
                rec.crop.capitalize(),
                rec.recommended_fertilizer,
                f"{rec.confidence:.1f}%",
                rec.created_at.strftime("%d/%m/%Y"),
            ])

        fert_table = Table(fert_data, colWidths=[4*cm, 6*cm, 3*cm, 3*cm])
        fert_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), GREEN_DARK),
            ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor("#d1fae5")),
        ]))
        story.append(fert_table)
        story.append(Spacer(1, 0.3 * cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(_divider())
    story.append(Paragraph(
        "Generated by CropGuard AI — Smart Farming Assistant | "
        f"{datetime.now().strftime('%d/%m/%Y at %I:%M %p')}",
        styles['subtitle'],
    ))
    story.append(Paragraph(
        "This report is for informational purposes only. "
        "Always consult a certified agronomist for critical decisions.",
        styles['label'],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()