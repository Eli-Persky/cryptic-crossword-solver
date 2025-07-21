# Cryptic Crossword Solver

This project is a web application designed to solve cryptic crossword clues using an advanced LangGraph-based approach with OpenAI's GPT-4. The solver uses a recurrent graph structure that iteratively analyzes clues, assigns roles to words, and employs specialized tools for anagram generation, dictionary lookups, and wordplay verification.

## Features

- **LangGraph-Based Solver**: Advanced multi-step reasoning with recurrent analysis
- **Specialized Tools**: Anagram generation, dictionary validation, synonym finding, hidden word detection
- **Iterative Refinement**: Multiple attempts with improving analysis
- **Web Interface**: Clean, modern UI for entering clues and viewing detailed solutions
- **Flexible Length Input**: Optional solution length specification
- **Detailed Reasoning**: View the complete thought process behind solutions

## Example

![example screenshot 1](https://github.com/Eli-Persky/cryptic-crossword-solver/blob/main/screenshot1.png)
![example screenshot 2](https://github.com/Eli-Persky/cryptic-crossword-solver/blob/main/screenshot2.png)

## How It Works

The LangGraph solver uses a multi-node approach:

1. **Analyze Clue**: Identify word roles (definition, indicator, target, synonym)
2. **Generate Solution**: Use tools to explore wordplay possibilities
3. **Verify Solution**: Check validity and scoring
4. **Decide Next**: Continue iterating or finalize based on confidence
5. **Finalize**: Select the best solution from all attempts

### Tools Available to the Solver

- **Anagram Generator**: Creates valid English anagrams from letter sets
- **Dictionary Checker**: Validates word existence in English
- **Synonym Finder**: Locates potential synonyms for definitions
- **Hidden Word Detector**: Finds words hidden within phrases
- **Word Reversal**: Handles reversal-based wordplay

## Project Structure

```
cryptic-crossword-solver
├── app
│   ├── __init__.py
│   ├── api.py
│   ├── get_solution.py         # Main solver interface
│   ├── langgraph_solver.py     # LangGraph-based solver implementation
│   ├── prompts
│   │   ├── reasoning_prompt.txt
│   │   └── structuring_prompt.txt
│   ├── schemas.py
│   ├── templates
│   │   └── index.html
│   ├── static
│   │   ├── css
│   │   │   └── styles.css
│   │   └── js
│   │       └── scripts.js
├── requirements.txt
├── config.py
├── setup.py                   # Setup script for dependencies
├── run.py
└── README.md
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Eli-Persky/cryptic-crossword-solver.git
   cd cryptic-crossword-solver
   ```

2. Run the automated setup:
   ```bash
   python setup.py
   ```
   
   Or install manually:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file
   - Adjust other settings as needed

## Configuration

Key environment variables in `.env`:

- `LLM_API_PROVIDER`: Set to "openai" for LangGraph solver
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `USE_LANGGRAPH`: Enable/disable LangGraph solver (default: true)
- `MAX_SOLVER_ITERATIONS`: Maximum analysis iterations (default: 3)
- `TEST_MODE`: Use dummy responses for testing (default: false)

## Usage

1. Start the application:
   ```bash
   python run.py
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Enter your cryptic crossword clue and optionally specify the solution length

4. View the detailed analysis including:
   - Final solution
   - Definition identification
   - Wordplay breakdown
   - Reasoning process (expandable)

## LangGraph Architecture

The solver uses a sophisticated graph-based approach:

- **Recurrent Processing**: Returns to analysis node for iterative refinement
- **Tool Integration**: Seamlessly uses specialized cryptic crossword tools
- **State Management**: Maintains context across iterations
- **Confidence Scoring**: Evaluates solution quality at each step

## Requirements

- Python 3.8+
- OpenAI API access
- Internet connection for API calls and dictionary services

## API Integration

This application requires an OpenAI API key for the LangGraph-based solver. The traditional two-stage prompting approach is maintained as a fallback but the LangGraph approach provides superior results through its iterative, tool-enhanced analysis.
