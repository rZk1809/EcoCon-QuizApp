import fitz # PyMuPDF
import re
import json
import os

def parse_mcq_pdf(pdf_path):
    """
    Parses an MCQ PDF to extract questions, options, and the correct answer.
    Skips questions that start with "Placeholder: Generation failed/incomplete".
    """
    if not os.path.exists(pdf_path):
        print(f"Error: MCQ PDF not found at '{pdf_path}'")
        return []

    mcqs = []
    current_mcq = None
    current_options = []
    placeholder_prefix = "Placeholder: Generation failed/incomplete"

    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text("text")
        doc.close()

        lines = full_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            q_match = re.match(r'^(\d+)\.\s*(.*)', line)
            if q_match:
                if current_mcq:
                    current_mcq['options'] = current_options
                    is_placeholder = current_mcq['question'].startswith(placeholder_prefix)
                    is_valid = True
                    if is_placeholder:
                         #print(f"Skipping placeholder question: {current_mcq.get('question_number','N/A')}")
                         is_valid = False
                    elif len(current_mcq['options']) != 4:
                         print(f"Warning: Question {current_mcq.get('question_number','N/A')} in {pdf_path} does not have exactly 4 options. Skipping.")
                         is_valid = False
                    elif current_mcq['correct_answer_text'] is None:
                         print(f"Warning: Question {current_mcq.get('question_number','N/A')} in {pdf_path} does not have a '(Correct)' marker. Skipping.")
                         is_valid = False
                    elif current_mcq['correct_answer_text'] not in current_mcq['options']:
                         print(f"Warning: Correct answer text for Q {current_mcq.get('question_number','N/A')} not found in options list. Skipping.")
                         is_valid = False

                    if is_valid:
                         mcqs.append(current_mcq)

                q_num = int(q_match.group(1))
                q_text = q_match.group(2).strip()
                current_mcq = {"question_number": q_num, "question": q_text, "options": [], "correct_answer_text": None}
                current_options = []
                continue

            if current_mcq:
                opt_match = re.match(r'^([A-D])\.\s*(.*)', line, re.IGNORECASE)
                if opt_match:
                    letter = opt_match.group(1).upper()
                    text = opt_match.group(2).strip()

                    if text.endswith("(Correct)"):
                        processed_text = re.sub(r'\s*\(Correct\)$', '', text, flags=re.IGNORECASE).strip()
                        if current_mcq['correct_answer_text'] is None:
                             current_mcq['correct_answer_text'] = processed_text
                        current_options.append(processed_text)
                    else:
                        current_options.append(text)

        if current_mcq:
            current_mcq['options'] = current_options
            is_placeholder = current_mcq['question'].startswith(placeholder_prefix)
            is_valid = True
            if is_placeholder:
                 #print(f"Skipping placeholder question: {current_mcq.get('question_number','N/A')}")
                 is_valid = False
            elif len(current_mcq['options']) != 4:
                 print(f"Warning: Final Question {current_mcq.get('question_number','N/A')} in {pdf_path} does not have exactly 4 options. Skipping.")
                 is_valid = False
            elif current_mcq['correct_answer_text'] is None:
                 print(f"Warning: Final Question {current_mcq.get('question_number','N/A')} in {pdf_path} does not have a '(Correct)' marker. Skipping.")
                 is_valid = False
            elif current_mcq['correct_answer_text'] not in current_mcq['options']:
                 print(f"Warning: Final correct answer text for Q {current_mcq.get('question_number','N/A')} not found in options list. Skipping.")
                 is_valid = False

            if is_valid:
                 mcqs.append(current_mcq)

    except Exception as e:
        print(f"Error parsing MCQ PDF {pdf_path}: {e}")
        if 'doc' in locals() and doc:
            doc.close()
        return []

    print(f"Parsed {len(mcqs)} valid (non-placeholder) MCQs from {pdf_path}")
    return mcqs
