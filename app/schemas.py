# JSON Schemas for structured LLM outputs

WORDPLAY_COMPONENT_SCHEMA = {
	"type": "object",
	"properties": {
		"indicator": {
			"type": "string",
			"description": "The word or phrase which is indicating some form of wordplay"
		},
		"wordplay_type": {
			"type": "string",
			"enum": ["charade", "link", "anagram", "container", "contents", "reversal", "hidden", "homophone", "deletion", "selection", "replacement", "other"],
			"description": "The type of wordplay indicated by the indicator"
		},
		"target": {
			"type": "string",
			"description": "This must be a word or words from the clue which are targeted by the indicator word. Each type of wordplay affects its target in a different way or may not have a target at all"
		}
	},
	"required": ["indicator", "wordplay_type"]
}

PARTIAL_SOLUTION_SCHEMA = {
	"type": "object",
	"properties": {
		"solution": {
			"type": "string",
			"description": "Solution to the crossword clue, only populated if a solution was found in this attempt"
		},
		"definition": {
			"type": "string",
			"description": "The part of the clue which defines the answer, only populated if the definition was determined in this attempt. The definition is usually found at the start or end of a clue"
		},
		"wordplay_components": {
			"type": "array",
			"items": WORDPLAY_COMPONENT_SCHEMA,
			"description": "Each component of the wordplay in this attempted solution. Each should include the indicator word, the type of wordplay that is used, and any part of the clue that is targeted by the indicator word"
		}
    }
}

COMPLETE_SOLUTION_SCHEMA = {
	"type": "object",
	"properties": {
		"solution": {
			"type": "string",
			"description": "Solution to the crossword clue"
		},
		"definition": {
			"type": "string",
			"description": "The part of the clue which defines the answer. The definition is usually found at the start or end of a clue"
		},
		"wordplay_components": {
			"type": "array",
			"items": WORDPLAY_COMPONENT_SCHEMA,
			"description": "Each component of the wordplay used in the solution. These must populated in the order they appear in the clue. Each should include the indicator word or phrase, the type of wordplay that is used, and any part of the clue that is targeted by the indicator word"
		}
    },
    "required": ["solution", "definition", "wordplay_components"]
}

CROSSWORD_SOLUTION_SCHEMA = {
	"type": "object",
	"properties": {
		"attempted_solutions": {
			"type": "array",
			"items": PARTIAL_SOLUTION_SCHEMA,
			"description": "All incomplete attempts at finding a solution, these may or may not include a solution but should contain some amount of wordplay"
		},
		"complete_solution": COMPLETE_SOLUTION_SCHEMA
	},
	"required": ["complete_solution"]
}

ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "string",
            "description": "Error message"
        },
        "error_code": {
            "type": "string",
            "enum": ["INVALID_CLUE", "API_ERROR", "RATE_LIMIT", "PARSING_ERROR", "UNKNOWN"],
            "description": "Categorized error code"
        },
        "suggestions": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Suggestions for fixing the issue"
        }
    },
    "required": ["error", "error_code"]
}

# OpenAI function calling format
OPENAI_FUNCTION_SCHEMAS = {
    "solve_cryptic_clue": {
        "name": "solve_cryptic_clue",
        "description": "Solve a cryptic crossword clue with detailed wordplay analysis",
        "parameters": CROSSWORD_SOLUTION_SCHEMA
    }
}

# Anthropic tool format
ANTHROPIC_TOOL_SCHEMAS = [
    {
        "name": "solve_cryptic_clue",
        "description": "Solve a cryptic crossword clue with detailed wordplay analysis",
        "input_schema": CROSSWORD_SOLUTION_SCHEMA
    }
]
















