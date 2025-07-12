import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global variables
LAST_API_CALL = 0  # Timestamp of the last API call
API_RATE_LIMIT = 5  # Minimum seconds between API calls

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
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
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
    Return a dummy solution for testing purposes.
    This avoids making actual API calls during development and testing.
    
    :param clue: The cryptic crossword clue as a string.
    :return: A dummy solution string.
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
    
    return f"""Solution: {selected_solution}
    
    Explanation: This is a dummy solution generated in test mode.
    The actual clue was: "{clue}"

    To use actual LLM solutions, disable TEST_MODE in your .env file."""

def get_openai_solution(clue):
    """Use OpenAI's API to solve the cryptic crossword clue."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: OpenAI API key not found. Set OPENAI_API_KEY in .env file."
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = f"""
    You are an expert at solving cryptic crossword clues. 
    Please solve the following cryptic crossword clue and explain your reasoning step by step.
    
    Clue: {clue}
    
    Provide your answer in this format:
    Solution: [answer word or phrase]
    Explanation: [your step-by-step reasoning]
    """
    
    data = {
        "model": "gpt-4", # Or "gpt-3.5-turbo" for a less expensive option
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3  # Lower temperature for more deterministic results
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        result = response.json()
        solution_text = result["choices"][0]["message"]["content"]
        return solution_text
    except Exception as e:
        return f"Error: {str(e)}"

def get_claude_solution(clue):
    """Use Anthropic's Claude API to solve the cryptic crossword clue."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: Anthropic API key not found. Set ANTHROPIC_API_KEY in .env file."
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    prompt = f"""
    You are an expert at solving cryptic crossword clues. 
    Please solve the following cryptic crossword clue and explain your reasoning step by step.
    
    Clue: {clue}
    
    Provide your answer in this format:
    Solution: [answer word or phrase]
    Explanation: [your step-by-step reasoning]
    """
    
    data = {
        "model": "claude-3-opus-20240229",  # Or use a different Claude model
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        solution_text = result["content"][0]["text"]
        return solution_text
    except Exception as e:
        return f"Error: {str(e)}"
    

    """Example clue: Initially irritated, rising uproar about drink, tasteless (7)"""