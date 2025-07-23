"""
LangGraph-based cryptic crossword solver with recurrent analysis.
"""
from tkinter import Image
from typing import Dict, List, Optional, TypedDict, Annotated, cast
from dataclasses import dataclass
import random

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .tools import generate_anagrams, get_definitions, find_hidden_words, reverse_word, check_given_letters

class WordPlayComponent(TypedDict):
    """Analysis of a word or phrase in the clue."""
    text: str
    start_pos: int
    end_pos: int
    role: str  # 'definition', 'indicator', 'target', 'synonym', 'unknown'
    wordplay_type: str  # 'anagram', 'container', etc.
    description: str  # Additional description of the role

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
    messages: Annotated[list, add_messages]

class SolverState(TypedDict):
    """State for the LangGraph solver."""
    clue: str
    clue_words: List[str]
    target_length: Optional[int]
    given_letters: dict[int, str]
    word_analyses: List[WordPlayComponent]
    solution_attempts: List[SolutionAttempt]
    current_attempt: Optional[CurrentAttemptState]
    iteration_count: int
    max_iterations: int
    final_solution: Optional[SolutionAttempt]
    solved: bool

class CrypticCrosswordSolver:
    """LangGraph-based cryptic crossword solver."""
    
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            api_key=openai_api_key,
            temperature=0.3
        )
        
        # Create tools node
        self.tools = [
            generate_anagrams,
            get_definitions,
            find_hidden_words,
            reverse_word,
            # Lookup synonyms
        ]
        self.tool_node = ToolNode(self.tools)
        
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
        workflow.add_node("generate_solution", self._generate_solution) # Generate an attempt at a solution, one word r phrase at a time
        workflow.add_node("decide_continue_attempt", lambda state: state)
        workflow.add_node("analyse_component", self._analyse_component) # The selected word or phrase is assigned a role and wordplay type
        workflow.add_node("verify_solution", self._verify_solution) # Verify the proposed solution
        workflow.add_node("decide_next", lambda state: state) # Decide if solved, try another attempt or give up
        workflow.add_node("tools", self.tool_node) # Use tools to generate anagrams, definitions, etc.
        workflow.add_node("finalize", lambda state: state)
        
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

        workflow.add_edge("analyse_component", "tools")
        workflow.add_edge("tools", "analyse_component")
        workflow.add_edge("analyse_component", "generate_solution")

        workflow.add_edge("verify_solution", "tools")
        workflow.add_edge("tools", "verify_solution")
        workflow.add_edge("verify_solution", "decide_next")
        
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
        # Select words or sets of words from the clue to be sent on for analysis and populate current_component_to_analyse
        clue = state["clue_words"]

        if state["current_attempt"] is None:
            # Initialize the current attempt state
            state["current_attempt"] = CurrentAttemptState(
                solution_attempt=None,
                current_component=None,
                remaining_word_idxs=list(range(len(clue))),
                messages=[]
            )

        attempt_data = state["current_attempt"]
        if attempt_data["solution_attempt"] is None:
            # Create a new solution attempt
            attempt_data["solution_attempt"] = SolutionAttempt(
                solution="",
                definition_part="",
                wordplay_analysis=[]
            )
        attempt = attempt_data["solution_attempt"]

        if not attempt_data["remaining_word_idxs"]:
            attempt_data["current_component"] = None
            return state

        component_idx = random.choice(attempt_data["remaining_word_idxs"]) # TODO: Allow multiword selection
        word_to_analyse = clue[component_idx]

        attempt["wordplay_analysis"].append(
            WordPlayComponent(
                text=word_to_analyse,
                start_pos=component_idx,
                end_pos=component_idx,
                role="",
                wordplay_type="",
                description=""
            )
        )
        
        return state
    
    def _decide_continue_attempt(self, state: SolverState) -> str:
        """Check if the attempt is finished."""
        current_attempt = state["current_attempt"]
       
        if current_attempt is None or current_attempt["current_component"] is None:
            return "stop"  # No component to analyse
        else:
            return "continue"  # Continue with the current component
    
    def _analyse_component(self, state: SolverState) -> SolverState:
        """Determine the role and worplay type of the selected word or phrase and finish populating current_component"""
         # This is where the magic happens

         # Give LLM context including clue, solved components, ideas relating to the current component
        
        # TODO: Make LLM return structured output to populate the current_component

        # Add component to the current attempt and the state for future reference
        return state
    
    def _verify_solution(self, state: SolverState) -> SolverState:
        """Verify the proposed solution."""
        if not state["current_attempt"]:
            state["solved"] = False
            return state
        solution = state["current_attempt"]["solution_attempt"]
        
        # Objective tests
        if not solution or not solution["solution"]:
            state["solved"] = False
            return state
        
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
        dictionary_meanings = get_definitions(solution["solution"])
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
        state["iteration_count"] += 1
        return state["iteration_count"] >= state["max_iterations"]
    
    def solve(self, clue: str, given_letters: dict[int, str], target_length: Optional[int] = None, max_iterations: int = 3) -> Dict:
        """Solve a cryptic crossword clue."""

        initial_state = SolverState(
            clue=clue,
            clue_words=clue.split(),
            target_length=target_length,
            given_letters=given_letters,
            word_analyses=[],
            solution_attempts=[],
            current_attempt=None,
            iteration_count=0,
            max_iterations=max_iterations,
            final_solution=None,
            solved=False
        )
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Convert to the expected output format
        return final_state
