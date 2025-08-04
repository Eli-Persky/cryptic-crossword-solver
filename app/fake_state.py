"""
Hardcoded fake LangGraph state for UI testing.
This provides realistic example data as if it came from the actual algorithm.
"""
from .state import SolverState, CurrentAttemptState, SolutionAttempt, WordPlayComponent


def get_fake_langgraph_state(clue: str = "Initially irritated, raised uproar about drink that's tasteless", 
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
            description="Indicates selecting the first letter",
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
            result="INSIPID",
            targeted_by=None,
            messages=[]
        )
    )
    wrong_components = []
    wrong_components.append(wordplay_components[-1])

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

    attempt1 = SolutionAttempt(
        solution="INSIPID",
        definition_part="tasteless",
        wordplay_analysis=wordplay_components[:3],  # Only first 3 components analyzed
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


def get_fake_ui_response(clue: str = "Initially irritated, raised uproar about drink that's tasteless",
                        target_length: int = 7) -> dict:
    """
    Returns fake data in the exact format expected by the UI.
    This is what would be returned by the /solve endpoint.
    """
    
    # Get the fake state
    state = get_fake_langgraph_state(clue, target_length)
    
    # Convert to UI format
    attempted_solutions = []
    for attempt in state["solution_attempts"]:  # All attempts including final
        ui_attempt = {
            "solution": attempt["solution"],
            "definition": attempt["definition_part"],
            "wordplay_components": [
                {
                    "indicator": comp["text"],
                    "wordplay_type": comp["wordplay_type"],
                    "target": comp.get("result", ""),
                    "description": comp["description"]
                }
                for comp in attempt["wordplay_analysis"]
            ]
        }
        attempted_solutions.append(ui_attempt)
    
    # Final solution
    final_solution = state["final_solution"]
    if not final_solution:
        return {"error": "No final solution available"}
        
    complete_solution = {
        "solution": final_solution["solution"],
        "definition": final_solution["definition_part"],
        "wordplay_components": [
            {
                "indicator": comp["text"],
                "wordplay_type": comp["wordplay_type"], 
                "target": comp.get("result", ""),
                "description": comp["description"]
            }
            for comp in final_solution["wordplay_analysis"]
        ]
    }
    
    # Create interactive clue mapping for UI
    clue_words = clue.split()
    word_mapping = []
    
    for i, word in enumerate(clue_words):
        # Find the component that corresponds to this word position
        component = None
        for comp in final_solution["wordplay_analysis"]:
            if comp["start_pos"] <= i <= comp["end_pos"]:
                component = comp
                break
        
        if component:
            # Find related words (targets or indicators)
            related_positions = []
            
            # If this is an indicator, find what it targets
            if component["role"] == "indicator":
                for comp in final_solution["wordplay_analysis"]:
                    targeted_by = comp.get("targeted_by")
                    if (targeted_by is not None and 
                        targeted_by["start_pos"] == component["start_pos"] and
                        targeted_by["end_pos"] == component["end_pos"]):
                        for pos in range(comp["start_pos"], comp["end_pos"] + 1):
                            related_positions.append(pos)
            
            # If this is a target, find its indicator
            elif component.get("targeted_by") is not None:
                indicator = component["targeted_by"]
                if indicator is not None:
                    for pos in range(indicator["start_pos"], indicator["end_pos"] + 1):
                        related_positions.append(pos)
            
            # Remove duplicates and current position
            related_positions = list(set(related_positions))
            if i in related_positions:
                related_positions.remove(i)
            
            word_info = {
                "word": word,
                "position": i,
                "role": component["role"],
                "wordplay_type": component["wordplay_type"],
                "description": component["description"],
                "result": component.get("result", ""),
                "related_positions": related_positions,
                "component_id": f"comp_{component['start_pos']}_{component['end_pos']}"
            }
        else:
            # Word not part of any component (likely connectors)
            word_info = {
                "word": word,
                "position": i,
                "role": "connector",
                "wordplay_type": "none",
                "description": "Connecting word",
                "result": "",
                "related_positions": [],
                "component_id": None
            }
        
        word_mapping.append(word_info)
    
    
    return {
        "attempted_solutions": attempted_solutions,
        "complete_solution": complete_solution,
        "interactive_clue": {
            "original_clue": clue,
            "word_mapping": word_mapping
        }
    }


# Additional fake states for different scenarios
def get_fake_unsolved_state() -> dict:
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
