"""
Hardcoded fake LangGraph state for UI testing.
This provides realistic example data as if it came from the actual algorithm.
"""
from .state import SolverState, CurrentAttemptState, SolutionAttempt, WordPlayComponent
from .state_transformer import transform_state_to_ui_format


def get_mock_langgraph_state(clue: str = "Initially irritated, raised uproar about drink that's tasteless", 
                            target_length: int = 7) -> SolverState:
    """
    Returns a hardcoded fake LangGraph state that looks like it came from the actual solver.
    You can modify the data below to test different UI scenarios.
    """
    
    # Hardcoded wordplay components as if analyzed by the algorithm
    wordplay_components = []

    wordplay_components.append(
        WordPlayComponent(
            text="Initially",
            start_pos=0,
            end_pos=0,
            role="indicator",
            wordplay_type="selection",
            description="Indicates selection of the first letter",
            result=None,
            targeted_by=None,
            messages=[]
        )
    )
    wordplay_components.append(
        WordPlayComponent(
            text="irritated",
            start_pos=1,
            end_pos=1,
            role="target",
            wordplay_type="selection",
            description="First letter is selected",
            result="I",
            targeted_by=wordplay_components[0],
            messages=[]
        )
    )
    wordplay_components.append(
        WordPlayComponent(
            text="raised",
            start_pos=2,
            end_pos=2,
            role="indicator",
            wordplay_type="reversal",
            description="Indicates reversal in a down clue",
            result=None,
            targeted_by=None,
            messages=[]
        )
    )
    wordplay_components.append(
        WordPlayComponent(
            text="uproar",
            start_pos=3,
            end_pos=3,
            role="target",
            wordplay_type="synonym",
            description="DIN is a synonym for 'uproar' and is targeted by a reversal indicator",
            result="NID",
            targeted_by=wordplay_components[2],
            messages=[]
        )
    )
    wordplay_components.append(
        WordPlayComponent(
            text="about",
            start_pos=4,
            end_pos=4,
            role="indicator",
            wordplay_type="container",
            description="Container indicator - something goes around",
            result=None,
            targeted_by=None,
            messages=[]
        )
    )
    wordplay_components.append(
        WordPlayComponent(
            text="drink",
            start_pos=5,
            end_pos=5,
            role="target",
            wordplay_type="synonym",
            description="SIP is a synonym for 'drink' and is targeted by a container indicator",
            result="NSIPID",
            targeted_by=wordplay_components[4],
            messages=[]
        )
    )
    wordplay_components.append(
        WordPlayComponent(
            text="that's",
            start_pos=6,
            end_pos=6,
            role="indicator",
            wordplay_type="link word",
            description="Links the wordplay to the definition",
            result=None,
            targeted_by=None,
            messages=[]
        )
    )
    wordplay_components.append(
        WordPlayComponent(
            text="tasteless",
            start_pos=7,
            end_pos=7,
            role="definition",
            wordplay_type="definition",
            description="INSIPID is a synonym for 'tasteless'",
            result=None,
            targeted_by=None,
            messages=[]
        )
    )
    wrong_components = []
    wrong_components.append(
        WordPlayComponent(
            text="irritated",
            start_pos=1,
            end_pos=1,
            role="indicator",
            wordplay_type="anagram",
            description="Indicator of an anagram'",
            result="",
            targeted_by=None,
            messages=[]
        )
    )

    wrong_components.append(
        WordPlayComponent(
            text="raised",
            start_pos=2,
            end_pos=2,
            role="target",
            wordplay_type="anagram",
            description="Word to be anagrammed",
            result="AIDERS",
            targeted_by=wrong_components[0],
            messages=[]
        )
    )
    wrong_components.append(wordplay_components[-1])

    attempt1 = SolutionAttempt(
        solution="INSIPID",
        definition_part="tasteless",
        wordplay_analysis=wordplay_components[:3] + [wordplay_components[-1]], 
        clue_with_synonyms=clue.split()
    )

    attempt2 = SolutionAttempt(
        solution="INSIPID",
        definition_part="tasteless",
        wordplay_analysis=wrong_components,
        clue_with_synonyms=clue.split()
    )

    # Correct solution
    attempt3 = SolutionAttempt(
        solution="INSIPID", 
        definition_part="tasteless",
        wordplay_analysis=wordplay_components,  # All components analyzed
        clue_with_synonyms=["Initially", "irritated", "raised", "DIN", "about", "SIP", "that's", "tasteless"]
    )
    
    # Create the fake final state
    fake_state = SolverState(
        clue=clue,
        clue_words=clue.split(),
        target_length=target_length,
        given_letters={2: "N", 5: "P"},
        solved=True,
        final_solution=attempt3,
        max_attempts=3,
        current_attempt=None,
        solution_attempts=[attempt1, attempt2],
        word_analyses={},
        stage="finalized",
        messages=[]
    )
    
    return fake_state


def get_mock_ui_response(clue: str = "Initially irritated, raised uproar about drink that's tasteless",
                        target_length: int = 7) -> dict:
    """
    Returns fake data in the exact format expected by the UI.
    This is what would be returned by the /solve endpoint.
    """
    
    # Get the fake state
    state = get_mock_langgraph_state(clue, target_length)
    
    # Use the shared transformer to convert to UI format
    return transform_state_to_ui_format(state, clue)


# Additional fake states for different scenarios
def get_mock_unsolved_state() -> dict:
    """Returns a fake state where the solver couldn't find a solution."""
    return {
        "attempted_solutions": [
            {
                "solution": "",
                "definition": "",
                "wordplay_components": [
                    {
                        "indicator": "word1",
                        "wordplay_type": "unknown",
                        "target": "",
                        "description": "Could not determine role"
                    }
                ]
            }
        ],
        "complete_solution": None
    }
