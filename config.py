import os

class Config:
    # API Configuration
    API_PROVIDER = os.environ.get('LLM_API_PROVIDER', 'openai')  # Changed from API_PROVIDER
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your_default_openai_api_key'
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY') or 'your_default_anthropic_api_key'
    API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT', 5)) or 5
    
    # Solver Configuration
    USE_LANGGRAPH = os.environ.get('USE_LANGGRAPH', 'True').lower() == 'true'
    MAX_SOLVER_ITERATIONS = int(os.environ.get('MAX_SOLVER_ITERATIONS', 3))
    
    # Flask Configuration
    DEBUG = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))