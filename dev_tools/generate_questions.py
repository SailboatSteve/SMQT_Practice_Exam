#!/usr/bin/env python3
"""
SMQT Question Generator

This script generates SMQT practice questions using OpenAI's API and saves them to a JSON file.
Supports batch generation of large quantities of questions with regulation mapping.
"""

import argparse
import json
import logging
import os
import time
import math
import random
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import importlib.util

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
CONTEXT_QUESTIONS_FILE = os.path.join('..', 'context_questions.json')  # Path relative to dev_tools
REGULATIONS_FILE = os.path.join('..', 'regulations.json')  # Path relative to dev_tools
DEFAULT_OUTPUT_FILE = os.path.join('..', 'test_questions.json')  # Path relative to dev_tools
BATCH_SIZE = 5  # OpenAI's preferred batch size
DEFAULT_NUM_QUESTIONS = 10

try:
    client = OpenAI()
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not installed. Please install it with: pip install openai")
    OPENAI_AVAILABLE = False


def load_regulations() -> Dict:
    """Load regulations mapping from the regulations file."""
    try:
        with open(REGULATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading regulations: {e}")
        return {"categories": {}, "keywords": {}}


def get_random_regulation_topics(regulations: Dict, num_topics: int = 3) -> List[Tuple[str, str, List[str]]]:
    """Get random regulation categories and their topics for question generation."""
    categories = list(regulations["categories"].items())
    selected = random.sample(categories, min(num_topics, len(categories)))
    
    result = []
    for cat_id, cat_data in selected:
        if cat_data["regulations"]:
            reg = random.choice(cat_data["regulations"])
            result.append((
                cat_data["title"],
                reg["id"],
                reg["topics"]
            ))
    return result


def load_example_questions() -> List[Dict]:
    """Load example questions from the context questions file."""
    try:
        with open(CONTEXT_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('questions', [])
    except Exception as e:
        logger.error(f"Error loading context questions: {e}")
        return []


def load_existing_questions(file_path: str) -> List[Dict]:
    """Load existing questions from a JSON file."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Error loading existing questions from {file_path}. Starting with empty list.")
            return []
    else:
        logger.info(f"No existing questions file found at {file_path}. Starting with empty list.")
        return []


def save_questions(questions: List[Dict], file_path: str) -> None:
    """Save questions to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2)
    logger.info(f"Saved {len(questions)} questions to {file_path}")


def generate_questions_with_openai(
    num_questions: int,
    api_key: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.8,  # Increased temperature for more variety
    topics: Optional[List[str]] = None
) -> List[Dict]:
    """
    Generate SMQT practice questions using OpenAI's API.
    
    Args:
        num_questions: Number of questions to generate.
        api_key: OpenAI API key.
        model: OpenAI model to use.
        temperature: Temperature parameter for generation.
        topics: Optional list of topics to focus on.
    
    Returns:
        List of generated questions.
    """
    if not OPENAI_AVAILABLE:
        logger.error("OpenAI package not installed. Cannot generate questions.")
        return []
    
    client = OpenAI(api_key=api_key)
    
    # Load regulations and get random topics if none specified
    regulations = load_regulations()
    if not topics:
        selected_regs = get_random_regulation_topics(regulations, num_topics=2)
        topics = [f"{title} ({reg_id}): {', '.join(random.sample(reg_topics, min(3, len(reg_topics))))}"
                 for title, reg_id, reg_topics in selected_regs]
    
    # Load example questions
    example_questions = load_example_questions()
    if not example_questions:
        logger.warning("No example questions found. Using default format.")
    
    # Format example questions for the prompt
    example_str = json.dumps(example_questions[:2], indent=2) if example_questions else ""
    
    topics_str = ", ".join(topics) if topics else "various aspects of long-term care facility surveying"
    
    system_prompt = f"""
    You are an expert on the Surveyor Minimum Qualifications Test (SMQT) for long-term care facility surveyors.
    Generate {num_questions} realistic multiple-choice SMQT practice questions about {topics_str}.
    
    Each question must follow this exact format and requirements:
    1. Include a "ksa" field with a letter A-K representing the Knowledge, Skill, or Ability being tested
    2. Include a "question" field that starts with "Scenario: " for scenario-based questions
    3. Include "choices" as a list of 4 options labeled A-D
    4. Include "correct_answers" as a list of letter(s) representing correct choice(s)
    5. Include an "explanation" field with:
       - Specific F-tag references (e.g., F880 for infection control)
       - Relevant regulation citations (e.g., 42 CFR 483.80)
       - Clear rationale for correct and incorrect answers
    6. Include a "regulations" field as a list of objects with:
       - "id": regulation number (e.g., "483.80")
       - "section": F-tag (e.g., "F880")
       - "title": regulation title
    
    CRITICAL REQUIREMENTS:
    1. EXACTLY 50% of questions MUST have multiple correct answers:
       - Some with 2 correct answers (e.g., ["A", "C"])
       - Some with 3 correct answers (e.g., ["A", "B", "D"])
       - Never all 4 options correct
    2. ALL explanations MUST include specific F-tags
    3. ALL explanations MUST reference relevant regulations
    4. Questions should focus on:
       - Real-world scenarios surveyors encounter
       - Application of regulations and best practices
       - Decision-making and critical thinking
       - Proper surveyor conduct and methodology
    
    Here are examples of well-formatted questions:
    {example_str}
    
    Follow these examples closely, maintaining the same style, depth, and professional tone.
    Return the questions as a JSON array with the same structure as the examples.
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate {num_questions} SMQT practice questions about {topics_str}."}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        
        # Extract JSON array from response
        try:
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                questions = json.loads(json_str)
                
                # Validate question format and requirements
                required_fields = ['ksa', 'question', 'choices', 'correct_answers', 'explanation', 'regulations']
                multi_answer_count = 0
                
                for q in questions:
                    # Check required fields
                    missing_fields = [f for f in required_fields if f not in q]
                    if missing_fields:
                        logger.warning(f"Question missing fields: {missing_fields}")
                        continue
                        
                    # Count multiple answer questions
                    if len(q['correct_answers']) > 1:
                        multi_answer_count += 1
                    
                    # Verify F-tag references
                    if not any(f"F" in exp for exp in q['explanation'].split()):
                        logger.warning("Question missing F-tag references in explanation")
                    
                    # Verify regulation references
                    if not any("483." in exp for exp in q['explanation'].split()):
                        logger.warning("Question missing regulation references in explanation")
                
                # Log statistics
                logger.info(f"Generated {len(questions)} questions:")
                logger.info(f"  Multiple answer questions: {multi_answer_count}")
                logger.info(f"  Single answer questions: {len(questions) - multi_answer_count}")
                
                return questions
            else:
                logger.error("Could not find JSON array in response")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {e}")
            return []
            
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return []


def generate_and_merge_questions(
    total_questions: int,
    api_key: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.8,
    topics: Optional[List[str]] = None,
    output_file: str = DEFAULT_OUTPUT_FILE
) -> None:
    """
    Generate questions in batches and merge them into the main question bank.
    
    Args:
        total_questions: Total number of questions to generate.
        api_key: OpenAI API key.
        model: OpenAI model to use.
        temperature: Temperature parameter for generation.
        topics: Optional list of topics to focus on.
        output_file: Path to the output JSON file.
    """
    num_batches = math.ceil(total_questions / BATCH_SIZE)
    all_questions = load_existing_questions(output_file)
    initial_count = len(all_questions)
    
    for batch in range(num_batches):
        remaining = total_questions - (batch * BATCH_SIZE)
        batch_size = min(BATCH_SIZE, remaining)
        
        logger.info(f"Generating batch {batch + 1}/{num_batches} ({batch_size} questions)")
        
        new_questions = generate_questions_with_openai(
            batch_size,
            api_key,
            model=model,
            temperature=temperature,
            topics=topics
        )
        
        if new_questions:
            all_questions.extend(new_questions)
            save_questions(all_questions, output_file)
            
            # Log statistics about correct answers distribution
            multi_correct = sum(1 for q in new_questions if len(q['correct_answers']) > 1)
            logger.info(f"Batch {batch + 1} stats:")
            logger.info(f"  Multiple correct answers: {multi_correct}/{len(new_questions)}")
        
        if batch < num_batches - 1:
            time.sleep(1)  # Rate limiting
    
    final_count = len(all_questions)
    logger.info(f"Generation complete. Added {final_count - initial_count} questions.")
    logger.info(f"Total questions in bank: {final_count}")


def main():
    """Main function to run the question generator."""
    parser = argparse.ArgumentParser(description='Generate SMQT practice questions')
    parser.add_argument('--num-questions', type=int, default=DEFAULT_NUM_QUESTIONS,
                      help=f'Number of questions to generate (default: {DEFAULT_NUM_QUESTIONS})')
    parser.add_argument('--model', type=str, default="gpt-3.5-turbo",
                      help='OpenAI model to use (default: gpt-3.5-turbo)')
    parser.add_argument('--temperature', type=float, default=0.8,
                      help='Temperature parameter for generation (default: 0.8)')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_FILE,
                      help=f'Output JSON file (default: {DEFAULT_OUTPUT_FILE})')
    parser.add_argument('--topics', nargs='+',
                      help='Optional list of topics to focus on')
    
    args = parser.parse_args()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return
    
    generate_and_merge_questions(
        args.num_questions,
        api_key,
        model=args.model,
        temperature=args.temperature,
        topics=args.topics,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
