import fitz
import re
import os
import json
from reportlab.lib.pagesizes import letter as PAGE_SIZE
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from file (adjust the filename if needed)
load_dotenv('t.env')  # Or '.env'
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

WEEKLY_PDF_DIR = 'weekly_pdfs'
MCQ_OUTPUT_DIR = 'mcq_pdfs'
TOTAL_WEEKS = 12
QUESTIONS_PER_WEEK = 100

def get_text_from_pdf(pdf_path):
    """
    Extract text from a PDF using PyMuPDF.
    Returns the full text with normalized whitespace, or None on error.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at '{pdf_path}'")
        return None
    try:
        doc = fitz.open(pdf_path)
        full_text = "".join(page.get_text("text") for page in doc)
        doc.close()
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        return full_text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None

def generate_mcqs_with_gemini(text_content, week_number, target_count=100):
    """
    Calls the Gemini API to generate MCQs based on the provided text.
    Returns a list of dictionaries representing MCQs.
    """
    if not GEMINI_API_KEY:
        print(f"Error: API Key missing for Week {week_number}. Cannot generate.")
        return [{
            "question": f"Error: API Key missing for Week {week_number}",
            "options": ["N/A"] * 4,
            "correct_option_letter": "A"
        }] * target_count

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return [{
            "question": f"Error: Could not configure API for Week {week_number}",
            "options": ["N/A"] * 4,
            "correct_option_letter": "A"
        }] * target_count

    # Truncate text if too long for the API call
    MAX_TEXT_LENGTH = 100000
    truncated_text = text_content[:MAX_TEXT_LENGTH]
    if len(text_content) > MAX_TEXT_LENGTH:
        print(f"Warning: Text content for Week {week_number} truncated to {MAX_TEXT_LENGTH} characters for API call.")

    prompt = f"""
    Based ONLY on the following text from Week {week_number} of a Conservation Economics course, generate exactly {target_count} unique multiple-choice questions (MCQs).

    For each MCQ, provide:
    1. The question text.
    2. A list of 4 options (A, B, C, D).
    3. One option must be the correct answer based *solely* on the provided text.
    4. The other 3 options must be plausible but incorrect distractors, also derived *only* from the context of the provided text for Week {week_number}. Do not introduce outside information.
    5. Indicate the correct option (e.g., by specifying the letter 'A', 'B', 'C', or 'D').

    Format the output STRICTLY as a valid JSON list of dictionaries, like this example:
    [
      {{
        "question": "What is the primary topic discussed?",
        "options": ["Option A text", "Option B text", "Correct Answer text", "Option D text"],
        "correct_option_letter": "C"
      }}
    ]

    Here is the text for Week {week_number}:
    --- START TEXT ---
    {truncated_text}
    --- END TEXT ---

    Generate {target_count} MCQs in the specified JSON format. Ensure the JSON is valid. Do not include any text before or after the JSON list itself.
    """

    mcqs_list = []
    print(f"--- Generating MCQs for Week {week_number} using Gemini API... ---")

    try:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        response = model.generate_content(prompt, safety_settings=safety_settings)
        cleaned_response_text = response.text.strip().lstrip('```json').rstrip('```').strip()
        mcqs_list = json.loads(cleaned_response_text)
        print(f"   -> Successfully received and parsed response for Week {week_number}.")
        if len(mcqs_list) < target_count:
            print(f"   -> Warning: Received only {len(mcqs_list)} MCQs, expected {target_count}.")

    except json.JSONDecodeError as json_err:
        print(f"   *** Error decoding JSON from API response for Week {week_number}: {json_err} ***")
        print(f"   Raw response text was: {getattr(response, 'text', 'N/A')[:500]}...")
        mcqs_list = []
    except ValueError as val_err:
        print(f"   *** API call blocked or failed for Week {week_number}. Error: {val_err} ***")
        mcqs_list = []
    except Exception as e:
        print(f"   *** Error calling Gemini API for Week {week_number}: {e} ***")
        mcqs_list = []

    # Ensure we have exactly target_count MCQs
    while len(mcqs_list) < target_count:
        mcqs_list.append({
            "question": f"Placeholder: Generation failed/incomplete for Week {week_number} - Q{len(mcqs_list) + 1}",
            "options": ["Failed A", "Failed B", "Failed C", "Failed D"],
            "correct_option_letter": "A"
        })

    return mcqs_list[:target_count]

def save_mcqs_to_pdf(mcqs, output_pdf_path):
    """
    Saves the provided MCQs to a PDF file using ReportLab.
    Returns True if successful, False otherwise.
    """
    success = False
    try:
        doc = SimpleDocTemplate(output_pdf_path, pagesize=PAGE_SIZE)
        styles = getSampleStyleSheet()
        story = []

        # Create a custom style for options with a left indent
        option_style = ParagraphStyle('OptionStyle', parent=styles['Normal'], leftIndent=20)

        week_num_title = mcqs[0].get('week_num', 'Unknown') if mcqs else 'Unknown'
        title = f"Week {week_num_title} MCQs"
        story.append(Paragraph(title, styles['h1']))
        story.append(Spacer(1, 0.2 * inch))

        q_num = 1
        option_labels = ['A', 'B', 'C', 'D']
        for mcq in mcqs:
            # Add question
            question_text = mcq.get('question', 'N/A')
            story.append(Paragraph(f"{q_num}. {question_text}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

            # Add options, each with the custom option style
            correct_letter = mcq.get('correct_option_letter', '').upper()
            options = mcq.get('options', [])
            if isinstance(options, list) and options:
                for i, option in enumerate(options):
                    if i < len(option_labels):
                        label = option_labels[i]
                        option_str = str(option) if option is not None else ""
                        option_text = f"{label}. {option_str}"
                        if label == correct_letter:
                            # Bold the correct answer in the option text
                            option_text = f"<b>{option_text} (Correct)</b>"
                        story.append(Paragraph(option_text, option_style))
                        story.append(Spacer(1, 0.05 * inch))
            else:
                story.append(Paragraph("(Options missing or invalid)", styles['Italic']))
                story.append(Spacer(1, 0.05 * inch))

            story.append(Spacer(1, 0.2 * inch))
            q_num += 1

        doc.build(story)
        success = True
    except Exception as e:
        print(f"Error saving PDF {output_pdf_path}: {e}")
        success = False
    return success

if __name__ == "__main__":
    if not os.path.exists(WEEKLY_PDF_DIR):
        print(f"Error: Input directory '{WEEKLY_PDF_DIR}' not found.")
    elif not GEMINI_API_KEY:
        print("Error: Cannot proceed without GEMINI_API_KEY set in .env or t.env file.")
    else:
        if not os.path.exists(MCQ_OUTPUT_DIR):
            try:
                os.makedirs(MCQ_OUTPUT_DIR)
                print(f"Created MCQ output directory: {MCQ_OUTPUT_DIR}")
            except OSError as e:
                print(f"Error creating MCQ output directory '{MCQ_OUTPUT_DIR}': {e}")
                exit()

        print("\nStarting MCQ Generation Process...")
        all_successful = True

        for week in range(1, TOTAL_WEEKS + 1):
            print(f"\nProcessing Week {week} PDF...")
            pdf_file = os.path.join(WEEKLY_PDF_DIR, f"week_{week}.pdf")
            week_text = get_text_from_pdf(pdf_file)

            if week_text:
                generated_mcqs = generate_mcqs_with_gemini(week_text, week, target_count=QUESTIONS_PER_WEEK)

                if generated_mcqs and not generated_mcqs[0]['question'].startswith("Error:"):
                    for mcq in generated_mcqs:
                        mcq['week_num'] = week

                    output_pdf = os.path.join(MCQ_OUTPUT_DIR, f"week_{week}_mcqs.pdf")
                    success = save_mcqs_to_pdf(generated_mcqs, output_pdf)
                    if success:
                        print(f" -> Successfully saved MCQs for Week {week} to {output_pdf}")
                    else:
                        print(f"   -> Failed to save PDF for Week {week} due to errors.")
                        all_successful = False
                else:
                    print(f"   -> No MCQs generated or an error occurred during generation for Week {week}.")
                    all_successful = False
            else:
                print(f"   -> Could not read text from {pdf_file}.")
                all_successful = False

        print("\nMCQ PDF generation process complete.")
        if not all_successful:
            print("*** WARNING: Errors occurred during the process. Some PDFs may not have been saved correctly. ***")
        print(f"*** Check '{MCQ_OUTPUT_DIR}' for output files. Review the generated MCQs for correctness. ***")

