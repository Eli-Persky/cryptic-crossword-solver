import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key'
    LLM_API_KEY = os.environ.get('LLM_API_KEY') or 'your_default_llm_api_key'
    LLM_API_URL = os.environ.get('LLM_API_URL') or 'https://api.example.com/llm'
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))