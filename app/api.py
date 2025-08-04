from flask import Flask, Blueprint, request, jsonify
from app.get_solution import get_llm_solution
from app.mock_state import get_mock_ui_response
from app.state_transformer import transform_state_to_ui_format

# Create a blueprint
api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/api/submit_clue', methods=['POST'])
def submit_clue():
    data = request.json
    if data is None:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    clue = data.get('clue')
    length = data.get('length', None)
    use_mock = data.get('mock', False)  # Add mock parameter
    
    if not clue:
        return jsonify({'error': 'No clue provided'}), 400
    
    if use_mock:
        # Use mock state for UI testing
        solution = get_mock_ui_response(clue, length)
        return jsonify({
            'clue': clue,
            'solution': solution
        }), 200
    else:
        # Use real LLM solver
        raw_solution = get_llm_solution(clue, {}, length)
    
        # Handle both structured responses and error responses
        if isinstance(raw_solution, dict):
            if 'error' in raw_solution:
                # Return error response
                return jsonify(raw_solution), 500
            else:
                # Check if this is already a UI-formatted response or raw state
                if 'attempted_solutions' in raw_solution and 'complete_solution' in raw_solution:
                    # Already formatted for UI
                    solution = raw_solution
                else:
                    # Transform raw state to UI format
                    solution = transform_state_to_ui_format(raw_solution, clue)
                
                return jsonify({
                    'clue': clue,
                    'solution': solution
                }), 200
        else:
            # Fallback for string responses (legacy support)
            return jsonify({
                'clue': clue, 
                'solution': {
                    'attempted_solutions': [],
                    'complete_solution': {
                        'solution': str(raw_solution),
                        'definition': 'Legacy response format',
                        'wordplay_components': [
                            {
                                'indicator': 'legacy',
                                'wordplay_type': 'other',
                                'target': 'unstructured'
                            }
                        ]
                    }
                }
            }), 200

@api_blueprint.route('/api/submit_clue_mock', methods=['POST'])
def submit_clue_mock():
    """Dedicated mock endpoint for UI testing."""
    
    # For mock mode, ignore the clue from the form and use the default mock clue
    # This allows testing without having to type a clue
    solution = get_mock_ui_response()  # Use default parameters
    return jsonify({
        'clue': solution["interactive_clue"]["original_clue"],
        'solution': solution
    }), 200

@api_blueprint.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200