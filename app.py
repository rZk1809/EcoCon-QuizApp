# app.py (Reverted to simple 'testuser' logic, loads MCQs from JSON)
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from database import init_app, db
from models import User, QuizAttempt, AnswerLog # Assumes basic User model WITHOUT password
import os
import json
import random
from datetime import datetime

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'instance', 'quiz.db')
PARSED_DATA_DIR = os.path.join(BASE_DIR, "data") # Directory with week_X_questions.json
TOTAL_WEEKS = 12
QUESTIONS_PER_QUIZ = 10

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key_please_change')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
init_app(app)

# --- Helper to Load Questions ---
def load_questions_for_week(week_number):
    """Loads parsed questions from the JSON file for the specified week."""
    json_path = os.path.join(PARSED_DATA_DIR, f"week_{week_number}_questions.json")
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found for week {week_number} at {json_path}")
        return None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        # Sort questions by number just in case they aren't saved in order
        questions.sort(key=lambda x: x.get('question_number', float('inf')))
        return questions
    except Exception as e:
        print(f"Error loading or parsing JSON for week {week_number}: {e}")
        return None

# --- User Handling (Simple 'testuser' logic - Corrected Version) ---
@app.before_request
def before_request():
    # Simulates a single user 'testuser' using session
    if 'user_id' not in session:
        user = User.query.filter_by(username='testuser').first()
        if not user:
            print("Creating test user...")
            # Ensure context for DB operations if running outside request context initially
            # with app.app_context(): # Usually not needed if run within app start
            user = User(username='testuser')
            # IMPORTANT: If your User model now requires password_hash,
            # you MUST set a dummy password here before committing.
            # Example: user.set_password("dummy_password") # If you added set_password
            db.session.add(user)
            db.session.commit()
            print(f"Test user created.")
            # Re-fetch after commit is safest
            user = User.query.filter_by(username='testuser').first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            # print(f"User {user.username} (ID: {user.id}) set in session.") # Optional debug
        else:
             print("Error: Could not find or create test user in before_request.")
             # Handle error if user still not found/created
             flash("Error setting up user session.", "error")


# --- Routes ---
@app.route('/')
def index():
    available_weeks = []
    for i in range(1, TOTAL_WEEKS + 1):
        if os.path.exists(os.path.join(PARSED_DATA_DIR, f"week_{i}_questions.json")):
             available_weeks.append(i)

    # Pass necessary info, user info comes from session implicitly now
    return render_template('index.html', total_weeks=TOTAL_WEEKS, available_weeks=available_weeks)


@app.route('/quiz/<int:week_number>')
def quiz_page(week_number):
    # Basic validation
    if not (1 <= week_number <= TOTAL_WEEKS):
        flash("Invalid week number.", "error")
        return redirect(url_for('index'))

    # Check question availability
    questions = load_questions_for_week(week_number)
    if questions is None:
        flash(f"Could not load questions for Week {week_number}.", "error")
        return redirect(url_for('index'))
    if len(questions) < QUESTIONS_PER_QUIZ:
        flash(f"Not enough questions available for Week {week_number}.", "warning")
        return redirect(url_for('index'))

    return render_template('quiz.html', week_number=week_number)


@app.route('/progress')
def progress_page():
     # This version relies on the 'testuser' being set by before_request
     username = session.get('username', 'Test User') # Provide default if session missing
     return render_template('progress.html', username=username)


# --- API Endpoints ---
@app.route('/api/quiz/<int:week_number>', methods=['GET'])
def get_quiz_questions(week_number):
    # Get user_id from session for user-specific session key
    user_id = session.get('user_id', 'testuser') # Default to 'testuser' if somehow missing

    if not (1 <= week_number <= TOTAL_WEEKS):
        return jsonify({"error": "Invalid week number"}), 400

    all_week_questions = load_questions_for_week(week_number)

    if all_week_questions is None: return jsonify({"error": f"Could not load questions file for week {week_number}."}), 500
    if len(all_week_questions) < QUESTIONS_PER_QUIZ: return jsonify({"error": f"Not enough questions available."}), 500

    try: selected_mcqs = random.sample(all_week_questions, QUESTIONS_PER_QUIZ)
    except ValueError: return jsonify({"error": "Sampling error."}), 500

    # Store questions in session (key can be simpler now if only one 'user')
    session_key = f'quiz_week_{week_number}_questions'
    session[session_key] = selected_mcqs

    frontend_mcqs = []
    for i, mcq in enumerate(selected_mcqs):
         frontend_mcqs.append({
            "id": f"q_{i}",
            "question": mcq.get("question", "N/A"),
            "options": mcq.get("options", []) })
    return jsonify(frontend_mcqs)


@app.route('/api/submit', methods=['POST'])
def submit_quiz():
    user_id = session.get('user_id') # Get the simulated user ID

    data = request.get_json()
    if not data: return jsonify({"error": "No data received"}), 400

    week_number = data.get('week_number')
    answers = data.get('answers')

    if week_number is None or answers is None or not isinstance(answers, dict):
        return jsonify({"error": "Missing or invalid data"}), 400

    # Use the simpler session key
    questions_key = f'quiz_week_{week_number}_questions'
    original_mcqs_with_answers = session.get(questions_key)

    if not original_mcqs_with_answers: return jsonify({"error": "Quiz data/session expired"}), 400
    if len(answers) != len(original_mcqs_with_answers): return jsonify({"error": "Answer count mismatch"}), 400

    score = 0
    total_questions = len(original_mcqs_with_answers)
    results_log = []

    # --- Grading Logic (same as before) ---
    for i, mcq in enumerate(original_mcqs_with_answers):
        question_id = f"q_{i}"
        selected_index = answers.get(question_id)
        is_correct = False
        valid_selection = False
        correct_index = -1
        if selected_index is not None:
             try: selected_index = int(selected_index); valid_selection = True
             except (ValueError, TypeError): selected_index = None
        options = mcq.get('options', [])
        correct_text = mcq.get('correct_answer_text')
        if correct_text and isinstance(options, list) and options:
            try: correct_index = options.index(correct_text)
            except ValueError: correct_index = -1
        if valid_selection and correct_index != -1 and selected_index == correct_index:
            is_correct = True; score += 1
        results_log.append({
            "question_text": mcq.get("question", "N/A"), "options_text": json.dumps(options),
            "selected_option_index": selected_index, "correct_option_index": correct_index,
            "is_correct": is_correct })
    # --- End Grading Logic ---

    # --- Save to Database ---
    save_message = ""
    if user_id: # Check if user_id was actually set in session
        try:
            attempt = QuizAttempt(
                user_id=user_id, week_number=week_number, score=score,
                total_questions=total_questions, timestamp=datetime.utcnow() )
            db.session.add(attempt)
            db.session.flush()
            for log_data in results_log:
                answer = AnswerLog(attempt_id=attempt.id, **log_data)
                db.session.add(answer)
            db.session.commit()
            save_message = "(Results saved)"
            print(f"Attempt saved for user {user_id}, week {week_number}.")
        except Exception as e:
             db.session.rollback()
             print(f"Error saving attempt to database: {e}")
             save_message = "(Error saving results)"
    else:
         save_message = "(Results not saved - no user session)"
         print("Warning: User not in session, attempt not saved.")
    # --- End Save DB ---

    session.pop(questions_key, None)

    return jsonify({"message": f"Quiz submitted successfully! {save_message}", "score": score, "total_questions": total_questions})


@app.route('/api/progress', methods=['GET'])
def get_progress():
    user_id = session.get('user_id') # Get the simulated user ID
    if not user_id:
         # Return empty list if no user session (e.g., after clearing cookies)
         return jsonify([])

    try:
        attempts = QuizAttempt.query.filter_by(user_id=user_id).order_by(QuizAttempt.timestamp.desc()).all()
        progress_data = [{
            "attempt_id": attempt.id, "week": attempt.week_number, "score": attempt.score,
            "total": attempt.total_questions,
            "percentage": round((attempt.score / attempt.total_questions) * 100) if attempt.total_questions > 0 else 0,
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
        try:
            os.makedirs(instance_path)
            print(f"Created instance folder at: {instance_path}")
        except OSError as e:
             print(f"Error creating instance folder: {e}")
    app.run(debug=True)