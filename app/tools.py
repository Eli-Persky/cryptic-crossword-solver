from typing import Dict, List, Optional, TypedDict, Annotated
import re
import itertools
from langchain_core.tools import tool
from .utils import check_given_letters

# Tools for the agent
@tool
def generate_anagrams(text: str, target_length: Optional[int] = None) -> List[str]:
    """Generate all possible anagrams of the given text."""
    # Convert to lowercase, and remove non-letter characters
    letters = re.sub(r'[^a-zA-Z]', '', text.lower())
    
    # If target_length is specified, only generate anagrams of that length
    if target_length:
        if len(letters) != target_length:
            return []
    
    # Generate permutations - simplified approach without dictionary validation
    # This will be enhanced when dictionary API is added
    anagrams = []
    
    # For longer words, only generate a subset to avoid too many permutations
    max_perms = 100 if len(letters) > 6 else 500
    
    count = 0
    for perm in itertools.permutations(letters):
        if count >= max_perms:
            break
        anagram = ''.join(perm)
        anagrams.append(anagram.upper())
        # Could use this filtering to help prioritse anagrams in limited selection
        # Basic filtering - avoid anagrams with 4 consecutive consonants (usually useless)
        #if not re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', word) and word.upper() not in anagrams:
        #    anagrams.append(word.upper())
        count += 1
    
    return anagrams

@tool
def get_definitions(word: str) -> List[str]:
    """Retrieve all meanings of a word. Used to check if a word has an appropriate meaning for its use in the solution, either as a synonym, an indicator or as the solution definition."""
    # Will be replaced with proper dictionary API
    return []

@tool
def find_hidden_words(phrase: str, target_length: int) -> List[str]:
    """Find words hidden within a phrase of a target length. Used for clues where the solution is hidden with a phrase in the clue."""
    # Remove spaces and punctuation
    words = phrase.split()
    earliest_end = sum([len(re.sub(r'[^a-zA-Z]', '', word)) for word in words[:-1]]) + 1 # Hidden word must use all words in input
    
    clean_phrase = re.sub(r'[^a-zA-Z]', '', phrase.lower())

    substrings = []
    start_idx = min([earliest_end - target_length - 1, 0])
    while start_idx + target_length < len(clean_phrase):
        substring = clean_phrase[start_idx:start_idx + target_length]
        substrings += [substring]
    
    return substrings

@tool
def reverse_word(word: str) -> str:
    """Reverse a word."""
    return word[::-1].upper()

@tool
def check_given_letters_tool(word: str, givens: dict[int, str] = {}) -> bool:  ## TODO: have the givens passed automatically
    """Check if the word contains the correct given letters."""
    return check_given_letters(word, givens)
