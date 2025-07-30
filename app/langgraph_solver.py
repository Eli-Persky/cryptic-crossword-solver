from typing import Dict, Optional
import random

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .tools import generate_anagrams, get_meanings, find_hidden_words, reverse_word, check_given_letters
from .state import SolverState, CurrentAttemptState, SolutionAttempt, WordPlayComponent
from .prompt_generation import generate_analyse_component_prompt, generate_find_target_prompt

class CrypticCrosswordSolver:
    """LangGraph-based cryptic crossword solver."""
    
    def __init__(self, openai_api_key):
        
        # Create tools nodes
        self.tools = [
            generate_anagrams,
            get_meanings,
            find_hidden_words,
            reverse_word,
            # Lookup synonyms
        ]
        self.tool_node = ToolNode(self.tools)

        # Create the LLM with tools bound
        self.llm = ChatOpenAI(
            model="gpt-4o",
            api_key=openai_api_key,
            temperature=0.2
        ).bind_tools(self.tools)
       
        # Build the graph
        self.graph = self._build_graph()
        return

    def save_graph(self):
        """Save the LangGraph state graph as png."""
        if self.graph:
            self.graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
    
    def _build_graph(self):
        """Build the LangGraph state graph."""
        workflow = StateGraph(SolverState)
        
        # Add nodes
        workflow.add_node("generate_solution", self._generate_solution)
        workflow.add_node("decide_continue_attempt", lambda state: state)
        workflow.add_node("analyse_component", self._analyse_component)
        workflow.add_node("decide_use_tools_a", lambda state: state)
        workflow.add_node("decide_search_for_target", lambda state: state)
        workflow.add_node("find_target", self._find_target)
        workflow.add_node("verify_solution", self._verify_solution)
        workflow.add_node("decide_use_tools_v", lambda state: state)
        workflow.add_node("decide_next", lambda state: state)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("return_from_tools", lambda state: state)
        workflow.add_node("finalize", lambda state: state)
        workflow.add_node("decide_use_tools_f", lambda state: state)
        
        # Set entry point
        workflow.set_entry_point("generate_solution")
        
        # Add edges
        workflow.add_edge("generate_solution", "decide_continue_attempt")
        workflow.add_conditional_edges(
            "decide_continue_attempt",
            self._decide_continue_attempt,
            {
                "continue": "analyse_component",  # Recurrent edge
                "stop": "verify_solution"
            }
        )
        workflow.add_edge("analyse_component", "decide_use_tools_a")
        workflow.add_conditional_edges(
            "decide_use_tools_a",
            self._decide_use_tools,
            {
                "use_tools": "tools",
                "skip_tools": "decide_search_for_target"
            }
        )

        workflow.add_conditional_edges(
            "decide_search_for_target",
            self._decide_search_for_target,
            {
                "continue": "find_target",
                "stop": "generate_solution"
            }
        )

        workflow.add_edge("find_target", "decide_use_tools_f")
        workflow.add_conditional_edges(
            "decide_use_tools_f",
            self._decide_use_tools,
            {
                "use_tools": "tools",
                "skip_tools": "generate_solution"
            }
        )
        
        workflow.add_edge("verify_solution", "decide_use_tools_v")
        workflow.add_conditional_edges(
            "decide_use_tools_v",
            self._decide_use_tools,
            {
                "use_tools": "tools",
                "skip_tools": "decide_next"
            }
        )
        workflow.add_conditional_edges(
            "return_from_tools",
            lambda state: state["stage"],
            {
                "analyse_component": "analyse_component",
                "find_target": "find_target",
                "verify_solution": "verify_solution"
            }
        )
        
        workflow.add_edge("tools", "return_from_tools")
        
        workflow.add_conditional_edges(
            "decide_next",
            self._decide_next,
            {
                "stop": "finalize",
                "continue": "generate_solution"  # Recurrent edge
            }
        )

        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _generate_solution(self, state: SolverState) -> SolverState:
        """Generate a solution attempt based on current analysis."""
        state["messages"] = []  # Clear messages for a new attempt
        # Select words or sets of words from the clue to be sent on for analysis and populate current_component_to_analyse
        clue = state["clue_words"]
        if state["current_attempt"] is None:
            # Initialize the current attempt state
            state["current_attempt"] = CurrentAttemptState(
                solution_attempt=None,
                current_component=None,
                remaining_word_idxs=list(range(len(clue))),
                possible_target_idxs=list(range(len(clue))),
            )

        attempt_data = state["current_attempt"]
        if attempt_data["solution_attempt"] is None:
            # Create a new solution attempt
            attempt_data["solution_attempt"] = SolutionAttempt(
                solution="",
                definition_part="",
                wordplay_analysis=[],
                clue_with_synonyms=state["clue_words"]
            )

        if not attempt_data["remaining_word_idxs"]:
            attempt_data["current_component"] = None
            return state

        component_idx = random.choice(attempt_data["remaining_word_idxs"]) # TODO: Allow multiword selection
        word_to_analyse = clue[component_idx].strip(",.:;").strip()

        new_component = WordPlayComponent(
            text=word_to_analyse,
            start_pos=component_idx,
            end_pos=component_idx,
            role="",
            wordplay_type="",
            targeted_by=None,
            result=None,
            description="",
            messages=[]
        )
        
        # Set this as the current component to be analyzed
        attempt_data["current_component"] = new_component
        
        return state
    
    def _decide_continue_attempt(self, state: SolverState) -> str:
        """Check if the attempt is finished."""
        #  TODO: Need more robust way to decide to end attempt even if not all words are solved
        current_attempt = state["current_attempt"]
       
        if current_attempt is None or current_attempt["current_component"] is None:
            return "stop"  # No component to analyse
        
        if not current_attempt["remaining_word_idxs"]:
            return "stop"
        
        for idx in current_attempt["remaining_word_idxs"]:
            if state["clue_words"][idx].strip().lower() not in ["a", "an", "the", "of", "in", "on", "at", "to", "for", "with", "by", "is", "that's"]:
                return "continue"
        
        return "continue"  # Continue with the current component
    
    def _parse_component_response(self, response_text: str) -> tuple[str, str, Optional[str], str]:
        """Parse LLM response for component analysis."""
        role = "unknown"
        wordplay_type = "unknown" 
        result = None
        description = "No description provided"
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("Role:"):
                role = line.replace("Role:", "").strip().lower()
            elif line.startswith("Wordplay Type:"):
                wordplay_type = line.replace("Wordplay Type:", "").strip().lower()
            elif line.startswith("Result:"):
                result = line.replace("Result:", "").strip().upper()
                if result == "":
                    result = None
            elif line.startswith("Description:"):
                description = line.replace("Description:", "").strip().lower()
        
        return role, wordplay_type, result, description
    
    def _update_component_analysis(self, state: SolverState, current_component: WordPlayComponent, 
                                 role: str, wordplay_type: str, result: Optional[str], description: str) -> None:
        """Update the current component with analysis results and update state accordingly."""
        current_component["role"] = role
        current_component["wordplay_type"] = wordplay_type  
        current_component["description"] = description
        current_component["result"] = result
        
        if role != 'unknown' and wordplay_type != 'unknown':
            attempt = state["current_attempt"]
            if not attempt or not attempt["solution_attempt"]:
                return
                
            solution_attempt = attempt["solution_attempt"]
            start_idx = current_component["start_pos"]
            end_idx = current_component["end_pos"]
            
            # Append component to the state["word_analyses"][(start_idx, end_idx)] for future reference
            if (start_idx, end_idx) not in state["word_analyses"]:
                state["word_analyses"][(start_idx, end_idx)] = []
            
            state["word_analyses"][(start_idx, end_idx)].append(current_component)
            solution_attempt["wordplay_analysis"].append(current_component)
            
            if role == 'definition' and result:
                solution_attempt["definition_part"] = current_component["text"]
                solution_attempt["solution"] = result.upper()
            elif role == "synonym" and result:
                # Replace the word in the clue with the synonym
                clue_with_syn = solution_attempt["clue_with_synonyms"]
                clue_with_syn[start_idx] = result.upper()
                if end_idx > start_idx:
                    for idx in range(start_idx + 1, end_idx + 1):
                        clue_with_syn[idx] = ""
            
            # Remove this word from remaining_word_idxs since it's been analyzed
            for idx in range(start_idx, end_idx + 1):
                if idx in attempt["remaining_word_idxs"]:
                    attempt["remaining_word_idxs"].remove(idx)
                if role != 'synonym' and idx in attempt["possible_target_idxs"]:
                    attempt["possible_target_idxs"].remove(idx)
    
    def _analyse_component(self, state: SolverState) -> SolverState:
        """Determine the role and worplay type of the selected word or phrase and finish populating current_component"""
        if not state["current_attempt"] or not state["current_attempt"]["solution_attempt"]:
            return state
            
        attempt = state["current_attempt"]
        solution_attempt = attempt["solution_attempt"]
        current_component = attempt["current_component"]
        if not solution_attempt or not current_component:
            return state
        state["stage"] = "analyse_component"
        state_messages = state.get("messages", [])
        tool_results = []
        
        # Check if we have tool results to process
        if state_messages:
            # Process any tool call results - look for ToolMessage objects or messages with tool content
            for msg in state_messages:
                # Check for ToolMessage type from LangChain
                if str(type(msg).__name__) == 'ToolMessage':
                    tool_results.append({
                        'tool_name': getattr(msg, 'name', 'unknown_tool'),
                        'result': msg.content
                    })
                # Also check for messages with tool_call_id (alternative structure)
                elif hasattr(msg, 'tool_call_id'):
                    tool_results.append({
                        'tool_name': getattr(msg, 'name', 'unknown_tool'),
                        'result': msg.content
                    })

        full_prompt = generate_analyse_component_prompt(state, tool_results)
        if not full_prompt:
            return state  # No prompt generated, skip analysis

        try:
            messages = [HumanMessage(content=full_prompt)]
            response = self.llm.invoke(messages)
            
            # If we have tool results, process them and provide final response
            if tool_results:
                # We have tool results, so process the final response
                if hasattr(response, 'content'):
                    response_text = str(response.content).strip()
                else:
                    response_text = str(response).strip()
                
                # Parse and update the component
                role, wordplay_type, result, description = self._parse_component_response(response_text)
                self._update_component_analysis(state, current_component, role, wordplay_type, result, description)
                
                # Clear messages after processing
                state["messages"] = []
            else:
                # No tool results yet - check if response contains tool calls
                if hasattr(response, 'additional_kwargs') and 'tool_calls' in response.additional_kwargs:
                    # LLM wants to call tools - add to messages and let tools node handle it
                    state["messages"] = messages + [response]
                else:
                    # No tool calls needed - process the response directly
                    if hasattr(response, 'content'):
                        response_text = str(response.content).strip()
                    else:
                        response_text = str(response).strip()
                    
                    # Parse and update the component
                    role, wordplay_type, result, description = self._parse_component_response(response_text)
                    self._update_component_analysis(state, current_component, role, wordplay_type, result, description)
                    
                    # Clear messages after processing
                    state["messages"] = []

        except Exception as e:
            # Fallback if LLM call fails
            current_component["role"] = "unknown"
            current_component["wordplay_type"] = "unknown"
            current_component["description"] = f"Analysis failed: {str(e)}"
            # Clear messages even on error
            state["messages"] = []
        
        return state
    
    def _decide_use_tools(self, state: SolverState) -> str:
        """Decide whether to use tools in component analysis or skip to target search."""
        current_attempt = state["current_attempt"]
        if not current_attempt or not current_attempt["current_component"]:
            state["messages"] = []
            return "skip_tools"
        
        messages = state.get("messages", [])
        
        # Check if there are pending tool calls in the messages
        if messages:
            msg = messages[-1]
            if hasattr(msg, 'additional_kwargs') and 'tool_calls' in msg.additional_kwargs:
                # Found tool calls - let ToolNode handle them
                return "use_tools"
        
        # No tool calls found - clear messages and skip tools
        state["messages"] = []
        return "skip_tools" 
    
    def _parse_target_response(self, response_text: str) -> tuple[Optional[int], str, str, Optional[str], str]:
        """Parse LLM response for target finding."""
        target_idx = None
        target_text = ""
        role = "target"
        result = None
        description = ""
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("Target Index:"):
                try:
                    target_idx = int(line.replace("Target Index:", "").strip())
                except ValueError:
                    continue
            elif line.startswith("Target Text:"):
                target_text = line.replace("Target Text:", "").strip()
            elif line.startswith("Result:"):
                result = line.replace("Result:", "").strip().upper()
                if result == "":
                    result = None
            elif line.startswith("Role:"):
                role = line.replace("Role:", "").strip().lower()
                if role == "":
                    role = "target"
                elif role not in ["target", "synonym"]:
                    role = "unknown"
            elif line.startswith("Description:"):
                description = line.replace("Description:", "").strip()
        
        return target_idx, target_text, role, result, description
    
    def _update_target_analysis(self, state: SolverState, indicator_component: WordPlayComponent, 
                               target_component: WordPlayComponent, target_idx: Optional[int], 
                               target_text: str, role: str, result: Optional[str], description: str) -> None:
        """Update target component analysis and state accordingly."""
        current_attempt = state["current_attempt"]
        if not current_attempt:
            return
            
        possible_target_idxs = current_attempt["possible_target_idxs"]
        if target_idx is not None and target_idx in possible_target_idxs:
            # Update the indicator component with target information
            indicator_component["description"] += f" Targeting '{target_text}' at position {target_idx}"                
            
            target_component["text"] = target_text
            target_component["start_pos"] = target_idx
            target_component["end_pos"] = target_idx
            target_component["result"] = result
            target_component["role"] = role
            target_component["description"] = description               
            
            if target_idx in current_attempt["remaining_word_idxs"]:
                current_attempt["remaining_word_idxs"].remove(target_idx)
            if target_idx in current_attempt["possible_target_idxs"]:
                current_attempt["possible_target_idxs"].remove(target_idx)
    
    def _decide_search_for_target(self, state: SolverState) -> str:
        """Decide if the current component needs a target to be found in the clue."""
        current_attempt = state["current_attempt"]
        if not current_attempt:
            return "stop"
        
        solution_attempt = current_attempt["solution_attempt"]
        if not solution_attempt or not solution_attempt["wordplay_analysis"]:
            return "stop"
        
        current_component = current_attempt["current_component"]
        if not current_component:
            return "stop"
        
        # If the component is an indicator, we need to find its target
        if current_component["role"] == "indicator":
            return "continue"
        else:
            return "stop"
        
    def _find_target(self, state: SolverState) -> SolverState:
        """Find the target component for the current indicator."""
        current_attempt = state["current_attempt"]
        if not current_attempt or not current_attempt["current_component"]:
            return state
        
        solution_attempt = current_attempt["solution_attempt"]
        if not solution_attempt:
            return state
        
        current_component = current_attempt["current_component"]
        if not current_component or current_component["role"] not in ["indicator", "target"]:
            return state
        
        if current_component["targeted_by"] is not None:
            indicator_component = current_component["targeted_by"]
            target_component = current_component
        else:
            indicator_component = current_component
            target_component = WordPlayComponent(
                text="",
                start_pos=0,
                end_pos=0,
                role="target",
                wordplay_type=indicator_component["wordplay_type"],
                targeted_by=indicator_component,
                result=None,
                description="",
                messages=[]
            )
            current_attempt["current_component"] = target_component
        
        state["stage"] = "find_target"

        # Check if we have tool results to process
        state_messages = state.get("messages", [])
        tool_results = []
        if state_messages:
            # Process any tool call results - look for ToolMessage objects or messages with tool content
            for msg in state_messages:
                # Check for ToolMessage type from LangChain
                if str(type(msg).__name__) == 'ToolMessage':
                    tool_results.append({
                        'tool_name': getattr(msg, 'name', 'unknown_tool'),
                        'result': msg.content
                    })
                # Also check for messages with tool_call_id (alternative structure)
                elif hasattr(msg, 'tool_call_id'):
                    tool_results.append({
                        'tool_name': getattr(msg, 'name', 'unknown_tool'),
                        'result': msg.content
                    })

        prompt = generate_find_target_prompt(state, indicator_component, tool_results)
        if not prompt:
            return state 
        try:
            messages_to_send = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages_to_send)
            
            # If we have tool results, process them and provide final response
            if tool_results:
                # We have tool results, so process the final response
                response_text = str(response.content).strip()
                
                # Parse and update the target
                target_idx, target_text, role, result, description = self._parse_target_response(response_text)
                self._update_target_analysis(state, indicator_component, target_component, 
                                           target_idx, target_text, role, result, description)
                
                # Clear messages after processing
                state["messages"] = []
            else:
                # No tool results yet - check if response contains tool calls
                if hasattr(response, 'additional_kwargs') and 'tool_calls' in response.additional_kwargs:
                    # LLM wants to call tools - add to messages and let tools node handle it
                    state["messages"] = messages_to_send + [response]
                else:
                    # No tool calls needed - process the response directly
                    response_text = str(response.content).strip()
                    
                    # Parse and update the target
                    target_idx, target_text, role, result, description = self._parse_target_response(response_text)
                    self._update_target_analysis(state, indicator_component, target_component, 
                                               target_idx, target_text, role, result, description)
                    
                    # Clear messages after processing
                    state["messages"] = []
        
        except Exception as e:
            # Fallback: mark indicator as processed but don't create target
            indicator_component["description"] = f"Target identification failed: {str(e)}"
            current_attempt["current_component"] = None
            # Clear messages even on error
            state["messages"] = []
        
        return state
    
    def _verify_solution(self, state: SolverState) -> SolverState:
        """Verify the proposed solution."""
        if not state["current_attempt"]:
            state["solved"] = False
            return state
        
        solution = state["current_attempt"]["solution_attempt"]
        
        # Objective tests
        if not solution or not solution["solution"] or not solution["definition_part"]:
            state["solved"] = False
            return state
        state["stage"] = "verify_solution"
        state["solution_attempts"].append(solution)

        if state["target_length"] and len(solution["solution"]) != state["target_length"]:
            state["solved"] = False
            return state
        if not check_given_letters(solution["solution"], state["given_letters"]):
            state["solved"] = False
            return state
        
        wordplay_analysis = solution["wordplay_analysis"]
        for component in wordplay_analysis:
            # TODO: Test objective use of each wordplay component in constructing the solution
            pass
        
        # Test definition
        definition = solution["definition_part"]
        dictionary_meanings = get_meanings(solution["solution"])
        if not definition or not dictionary_meanings:
            state["solved"] = False
            return state
        
        # TODO: Call LLM to verify if the definition is a semantic match for one of the solution meanings
        
        # Test validity of wordplay
        wordplay_analysis = solution["wordplay_analysis"]
        for component in wordplay_analysis:
            # TODO: Call LLM to verify if the wordplay selection is valid, 
            pass
        state["solved"] = True  # If all tests pass, the solution is considered solved
        state["final_solution"] = solution
        return state
    
    def _decide_next(self, state: SolverState) -> str:
        """Check if the solution is solved."""
        if state["solved"]:
            return "stop"
        else:
            give_up = self.decide_give_up(state)
            if give_up:
                return "stop"
            else:
                return "continue"
            
    def decide_give_up(self, state: SolverState) -> bool:
        """Decide whether to continue iterating or finalize."""
        # TODO: add better logic for deciding to give up
        return len(state["solution_attempts"]) >= state["max_attempts"]
    
    def solve(self, clue: str, given_letters: dict[int, str], target_length: Optional[int] = None, max_iterations: int = 3) -> Dict:
        """Solve a cryptic crossword clue."""

        initial_state = SolverState(
            clue=clue,
            clue_words=clue.split(),
            target_length=target_length,
            given_letters=given_letters,
            solved=False,
            final_solution=None,
            max_attempts=max_iterations,
            current_attempt=None,
            solution_attempts=[],
            word_analyses={},
            stage="initial",
            messages=[]
        )
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Convert to the expected output format
        return final_state
