from flask import Flask, Blueprint, request, jsonify
from app.utils import get_llm_solution

# Create a blueprint
api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/api/submit_clue', methods=['POST'])
def submit_clue():
    data = request.json
    clue = data.get('clue')
    
    if not clue:
        return jsonify({'error': 'No clue provided'}), 400
    
    solution = get_llm_solution(clue)
    
    # Handle both structured responses and error responses
    if isinstance(solution, dict):
        if 'error' in solution:
            # Return error response
            return jsonify(solution), 500
        else:
            # Return structured solution
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
                    'solution': str(solution),
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

@api_blueprint.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200