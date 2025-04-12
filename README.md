# EcoCon QuizApp - Conservation Economics Quiz Website

## Project Overview

This project provides a web application built with Flask for students to take weekly multiple-choice quizzes based on the content of the "Conservation Economics" course ([cite: 11966]). The application parses questions from pre-generated weekly MCQ PDF files, stores them in JSON format, and serves 10 random questions per week to the user via a web interface. It uses a simple SQLite database to track quiz attempts and progress for a default user.

**Workflow:**

1.  **MCQ PDFs:** Assumes 12 PDF files (`mcq_pdfs/week_1_mcqs.pdf`, etc.) containing the questions for each week have been generated.
2.  **Preprocessing:** A script (`preprocess_mcqs.py`) parses these PDFs, extracts structured MCQ data (question, options, correct answer), filters out placeholders, and saves the data into JSON files (`data/week_X_questions.json`). **This step must be run once before starting the web app.**
3.  **Web Application:** The Flask application (`app.py`) serves the website. When a user selects a week, it loads the corresponding JSON data, randomly selects 10 questions, displays the quiz, grades the submission, and saves the attempt.

**Core Technologies:**

* **Backend:** Python, Flask, Flask-SQLAlchemy
* **Frontend:** HTML (Jinja2 Templates), CSS, JavaScript
* **PDF Parsing:** PyMuPDF (`fitz`)
* **Database:** SQLite
* **Environment:** Python Virtual Environment (e.g., `venv`, `rag_env`)
* **Configuration:** `python-dotenv`


## Setup and Execution

**Prerequisites:**

* Python 3.x installed.
* The 12 generated `week_X_mcqs.pdf` files must be placed inside the `mcq_pdfs/` directory within your project root (`basic/`).
* Your environment file (`t.env` or rename to `.env`) present in the root directory (needed mainly if other scripts use API keys, but good practice).

**Steps:**

1.  **Navigate to Project Directory:**
    Open your terminal or command prompt and change to your project's root directory.
    ```bash
    cd /path/to/your/basic
    ```

2.  **Create & Activate Virtual Environment (Recommended):**
    ```bash
    # Create (only once)
    python -m venv venv
    # Activate (Windows):
    .\venv\Scripts\activate
    # Activate (Linux/macOS):
    source venv/bin/activate
    ```
    *(Replace `venv` with `rag_env` if that's your chosen name)*

3.  **Install Dependencies:**
    Make sure your virtual environment is active.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Preprocess MCQ PDFs (Run This Once):**
    This crucial step parses the MCQ PDFs into JSON files used by the web app.
    ```bash
    python preprocess_mcqs.py
    ```
    * This script reads from `mcq_pdfs/` and writes to `data/`.
    * Check the terminal output for any errors (e.g., "PDF not found", "does not have exactly 4 options", "does not have a '(Correct)' marker"). Ensure you have 12 `.json` files in the `data/` folder afterwards. Resolve any parsing issues by correcting the `mcq_pdfs` or the `mcq_parser.py` script if needed, then rerun preprocessing.

5.  **Run the Flask Web Application:**
    Make sure your virtual environment is active.
    ```bash
    python app.py
    ```
    * The first time you run this, it will create the `instance/` folder (if it doesn't exist) and the `instance/quiz.db` database file.
    * The server will start, usually on `http://127.0.0.1:5000`. Note the URL provided in the terminal.

6.  **Access the Website:**
    Open your web browser and navigate to the URL shown in the terminal (e.g., `http://127.0.0.1:5000`).

## Functionality

* The homepage (`/`) displays links to quizzes for weeks 1-12 (links appear only if the corresponding `week_X_questions.json` file exists in `data/`).
* Clicking a week link navigates to the quiz page for that week.
* The quiz page loads 10 random, unique questions for the selected week, numbered sequentially 1-10.
* Users select answers and click "Submit Answers".
* The answers are checked, and the results page displays the score (e.g., "Your score: 7 / 10").
* All quiz attempts are automatically saved under a default 'testuser'.
* The "View My Progress" link navigates to a page showing the history of attempts for 'testuser'.

## Notes

* **User System:** This version uses a simplified system that automatically logs in or creates a single user named 'testuser'. All progress is tracked against this user.
* **Database:** Uses SQLite, which is suitable for development but may need changing (e.g., to PostgreSQL via Cloud SQL) for online deployment with multiple users.
* **MCQ Quality:** The quality of the quizzes depends entirely on the questions contained within your `mcq_pdfs/` files and how well they were parsed by `preprocess_mcqs.py`.
* **Deployment:** This setup runs locally. For online hosting accessible to others, you would need to deploy it to a platform like PythonAnywhere, Render, Google Cloud Run, etc., which involves additional steps (like configuring a production WSGI server like Gunicorn and likely migrating the database).


