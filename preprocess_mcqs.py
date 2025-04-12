import os
import json
from utils.mcq_parser import parse_mcq_pdf # Assuming mcq_parser.py is in utils folder

# --- Configuration ---
MCQ_PDF_DIR = 'mcq_pdfs' # Directory containing week_1_mcqs.pdf etc.
PARSED_DATA_DIR = 'data' # Directory to save parsed JSON question files
TOTAL_WEEKS = 12
# --- End Configuration ---

def run_mcq_preprocessing():
    if not os.path.exists(MCQ_PDF_DIR):
        print(f"Error: MCQ PDF directory '{MCQ_PDF_DIR}' not found.")
        return

    if not os.path.exists(PARSED_DATA_DIR):
        try:
            os.makedirs(PARSED_DATA_DIR)
            print(f"Created data directory: {PARSED_DATA_DIR}")
        except OSError as e:
            print(f"Error creating data directory '{PARSED_DATA_DIR}': {e}")
            return

    print("\n--- Starting MCQ PDF Parsing ---")
    all_successful = True
    for week in range(1, TOTAL_WEEKS + 1):
        mcq_pdf_path = os.path.join(MCQ_PDF_DIR, f"week_{week}_mcqs.pdf")
        print(f"Processing: {mcq_pdf_path}")

        parsed_mcqs = parse_mcq_pdf(mcq_pdf_path)

        if parsed_mcqs:
            json_output_path = os.path.join(PARSED_DATA_DIR, f"week_{week}_questions.json")
            try:
                # Ensure questions are sorted by original number before saving
                parsed_mcqs.sort(key=lambda x: x.get('question_number', float('inf')))
                with open(json_output_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_mcqs, f, indent=2, ensure_ascii=False)
                print(f" -> Successfully parsed {len(parsed_mcqs)} MCQs and saved to {json_output_path}")
            except Exception as e:
                print(f" -> Error saving JSON for Week {week}: {e}")
                all_successful = False
        else:
            print(f" -> Failed to parse MCQs for Week {week} or PDF not found/empty.")
            all_successful = False

    print("\n--- MCQ PDF Parsing Complete ---")
    if not all_successful:
        print("*** WARNING: Errors occurred during parsing. Some JSON files may be missing or incomplete. ***")

if __name__ == "__main__":
    run_mcq_preprocessing()
