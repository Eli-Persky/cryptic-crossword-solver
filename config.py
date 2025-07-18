import os

class Config:
    API_PROVIDER = os.environ.get('API_PROVIDER', 'openai')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your_default_openai_api_key'
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY') or 'your_default_anthropic_api_key'
    API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT', 5)) or 5
    DEBUG = os.environ.get('TEST_MODE', 'False') == 'True'
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))