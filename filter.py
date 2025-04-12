import os
import re
import fitz  # PyMuPDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Folders
INPUT_PDF_DIR = "mcq_pdfs"             # Where your original MCQ PDFs are located
OUTPUT_PDF_DIR = "filtered_mcq_pdfs"   # Where to output the cleaned PDFs

PLACEHOLDER_TEXT = "Placeholder: Generation failed/incomplete"  # Adjust if needed

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from the given PDF using PyMuPDF.
    Returns the entire text as a string.
    """
    try:
        doc = fitz.open(pdf_path)
        all_text = ""
        for page in doc:
            all_text += page.get_text("text") + "\n"
        doc.close()
        return all_text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def split_into_question_blocks(full_text):
    """
    Splits the text into separate question blocks.
    Uses a regex that matches lines like '1. ', '2. ', etc. as question starters.
    Returns a list of question-block strings.
    """
    # Split right before a line that starts with one or more digits, a dot, and a space:
    blocks = re.split(r'(?=\d+\.\s)', full_text)
    # Clean up whitespace and remove empty entries
    blocks = [b.strip() for b in blocks if b.strip()]
    return blocks

def filter_out_placeholders(blocks):
    """
    Removes any blocks that contain the known placeholder text.
    You can add additional criteria if needed.
    """
    valid = []
    for block in blocks:
        if PLACEHOLDER_TEXT in block:
            continue  # Skip faulty question
        valid.append(block)
    return valid

def renumber_questions(blocks):
    """
    Renumbers each question block sequentially from 1, 2, 3, ...
    to avoid gaps if placeholders were removed.
    
    Assumes the first line of each block starts with something like '8. Question text...'
    We'll replace the leading number with our new question number.
    """
    renumbered = []
    q_num = 1
    for block in blocks:
        lines = block.splitlines()
        if not lines:
            continue

        # On the first line, replace '^\d+\.\s' with 'q_num. '
        new_first = re.sub(r'^\d+\.\s*', f"{q_num}. ", lines[0])
        lines[0] = new_first
        new_block = "\n".join(lines)
        renumbered.append(new_block)
        q_num += 1
    return renumbered

def save_blocks_to_pdf(blocks, output_path, title="MCQs (Filtered)"):
    """
    Saves each block as a paragraph in a new PDF, with re-numbered questions.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Custom style for answer lines (indented), if needed
    option_style = ParagraphStyle(name='OptionStyle', parent=styles['Normal'], leftIndent=20)

    # Title
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 0.2 * inch))

    # Add each question block
    for block in blocks:
        # Replace newlines with <br/> for better formatting
        block_html = block.replace("\n", "<br/>")
        story.append(Paragraph(block_html, styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

    try:
        doc.build(story)
        print(f"Saved filtered PDF: {output_path}")
    except Exception as e:
        print(f"Error saving PDF {output_path}: {e}")

def process_pdf(input_pdf, output_pdf):
    """
    Orchestrates reading, splitting, filtering, re-numbering, and saving a single PDF.
    """
    print(f"Processing {input_pdf}...")
    text = extract_text_from_pdf(input_pdf)
    if not text:
        print("No text found, skipping.")
        return

    # 1) Split into question blocks
    blocks = split_into_question_blocks(text)
    print(f"Found {len(blocks)} total question blocks.")

    # 2) Filter out placeholders
    filtered = filter_out_placeholders(blocks)
    print(f"After filter: {len(filtered)} valid blocks remain.")

    # 3) Renumber so questions are sequential
    renumbered = renumber_questions(filtered)

    # 4) Save to PDF
    if renumbered:
        save_blocks_to_pdf(renumbered, output_pdf)
    else:
        print("No valid questions remain after filtering. Skipping output.")

if __name__ == "__main__":
    # Make sure output directory exists
    os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)

    # Process all PDFs in INPUT_PDF_DIR
    for filename in os.listdir(INPUT_PDF_DIR):
        if filename.lower().endswith(".pdf"):
            in_pdf = os.path.join(INPUT_PDF_DIR, filename)
            out_pdf = os.path.join(OUTPUT_PDF_DIR, filename.replace(".pdf", "_filtered.pdf"))
            process_pdf(in_pdf, out_pdf)

