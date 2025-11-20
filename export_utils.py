"""Export results to PDF and DOCX formats."""

from docx import Document
from docx.shared import Pt, RGBColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import uuid
from datetime import datetime


# Create directory for exports
EXPORT_DIR = Path("static/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def export_to_docx(original_text: str, results: list, result_type: str = "Paraphrased") -> str:
    """
    Export results to DOCX format.
    
    Args:
        original_text: The original input text
        results: List of results (paraphrases, translations, etc.)
        result_type: Type of result (e.g., "Paraphrased", "Translated")
    
    Returns:
        Relative path to the generated DOCX file
    """
    try:
        filename = f"{uuid.uuid4().hex}.docx"
        filepath = EXPORT_DIR / filename
        
        doc = Document()
        
        # Add title
        title = doc.add_heading(f'{result_type} Text Results', 0)
        
        # Add metadata
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph("")
        
        # Add original text
        doc.add_heading('Original Text:', level=1)
        doc.add_paragraph(original_text)
        doc.add_paragraph("")
        
        # Add results
        doc.add_heading(f'{result_type} Versions:', level=1)
        
        if isinstance(results, list):
            for idx, result in enumerate(results, 1):
                para = doc.add_paragraph()
                run = para.add_run(f"{idx}. {result}")
                run.font.size = Pt(11)
                doc.add_paragraph("")
        else:
            para = doc.add_paragraph(str(results))
            para.style.font.size = Pt(11)
        
        doc.save(str(filepath))
        
        return f"exports/{filename}"
    
    except Exception as e:
        raise RuntimeError(f"DOCX export failed: {str(e)}")


def export_to_pdf(original_text: str, results: list, result_type: str = "Paraphrased") -> str:
    """
    Export results to PDF format.
    
    Args:
        original_text: The original input text
        results: List of results (paraphrases, translations, etc.)
        result_type: Type of result (e.g., "Paraphrased", "Translated")
    
    Returns:
        Relative path to the generated PDF file
    """
    try:
        filename = f"{uuid.uuid4().hex}.pdf"
        filepath = EXPORT_DIR / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=RGBColor(0, 0, 128),
            spaceAfter=12
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=RGBColor(0, 0, 0),
            spaceAfter=6
        )
        
        # Add title
        story.append(Paragraph(f"{result_type} Text Results", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Add metadata
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Add original text
        story.append(Paragraph("Original Text:", heading_style))
        story.append(Paragraph(original_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Add results
        story.append(Paragraph(f"{result_type} Versions:", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        if isinstance(results, list):
            for idx, result in enumerate(results, 1):
                story.append(Paragraph(f"{idx}. {result}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph(str(results), styles['Normal']))
        
        doc.build(story)
        
        return f"exports/{filename}"
    
    except Exception as e:
        raise RuntimeError(f"PDF export failed: {str(e)}")


def cleanup_old_exports(max_age_hours: int = 24):
    """Remove export files older than max_age_hours."""
    import time
    current_time = time.time()
    
    for export_file in EXPORT_DIR.glob("*.*"):
        file_age = (current_time - export_file.stat().st_mtime) / 3600
        if file_age > max_age_hours:
            export_file.unlink()
