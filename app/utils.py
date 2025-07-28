from typing import Optional, List, Dict
import re

def check_given_letters(word: str, givens: Dict[int, str] = {}) -> bool:
    """Check if the word contains the correct given letters."""
    for position, letter in givens.items():
        if word[position].upper() != letter.upper():
            return False
    return True

def clean_wiktionary_string(s: str) -> str:
    # Remove all HTML tags, including those with attributes
    filter_re = re.compile(r'<[^>]+>', re.IGNORECASE)
    s = filter_re.sub('', s)
    s = s.replace('&nbsp;', ' ')
    return s