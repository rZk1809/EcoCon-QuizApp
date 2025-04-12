# app.py (Complete - Including Notes Route)
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, g, send_from_directory # Added send_from_directory
from database import init_app, db
from models import User, QuizAttempt, AnswerLog # Assuming User model WITHOUT password hash/methods now
import os
import json
import random
from datetime import datetime
# Removed werkzeug imports if not using auth
from functools import wraps # Still needed if keeping login_required temporarily

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'instance', 'quiz.db')
PARSED_DATA_DIR = os.path.join(BASE_DIR, "data")
# --- NEW: Path to the original weekly PDFs ---
WEEKLY_NOTES_DIR = os.path.join(BASE_DIR, 'weekly_pdfs') # Assumes 'weekly_pdfs' folder exists
# --- End New ---
TOTAL_WEEKS = 12
QUESTIONS_PER_QUIZ = 10

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key_please_change')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# --- NEW: Store notes dir in app config ---
app.config['WEEKLY_NOTES_DIR'] = WEEKLY_NOTES_DIR
# --- End New ---


# Initialize Database
init_app(app)

# --- Helper to Load Questions ---
def load_questions_for_week(week_number):
    json_path = os.path.join(PARSED_DATA_DIR, f"week_{week_number}_questions.json")
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found for week {week_number} at {json_path}")
        return None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        questions.sort(key=lambda x: x.get('question_number', float('inf')))
        return questions
    except Exception as e:
        print(f"Error loading or parsing JSON for week {week_number}: {e}")
        return None

# --- Authentication Logic / User Handling ---

# Revert back to simple 'testuser' logic as requested
@app.before_request
def before_request():
    if 'user_id' not in session:
        user = User.query.filter_by(username='testuser').first()
        if not user:
            # Check if models.py still requires password or was reverted
            user = User(username='testuser')
            # If User requires password, uncomment and set a dummy one:
            # from werkzeug.security import generate_password_hash
            # user.password_hash = generate_password_hash("testpassword")
            try:
                 with app.app_context(): # Ensure context if needed
                      db.session.add(user)
                      db.session.commit()
                      print(f"Test user created.")
                      user = User.query.filter_by(username='testuser').first() # Re-fetch
            except Exception as e:
                 db.session.rollback()
                 print(f"Error creating test user: {e}")
                 user = None # Ensure user is None if creation failed

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
        else:
             print("Error: Could not find or create test user in before_request.")
             # flash("Error setting up user session.", "error") # Careful with flash here


# --- Routes ---
@app.route('/')
def index():
    available_weeks = []
    for i in range(1, TOTAL_WEEKS + 1):
        if os.path.exists(os.path.join(PARSED_DATA_DIR, f"week_{i}_questions.json")):
             available_weeks.append(i)
    # Pass username from session for the simple version
    return render_template('index.html', total_weeks=TOTAL_WEEKS, available_weeks=available_weeks)

# --- NEW ROUTE FOR VIEWING NOTES ---
@app.route('/notes/<int:week_number>')
def view_notes(week_number):
    # You might want to add @login_required back here if notes shouldn't be public
    if not (1 <= week_number <= TOTAL_WEEKS):
        flash("Invalid week number for notes.", "error")
        return redirect(url_for('index'))

    filename = f"week_{week_number}.pdf" # Assuming original weekly PDFs are named this way
    notes_directory = app.config['WEEKLY_NOTES_DIR']

    # Check if the weekly_pdfs directory and the specific file exist
    if not os.path.isdir(notes_directory) or \
       not os.path.exists(os.path.join(notes_directory, filename)):
           flash(f"Notes PDF not found for Week {week_number}. Ensure 'weekly_pdfs' folder exists and contains the file.", "error")
           return redirect(url_for('index'))

    try:
        # Serve the PDF file securely; as_attachment=False tries to display inline
        return send_from_directory(notes_directory, filename, as_attachment=False)
    except FileNotFoundError:
         flash(f"Notes PDF file could not be sent for Week {week_number}.", "error")
         return redirect(url_for('index'))
    except Exception as e:
         print(f"Error sending file {filename}: {e}")
         flash("An error occurred while retrieving the notes.", "error")
         return redirect(url_for('index'))
# --- END NEW ROUTE ---


@app.route('/quiz/<int:week_number>')
# Add @login_required back if needed
def quiz_page(week_number):
    if not (1 <= week_number <= TOTAL_WEEKS):
        flash("Invalid week number.", "error")
        return redirect(url_for('index'))

    questions = load_questions_for_week(week_number)
    if questions is None:
        flash(f"Could not load questions for Week {week_number}.", "error")
        return redirect(url_for('index'))
    if len(questions) < QUESTIONS_PER_QUIZ:
        flash(f"Not enough questions available for Week {week_number}.", "warning")
        return redirect(url_for('index'))

    return render_template('quiz.html', week_number=week_number)


@app.route('/progress')
# Add @login_required back if needed
def progress_page():
     username = session.get('username', 'Test User')
     return render_template('progress.html', username=username)


# --- API Endpoints ---
@app.route('/api/quiz/<int:week_number>', methods=['GET'])
# Add @login_required back if needed
def get_quiz_questions(week_number):
    # Use simple session key if reverted from multi-user auth
    session_key = f'quiz_week_{week_number}_questions'

    if not (1 <= week_number <= TOTAL_WEEKS): return jsonify({"error": "Invalid week number"}), 400
    all_week_questions = load_questions_for_week(week_number)
    if all_week_questions is None: return jsonify({"error": f"Could not load questions file."}), 500
    if len(all_week_questions) < QUESTIONS_PER_QUIZ: return jsonify({"error": f"Not enough questions available."}), 500
    try: selected_mcqs = random.sample(all_week_questions, QUESTIONS_PER_QUIZ)
    except ValueError: return jsonify({"error": "Sampling error."}), 500

    session[session_key] = selected_mcqs

    frontend_mcqs = []
    for i, mcq in enumerate(selected_mcqs):
         frontend_mcqs.append({
            "id": f"q_{i}", "question": mcq.get("question", "N/A"),
            "options": mcq.get("options", []) })
    return jsonify(frontend_mcqs)
@app.route('/api/submit', methods=['POST'])
# Add @login_required back if using authentication
def submit_quiz():
    # Get user_id if using authentication, otherwise handle testuser
    user_id = session.get('user_id') # Assuming simple testuser logic for now

    data = request.get_json()
    if not data: return jsonify({"error": "No data received"}), 400

    week_number = data.get('week_number')
    answers = data.get('answers') # Expected: { "q_0": 1, "q_1": 3, ... }

    if week_number is None or answers is None or not isinstance(answers, dict):
        return jsonify({"error": "Missing or invalid data"}), 400

    # Use the simpler session key for testuser logic
    questions_key = f'quiz_week_{week_number}_questions'
    original_mcqs_with_answers = session.get(questions_key)

    if not original_mcqs_with_answers: return jsonify({"error": "Quiz data/session expired"}), 400
    # Ensure number of answers matches questions served (using keys count)
    # We should ideally check if all question_ids match, but count is a basic check
    if len(answers) != len(original_mcqs_with_answers):
         return jsonify({"error": "Answer count mismatch."}), 400

    score = 0
    total_questions = len(original_mcqs_with_answers)
    results_log = [] # Will store detailed results for frontend

    for i, mcq in enumerate(original_mcqs_with_answers):
        question_id = f"q_{i}"
        selected_index = answers.get(question_id)
        is_correct = False
        valid_selection = False
        correct_index = -1

        # Validate selected_index
        if selected_index is not None:
             try: selected_index = int(selected_index); valid_selection = True
             except (ValueError, TypeError): selected_index = None

        options = mcq.get('options', [])
        correct_text = mcq.get('correct_answer_text')

        # Find correct index based on text stored during parsing
        if correct_text and isinstance(options, list) and options:
            try: correct_index = options.index(correct_text)
            except ValueError: correct_index = -1

        # Grade
        if valid_selection and correct_index != -1 and selected_index == correct_index:
            is_correct = True; score += 1

        # Add detailed info to results_log for frontend display AND database saving
        results_log.append({
            "question_id": question_id, # Include the temporary ID
            "question_text": mcq.get("question", "N/A"),
            "options": options, # Send the options list
            "selected_option_index": selected_index, # User's answer index (or None)
            "correct_option_index": correct_index, # Correct answer index (or -1)
            "is_correct": is_correct
        })

    # --- Save to Database (Only if user_id exists) ---
    db_save_error = None
    if user_id:
        try:
            attempt = QuizAttempt( user_id=user_id, week_number=week_number, score=score,
                total_questions=total_questions, timestamp=datetime.utcnow() )
            db.session.add(attempt); db.session.flush()
            for item in results_log: # Use detailed log for DB saving
                answer = AnswerLog(
                    attempt_id=attempt.id,
                    question_text=item["question_text"],
                    options_text=json.dumps(item["options"]), # Save options as JSON string
                    selected_option_index=item["selected_option_index"],
                    correct_option_index=item["correct_option_index"],
                    is_correct=item["is_correct"] )
                db.session.add(answer)
            db.session.commit();
            print(f"Attempt saved for user {user_id}, week {week_number}.")
        except Exception as e:
             db.session.rollback(); print(f"Error saving attempt: {e}");
             db_save_error = "Error saving results."
    else: print("Warning: User not in session, attempt not saved.")
    # --- End Save DB ---

    session.pop(questions_key, None) # Clear quiz data from session

    # --- Return detailed results to frontend ---
    return jsonify({
        "message": f"Quiz submitted! {db_save_error or '(Results not saved - no user session)' if not user_id else '(Results saved)'}",
        "score": score,
        "total_questions": total_questions,
        "results": results_log # Send the detailed log
    })

@app.route('/api/progress', methods=['GET'])
# Add @login_required back if needed
def get_progress():
    user_id = session.get('user_id')
    if not user_id: return jsonify([]) # Return empty if no user

    try:
        attempts = QuizAttempt.query.filter_by(user_id=user_id).order_by(QuizAttempt.timestamp.desc()).all()
        progress_data = [{ "attempt_id": attempt.id, "week": attempt.week_number, "score": attempt.score,
            "total": attempt.total_questions, "percentage": round((attempt.score / attempt.total_questions) * 100) if attempt.total_questions > 0 else 0,
            "timestamp": attempt.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        } for attempt in attempts]
        return jsonify(progress_data)
    except Exception as e:
        print(f"Error fetching progress: {e}")
        return jsonify({"error": "Could not retrieve progress data."}), 500

# --- Main Execution ---
if __name__ == '__main__':
    instance_path = os.path.join(BASE_DIR, 'instance')
    if not os.path.exists(instance_path):
        try: os.makedirs(instance_path); print(f"Created instance folder: {instance_path}")
        except OSError as e: print(f"Error creating instance folder: {e}")
    # Make sure the notes directory exists
    if not os.path.exists(app.config['WEEKLY_NOTES_DIR']):
         print(f"Warning: Notes directory '{app.config['WEEKLY_NOTES_DIR']}' not found. 'View Notes' links will likely fail.")
         # Optionally create it: os.makedirs(app.config['WEEKLY_NOTES_DIR'])
    app.run(debug=True)