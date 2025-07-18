from flask import Flask, render_template, request
from .get_solution import get_llm_solution

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)

    # Import and register the blueprint
    from .api import api_blueprint
    app.register_blueprint(api_blueprint)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/solve', methods=['POST'])
    def solve_clue():
        clue = request.form.get('clue')
        if not clue:
            return render_template('index.html', error="Please enter a clue.")
        
        solution = get_llm_solution(clue)
        return render_template('index.html', clue=clue, solution=solution)

    return app