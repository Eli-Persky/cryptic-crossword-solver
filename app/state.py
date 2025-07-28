from typing import Dict, List, Optional, TypedDict, Annotated, Tuple
from langgraph.graph.message import add_messages

class WordPlayComponent(TypedDict):
    """Analysis of a word or phrase in the clue."""
    text: str
    start_pos: int
    end_pos: int
    role: str  # 'definition', 'indicator', 'target', 'synonym', 'unknown'
    wordplay_type: str  # 'anagram', 'container', etc.
    description: str  # Additional description of the role
    result: Optional[str]  # Result of the wordplay, if applicable
    targeted_by: Optional['WordPlayComponent']  # If this component's role is target, which component is the indicator
    messages: Annotated[list, add_messages]


class SolutionAttempt(TypedDict):
    """A single attempt at solving the clue."""
    solution: str
    definition_part: str
    wordplay_analysis: List[WordPlayComponent]

class CurrentAttemptState(TypedDict):
    """State of the current attempt at solving the clue."""
    solution_attempt: Optional[SolutionAttempt]
    current_component: Optional[WordPlayComponent] # The component currently being analysed
    remaining_word_idxs: List[int]
    possible_target_idxs: List[int] 

class SolverState(TypedDict):
    """State for the LangGraph solver."""
    clue: str
    clue_words: List[str]
    target_length: Optional[int]
    given_letters: dict[int, str]
    word_analyses: Dict[Tuple[int, int], List[WordPlayComponent]]
    solution_attempts: List[SolutionAttempt]
    current_attempt: Optional[CurrentAttemptState]
    max_attempts: int
    final_solution: Optional[SolutionAttempt]
    solved: bool
    stage: str