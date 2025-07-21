"""
LangGraph-based cryptic crossword solver with recurrent analysis.
"""
import os
import re
import itertools
from typing import Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

@dataclass
class WordAnalysis:
    """Analysis of a word or phrase in the clue."""
    text: str
    start_pos: int
    end_pos: int
    role: str  # 'definition', 'indicator', 'target', 'synonym', 'unknown'
    wordplay_type: Optional[str] = None  # 'anagram', 'container', etc.
    confidence: float = 0.0

@dataclass
class SolutionAttempt:
    """A single attempt at solving the clue."""
    solution: str
    definition_part: str
    wordplay_analysis: List[WordAnalysis]
    verification_score: float
    reasoning: str

class SolverState(TypedDict):
    """State for the LangGraph solver."""
    clue: str
    target_length: Optional[int]
    word_analyses: List[WordAnalysis]
    solution_attempts: List[SolutionAttempt]
    current_attempt: Optional[SolutionAttempt]
    iteration_count: int
    max_iterations: int
    final_solution: Optional[SolutionAttempt]
    messages: Annotated[list, add_messages]

# Tools for the agent
@tool
def generate_anagrams(text: str, target_length: Optional[int] = None) -> List[str]:
    """Generate all possible anagrams of the given text."""
    # Remove spaces and convert to lowercase
    letters = ''.join(text.lower().split())
    
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
        word = ''.join(perm)
        # Basic filtering - avoid obviously invalid combinations
        if not re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', word) and word.upper() not in anagrams:
            anagrams.append(word.upper())
        count += 1
    
    return anagrams[:20]  # Limit results

@tool
def check_word_validity(word: str) -> bool:
    """Check if a word is valid - placeholder for dictionary API."""
    # Simplified check - will be replaced with proper dictionary API
    return True

@tool
def find_synonyms(word: str) -> List[str]:
    """Find potential synonyms for a word (simplified implementation)."""
    # This is a simplified version - in practice you'd use a proper thesaurus API
    synonym_map = {
        'big': ['large', 'huge', 'massive', 'enormous'],
        'small': ['tiny', 'little', 'mini', 'minute'],
        'fast': ['quick', 'rapid', 'swift', 'speedy'],
        'slow': ['sluggish', 'gradual', 'leisurely'],
        'happy': ['glad', 'joyful', 'cheerful', 'pleased'],
        'sad': ['unhappy', 'gloomy', 'sorrowful', 'melancholy'],
        # Add more as needed
    }
    return synonym_map.get(word.lower(), [])

@tool
def find_hidden_words(phrase: str, target_length: Optional[int] = None) -> List[str]:
    """Find words hidden within a phrase."""
    # Remove spaces and punctuation
    clean_phrase = re.sub(r'[^a-zA-Z]', '', phrase.lower())
    
    hidden_words = []
    for i in range(len(clean_phrase)):
        for j in range(i + 3, len(clean_phrase) + 1):  # Minimum 3 letters
            substring = clean_phrase[i:j]
            if target_length and len(substring) != target_length:
                continue
            # Basic filtering - will be enhanced with dictionary API
            if len(substring) >= 3 and len(substring) <= 15:
                # Avoid substrings with too many consonants in a row
                if not re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', substring):
                    hidden_words.append(substring.upper())
                    if len(hidden_words) >= 10:  # Limit results
                        break
    
    return hidden_words

@tool
def reverse_word(word: str) -> str:
    """Reverse a word."""
    return word[::-1].upper()

@tool
def lookup_word_definition(word: str) -> Dict[str, str]:
    """Look up the definition of a word - placeholder for dictionary API."""
    # Placeholder implementation - will be replaced with proper dictionary API
    basic_definitions = {
        'cat': 'a small domesticated carnivorous mammal',
        'dog': 'a domesticated carnivorous mammal',
        'house': 'a building for human habitation',
        'tree': 'a woody perennial plant',
        'water': 'a colorless, transparent, odorless liquid',
        'fire': 'combustion or burning',
        'earth': 'the planet on which we live',
        'air': 'the invisible gaseous substance',
        'sun': 'the star around which the earth orbits',
        'moon': 'the natural satellite of the earth'
    }
    
    return {
        'word': word,
        'definition': basic_definitions.get(word.lower(), 'Definition not available'),
        'part_of_speech': 'noun'  # Simplified
    }

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
            check_word_validity,
            find_synonyms,
            find_hidden_words,
            reverse_word,
            lookup_word_definition
        ]
        self.tool_node = ToolNode(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph state graph."""
        workflow = StateGraph(SolverState)
        
        # Add nodes
        workflow.add_node("analyze_clue", self._analyze_clue)
        workflow.add_node("generate_solution", self._generate_solution)
        workflow.add_node("verify_solution", self._verify_solution)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("decide_next", self._decide_next_action)
        workflow.add_node("finalize", self._finalize_solution)
        
        # Set entry point
        workflow.set_entry_point("analyze_clue")
        
        # Add edges
        workflow.add_edge("analyze_clue", "generate_solution")
        workflow.add_edge("generate_solution", "tools")
        workflow.add_edge("tools", "verify_solution")
        workflow.add_edge("verify_solution", "decide_next")
        
        # Conditional edges from decide_next
        workflow.add_conditional_edges(
            "decide_next",
            self._should_continue,
            {
                "continue": "analyze_clue",  # Recurrent edge
                "finalize": "finalize",
                "end": END
            }
        )
        
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _analyze_clue(self, state: SolverState) -> SolverState:
        """Analyze the clue and identify word roles."""
        clue = state["clue"]
        iteration = state["iteration_count"]
        
        system_prompt = """You are an expert cryptic crossword solver. Analyze the given clue and identify the role of each word or phrase.

        Roles to identify:
        - definition: The straightforward definition (usually at start or end)
        - indicator: Words that signal wordplay (anagram, container, reversal, etc.)
        - target: Words that are operated on by indicators
        - synonym: Words that need to be replaced by synonyms
        - link: Connector words
        
        Wordplay types:
        - anagram: Letters rearranged (indicators: mixed, confused, broken, etc.)
        - container: One word contains another (indicators: in, inside, around, etc.)
        - reversal: Word backwards (indicators: back, reverse, returns, etc.)
        - hidden: Word hidden in phrase (indicators: some, part of, within, etc.)
        - deletion: Remove letters (indicators: without, losing, drops, etc.)
        - homophone: Sounds like (indicators: sounds, heard, spoken, etc.)
        """
        
        human_prompt = f"""Clue: "{clue}"
        Target length: {state.get('target_length', 'unknown')}
        Iteration: {iteration + 1}
        
        Analyze each word/phrase and suggest their roles. Consider multiple interpretations if this is not the first iteration."""
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        # Parse the response to extract word analyses (simplified)
        # In a full implementation, you'd use structured output
        word_analyses = self._parse_analysis_response(response.content, clue)
        
        state["word_analyses"] = word_analyses
        state["messages"].append(response)
        
        return state
    
    def _generate_solution(self, state: SolverState) -> SolverState:
        """Generate a solution attempt based on current analysis."""
        clue = state["clue"]
        analyses = state["word_analyses"]
        target_length = state.get("target_length")
        
        system_prompt = """Based on the word analysis, generate a specific solution attempt. 
        Use the available tools to check anagrams, synonyms, hidden words, etc.
        
        Be specific about which words you're using and how the wordplay works."""
        
        human_prompt = f"""Clue: "{clue}"
        Target length: {target_length}
        Word analyses: {[f"{a.text}: {a.role}" for a in analyses]}
        
        Generate a specific solution using the tools available."""
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        # The LLM should call tools here, which will be handled by the tools node
        state["messages"].append(response)
        
        return state
    
    def _verify_solution(self, state: SolverState) -> SolverState:
        """Verify the proposed solution."""
        # Extract the most recent message to see if tools were called
        messages = state.get("messages", [])
        tool_results = []
        
        # Initialize defaults
        solution_candidate = "UNKNOWN"
        reasoning = "Based on current analysis"
        
        # Look for tool calls in recent messages
        if messages:
            latest_message = messages[-1]
            if hasattr(latest_message, 'tool_calls') and latest_message.tool_calls:
                # Process tool results to create a solution attempt
                reasoning = "Based on tool analysis"
                
                for tool_call in latest_message.tool_calls:
                    if tool_call['name'] == 'generate_anagrams' and tool_call.get('result'):
                        anagrams = tool_call['result']
                        if anagrams:
                            solution_candidate = anagrams[0]  # Take first anagram
                            reasoning += f" - Found anagram: {solution_candidate}"
        
        # Create a solution attempt based on current analysis
        attempt = SolutionAttempt(
            solution=solution_candidate,
            definition_part="Identified definition part",
            wordplay_analysis=state["word_analyses"],
            verification_score=0.6,  # Base score - will be improved with better validation
            reasoning=f"Iteration {state['iteration_count'] + 1}: {reasoning}"
        )
        
        state["current_attempt"] = attempt
        state["solution_attempts"].append(attempt)
        
        return state
    
    def _decide_next_action(self, state: SolverState) -> SolverState:
        """Decide whether to continue iterating or finalize."""
        state["iteration_count"] += 1
        return state
    
    def _should_continue(self, state: SolverState) -> str:
        """Determine the next action based on current state."""
        current_attempt = state.get("current_attempt")
        iteration_count = state["iteration_count"]
        max_iterations = state["max_iterations"]
        
        # If we have a high-confidence solution, finalize
        if current_attempt and current_attempt.verification_score > 0.8:
            return "finalize"
        
        # If we've reached max iterations, end
        if iteration_count >= max_iterations:
            return "finalize"
        
        # Otherwise, continue iterating
        return "continue"
    
    def _finalize_solution(self, state: SolverState) -> SolverState:
        """Select the best solution from all attempts."""
        attempts = state["solution_attempts"]
        
        if attempts:
            # Select the attempt with the highest verification score
            best_attempt = max(attempts, key=lambda x: x.verification_score)
            state["final_solution"] = best_attempt
        
        return state
    
    def _parse_analysis_response(self, response, clue: str) -> List[WordAnalysis]:
        """Parse the LLM response to extract word analyses."""
        # This is a simplified implementation
        # In practice, you'd use structured output or more sophisticated parsing
        
        words = clue.split()
        analyses = []
        
        for i, word in enumerate(words):
            analysis = WordAnalysis(
                text=word,
                start_pos=i,
                end_pos=i,
                role="unknown",
                confidence=0.5
            )
            analyses.append(analysis)
        
        return analyses
    
    def solve(self, clue: str, target_length: Optional[int] = None, max_iterations: int = 3) -> Dict:
        """Solve a cryptic crossword clue."""
        # Extract length from clue if present
        length_match = re.search(r'\((\d+)\)$', clue.strip())
        if length_match and not target_length:
            target_length = int(length_match.group(1))
            clue = re.sub(r'\s*\(\d+\)$', '', clue.strip())
        
        initial_state = SolverState(
            clue=clue,
            target_length=target_length,
            word_analyses=[],
            solution_attempts=[],
            current_attempt=None,
            iteration_count=0,
            max_iterations=max_iterations,
            final_solution=None,
            messages=[]
        )
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Convert to the expected output format
        return self._format_output(final_state)
    
    def _format_output(self, state: dict) -> Dict:
        """Format the output to match the expected schema."""
        final_solution = state.get("final_solution")
        
        if not final_solution:
            return {
                "error": "No solution found",
                "error_code": "NO_SOLUTION"
            }
        
        return {
            "attempted_solutions": [
                {
                    "solution": attempt.solution,
                    "definition": attempt.definition_part,
                    "wordplay_components": [
                        {
                            "indicator": analysis.text,
                            "wordplay_type": analysis.wordplay_type or "other",
                            "target": ""
                        }
                        for analysis in attempt.wordplay_analysis
                        if analysis.role in ["indicator", "target"]
                    ]
                }
                for attempt in state["solution_attempts"][:-1]  # All but the final
            ],
            "complete_solution": {
                "solution": final_solution.solution,
                "definition": final_solution.definition_part,
                "wordplay_components": [
                    {
                        "indicator": analysis.text,
                        "wordplay_type": analysis.wordplay_type or "other",
                        "target": ""
                    }
                    for analysis in final_solution.wordplay_analysis
                    if analysis.role in ["indicator", "target"]
                ]
            },
            "reasoning_analysis": final_solution.reasoning
        }
