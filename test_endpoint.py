from flask import Flask, request, jsonify, session
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from functools import wraps
from github import Github
import os
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)
csrf = CSRFProtect(app)

# Load config
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['GITHUB_TOKEN'] = os.getenv('GITHUB_TOKEN')
app.config['GITHUB_REPO'] = 'SailboatSteve/SMQT_Practice_Exam'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For testing, always allow access
        return f(*args, **kwargs)
    return decorated_function

@app.route('/test_csrf')
def test_csrf():
    """Return a page with CSRF token."""
    token = generate_csrf()
    print(f"Generated CSRF token: {token}")  # Debug print
    return f'''
    <html>
        <body>
            <form id="testForm">
                <input type="hidden" name="csrf_token" value="{token}">
                <button type="button" onclick="submitTest()">Test Share</button>
            </form>
            <div id="result"></div>

            <script>
            async function submitTest() {{
                try {{
                    const token = document.querySelector('input[name="csrf_token"]').value;
                    console.log('Using CSRF token:', token);
                    
                    const response = await fetch('/admin/share_questions', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'X-CSRFToken': token,
                        }},
                        credentials: 'same-origin'
                    }});
                    
                    console.log('Response status:', response.status);
                    const result = await response.json();
                    console.log('Response:', result);
                    
                    document.getElementById('result').textContent = 
                        response.ok ? 'Success: ' + result.pr_url : 'Error: ' + result.error;
                }} catch (error) {{
                    console.error('Error:', error);
                    document.getElementById('result').textContent = 'Error: ' + error;
                }}
            }}
            </script>
        </body>
    </html>
    '''

@app.route('/admin/share_questions', methods=['POST'])
@admin_required
def share_questions():
    """Test endpoint for sharing questions."""
    try:
        # Verify CSRF token
        token = request.headers.get('X-CSRFToken')
        if not token:
            return jsonify({'error': 'Missing CSRF token'}), 403
        
        try:
            validate_csrf(token)
        except Exception as e:
            print(f"CSRF validation error: {str(e)}")  # Debug print
            return jsonify({'error': 'Invalid CSRF token'}), 403

        # Get GitHub token
        github_token = app.config.get('GITHUB_TOKEN')
        if not github_token:
            return jsonify({'error': 'GitHub token not configured'}), 500

        # Use test content
        content = '{"test": "This is a test submission"}'

        # Initialize GitHub
        g = Github(github_token)
        repo = g.get_repo(app.config['GITHUB_REPO'])

        # Create a new branch
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        branch_name = f'test_submission_{timestamp}'
        base_branch = repo.get_branch('main')
        repo.create_git_ref(f'refs/heads/{branch_name}', base_branch.commit.sha)

        # Create file in submissions directory
        file_path = f'submissions/test_{timestamp}.json'
        message = f'Test submission {timestamp}'
        repo.create_file(
            file_path,
            message,
            content,
            branch=branch_name
        )

        # Create pull request
        pr = repo.create_pull(
            title=f'Test Submission {timestamp}',
            body='This is a test submission.',
            head=branch_name,
            base='main'
        )

        return jsonify({'success': True, 'pr_url': pr.html_url})

    except Exception as e:
        print(f"Error in share_questions: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
