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
    
    if solution:
        return jsonify({'clue': clue, 'solution': solution}), 200
    else:
        return jsonify({'error': 'Could not retrieve solution'}), 500

@api_blueprint.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200