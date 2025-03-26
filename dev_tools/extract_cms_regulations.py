#!/usr/bin/env python3
"""
SMQT Question Generator from CMS Regulations

This script extracts CMS regulations and generates SMQT practice questions.
"""

import argparse
import json
import logging
import os
import re
from typing import Dict, List, Optional, Union
import random

import requests
from bs4 import BeautifulSoup

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# CMS regulation sources
CMS_SOURCES = [
    {
        "name": "State Operations Manual",
        "url": "https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/som107ap_pp_guidelines_ltcf.pdf"
    },
    {
        "name": "Survey Protocols",
        "url": "https://www.cms.gov/Medicare/Provider-Enrollment-and-Certification/SurveyCertificationGenInfo/Downloads/Survey-and-Cert-Letter-16-04.pdf"
    },
    {
        "name": "CMS Regulations",
        "url": "https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-483"
    },
    {
        "name": "Infection Control",
        "url": "https://www.cms.gov/files/document/qso-20-38-nh-revised.pdf"
    },
    {
        "name": "Immediate Jeopardy",
        "url": "https://www.cms.gov/Medicare/Provider-Enrollment-and-Certification/SurveyCertificationGenInfo/Downloads/QSO19-09-ALL.pdf"
    },
    {
        "name": "Emergency Preparedness",
        "url": "https://www.cms.gov/files/document/qso-21-15-all.pdf"
    },
    {
        "name": "Resident Rights",
        "url": "https://www.cms.gov/files/document/qso-21-19-nh.pdf"
    },
    {
        "name": "Nursing Home Survey Process",
        "url": "https://www.cms.gov/files/document/qso-20-31-all.pdf"
    }
]


def download_cms_document(url: str, output_dir: str = "cms_docs") -> Optional[str]:
    """
    Download a CMS document.
    
    Args:
        url: URL of the document.
        output_dir: Directory to save the document to.
    
    Returns:
        Path to the downloaded document, or None if download failed.
    """
    logger.info(f"Downloading document from {url}")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract filename from URL
        filename = os.path.basename(url)
        output_path = os.path.join(output_dir, filename)
        
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded document to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error downloading document: {e}")
        return None


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file.
    
    Returns:
        Extracted text.
    """
    logger.info(f"Extracting text from {pdf_path}")
    
    try:
        # Try to import PyPDF2
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                logger.info(f"Extracted {len(text)} characters from {pdf_path}")
                return text
        
        except ImportError:
            logger.warning("PyPDF2 not installed. Please install it with: pip install PyPDF2")
            return ""
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_html(url: str) -> str:
    """
    Extract text from an HTML page.
    
    Args:
        url: URL of the HTML page.
    
    Returns:
        Extracted text.
    """
    logger.info(f"Extracting text from {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info(f"Extracted {len(text)} characters from {url}")
        return text
    
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {e}")
        return ""


def extract_regulations(text: str, source_name: str = "") -> List[Dict]:
    """
    Extract regulations from text.
    
    Args:
        text: Text to extract regulations from.
        source_name: Name of the source document.
    
    Returns:
        List of regulation dictionaries.
    """
    logger.info(f"Extracting regulations from text ({source_name})")
    
    regulations = []
    
    # Look for section headers and paragraphs
    section_pattern = r'§\s*(\d+\.\d+)\s+(.+?)(?=§|\Z)'
    subsection_pattern = r'\(([a-z0-9]+)\)\s+(.+?)(?=\([a-z0-9]+\)|\Z)'
    
    # Find all sections
    sections = re.findall(section_pattern, text, re.DOTALL)
    
    if sections:
        for section_num, section_text in sections:
            # Extract section title
            title_match = re.search(r'^(.*?)\.', section_text.strip())
            title = title_match.group(1).strip() if title_match else "Untitled Section"
            
            # Find all subsections
            subsections = re.findall(subsection_pattern, section_text, re.DOTALL)
            
            for subsection_num, subsection_text in subsections:
                regulations.append({
                    "section": section_num,
                    "title": title,
                    "subsection": subsection_num,
                    "text": subsection_text.strip(),
                    "source": source_name
                })
    else:
        # Alternative extraction for documents without standard section formatting
        # Look for F-tags (common in CMS documents)
        f_tag_pattern = r'(F\d{3,4})\s*[-–]\s*(.+?)(?=F\d{3,4}|\Z)'
        f_tags = re.findall(f_tag_pattern, text, re.DOTALL)
        
        for f_tag, tag_text in f_tags:
            # Extract first paragraph as the main content
            paragraph_match = re.search(r'^(.*?)(?:\n\n|\Z)', tag_text.strip(), re.DOTALL)
            paragraph = paragraph_match.group(1).strip() if paragraph_match else tag_text.strip()
            
            regulations.append({
                "section": f_tag,
                "title": "F-Tag Requirement",
                "subsection": "1",
                "text": paragraph,
                "source": source_name
            })
        
        # Look for sections with "§" but in a different format
        alt_section_pattern = r'(\d+\.\d+)\s*\(([a-z0-9]+)\)\s*(.+?)(?=\d+\.\d+|\Z)'
        alt_sections = re.findall(alt_section_pattern, text, re.DOTALL)
        
        for section_num, subsection_num, section_text in alt_sections:
            # Extract first paragraph
            paragraph_match = re.search(r'^(.*?)(?:\n\n|\Z)', section_text.strip(), re.DOTALL)
            paragraph = paragraph_match.group(1).strip() if paragraph_match else section_text.strip()
            
            regulations.append({
                "section": section_num,
                "title": "CMS Requirement",
                "subsection": subsection_num,
                "text": paragraph,
                "source": source_name
            })
        
        # If still no regulations found, extract key paragraphs with regulatory language
        if not regulations:
            # Look for paragraphs that contain regulatory language
            reg_keywords = [
                "must", "shall", "required", "requirement", "comply", "compliance",
                "standard", "regulation", "policy", "procedure", "surveyor", "survey",
                "deficiency", "citation", "violation", "F-tag", "F tag"
            ]
            
            # Split text into paragraphs
            paragraphs = re.split(r'\n\s*\n', text)
            
            # Extract paragraphs with regulatory keywords
            for i, paragraph in enumerate(paragraphs):
                paragraph = paragraph.strip()
                if len(paragraph) > 100 and any(keyword in paragraph.lower() for keyword in reg_keywords):
                    regulations.append({
                        "section": f"{source_name}-{i+1}",
                        "title": "CMS Guidance",
                        "subsection": "1",
                        "text": paragraph,
                        "source": source_name
                    })
    
    # Deduplicate regulations by text similarity
    unique_regulations = []
    texts_seen = set()
    
    for reg in regulations:
        # Create a simplified version of the text for comparison
        simple_text = ' '.join(reg["text"].lower().split())[:100]
        
        if simple_text not in texts_seen:
            texts_seen.add(simple_text)
            unique_regulations.append(reg)
    
    logger.info(f"Extracted {len(unique_regulations)} regulations from {source_name}")
    return unique_regulations


def generate_question_from_regulation(
    regulation: Dict,
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    question_type: str = "random"
) -> Optional[Dict]:
    """
    Generate a question from a regulation.
    
    Args:
        regulation: Regulation dictionary.
        api_key: OpenAI API key.
        model: OpenAI model to use.
        question_type: Type of question to generate (scenario, regulatory, knowledge, select_all, or random).
    
    Returns:
        Question dictionary, or None if generation failed.
    """
    logger.info(f"Generating {question_type} question from regulation {regulation['section']}-{regulation['subsection']}")
    
    # If OpenAI is available and API key is provided, use it
    if OPENAI_AVAILABLE and api_key:
        client = OpenAI(api_key=api_key)
        
        # Determine question type if random
        if question_type == "random":
            question_types = ["scenario", "regulatory", "knowledge", "select_all"]
            question_type = random.choice(question_types)
        
        # Create prompt based on question type
        if question_type == "scenario":
            prompt = f"""
            Generate a scenario-based multiple-choice question for the SMQT (Surveyor Minimum Qualifications Test) based on the following CMS regulation:
            
            Section {regulation['section']} ({regulation['title']}), Subsection ({regulation['subsection']}):
            {regulation['text']}
            
            Create a realistic scenario that a surveyor might encounter, followed by a question about what action they should take or what violation they should identify.
            Include 4 answer choices (labeled A, B, C, D).
            
            Format the response as a JSON object with the following structure:
            {{
              "question": "The scenario-based question text",
              "choices": ["A. First choice", "B. Second choice", "C. Third choice", "D. Fourth choice"],
              "correct_answers": ["A"],  // Letters of correct answers (can be multiple)
              "explanation": "Explanation of why this answer is correct, referencing the regulation"
            }}
            """
        elif question_type == "select_all":
            prompt = f"""
            Generate a "select all that apply" multiple-choice question for the SMQT (Surveyor Minimum Qualifications Test) based on the following CMS regulation:
            
            Section {regulation['section']} ({regulation['title']}), Subsection ({regulation['subsection']}):
            {regulation['text']}
            
            Create a question where multiple answers are correct (2-3 correct options).
            Include 4-5 answer choices (labeled A, B, C, D, E).
            
            Format the response as a JSON object with the following structure:
            {{
              "question": "The question text (make sure to include 'Select all that apply' in the question)",
              "choices": ["A. First choice", "B. Second choice", "C. Third choice", "D. Fourth choice", "E. Fifth choice (optional)"],
              "correct_answers": ["A", "C", "D"],  // Letters of ALL correct answers
              "explanation": "Explanation of why these answers are correct, referencing the regulation"
            }}
            """
        elif question_type == "regulatory":
            prompt = f"""
            Generate a regulatory interpretation multiple-choice question for the SMQT (Surveyor Minimum Qualifications Test) based on the following CMS regulation:
            
            Section {regulation['section']} ({regulation['title']}), Subsection ({regulation['subsection']}):
            {regulation['text']}
            
            Create a question that tests understanding of how to interpret and apply this specific regulation.
            Include 4 answer choices (labeled A, B, C, D).
            
            Format the response as a JSON object with the following structure:
            {{
              "question": "The regulatory interpretation question text",
              "choices": ["A. First choice", "B. Second choice", "C. Third choice", "D. Fourth choice"],
              "correct_answers": ["A"],  // Letters of correct answers (can be multiple)
              "explanation": "Explanation of why this answer is correct, referencing the regulation"
            }}
            """
        else:  # knowledge
            prompt = f"""
            Generate a direct knowledge multiple-choice question for the SMQT (Surveyor Minimum Qualifications Test) based on the following CMS regulation:
            
            Section {regulation['section']} ({regulation['title']}), Subsection ({regulation['subsection']}):
            {regulation['text']}
            
            Create a straightforward question that tests factual knowledge of this regulation.
            Include 4 answer choices (labeled A, B, C, D).
            
            Format the response as a JSON object with the following structure:
            {{
              "question": "The knowledge-based question text",
              "choices": ["A. First choice", "B. Second choice", "C. Third choice", "D. Fourth choice"],
              "correct_answers": ["A"],  // Letters of correct answers (can be multiple)
              "explanation": "Explanation of why this answer is correct, referencing the regulation"
            }}
            """
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert on CMS regulations and the SMQT exam."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                # Find JSON object in the response
                json_match = re.search(r'({.*})', content, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    question = json.loads(json_str)
                    
                    # Validate the question
                    if all(key in question for key in ["question", "choices", "correct_answers", "explanation"]):
                        # Add metadata about the source regulation
                        question["source"] = {
                            "section": regulation["section"],
                            "title": regulation["title"],
                            "subsection": regulation["subsection"]
                        }
                        return question
                
                logger.warning("Failed to extract valid question from OpenAI response")
                return None
            
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from OpenAI response")
                return None
        
        except Exception as e:
            logger.error(f"Error generating question with OpenAI: {e}")
            return None
    
    # If OpenAI is not available or no API key, generate a mock question
    logger.warning("OpenAI API key not provided or OpenAI not available. Generating mock question.")
    
    section = regulation['section']
    title = regulation['title']
    subsection = regulation['subsection']
    text = regulation['text']
    
    # Generate a mock question based on the question type
    if question_type == "scenario":
        question = f"Scenario: During a survey at a long-term care facility, you observe that {text[:100]}... What action should you take as a surveyor?"
        choices = [
            "A. Issue an immediate citation for non-compliance",
            "B. Document the observation and continue the survey",
            "C. Consult with the facility administrator",
            "D. Report the issue to the state licensing board"
        ]
        explanation = f"The correct answer is B. According to CMS regulation §{section} ({title}), subsection ({subsection}), surveyors should document observations related to {text[:50]}... and continue gathering evidence before making compliance determinations."
    
    elif question_type == "select_all":
        question = f"Select all that apply: Which of the following statements are true regarding {title} according to CMS regulation §{section}?"
        choices = [
            "A. Facilities must document compliance with this requirement",
            "B. This regulation applies only to facilities with more than 50 beds",
            "C. Surveyors must verify compliance during each standard survey",
            "D. Non-compliance may result in enforcement actions",
            "E. Annual training is required for all staff"
        ]
        explanation = f"The correct answers are A, C, and D. According to CMS regulation §{section} ({title}), subsection ({subsection}): {text}"
        return {
            "question": question,
            "choices": choices,
            "correct_answers": ["A", "C", "D"],
            "explanation": explanation,
            "source": {
                "section": section,
                "title": title,
                "subsection": subsection,
                "source": regulation.get("source", "")
            }
        }
    
    elif question_type == "regulatory":
        question = f"According to CMS regulation §{section} ({title}), what is required regarding {text[:50]}...?"
        choices = [
            f"A. {text[:100]}...",
            "B. Facilities are exempt from this requirement if they have fewer than 50 beds",
            "C. This requirement applies only during initial certification surveys",
            "D. None of the above"
        ]
    
    else:  # knowledge
        question = f"What does CMS regulation §{section} ({title}), subsection ({subsection}) require regarding {text[:50]}...?"
        choices = [
            f"A. {text[:100]}...",
            "B. The facility must document all incidents in the medical record only",
            "C. The facility is exempt from this requirement if it has fewer than 50 beds",
            "D. None of the above"
        ]
    
    return {
        "question": question,
        "choices": choices,
        "correct_answers": ["A"],
        "explanation": f"The correct answer is A, as stated in CMS regulation §{section} ({title}), subsection ({subsection}): {text}",
        "source": {
            "section": section,
            "title": title,
            "subsection": subsection,
            "source": regulation.get("source", "")
        }
    }


def main():
    """Main function to run the regulation extractor and question generator."""
    parser = argparse.ArgumentParser(description='Extract CMS regulations and generate SMQT questions.')
    parser.add_argument('--output', default='smqt_questions.json', help='Output file path')
    parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    parser.add_argument('--model', default='gpt-3.5-turbo', help='OpenAI model to use')
    parser.add_argument('--num-questions', type=int, default=100, help='Number of questions to generate')
    parser.add_argument('--append', action='store_true', help='Append to existing questions file')
    parser.add_argument('--scenario-percent', type=int, default=50, help='Percentage of questions that should be scenario-based (0-100)')
    parser.add_argument('--max-regulations', type=int, default=500, help='Maximum number of regulations to extract')
    
    args = parser.parse_args()
    
    # Get API key from arguments or environment variable
    api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
    
    # Load existing questions if appending
    questions = []
    if args.append and os.path.exists(args.output):
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            logger.info(f"Loaded {len(questions)} existing questions from {args.output}")
        except json.JSONDecodeError:
            logger.warning(f"Error loading existing questions from {args.output}. Starting with empty list.")
    
    # Create output directory for downloaded documents
    os.makedirs("cms_docs", exist_ok=True)
    
    # Process each CMS source
    regulations = []
    
    for source in CMS_SOURCES:
        name = source["name"]
        url = source["url"]
        
        if url.endswith(".pdf"):
            # Download and extract text from PDF
            pdf_path = download_cms_document(url)
            if pdf_path:
                text = extract_text_from_pdf(pdf_path)
                if text:
                    regs = extract_regulations(text, name)
                    regulations.extend(regs)
        else:
            # Extract text from HTML
            text = extract_text_from_html(url)
            if text:
                regs = extract_regulations(text, name)
                regulations.extend(regs)
    
    logger.info(f"Extracted {len(regulations)} regulations from all sources")
    
    # Limit the number of regulations to prevent overwhelming the API
    if len(regulations) > args.max_regulations:
        logger.info(f"Limiting to {args.max_regulations} regulations")
        regulations = regulations[:args.max_regulations]
    
    # Shuffle regulations to get a good mix
    random.shuffle(regulations)
    
    # Calculate how many of each question type to generate
    scenario_count = int(args.num_questions * args.scenario_percent / 100)
    regulatory_count = int(args.num_questions * 0.2)  # 20% regulatory
    knowledge_count = int(args.num_questions * 0.2)   # 20% knowledge
    select_all_count = args.num_questions - scenario_count - regulatory_count - knowledge_count  # Remainder
    
    logger.info(f"Planning to generate {scenario_count} scenario, {regulatory_count} regulatory, "
                f"{knowledge_count} knowledge, and {select_all_count} select-all questions")
    
    # Generate questions from regulations
    num_generated = 0
    question_types_remaining = {
        "scenario": scenario_count,
        "regulatory": regulatory_count,
        "knowledge": knowledge_count,
        "select_all": select_all_count
    }
    
    # First pass: try to generate the specified number of each type
    for regulation in regulations:
        if num_generated >= args.num_questions:
            break
        
        # Choose a question type that still needs more questions
        available_types = [t for t, count in question_types_remaining.items() if count > 0]
        if not available_types:
            break
        
        question_type = random.choice(available_types)
        
        question = generate_question_from_regulation(regulation, api_key, args.model, question_type)
        
        if question:
            questions.append(question)
            num_generated += 1
            question_types_remaining[question_type] -= 1
            logger.info(f"Generated {question_type} question {num_generated}/{args.num_questions}")
    
    # Second pass: fill in any remaining questions with random types
    while num_generated < args.num_questions and regulations:
        regulation = regulations[num_generated % len(regulations)]
        
        question = generate_question_from_regulation(regulation, api_key, args.model, "random")
        
        if question:
            questions.append(question)
            num_generated += 1
            logger.info(f"Generated random question {num_generated}/{args.num_questions}")
    
    # Save questions to file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2)
    
    logger.info(f"Saved {len(questions)} questions to {args.output}")
    
    # Print summary of question types
    scenario_count = sum(1 for q in questions if "scenario" in q.get("question", "").lower() or "scenario" in q.get("explanation", "").lower())
    select_all_count = sum(1 for q in questions if "select all" in q.get("question", "").lower())
    multiple_answers = sum(1 for q in questions if len(q.get("correct_answers", [])) > 1)
    
    logger.info(f"Question type summary:")
    logger.info(f"  Scenario-based: {scenario_count}")
    logger.info(f"  Select-all: {select_all_count}")
    logger.info(f"  Multiple correct answers: {multiple_answers}")


if __name__ == "__main__":
    main()
