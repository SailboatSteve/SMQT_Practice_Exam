#!/usr/bin/env python3
"""
SMQT Practice Test Application

A web application for practicing SMQT (Surveyor Minimum Qualifications Test) questions.
"""

import json
import os
import random
import sys
import webbrowser
import requests
import glob
from datetime import datetime
from typing import Dict, List, Optional, Set, Union
import signal
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import threading
import time
import shutil
from github import Github
from base64 import b64encode
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, flash, Response, jsonify, send_from_directory
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing-only')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching
app.config['GITHUB_TOKEN'] = os.getenv('GITHUB_TOKEN')
app.config['GITHUB_REPO'] = 'SailboatSteve/SMQT_Practice_Exam'
csrf = CSRFProtect(app)

# Add no-cache headers to all responses
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Constants
DEFAULT_NUM_QUESTIONS = 10
QUESTION_COUNT_OPTIONS = [10, 35, 70, 140]  # Available options for test length
REGULATIONS_FILE = 'regulations.json'
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', generate_password_hash('admin'))  # Default password: admin

def get_data_dir():
    """Get the user data directory for storing modifiable files."""
    app_data = os.getenv('APPDATA') or os.path.expanduser('~')
    data_dir = os.path.join(app_data, 'smqt_practice')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_user_data_dir():
    """Get the user data directory for storing modifiable files."""
    app_data = os.getenv('APPDATA') or os.path.expanduser('~')
    data_dir = os.path.join(app_data, 'smqt_practice')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_questions_file():
    """Get the path to the questions file, initializing from the bundled file if needed."""
    data_dir = get_user_data_dir()
    questions_file = os.path.join(data_dir, 'test_questions.json')
    
    # If questions file doesn't exist in user data dir, initialize it
    if not os.path.exists(questions_file):
        # Try to copy from the bundled file first
        bundled_questions = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_questions.json')
        if os.path.exists(bundled_questions):
            shutil.copy2(bundled_questions, questions_file)
        else:
            # If no bundled file, download from GitHub
            update_questions_from_github(questions_file)
            
    return questions_file

# Update the global QUESTIONS_FILE to use the user data directory
QUESTIONS_FILE = get_questions_file()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            print("Admin check failed - redirecting to login")  # Debug print
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('admin_login'))
        print("Admin check passed")  # Debug print
        return f(*args, **kwargs)
    return decorated_function

def save_questions(questions):
    """Save questions to the JSON file."""
    with open(QUESTIONS_FILE, 'w') as f:
        json.dump(questions, f, indent=2)

def load_regulations() -> Dict:
    """Load regulations mapping from the regulations file."""
    try:
        with open(REGULATIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading regulations: {e}")
        return {"categories": {}, "keywords": {}}

def load_questions() -> List[Dict]:
    """Load questions from the JSON file."""
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            questions = json.load(f)
            # Handle both formats: array of questions or object with questions array
            if isinstance(questions, list):
                return questions
            return questions.get('questions', [])
    except Exception as e:
        print(f"Error loading questions from {QUESTIONS_FILE}: {e}")
        return []

def get_question_by_id(question_id: int, questions_list: List[Dict]) -> Optional[Dict]:
    """Get a question by its index from the questions list."""
    try:
        return questions_list[question_id]
    except (IndexError, TypeError):
        return None

@app.context_processor
def inject_globals():
    """Inject global variables and functions into templates."""
    return {
        'now': datetime.utcnow(),
        'chr': chr  # Add chr function for letter generation
    }

@app.route('/')
def index():
    """Render the home page."""
    # Clear any existing test session
    session.clear()
    
    # Load questions to display count
    questions = load_questions()
    total_questions = len(questions)
    
    # Filter question count options based on available questions
    available_options = [n for n in QUESTION_COUNT_OPTIONS if n <= total_questions]
    if not available_options:
        available_options = [min(total_questions, DEFAULT_NUM_QUESTIONS)]
    
    return render_template(
        'index.html',
        total_questions=total_questions,
        question_count_options=available_options
    )


@app.route('/start', methods=['POST'])
def start_test():
    """Start a new test."""
    try:
        num_questions = int(request.form.get('num_questions', DEFAULT_NUM_QUESTIONS))
    except ValueError:
        num_questions = DEFAULT_NUM_QUESTIONS
    
    # Load and shuffle questions
    all_questions = load_questions()
    if not all_questions:
        flash('No questions available. Please check the questions file.', 'error')
        return redirect(url_for('index'))
    
    # Ensure we don't try to select more questions than available
    num_questions = min(num_questions, len(all_questions))
    
    # Select random question indices instead of full questions
    total_questions = len(all_questions)
    selected_indices = random.sample(range(total_questions), num_questions)
    
    # Store only indices in session
    session['question_indices'] = selected_indices
    session['current_question'] = 0
    session['answers'] = {}
    session['start_time'] = datetime.utcnow().isoformat()
    
    return redirect(url_for('question', question_id=0))


@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def question(question_id: int):
    """Display a question and process the answer."""
    if 'question_indices' not in session:
        return redirect(url_for('index'))
    
    indices = session['question_indices']
    if question_id >= len(indices):
        return redirect(url_for('results'))
    
    # Load all questions and get the current one by index
    all_questions = load_questions()
    current_question = get_question_by_id(indices[question_id], all_questions)
    if not current_question:
        flash('Error loading question', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get selected answers (handles multiple selections)
        selected = request.form.getlist('answer')
        
        # Store answer in session
        if selected:
            session['answers'] = dict(session.get('answers', {}))
            session['answers'][str(question_id)] = selected
            session.modified = True
        
        # Move to next question or results
        next_id = question_id + 1
        if next_id >= len(indices):
            return redirect(url_for('results'))
        return redirect(url_for('question', question_id=next_id))
    
    # Load regulations for reference
    regulations = load_regulations()
    
    return render_template(
        'question.html',
        question=current_question,
        question_id=question_id,
        total_questions=len(indices),
        regulations=regulations
    )


@app.route('/results')
def results():
    """Display test results."""
    if 'question_indices' not in session or 'answers' not in session:
        return redirect(url_for('index'))
    
    indices = session['question_indices']
    answers = session['answers']
    all_questions = load_questions()
    
    # Calculate results
    num_questions = len(indices)
    correct_count = 0
    question_results = []
    
    for i, q_index in enumerate(indices):
        question = get_question_by_id(q_index, all_questions)
        if not question:
            continue
            
        user_answers = set(answers.get(str(i), []))
        correct_answers = set(question['correct_answers'])
        
        is_correct = user_answers == correct_answers
        if is_correct:
            correct_count += 1
        
        question_results.append({
            'question': question['question'],
            'choices': question['choices'],
            'user_answers': sorted(list(user_answers)),
            'correct_answers': sorted(list(correct_answers)),
            'is_correct': is_correct,
            'explanation': question['explanation'],
            'regulations': question.get('regulations', [])
        })
    
    score = (correct_count / num_questions) * 100 if num_questions > 0 else 0
    
    start_time = datetime.fromisoformat(session['start_time'])
    end_time = datetime.utcnow()
    time_taken = end_time - start_time
    
    # Load regulations for reference
    regulations = load_regulations()
    
    return render_template(
        'results.html',
        score=score,
        correct_count=correct_count,
        total_questions=num_questions,
        time_taken=time_taken,
        question_results=question_results,
        regulations=regulations
    )


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        password = request.form.get('password')
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['is_admin'] = True
            return redirect(url_for('admin'))
        flash('Invalid password', 'error')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('is_admin', None)
    return redirect(url_for('index'))


@app.route('/admin')
@admin_required
def admin():
    """Admin page for managing questions."""
    questions = load_questions()
    regulations = load_regulations()
    return render_template('admin.html', questions=questions, regulations=regulations)


@app.route('/admin/question/<int:question_id>', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    """Edit a specific question."""
    questions = load_questions()
    if question_id >= len(questions):
        flash('Question not found', 'error')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        question = {
            'ksa': request.form.get('ksa'),
            'question': request.form.get('question_text'),
            'choices': request.form.getlist('choice'),
            'correct_answers': request.form.getlist('correct_answer'),
            'explanation': request.form.get('explanation'),
            'regulations': [
                {
                    'id': reg_id,
                    'section': section,
                    'title': title
                }
                for reg_id, section, title in zip(
                    request.form.getlist('regulation_id'),
                    request.form.getlist('regulation_section'),
                    request.form.getlist('regulation_title')
                )
            ]
        }
        
        # Update question
        questions[question_id] = question
        save_questions(questions)
        flash('Question updated successfully', 'success')
        return redirect(url_for('admin'))
    
    return render_template(
        'edit_question.html',
        question=questions[question_id],
        question_id=question_id,
        regulations=load_regulations()
    )


@app.route('/admin/question/<int:question_id>/data')
@admin_required
def get_question_data(question_id):
    """Get question data as JSON."""
    questions = load_questions()
    if question_id >= len(questions):
        return {'error': 'Question not found'}, 404
    return questions[question_id]


@app.route('/quit')
def quit_app():
    """Gracefully shutdown the Flask application and all related processes."""
    def shutdown():
        time.sleep(2)  # Give time for the goodbye page to load
        os.kill(os.getpid(), signal.SIGTERM)
    
    # Schedule the shutdown
    thread = threading.Thread(target=shutdown)
    thread.daemon = True
    thread.start()
    
    return render_template('goodbye.html')


@app.errorhandler(403)
def handle_csrf_error(e):
    """Handle CSRF errors."""
    flash('The form has expired. Please try again.', 'error')
    return redirect(url_for('index'))


def update_questions_from_github(target_file=None):
    """Fetch the latest questions from GitHub and update the local question bank."""
    if target_file is None:
        target_file = QUESTIONS_FILE
        
    try:
        # Create backup before updating
        backup_success, backup_result = create_backup()
        if not backup_success:
            return False, f"Failed to create backup: {backup_result}"

        # Fetch latest questions from GitHub
        url = "https://raw.githubusercontent.com/SailboatSteve/SMQT_Practice_Exam/main/test_questions.json"
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse and validate the JSON
        new_questions = response.json()
        
        # Basic validation that it's a list of questions
        if not isinstance(new_questions, list):
            raise ValueError("Invalid question format")
            
        # Save the new questions
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(new_questions, f, indent=2)
            
        return True, "Questions updated successfully!"

    except Exception as e:
        return False, f"Error updating questions: {str(e)}"


@app.route('/admin/update_questions', methods=['POST'])
@admin_required
def update_questions():
    """Update questions from GitHub."""
    try:
        # Verify CSRF token
        token = request.headers.get('X-CSRFToken')
        if not token:
            return jsonify({'error': 'Missing CSRF token'}), 403
        
        try:
            validate_csrf(token)
            print("CSRF validation passed")
        except Exception as e:
            print(f"CSRF validation error: {str(e)}")
            return jsonify({'error': 'Invalid CSRF token'}), 403

        # Update questions
        success, message = update_questions_from_github()
        if not success:
            return jsonify({'error': message}), 500

        # Clear the cached questions to force reload
        if 'questions' in session:
            del session['questions']
        if 'question_indices' in session:
            del session['question_indices']

        return jsonify({
            'success': True,
            'message': message
        })

    except Exception as e:
        print(f"Error updating questions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download():
    """Show download page."""
    return render_template('download.html')

@app.route('/help')
def help_page():
    """Show the help page."""
    return render_template('help.html')

def open_browser():
    """Open the browser after a short delay to ensure Flask is running."""
    time.sleep(1.5)  # Wait for Flask to start
    webbrowser.open('http://127.0.0.1:5000')

@app.route('/admin/share_questions', methods=['POST'])
@admin_required
def share_questions():
    """Share user's questions by creating a PR on GitHub."""
    try:
        print("Starting share_questions")  # Debug print
        print(f"Session: {session}")  # Debug print
        
        # Verify CSRF token
        token = request.headers.get('X-CSRFToken')
        print(f"Got CSRF token: {token}")  # Debug print
        
        if not token:
            return jsonify({'error': 'Missing CSRF token'}), 403
        
        try:
            validate_csrf(token)
            print("CSRF validation passed")  # Debug print
        except Exception as e:
            print(f"CSRF validation error: {str(e)}")
            return jsonify({'error': 'Invalid CSRF token'}), 403

        # Get GitHub token
        github_token = app.config.get('GITHUB_TOKEN')
        if not github_token:
            return jsonify({'error': 'GitHub token not configured'}), 500

        # Get user's questions
        questions_path = os.path.join(get_user_data_dir(), 'test_questions.json')
        if not os.path.exists(questions_path):
            return jsonify({'error': 'No questions found to share'}), 404

        with open(questions_path, 'r') as f:
            content = f.read()

        print("Successfully read questions file")  # Debug print

        # Initialize GitHub
        g = Github(github_token)
        repo = g.get_repo(app.config['GITHUB_REPO'])

        # Create a new branch
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        branch_name = f'user_submission_{timestamp}'
        base_branch = repo.get_branch('main')
        repo.create_git_ref(f'refs/heads/{branch_name}', base_branch.commit.sha)

        print(f"Created branch: {branch_name}")  # Debug print

        # Create file in submissions directory
        message = f'User question submission {timestamp}'
        result = repo.create_file(
            f'submissions/questions_{timestamp}.json',
            message,
            content,
            branch=branch_name
        )

        print(f"Created file: {result}")  # Debug print

        # Create pull request
        pr = repo.create_pull(
            title=f'Question Pool Submission {timestamp}',
            body='New question pool submission from a user.',
            head=branch_name,
            base='main'
        )

        print(f"Created PR: {pr.html_url}")  # Debug print
        return jsonify({'success': True, 'pr_url': pr.html_url})

    except Exception as e:
        print(f"Error sharing questions: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_backup_dir():
    """Get the backup directory path, creating it if needed."""
    backup_dir = os.path.join(get_user_data_dir(), 'backups')
    print(f"Backup directory path: {backup_dir}")
    if not os.path.exists(backup_dir):
        print(f"Creating backup directory: {backup_dir}")
        os.makedirs(backup_dir)
    return backup_dir

def create_backup():
    """Create a backup of the current questions file."""
    try:
        print(f"Creating backup... Questions file: {QUESTIONS_FILE}")
        
        # Get current questions
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            current_questions = f.read()

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        backup_dir = get_backup_dir()
        print(f"Using backup directory: {backup_dir}")
        
        backup_file = os.path.join(backup_dir, f'questions_{timestamp}.json')
        print(f"Creating backup file: {backup_file}")
        
        # Save backup
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(current_questions)
            print("Backup file written successfully")

        # Clean up old backups (keep only most recent 3)
        backup_files = glob.glob(os.path.join(backup_dir, 'questions_*.json'))
        backup_files.sort(reverse=True)
        for old_file in backup_files[3:]:
            print(f"Removing old backup: {old_file}")
            os.remove(old_file)

        print("Backup creation completed successfully")
        return True, backup_file
    except Exception as e:
        error_msg = f"Error creating backup: {str(e)}"
        print(error_msg)
        return False, error_msg

def get_available_backups():
    """Get list of available backups with timestamps."""
    try:
        backup_files = glob.glob(os.path.join(get_backup_dir(), 'questions_*.json'))
        backups = []
        for f in sorted(backup_files, reverse=True)[:3]:
            filename = os.path.basename(f)
            timestamp = filename.replace('questions_', '').replace('.json', '')
            date_obj = datetime.strptime(timestamp, '%Y%m%d_%H%M')
            backups.append({
                'file': f,
                'timestamp': timestamp,
                'date': date_obj.strftime('%B %d, %Y %I:%M %p')
            })
        return backups
    except Exception as e:
        print(f"Error getting backups: {str(e)}")
        return []

@app.route('/admin/get_backups', methods=['GET'])
@admin_required
def list_backups():
    """Get list of available backups."""
    backups = get_available_backups()
    return jsonify({'backups': backups})

@app.route('/admin/restore_backup', methods=['POST'])
@admin_required
def restore_backup():
    """Restore questions from a backup file."""
    try:
        data = request.get_json()
        backup_file = data.get('backup_file')
        
        if not backup_file or not os.path.exists(backup_file):
            return jsonify({'error': 'Invalid backup file'}), 400

        # Read backup file
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_content = f.read()

        # Validate JSON
        try:
            questions = json.loads(backup_content)
            if not isinstance(questions, list):
                raise ValueError("Invalid question format")
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid backup file format'}), 400

        # Restore backup
        with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
            f.write(backup_content)

        # Clear session cache
        if 'questions' in session:
            del session['questions']
        if 'question_indices' in session:
            del session['question_indices']

        return jsonify({
            'success': True,
            'message': 'Questions restored successfully!'
        })

    except Exception as e:
        print(f"Error restoring backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    # Run Flask app
    app.run(debug=True, use_reloader=False)  # Disable reloader to prevent multiple browser windows
