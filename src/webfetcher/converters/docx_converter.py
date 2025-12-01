"""
Convert DOCX documents to Markdown.
"""
import os
from pathlib import Path
from typing import Optional

try:
    import docx
    from docx.document import Document as _Document
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.table import _Cell, Table
    from docx.text.paragraph import Paragraph
except ImportError:
    docx = None

def convert_docx_to_markdown(input_path: str) -> str:
    """
    Convert a .docx file to Markdown string.
    
    Args:
        input_path: Path to the .docx file.
        
    Returns:
        str: The converted Markdown content.
        
    Raises:
        ImportError: If python-docx is not installed.
        FileNotFoundError: If input file doesn't exist.
    """
    if docx is None:
        raise ImportError("python-docx is not installed. Please install it via 'pip install python-docx'.")
        
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")
        
    document = docx.Document(input_path)
    md_lines = []
    
    # Helper to process paragraph content with formatting
    def process_paragraph(paragraph) -> str:
        text = ""
        for run in paragraph.runs:
            run_text = run.text
            if not run_text:
                continue
                
            # Apply formatting
            if run.bold:
                run_text = f"**{run_text}**"
            if run.italic:
                run_text = f"*{run_text}*"
                
            text += run_text
        return text.strip()

    # Iterate through document elements (paragraphs and tables) in order
    # Note: python-docx main iteration is typically just paragraphs or tables separately
    # To get them in order, we need to iterate over body elements
    
    # Simple version: Iterate paragraphs
    # Enhanced version (TODO): Use element tree to interleave tables
    
    for para in document.paragraphs:
        text = process_paragraph(para)
        if not text:
            continue
            
        style_name = para.style.name.lower()
        
        if 'heading 1' in style_name:
            md_lines.append(f"# {text}")
        elif 'heading 2' in style_name:
            md_lines.append(f"## {text}")
        elif 'heading 3' in style_name:
            md_lines.append(f"### {text}")
        elif 'heading 4' in style_name:
            md_lines.append(f"#### {text}")
        elif 'list bullet' in style_name:
            md_lines.append(f"- {text}")
        elif 'list number' in style_name:
            # Ideally we'd track numbering, but '1.' is a safe generic fallback
            md_lines.append(f"1. {text}")
        elif 'quote' in style_name:
            md_lines.append(f"> {text}")
        else:
            # Standard paragraph
            md_lines.append(text)
            
        # Add spacing
        md_lines.append("")
        
    return "\n".join(md_lines)
