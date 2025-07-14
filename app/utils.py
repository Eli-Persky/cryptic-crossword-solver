import os
import requests
import json
import time
from dotenv import load_dotenv
from app.schemas import OPENAI_FUNCTION_SCHEMAS, ANTHROPIC_TOOL_SCHEMAS, CROSSWORD_SOLUTION_SCHEMA

# Load environment variables from .env file
load_dotenv()

# Global variables
LAST_API_CALL = 0  # Timestamp of the last API call
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", 5))  # Minimum seconds between API calls

def format_response(data):
    # Function to format the response from the LLM API
    return {
        "status": "success",
        "data": data
    }

def handle_error(error_message):
    # Function to handle errors and format error responses
    return {
        "status": "error",
        "message": error_message
    }

def get_llm_solution(clue):
    """
    Send a cryptic crossword clue to an LLM API and return the solution.
    Rate-limited to one request per 5 seconds when not in test mode.
    
    :param clue: The cryptic crossword clue as a string.
    :return: The solution string or an error message.
    """
    # Check if we're in test mode
    test_mode = os.getenv("TEST_MODE", "true").lower() == "true"
    
    if test_mode:
        return get_dummy_solution(clue)
    
    # Rate limiting logic
    global LAST_API_CALL
    current_time = time.time()
    time_since_last_call = current_time - LAST_API_CALL
    
    if time_since_last_call < API_RATE_LIMIT:
        wait_time = round(API_RATE_LIMIT - time_since_last_call, 1)
        return f"Rate limit: Please wait {wait_time} seconds before making another request."
    
    # Update the last call timestamp
    LAST_API_CALL = current_time
    
    # Choose which API to use (OpenAI, Claude, etc.)
    api_choice = os.getenv("LLM_API_PROVIDER", "openai").lower()
    
    if api_choice == "openai":
        return get_openai_solution(clue)
    elif api_choice == "anthropic":
        return get_claude_solution(clue)
    else:
        return f"Unsupported API provider: {api_choice}"

def get_dummy_solution(clue):
    """
    Return a dummy solution for testing purposes with structured output.
    This avoids making actual API calls during development and testing.
    
    :param clue: The cryptic crossword clue as a string.
    :return: A structured dummy solution following the schema.
    """
    # Create a deterministic but varied response based on the clue
    word_count = len(clue.split())
    clue_length = len(clue)
    
    dummy_solutions = [
        "EXAMPLE",
        "TESTING",
        "DUMMYDATA",
        "PLACEHOLDER",
        "MOCKRESULT"
    ]
    
    # Select a solution based on properties of the clue
    solution_index = (word_count + clue_length) % len(dummy_solutions)
    selected_solution = dummy_solutions[solution_index]
    
    return {
        "attempted_solutions": [
            {
                "solution": "PARTIAL",
                "definition": "First attempt at definition",
                "wordplay_components": [
                    {
                        "indicator": "test",
                        "wordplay_type": "anagram",
                        "target": "dummy"
                    }
                ]
            }
        ],
        "complete_solution": {
            "solution": selected_solution,
            "definition": f"Test definition for {selected_solution.lower()}",
            "wordplay_components": [
                {
                    "indicator": "test indicator",
                    "wordplay_type": "charade",
                    "target": "test target"
                },
                {
                    "indicator": "dummy",
                    "wordplay_type": "anagram",
                    "target": "words from clue"
                }
            ]
        },
        "confidence": 0.8
    }

def load_prompt_template():
    """Load the main prompt template from file."""
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'main_prompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback prompt if file not found
        return """You are an expert at solving cryptic crossword clues. 
        
                Analyze the following cryptic crossword clue step by step:

                Clue: {clue}

                Provide a detailed analysis with wordplay breakdown."""

def get_openai_solution(clue):
    """Use OpenAI's API to solve the cryptic crossword clue with structured output."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "error": "OpenAI API key not found. Set OPENAI_API_KEY in .env file.",
            "error_code": "API_ERROR",
            "suggestions": ["Add OPENAI_API_KEY to your .env file"]
        }
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = load_prompt_template().format(clue=clue)
    
    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "functions": [OPENAI_FUNCTION_SCHEMAS["solve_cryptic_clue"]],
        "function_call": {"name": "solve_cryptic_clue"},
        "temperature": 0.3
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract structured response from function call
        if "choices" in result and result["choices"]:
            choice = result["choices"][0]
            if "message" in choice and "function_call" in choice["message"]:
                function_call = choice["message"]["function_call"]
                if function_call["name"] == "solve_cryptic_clue":
                    return json.loads(function_call["arguments"])
        """
        # Fallback to regular response if function calling failed
        if "choices" in result and result["choices"]:
            content = result["choices"][0]["message"]["content"]
            return parse_unstructured_response(content)
        """ 
        return {
            "error": "Unexpected response format from OpenAI",
            "error_code": "PARSING_ERROR"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "error_code": "API_ERROR"
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse response: {str(e)}",
            "error_code": "PARSING_ERROR"
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "error_code": "UNKNOWN"
        }
"""
def parse_unstructured_response(content):

    lines = content.strip().split('\n')
    solution = ""
    explanation = ""
    
    # Simple parsing - look for "Solution:" patterns
    for i, line in enumerate(lines):
        if line.lower().startswith('solution:'):
            solution = line.split(':', 1)[1].strip()
        elif line.lower().startswith('explanation:'):
            explanation = '\n'.join(lines[i:]).split(':', 1)[1].strip()
            break
    
    return {
        "attempted_solutions": [],
        "complete_solution": {
            "solution": solution or "Could not parse solution",
            "definition": "Parsed from unstructured response",
            "wordplay_components": [
                {
                    "indicator": "parsed",
                    "wordplay_type": "other",
                    "target": "unstructured text"
                }
            ]
        },
        "confidence": 0.5
    }
"""
def get_claude_solution(clue):
    """Use Anthropic's Claude API to solve the cryptic crossword clue with structured output."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "error": "Anthropic API key not found. Set ANTHROPIC_API_KEY in .env file.",
            "error_code": "API_ERROR",
            "suggestions": ["Add ANTHROPIC_API_KEY to your .env file"]
        }
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    # Load prompt template and insert the clue
    prompt = load_prompt_template().format(clue=clue)
    
    data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [{"role": "user", "content": prompt}],
        "tools": ANTHROPIC_TOOL_SCHEMAS,
        "tool_choice": {"type": "tool", "name": "solve_cryptic_clue"},
        "max_tokens": 1500,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        
        # Extract structured response from tool use
        if "content" in result:
            for content_block in result["content"]:
                if content_block.get("type") == "tool_use" and content_block.get("name") == "solve_cryptic_clue":
                    return content_block["input"]
        """"
        # Fallback to parsing text content
        if "content" in result and result["content"]:
            text_content = ""
            for content_block in result["content"]:
                if content_block.get("type") == "text":
                    text_content += content_block.get("text", "")
            
            if text_content:
                return parse_unstructured_response(text_content)
        """
        return {
            "error": "Unexpected response format from Claude",
            "error_code": "PARSING_ERROR"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "error_code": "API_ERROR"
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse response: {str(e)}",
            "error_code": "PARSING_ERROR"
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "error_code": "UNKNOWN"
        }