from typing import Optional, List, Dict

def check_given_letters(word: str, givens: Dict[int, str] = {}) -> bool:
    """Check if the word contains the correct given letters."""
    for position, letter in givens.items():
        if word[position].upper() != letter.upper():
            return False
    return True