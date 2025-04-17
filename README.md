# SMQT Practice Test Application

A free and open-source application for practicing SMQT (Surveyor Minimum Qualifications Test) questions.

## Quick Start

If you're just here for the app, download the latest version (v1.2.1) here:

[Download SMQT Practice Test Installer](https://github.com/SailboatSteve/SMQT_Practice_Exam/releases/latest/download/SMQT_Practice_Test_Setup.exe)

Just download and run the installer - no configuration needed! The application will automatically fetch the latest question bank during installation.

### New in Version 1.2.1
- Restored Windows installer for easier installation
- Added backup and restore functionality for question pool
- New help documentation with detailed guides
- Question sharing capability
- Improved modal handling and UI fixes
- Enhanced error handling

## Overview

This application provides a user-friendly interface for:
- Taking practice tests with configurable lengths (10, 35, 70, or 140 questions)
- Reviewing answers with detailed explanations
- Accessing relevant CMS regulations
- Managing questions through an admin interface

## License

This software is free and open source, distributed under the GNU General Public License v3.0 (GPL-3.0). You are free to:
- Use the software for any purpose
- Change the software to suit your needs
- Share the software with your friends and neighbors
- Share the changes you make

## Development Setup

1. Copy `.env.template` to `.env`
2. Add your OpenAI API key to `.env`
3. Install dependencies: `pip install -r requirements.txt`

## Using the Admin Portal

The application includes a password-protected admin interface for managing the question bank:

1. Access the admin portal by clicking "Admin" in the navigation bar
2. Login with the default password: `admin`
3. In the admin dashboard, you can:
   - View all questions in a sortable table
   - Edit any question by clicking the "Edit" button
   - Modify multiple aspects of each question:
     - Question text
     - Answer choices
     - Correct answer(s)
     - Explanation text
     - F-tags and KSAs
     - Regulation references

All changes are saved immediately to the question bank and will be available in future practice tests.

## Generating Custom Questions

The `dev_tools` directory contains utilities for generating custom questions using OpenAI's API:

1. Get an API key from [OpenAI](https://openai.com/api/)
2. Rename `.env.template` to `.env` and add your API key
3. Use the following tools in `dev_tools`:
   - `generate_questions.py`: Generate new questions
   - `extract_cms_regulations.py`: Extract regulations from CMS documents
   - `context_questions.json`: Example questions for the AI model, used to tune the questions the AI will generate. Adjust carefully, if desired.

### Using generate_questions.py

```bash
cd dev_tools
python generate_questions.py --num-questions 10 --temperature 0.8
```

Parameters:
- `--num-questions`: Number of questions to generate
- `--temperature`: Controls creativity (0.0-1.0, higher = more creative)
- `--model`: OpenAI model to use (default: gpt-3.5-turbo)

Generated questions will be automatically added to the main question bank.

## Contributing

Contributions are welcome! Feel free to:
- Add new questions
- Improve existing questions
- Enhance the application features
- Fix bugs

## Support

This is freeware - feel free to share and modify. For issues or suggestions:
1. Check the GitHub repository
2. Submit an issue
3. Propose improvements

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) and [Bootstrap](https://getbootstrap.com/)
- Uses [OpenAI's API](https://openai.com/api/) for question generation
- CMS regulations and guidelines provided by: [CMS](https://www.cms.gov/)
- 100% artisanally vibe coded using Windsurf by [Codeium](https://codeium.com/) and [Claude 3.5 Sonnet](https://www.anthropic.com/)

Special thanks to my wife, Melissa, whose legendary passion for caring for seniors is only rivaled by her legendary talent for panic-bombing exams. This app was inspired by her and built for her. Love you, babe.

