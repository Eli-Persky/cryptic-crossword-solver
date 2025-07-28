from typing import List, Dict, Optional, Tuple
from .state import SolverState, WordPlayComponent, SolutionAttempt

def generate_analyse_component_prompt(state: SolverState, tool_results: List[Dict]) -> str:    
    # Give LLM context including clue, solved components, ideas relating to the current component which are sourced from state["word_analyses"][word_idx]
    if not state["current_attempt"]:
            return ""
            
    attempt = state["current_attempt"]
    solution_attempt = attempt["solution_attempt"]
    if not solution_attempt:
        return ""
        
    current_component = attempt["current_component"]
    if not current_component:
        return ""
    
    clue_text = state["clue"]
    clue_words = state["clue_words"]
    target_length = state["target_length"]
    given_letters = state["given_letters"]

    chosen_solution = solution_attempt["solution"]
    definition = solution_attempt["definition_part"]

    start_idx = current_component["start_pos"]
    end_idx = current_component["end_pos"]
    
    # Get previous analyses for this word if any exist
    previous_analyses = state["word_analyses"].get((start_idx, end_idx), [])
    
    # Build context for the LLM
    context_parts = [
        f"Cryptic crossword clue: '{clue_text}'",
        f"Word being analyzed: '{current_component['text']}'",
    ]

    # Add tool results to context if available
    if tool_results:
        context_parts.append("Tool Results:")
        for result in tool_results:
            context_parts.append(f"  {result['tool_name']}: {result['result']}")

    solution_in_context = False
    length_in_context = False
    givens_in_context = False
    previous_analyses_in_context = False
    other_components_in_context = False
    
    if chosen_solution and definition:
        context_parts.append(f"Solution: '{chosen_solution}'")
        context_parts.append(f"Definition: '{definition}'")
        solution_in_context = True
    else:
        if target_length:
            context_parts.append(f"Target solution length: {target_length} letters")
            length_in_context = True
        if given_letters:
            given_str = ", ".join([f"position {pos}: '{letter}'" for pos, letter in given_letters.items()])
            context_parts.append(f"Given letters: {given_str}")
            givens_in_context = True
        
    if previous_analyses:
        previous_analyses_in_context = True
        context_parts.append("Previous analyses of this word:")
        for i, analysis in enumerate(previous_analyses):
            context_parts.append(f"  {i+1}. Role: {analysis['role']}, Type: {analysis['wordplay_type']}, Description: {analysis['description']}")
    
    # Add context about other analyzed components
    if solution_attempt and solution_attempt["wordplay_analysis"]:
        other_components = [comp for comp in solution_attempt["wordplay_analysis"][:-1] if comp["role"]]
        if other_components:
            other_components_in_context = True
            context_parts.append("Other analyzed components in current attempt:")
            for comp in other_components:
                context_parts.append(f"  '{comp['text']}': {comp['role']} ({comp['wordplay_type']})")
    
    context = "\n".join(context_parts)
    definition_line = "" if solution_in_context else "-definition: The straightforward definition part of the clue. This must either appear at the beginning or end of the clue\n"
    use_givens_line = "" if not givens_in_context else "Your analysis of this component should consider whether the result will help lead to a solution with the correct given letters.\n"
    use_others_line = "" if not other_components_in_context else "Your analysis of this component should consider how it relates to other analysed components in the current solution attempt.\n"
    use_previous_line = "" if not previous_analyses_in_context else "You may consider if any of the provided previous analysis of this component is useful for the current solution attempt.\n"

    # The LLM must return structured output in order to populate the role, wordplay type and description of the current component
    try:
        with open("app/prompts/analyse_comp_sys_nt.txt") as f:
            system_prompt = f.read().strip().format(
                definition_line=definition_line,
                use_givens_line=use_givens_line,
                use_others_line=use_others_line,
                use_previous_line=use_previous_line
            )
    except FileNotFoundError:
        print("Error: Prompt file not found. Please ensure 'analyse_comp_sys_nt.txt' exists in the prompts directory.")
        return ""
    
    user_prompt = f"{context}\n\nAnalyze the word '{current_component['text']}' within the clue and provide its role, wordplay_type, and description."
    
    # Make LLM call with tools available through the message system
    full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nRespond in the format:\nRole: [role]\nWordplay Type: [wordplay_type]\nResult: [result]\nDescription: [description]\n\nYou have access to these tools that may help with your analysis:\n- generate_anagrams(text): Generate anagrams from letters\n- get_meanings(word): Get word meanings  \n- find_hidden_words(phrase, target_length): Find hidden words in phrases\n- reverse_word(word, givens): Reverse a word\n- check_given_letters_tool(word): Check if a proposed solution has the correct given letters\n\nIf you need to use tools, make the tool calls first, then provide your analysis based on the results."

    if tool_results:
        # If tool results are available, include them in the final prompt
        tool_context = "\n".join([f"Tool result: {result['result']}" for result in tool_results])
        full_prompt += f"\n\n{tool_context}\n\nBased on these tool results, provide your final analysis:"
    
    return full_prompt


def generate_find_target_prompt(state: SolverState, indicator_component: WordPlayComponent, tool_results: List[Dict]) -> str:
     # Get available target candidates from remaining words and synonyms
     # TODO: Tidy this up and add conditional prompt sentences based on context
    current_attempt = state["current_attempt"]
    if not current_attempt:
        return ""
    solution_attempt = current_attempt["solution_attempt"]
    if not solution_attempt:
        return ""
    
    clue_words = state["clue_words"]
    possible_target_idxs = current_attempt["possible_target_idxs"]
    
    # Build candidate text for LLM analysis
    candidates = []
    for idx in possible_target_idxs:
        if idx < len(clue_words):
            candidates.append(f"{idx}: {clue_words[idx]}")
    
    # Create prompt for target identification
    wordplay_type = indicator_component["wordplay_type"]
    indicator_text = indicator_component["text"]
    
    context_parts = []

    if tool_results:
        context_parts.append("Tool Results:")
        for result in tool_results:
            context_parts.append(f"  {result['tool_name']}: {result['result']}")

    chosen_solution = solution_attempt["solution"]
    definition = solution_attempt["definition_part"]
    target_length = state["target_length"]
    given_letters = state["given_letters"]
    if chosen_solution and definition:
        context_parts.append(f"Solution: '{chosen_solution}'")
        context_parts.append(f"Definition: '{definition}'")
        solution_in_context = True
    else:
        if target_length:
            context_parts.append(f"Target solution length: {target_length} letters")
            length_in_context = True
        if given_letters:
            given_str = ", ".join([f"position {pos}: '{letter}'" for pos, letter in given_letters.items()])
            context_parts.append(f"Given letters: {given_str}")
            givens_in_context = True
                
    # Add context about other analyzed components
    if solution_attempt and solution_attempt["wordplay_analysis"]:
        other_components = [comp for comp in solution_attempt["wordplay_analysis"][:-1] if comp["role"]]
        if other_components:
            other_components_in_context = True
            context_parts.append("Other analyzed components in current attempt:")
            for comp in other_components:
                context_parts.append(f"  '{comp['text']}': {comp['role']} ({comp['wordplay_type']})")
    context = "\n".join(context_parts)
    prompt = f"""
You are analyzing a cryptic crossword clue: "{' '.join(clue_words)}"

The word "{indicator_text}" has been identified as an INDICATOR for {wordplay_type} wordplay.

Available target candidates:
{chr(10).join(candidates)}

{context}

You can use tools to help analyze the candidates (generate anagrams, find meanings, etc.) before making your decision.

If you need more information, call the appropriate tools. Otherwise, identify the target and provide your analysis.

When ready to provide your final answer, respond in this exact format:
Target Index: [number]
Target Text: [the actual word/phrase]
Role: [target/synonym]
Wordplay Type: {wordplay_type}
Result: [result of applying the wordplay]
Description: [brief explanation of the wordplay operation]
"""
    
    return prompt