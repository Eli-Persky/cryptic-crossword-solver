#!/usr/bin/env python3
"""
Flask app runner for UI testing with mock mode enabled by default.
"""

import os
from flask import Flask, render_template
from app.api import api_blueprint

def create_test_app():
    """Create Flask app configured for UI testing."""
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    
    # Register the API blueprint
    app.register_blueprint(api_blueprint)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/mock')
    def mock_mode():
        """Render the main page but with mock mode enabled by default."""
        return render_template('index.html', mock_mode=True)
    
    return app

def main():
    """Run the test Flask app."""
    app = create_test_app()
    
    print("Starting Flask app for UI testing...")
    print("Available endpoints:")
    print("  http://localhost:5000/ - Normal mode (uses real LLM)")
    print("  http://localhost:5000/mock - Mock mode (uses fake data)")
    print("  /api/submit_clue - Normal API endpoint")
    print("  /api/submit_clue_mock - Mock API endpoint")
    print("\nTip: Use /mock endpoint to test UI without LLM calls")
    
    # Run in debug mode for development
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
