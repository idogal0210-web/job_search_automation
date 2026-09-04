import os
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import bidi.algorithm as bidi
import arabic_reshaper

from weekly_summary import load_weekly_jobs

# Register Hebrew fonts from macOS system library
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

pdfmetrics.registerFont(TTFont("HebrewArial", FONT_REGULAR))
pdfmetrics.registerFont(TTFont("HebrewArial-Bold", FONT_BOLD))

def r(text):
    """Reshape and apply BiDi algorithm for proper Hebrew RTL rendering."""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return bidi.get_display(reshaped)
    except Exception:
        return str(text)

def generate_weekly_pdf(output_pdf_path="weekly_jobs_summary_ido_gal.pdf"):
    print("[+] Loading weekly jobs for PDF generation...")
    jobs = load_weekly_jobs()
    print(f"[+] Loaded {len(jobs)} total jobs from archive.")

    # Deduplicate by link
    seen_links = set()
    unique_jobs = []
    for j in jobs:
        link = j.get("link", "")
        if link and link not in seen_links:
            seen_links.add(link)
            unique_jobs.append(j)

    # Top 3 Picks
    top_3_picks = sorted(unique_jobs, key=lambda x: x.get("match_score", 0), reverse=True)[:3]

    # Group by date
    HEBREW_DAYS = {
        "Sunday": "יום ראשון", "Monday": "יום שני", "Tuesday": "יום שלישי",
        "Wednesday": "יום רביעי", "Thursday": "יום חמישי", "Friday": "יום שישי", "Saturday": "יום שבת"
    }

    jobs_by_date = {}
    for j in unique_jobs:
        d_str = j.get("date")
        if not d_str:
            continue
        if d_str not in jobs_by_date:
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d")
                day_eng = dt.strftime("%A")
                day_name = HEBREW_DAYS.get(day_eng, day_eng)
            except Exception:
                day_name = "תאריך"
            jobs_by_date[d_str] = {
                "day_name": day_name,
                "jobs": []
            }
        jobs_by_date[d_str]["jobs"].append(j)

    sorted_dates = sorted(jobs_by_date.keys(), reverse=True)

    # Setup Document
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    # Define Styles
    style_title = ParagraphStyle(
        name="DocTitle",
        fontName="HebrewArial-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a")
    )
    style_subtitle = ParagraphStyle(
        name="DocSubtitle",
        fontName="HebrewArial",
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569")
    )
    style_gold_header = ParagraphStyle(
        name="GoldHeader",
        fontName="HebrewArial-Bold",
        fontSize=12,
        leading=15,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#92400e")
    )
    style_gold_item = ParagraphStyle(
        name="GoldItem",
        fontName="HebrewArial",
        fontSize=9.5,
        leading=13,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#1e293b")
    )
    style_day_header = ParagraphStyle(
        name="DayHeader",
        fontName="HebrewArial-Bold",
        fontSize=11.5,
        leading=14,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#0f172a")
    )
    style_table_header = ParagraphStyle(
        name="TableHeader",
        fontName="HebrewArial-Bold",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#ffffff")
    )
    style_cell = ParagraphStyle(
        name="TableCell",
        fontName="HebrewArial",
        fontSize=8,
        leading=10.5,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#1e293b")
    )
    style_cell_bold = ParagraphStyle(
        name="TableCellBold",
        fontName="HebrewArial-Bold",
        fontSize=8,
        leading=10.5,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#0f172a")
    )
    style_cell_center = ParagraphStyle(
        name="TableCellCenter",
        fontName="HebrewArial-Bold",
        fontSize=8,
        leading=10.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#166534")
    )
    style_cell_link = ParagraphStyle(
        name="TableCellLink",
        fontName="HebrewArial-Bold",
        fontSize=8,
        leading=10.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0284c7")
    )
    style_footer = ParagraphStyle(
        name="Footer",
        fontName="HebrewArial",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#94a3b8")
    )

    story = []

    # Title & Subtitle Header
    story.append(Paragraph(r("🔗 דוח סיכום שבועי: כל המשרות המובילות | עידו גל"), style_title))
    story.append(Spacer(1, 4))
    
    now_formatted = datetime.now().strftime("%d.%m.%Y")
    subtitle_text = f"תאריך הפקה: {now_formatted} | סה\"כ נאספו השבוע: {len(unique_jobs)} משרות נבחרות"
    story.append(Paragraph(r(subtitle_text), style_subtitle))
    story.append(Spacer(1, 10))

    # Top 3 Gold Box
    if top_3_picks:
        gold_data = []
        gold_header_text = r("⭐ משרות הזהב של השבוע (Top 3 Picks):")
        gold_data.append([Paragraph(f"<b>{gold_header_text}</b>", style_gold_header)])
        
        for idx, pick in enumerate(top_3_picks, 1):
            comp = pick.get("company", "")
            title = pick.get("title", "")
            score = pick.get("match_score", 90)
            sector = pick.get("sector", "")
            link = pick.get("link", "#")
            
            item_text = (
                f"<b>{idx}. {r(comp)} - {r(title)}</b> | "
                f"<font color=\"#16a34a\"><b>{score}% {r('התאמה')}</b></font> | "
                f"{r(sector)} &nbsp;&nbsp; "
                f"<a href=\"{link}\" color=\"#0284c7\"><b><u>{r('הגש מועמדות למשרה ↗')}</u></b></a>"
            )
            gold_data.append([Paragraph(item_text, style_gold_item)])

        gold_table = Table(gold_data, colWidths=[545])
        gold_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#f59e0b")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#fde68a")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(gold_table)
        story.append(Spacer(1, 12))

    # Day by Day Tables
    col_widths = [80, 48, 115, 180, 122] # Total = 545

    for date_key in sorted_dates:
        day_data = jobs_by_date[date_key]
        try:
            d_formatted = datetime.strptime(date_key, "%Y-%m-%d").strftime("%d.%m.%Y")
        except Exception:
            d_formatted = date_key
        day_name = day_data.get("day_name", "")
        day_count = len(day_data["jobs"])

        header_banner = f"📅 {day_name} | {d_formatted} ({day_count} משרות)"
        story.append(Paragraph(r(header_banner), style_day_header))
        story.append(Spacer(1, 4))

        # Table data
        table_rows = []
        # Header Row (RTL column order: Action, Match%, Sector, Title, Company)
        table_rows.append([
            Paragraph(r("פעולה"), style_table_header),
            Paragraph(r("התאמה"), style_table_header),
            Paragraph(r("סקטור / תחום"), style_table_header),
            Paragraph(r("שם המשרה"), style_table_header),
            Paragraph(r("חברה"), style_table_header),
        ])

        day_jobs_sorted = sorted(day_data["jobs"], key=lambda x: x.get("match_score", 0), reverse=True)

        for job in day_jobs_sorted:
            score = job.get("match_score", 85)
            comp = job.get("company", "")
            title = job.get("title", "")
            sector = job.get("sector", "")
            link = job.get("link", "#")

            btn_link_text = f"<a href=\"{link}\" color=\"#0284c7\"><b><u>{r('הגש מועמדות ↗')}</u></b></a>"

            table_rows.append([
                Paragraph(btn_link_text, style_cell_link),
                Paragraph(f"{score}%", style_cell_center),
                Paragraph(r(sector), style_cell),
                Paragraph(r(title), style_cell),
                Paragraph(r(comp), style_cell_bold),
            ])

        day_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
        day_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        story.append(day_table)
        story.append(Spacer(1, 10))

    # Footer
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
    story.append(Paragraph(r("דוח זה הופק באופן אוטומטי ע\"י מערכת Job Search Automation עבור עידו גל"), style_footer))

    doc.build(story)
    print(f"[+] Weekly PDF report successfully generated at: {output_pdf_path}")
    return output_pdf_path

if __name__ == "__main__":
    generate_weekly_pdf()
