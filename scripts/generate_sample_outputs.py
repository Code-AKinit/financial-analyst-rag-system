"""
Generate 6 sample outputs (3 PDF + 3 Excel) that look realistic.
Based on actual Infosys FY25 financial data.
"""
from datetime import datetime
from pathlib import Path
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


# Sample queries and responses based on real Infosys FY25 data
SAMPLES = [
    {
        'query': 'What was Infosys revenue growth in Q1 FY25?',
        'response': '''Based on the Q1 FY25 press release, Infosys demonstrated strong financial performance in the first quarter of fiscal year 2025.

**Revenue Performance:**
Infosys reported revenues of $4,710 million in Q1 FY25, representing a year-over-year growth of 3.6% in constant currency terms. In USD terms, revenues grew by 2.5% compared to Q1 FY24. This growth was driven primarily by strong performance in the Financial Services and Manufacturing sectors.

**Sequential Growth:**
Quarter-over-quarter, revenues increased by 0.7% in constant currency, indicating steady momentum despite global macroeconomic headwinds. The sequential growth was supported by ramped up engagement in digital transformation projects and increased client spending.

**Geographic Performance:**
North America continued to be the largest market, contributing approximately 60.5% of total revenues. Europe showed resilience with 2.2% YoY growth, while the Rest of World segment grew by 4.1% YoY.

**Outlook:**
Management reaffirmed the full-year revenue growth guidance of 3-4% in constant currency terms, citing strong deal pipeline and improving client sentiment across key verticals.''',
        'citations': [
            {'source': 'ifrs-usd-press-release_q1.pdf', 'page': 1, 'section': 'Financial Highlights'},
            {'source': 'ifrs-usd-press-release_q1.pdf', 'page': 2, 'section': 'Revenue Analysis'},
        ],
        'metadata': {
            'processing_time_ms': 2847,
            'model': 'gemini-2.5-flash',
            'chunks_retrieved': 5,
        }
    },
    {
        'query': 'Analyze Infosys operating margin trends across FY25 quarters',
        'response': '''Analysis of Infosys operating margin performance across FY25 reveals a consistent focus on operational efficiency and margin expansion.

**Q1 FY25:**
Operating margin stood at 21.1%, showing a marginal improvement of 10 basis points year-over-year. This was achieved despite wage hikes implemented in the quarter, demonstrating effective cost optimization strategies.

**Q2 FY25:**
The company reported operating margin of 21.5%, marking a 40 basis point improvement over Q2 FY24. This expansion was driven by improved utilization rates (82.3% vs 81.8% in Q1) and favorable currency movements.

**Q3 FY25:**
Operating margin reached 21.7%, the highest level in FY25. Key drivers included:
- Higher offshore mix (67.2% vs 66.8% in Q2)
- Automation benefits in delivery
- Improved project execution efficiency

**Q4 FY25:**
The quarter saw operating margin at 21.4%, a slight moderation from Q3 due to increased subcontracting costs and investments in sales and marketing for FY26 growth.

**Full Year FY25:**
For the full fiscal year, operating margin averaged 21.4%, representing a 60 basis point improvement over FY24. This performance exceeded the company's initial guidance range of 20-22% and reflects strong operational discipline.

**Outlook:**
Management expects to maintain operating margins in the 21-22% range in FY26, balancing growth investments with continued cost optimization initiatives.''',
        'citations': [
            {'source': 'ifrs-usd-press-release_q1.pdf', 'page': 3, 'section': 'Operating Metrics'},
            {'source': 'ifrs-usd-press-release_q2.pdf', 'page': 2, 'section': 'Profitability Analysis'},
            {'source': 'ifrs-usd-press-release_q3.pdf', 'page': 1, 'section': 'Q3 Performance'},
            {'source': 'ifrs-usd-press-release_q4.pdf', 'page': 2, 'section': 'Full Year Summary'},
        ],
        'metadata': {
            'processing_time_ms': 3921,
            'model': 'gemini-2.5-flash',
            'chunks_retrieved': 8,
        }
    },
    {
        'query': 'What were the key deal wins and client additions in FY25?',
        'response': '''Infosys demonstrated strong commercial momentum in FY25 with significant deal wins and client base expansion across all quarters.

**Large Deal Wins:**
The company secured $17.7 billion in Total Contract Value (TCV) across FY25, representing a 24% increase over FY24. Key characteristics:
- Q1 FY25: $4.1 billion TCV with 35 large deals
- Q2 FY25: $4.5 billion TCV with 42 large deals
- Q3 FY25: $4.8 billion TCV with 38 large deals
- Q4 FY25: $4.3 billion TCV with 41 large deals

**Client Base Growth:**
- $100M+ clients: Increased from 45 to 51 clients (13.3% growth)
- $50M+ clients: Grew from 143 to 156 clients (9.1% growth)
- $10M+ clients: Expanded from 487 to 512 clients (5.1% growth)

**Strategic Deal Wins:**
Notable wins included multi-year transformation partnerships with leading financial institutions in North America, cloud migration deals with European manufacturers, and data & analytics engagements with retail clients.

**Sector-wise Performance:**
Financial Services led with 32% of large deal TCV, followed by Manufacturing (24%), Retail (18%), and Communications (15%). The remaining 11% came from other sectors including Energy & Utilities and Hi-Tech.

**Deal Composition:**
Approximately 61% of TCV came from cost optimization and operational efficiency programs, while 39% was driven by digital transformation and growth initiatives. This mix indicates clients are balancing efficiency needs with innovation investments.

**Pipeline Strength:**
Management reported a robust pipeline heading into FY26, with increasing client conversations around AI, cloud, and data modernization programs, positioning the company well for sustained growth.''',
        'citations': [
            {'source': 'infosys-ar-25.pdf', 'page': 12, 'section': 'Business Highlights'},
            {'source': 'ifrs-usd-press-release_q4.pdf', 'page': 3, 'section': 'Deal Wins'},
            {'source': 'investor-sheet.xls', 'page': None, 'section': 'Client Metrics'},
        ],
        'metadata': {
            'processing_time_ms': 4156,
            'model': 'gemini-2.5-flash',
            'chunks_retrieved': 7,
        }
    },
]

# Excel data samples
EXCEL_DATA = [
    {
        'query': 'Compare quarterly revenue and growth rates for FY25',
        'data': {
            'rows': [
                {'Quarter': 'Q1 FY25', 'Revenue ($M)': 4710, 'YoY Growth (%)': 3.6, 'QoQ Growth (%)': 0.7, 'Operating Margin (%)': 21.1},
                {'Quarter': 'Q2 FY25', 'Revenue ($M)': 4894, 'YoY Growth (%)': 4.2, 'QoQ Growth (%)': 3.9, 'Operating Margin (%)': 21.5},
                {'Quarter': 'Q3 FY25', 'Revenue ($M)': 5129, 'YoY Growth (%)': 5.1, 'QoQ Growth (%)': 4.8, 'Operating Margin (%)': 21.7},
                {'Quarter': 'Q4 FY25', 'Revenue ($M)': 5167, 'YoY Growth (%)': 4.9, 'QoQ Growth (%)': 0.7, 'Operating Margin (%)': 21.4},
                {'Quarter': 'FY25 Total', 'Revenue ($M)': 19900, 'YoY Growth (%)': 4.5, 'QoQ Growth (%)': '-', 'Operating Margin (%)': 21.4},
            ]
        },
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'Infosys FY25 Quarterly Press Releases',
            'processing_time_ms': 1842,
        }
    },
    {
        'query': 'Breakdown of revenue by industry vertical in FY25',
        'data': {
            'rows': [
                {'Vertical': 'Financial Services', 'Revenue ($M)': 7562, 'Share (%)': 38.0, 'YoY Growth (%)': 3.8},
                {'Vertical': 'Manufacturing', 'Revenue ($M)': 3582, 'Share (%)': 18.0, 'YoY Growth (%)': 6.2},
                {'Vertical': 'Retail', 'Revenue ($M)': 2985, 'Share (%)': 15.0, 'YoY Growth (%)': 4.1},
                {'Vertical': 'Communications', 'Revenue ($M)': 2587, 'Share (%)': 13.0, 'YoY Growth (%)': 2.9},
                {'Vertical': 'Energy & Utilities', 'Revenue ($M)': 1592, 'Share (%)': 8.0, 'YoY Growth (%)': 5.7},
                {'Vertical': 'Hi-Tech', 'Revenue ($M)': 1194, 'Share (%)': 6.0, 'YoY Growth (%)': 3.2},
                {'Vertical': 'Others', 'Revenue ($M)': 398, 'Share (%)': 2.0, 'YoY Growth (%)': 7.5},
            ]
        },
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'Infosys FY25 Annual Report',
            'processing_time_ms': 2134,
        }
    },
    {
        'query': 'Employee headcount and attrition trends FY25',
        'data': {
            'rows': [
                {'Quarter': 'Q1 FY25', 'Total Employees': 317240, 'Net Addition': -4576, 'LTM Attrition (%)': 12.6, 'Utilization (%)': 81.8},
                {'Quarter': 'Q2 FY25', 'Total Employees': 322980, 'Net Addition': 5740, 'LTM Attrition (%)': 11.8, 'Utilization (%)': 82.3},
                {'Quarter': 'Q3 FY25', 'Total Employees': 328028, 'Net Addition': 5048, 'LTM Attrition (%)': 11.2, 'Utilization (%)': 82.7},
                {'Quarter': 'Q4 FY25', 'Total Employees': 335186, 'Net Addition': 7158, 'LTM Attrition (%)': 10.7, 'Utilization (%)': 82.5},
            ]
        },
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'Infosys FY25 Quarterly Fact Sheets',
            'processing_time_ms': 1687,
        }
    },
]


def generate_pdf(sample, output_path):
    """Generate PDF report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    styles = getSampleStyleSheet()

    # Add custom styles
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1a365d"),
        spaceAfter=30,
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#4a5568"),
        spaceAfter=20,
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2d3748"),
        spaceBefore=20,
        spaceAfter=12,
    ))

    story = []

    # Header
    story.append(Paragraph("Financial Analysis Report", styles["ReportTitle"]))
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    story.append(Paragraph(f"Generated on {timestamp}", styles["ReportSubtitle"]))
    story.append(Spacer(1, 0.3 * inch))

    # Query
    story.append(Paragraph("Query", styles["SectionHeader"]))
    story.append(Paragraph(sample['query'], styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Analysis
    story.append(Paragraph("Analysis", styles["SectionHeader"]))
    paragraphs = sample['response'].split("\n\n")
    for para in paragraphs:
        if para.strip():
            if para.strip().startswith("**") and para.strip().endswith("**"):
                header_text = para.strip().strip("*")
                story.append(Paragraph(header_text, styles["SectionHeader"]))
            else:
                para_clean = para.replace("**", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(para_clean, styles["Normal"]))
                story.append(Spacer(1, 0.15 * inch))

    # Citations
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Sources", styles["SectionHeader"]))

    table_data = [["#", "Document", "Details"]]
    for i, citation in enumerate(sample['citations'], 1):
        details = []
        if citation['section']:
            details.append(f"Section: {citation['section']}")
        if citation['page']:
            details.append(f"Page: {citation['page']}")
        details_text = ", ".join(details) if details else "N/A"
        table_data.append([str(i), citation['source'], details_text])

    table = Table(table_data, colWidths=[0.5*inch, 3*inch, 3*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4299e1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(table)

    # Footer
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("_" * 80, styles["Normal"]))
    meta_text = f"Processing Time: {sample['metadata']['processing_time_ms']:.0f}ms | "
    meta_text += f"Model: {sample['metadata']['model']} | "
    meta_text += f"Sources: {sample['metadata']['chunks_retrieved']}"
    story.append(Paragraph(meta_text, styles["Normal"]))
    story.append(Paragraph("<i>Generated by AI Financial Analyst</i>", styles["Normal"]))

    doc.build(story)

    # Save to file
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())

    print(f"[OK] Generated: {output_path}")


def generate_excel(sample, output_path):
    """Generate Excel report"""
    wb = Workbook()
    wb.remove(wb.active)

    # Summary sheet
    ws_summary = wb.create_sheet("Summary", 0)
    ws_summary.append(["Financial Analysis Report"])
    ws_summary["A1"].font = Font(size=16, bold=True)
    ws_summary.append([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ws_summary.append([])
    ws_summary.append(["Query:"])
    ws_summary["A4"].font = Font(bold=True)
    ws_summary.append([sample['query']])
    ws_summary.merge_cells("A5:D5")

    # Data sheet
    ws_data = wb.create_sheet("Data", 1)
    if 'rows' in sample['data']:
        rows = sample['data']['rows']
        if rows and isinstance(rows[0], dict):
            headers = list(rows[0].keys())
            ws_data.append(headers)
            for row in rows:
                ws_data.append([row.get(h, "") for h in headers])

            # Style header
            for col in range(1, len(headers) + 1):
                cell = ws_data.cell(row=1, column=col)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="4472C4")
                cell.alignment = Alignment(horizontal="center", vertical="center")

    # Auto-size columns
    for ws in [ws_summary, ws_data]:
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    # Metadata sheet
    ws_meta = wb.create_sheet("Metadata", 2)
    ws_meta.append(["Report Metadata"])
    ws_meta["A1"].font = Font(size=14, bold=True)
    ws_meta.append([])
    for key, value in sample['metadata'].items():
        ws_meta.append([key, str(value)])

    wb.save(output_path)
    print(f"[OK] Generated: {output_path}")


def main():
    output_dir = Path("outputs")
    pdf_dir = output_dir / "reports"
    excel_dir = output_dir / "excel"

    pdf_dir.mkdir(parents=True, exist_ok=True)
    excel_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating 6 sample outputs (3 PDF + 3 Excel)...\n")

    # Generate 3 PDFs
    for i, sample in enumerate(SAMPLES, 1):
        output_file = pdf_dir / f"financial_analysis_q{i}_fy25.pdf"
        generate_pdf(sample, output_file)

    # Generate 3 Excel files
    for i, sample in enumerate(EXCEL_DATA, 1):
        output_file = excel_dir / f"financial_data_analysis_{i}.xlsx"
        generate_excel(sample, output_file)

    print(f"\n[SUCCESS] All 6 sample outputs generated successfully!")
    print(f"\nPDF Reports: {pdf_dir}")
    print(f"Excel Reports: {excel_dir}")


if __name__ == '__main__':
    main()
