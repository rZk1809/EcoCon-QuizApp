import fitz  # PyMuPDF library
import re    # Regular expression library
import os

def find_week_pages_skip_toc(pdf_path, pages_to_skip=3):
    """
    Reads a PDF, skipping initial pages (like TOC), and finds the page
    numbers where 'Week X' headings appear in the main content.

    Args:
        pdf_path (str): The full path to the PDF file.
        pages_to_skip (int): The number of pages to skip from the beginning
                             (e.g., 3 to skip PDF pages 1, 2, 3).

    Returns:
        dict: A dictionary where keys are week numbers (int) and values are
              lists of page numbers (int, 1-based) where the heading was found.
              Returns an empty dictionary if the PDF cannot be opened or processed.
    """
    week_pages = {}
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at '{pdf_path}'")
        return week_pages

    try:
        doc = fitz.open(pdf_path)
        print(f"Successfully opened PDF: {pdf_path}. Processing {doc.page_count} pages...")

        # Regex to find "Week" followed by space(s) and number(s)
        # Case-insensitive search
        week_pattern = re.compile(r'Module\s+(\d+)', re.IGNORECASE)

        # Start searching *after* the pages to skip
        start_page_index = pages_to_skip
        if start_page_index >= doc.page_count:
             print(f"Error: pages_to_skip ({pages_to_skip}) is too high. PDF only has {doc.page_count} pages.")
             doc.close()
             return {}

        print(f"Skipping first {pages_to_skip} pages (TOC/Index). Starting search from page {start_page_index + 1}.")

        for page_num in range(start_page_index, doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")

            # Search for all occurrences of the pattern on the page
            matches = week_pattern.findall(text)

            for match in matches:
                try:
                    week_num = int(match)
                    if 1 <= week_num <= 12: # Assuming weeks 1 through 12
                        page_actual = page_num + 1 # Convert 0-based index to 1-based page number
                        if week_num not in week_pages:
                            week_pages[week_num] = []
                        # Add page only if not already listed for this week
                        if page_actual not in week_pages[week_num]:
                            week_pages[week_num].append(page_actual)
                            # Optional: Print only the first time a week is found after skipping TOC
                            # print(f"Found 'Week {week_num}' heading start on page {page_actual}")
                except ValueError:
                    # Ignore if the number part isn't a valid integer
                    continue

        doc.close()
        print("Finished processing PDF.")

        # Sort page numbers for each week
        for week_num in week_pages:
            week_pages[week_num].sort()

    except Exception as e:
        print(f"An error occurred while processing the PDF: {e}")
        if 'doc' in locals() and doc:
             doc.close() # Ensure document is closed even on error
        return {} # Return empty on error

    return week_pages

# --- How to use the function ---

# IMPORTANT: Replace this with the actual path to your PDF file
# pdf_file_path = '102104086 .pdf' # If it's in the same directory as the script
pdf_file_path = '102104086 .pdf' # Use the full or relative path

# Set how many initial pages to skip (usually Title, Index pages)
# PDF Page 1 = index 0, Page 2 = index 1, Page 3 = index 2.
# To skip pages 1, 2, 3, set pages_to_skip = 3.
PAGES_TO_SKIP_COUNT = 3

print(f"Attempting to find week pages in: {pdf_file_path}, skipping first {PAGES_TO_SKIP_COUNT} pages.")
found_pages = find_week_pages_skip_toc(pdf_file_path, pages_to_skip=PAGES_TO_SKIP_COUNT)

if found_pages:
    print("\n--- Summary (Skipping TOC Pages) ---")
    # Sort the output by week number
    for week_num in sorted(found_pages.keys()):
        # Usually, we are interested in the *first* page a week heading appears on
        first_page = found_pages[week_num][0] if found_pages[week_num] else 'Not found after TOC'
        print(f"Week {week_num}: First found on page {first_page}")
        # Optional: Print all pages found for that week
        # pages_str = ', '.join(map(str, found_pages[week_num]))
        # print(f"Week {week_num}: Found on page(s) {pages_str}")

else:
    print("\nNo week headings found after skipping TOC pages, or an error occurred.")
