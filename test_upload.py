from github import Github
import os
from datetime import datetime
from dotenv import load_dotenv

def test_github_upload():
    """Test uploading a file to GitHub."""
    try:
        # Load environment variables
        load_dotenv()
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            print("Error: GitHub token not found in .env file")
            return False

        # Create test content
        test_content = '{"test": "This is a test submission"}'
        
        # Initialize GitHub
        g = Github(github_token)
        repo = g.get_repo('SailboatSteve/SMQT_Practice_Exam')
        
        # Create a new branch
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        branch_name = f'test_submission_{timestamp}'
        base_branch = repo.get_branch('main')
        print(f"Creating branch: {branch_name}")
        repo.create_git_ref(f'refs/heads/{branch_name}', base_branch.commit.sha)

        # Create file in submissions directory
        file_path = f'submissions/test_{timestamp}.json'
        message = f'Test submission {timestamp}'
        print(f"Creating file: {file_path}")
        result = repo.create_file(
            file_path,
            message,
            test_content,
            branch=branch_name
        )
        print(f"File created: {result}")

        # Create pull request
        print("Creating pull request...")
        pr = repo.create_pull(
            title=f'Test Submission {timestamp}',
            body='This is a test submission.',
            head=branch_name,
            base='main'
        )
        print(f"Pull request created: {pr.html_url}")
        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("Testing GitHub upload...")
    success = test_github_upload()
    print(f"\nTest {'succeeded' if success else 'failed'}")
