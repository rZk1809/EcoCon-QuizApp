
import fitz  # PyMuPDF library
import os

# --- Configuration ---
# IMPORTANT: Replace with the correct path to YOUR PDF file
SOURCE_PDF_PATH = '102104086 .pdf'

# IMPORTANT: Set where you want the output weekly PDFs to be saved
OUTPUT_DIR = 'weekly_pdfs'

# Week start pages (1-based index from PDF index)
# We convert these to 0-based index for PyMuPDF later
WEEK_START_PAGES_1_BASED = {
    1: 4,
    2: 50,
    3: 97,
    4: 145,
    5: 188,
    6: 230,
    7: 272,
    8: 312,
    9: 356,
    10: 396,
    11: 438,
    12: 481
}
TOTAL_WEEKS = 12
# --- End Configuration ---

def split_pdf_by_week(pdf_path, week_starts, output_dir):
    """
    Splits a source PDF into multiple PDFs based on weekly page ranges.

    Args:
        pdf_path (str): Path to the source PDF.
        week_starts (dict): Dictionary mapping week number (int) to
                            1-based start page number (int).
        output_dir (str): Directory to save the output weekly PDFs.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: Source PDF not found at '{pdf_path}'")
        return

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error creating output directory '{output_dir}': {e}")
            return

    try:
        source_doc = fitz.open(pdf_path)
        total_pages_in_doc = source_doc.page_count
        print(f"Opened source PDF: {pdf_path} ({total_pages_in_doc} pages)")

        for week_num in range(1, TOTAL_WEEKS + 1):
            # Get 0-based start index for the current week
            start_page_0_based = week_starts.get(week_num) - 1

            # Determine 0-based end index
            if week_num < TOTAL_WEEKS:
                # End page is the page *before* the next week starts
                end_page_0_based = week_starts.get(week_num + 1) - 1 - 1 # -1 for next start, -1 for index before that
            else:
                # For the last week, go to the end of the document
                end_page_0_based = total_pages_in_doc - 1

            # Basic validation for page numbers
            if start_page_0_based < 0 or start_page_0_based >= total_pages_in_doc:
                 print(f"Warning: Invalid start page index {start_page_0_based} for Week {week_num}. Skipping.")
                 continue
            if end_page_0_based < start_page_0_based or end_page_0_based >= total_pages_in_doc:
                 print(f"Warning: Invalid end page index {end_page_0_based} (Start was {start_page_0_based}) for Week {week_num}. Adjusting to end of document if possible.")
                 # If end page seems wrong, maybe default to just the start page or end of doc?
                 # Let's adjust to document end if start page was valid.
                 if week_num == TOTAL_WEEKS:
                     end_page_0_based = total_pages_in_doc - 1
                 else: # If not last week, something is wrong with next week's start page, maybe just take start page?
                      print(f"   -> Issue likely with Week {week_num+1} start page. Processing only page {start_page_0_based+1} for Week {week_num}.")
                      end_page_0_based = start_page_0_based # Process just the start page noted

            # Ensure end_page doesn't exceed document bounds after adjustments
            end_page_0_based = min(end_page_0_based, total_pages_in_doc - 1)


            if end_page_0_based < start_page_0_based:
                 print(f"Error: Calculated start index {start_page_0_based} is after end index {end_page_0_based} for Week {week_num}. Skipping.")
                 continue


            print(f"Processing Week {week_num}: Pages {start_page_0_based + 1} to {end_page_0_based + 1}")

            # Create a new PDF for the current week
            output_pdf_path = os.path.join(output_dir, f"week_{week_num}.pdf")
            new_doc = fitz.open() # Create empty PDF

            # Insert the required pages from source_doc into new_doc
            # insert_pdf uses 0-based indices, `to_page` is inclusive.
            new_doc.insert_pdf(source_doc, from_page=start_page_0_based, to_page=end_page_0_based)

            # Save the new PDF
            new_doc.save(output_pdf_path)
            new_doc.close()
            print(f" -> Saved: {output_pdf_path}")

        source_doc.close()
        print("\nFinished splitting PDF.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if 'source_doc' in locals() and source_doc:
            source_doc.close()
        if 'new_doc' in locals() and new_doc:
            new_doc.close() # Ensure new doc is closed on error during save

# --- Run the splitter ---
if __name__ == "__main__":
    # Verify the source path and output directory again
    if not os.path.exists(SOURCE_PDF_PATH):
        print(f"CRITICAL ERROR: Source PDF path is incorrect or file does not exist.")
        print(f"Please edit the SOURCE_PDF_PATH variable in the script to the correct location.")
    else:
        split_pdf_by_week(SOURCE_PDF_PATH, WEEK_START_PAGES_1_BASED, OUTPUT_DIR)
