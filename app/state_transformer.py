"""
Utility functions for transforming LangGraph state into UI-compatible format.
This module provides functions to convert the internal solver state into the format expected by the frontend.
"""

def transform_state_to_ui_format(state, clue: str | None = None) -> dict:
    """
    Transform a LangGraph SolverState into the format expected by the UI.
    
    Args:
        state: The SolverState object from the LangGraph solver
        clue: Optional clue text (will use state.clue if not provided)
        
    Returns:
        dict: UI-compatible response format
    """
    if clue is None:
        clue = state.get("clue", "")
    
    # Convert solution attempts to UI format
    attempted_solutions = []
    for attempt in state.get("solution_attempts", []):
        # Filter and combine components: only show indicators and definitions
        # For indicators, include their target information
        filtered_components = []
        
        for comp in attempt["wordplay_analysis"]:
            if comp["role"] == "indicator":
                # Find the target component for this indicator by checking targeted_by relationship
                target_comp = None
                for target in attempt["wordplay_analysis"]:
                    targeted_by = target.get("targeted_by")
                    if (targeted_by is not None and 
                        targeted_by.get("start_pos") == comp["start_pos"] and
                        targeted_by.get("end_pos") == comp["end_pos"] and
                        targeted_by.get("text") == comp["text"]):
                        target_comp = target
                        break
                
                # Create combined component info
                component_info = {
                    "indicator": comp["text"],
                    "wordplay_type": comp["wordplay_type"],
                    "target": target_comp["text"] if target_comp else "",
                    "result": target_comp.get("result", "") if target_comp else "",
                    "description": comp["description"]
                }
                
                # Add target info to description if available
                if target_comp and target_comp.get("result"):
                    component_info["description"] += f" → '{target_comp['text']}' gives '{target_comp['result']}'"
                
                filtered_components.append(component_info)
                
            elif comp["role"] in ["definition", "link word"]:
                # Include definitions and link words as-is
                filtered_components.append({
                    "indicator": comp["text"],
                    "wordplay_type": comp["wordplay_type"],
                    "target": "",
                    "result": comp.get("result", ""),
                    "description": comp["description"]
                })
            # Skip standalone targets - they're now included with their indicators
        
        ui_attempt = {
            "solution": attempt["solution"],
            "definition": attempt["definition_part"],
            "wordplay_components": filtered_components
        }
        attempted_solutions.append(ui_attempt)
    
    # Process final solution
    final_solution = state.get("final_solution")
    complete_solution = None
    interactive_clue = None
    
    if final_solution:
        # Filter and combine components for final solution too
        filtered_final_components = []
        
        for comp in final_solution["wordplay_analysis"]:
            if comp["role"] == "indicator":
                # Find the target component for this indicator by checking targeted_by relationship
                target_comp = None
                for target in final_solution["wordplay_analysis"]:
                    targeted_by = target.get("targeted_by")
                    if (targeted_by is not None and 
                        targeted_by.get("start_pos") == comp["start_pos"] and
                        targeted_by.get("end_pos") == comp["end_pos"] and
                        targeted_by.get("text") == comp["text"]):
                        target_comp = target
                        break
                
                # Create combined component info
                component_info = {
                    "indicator": comp["text"],
                    "wordplay_type": comp["wordplay_type"],
                    "target": target_comp["text"] if target_comp else "",
                    "result": target_comp.get("result", "") if target_comp else "",
                    "description": comp["description"]
                }
                
                # Add target info to description if available
                if target_comp and target_comp.get("result"):
                    component_info["description"] += f" → '{target_comp['text']}' gives '{target_comp['result']}'"
                
                filtered_final_components.append(component_info)
                
            elif comp["role"] in ["definition", "link word"]:
                # Include definitions and link words as-is
                filtered_final_components.append({
                    "indicator": comp["text"],
                    "wordplay_type": comp["wordplay_type"],
                    "target": "",
                    "result": comp.get("result", ""),
                    "description": comp["description"]
                })
            # Skip standalone targets - they're now included with their indicators
            
        complete_solution = {
            "solution": final_solution["solution"],
            "definition": final_solution["definition_part"],
            "wordplay_components": filtered_final_components
        }
        
        # Create interactive clue mapping for UI
        if clue:
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
            
            interactive_clue = {
                "original_clue": clue,
                "word_mapping": word_mapping
            }
        else:
            interactive_clue = None
    
    return {
        "attempted_solutions": attempted_solutions,
        "complete_solution": complete_solution,
        "interactive_clue": interactive_clue
    }
