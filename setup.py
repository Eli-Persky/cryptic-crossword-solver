#!/usr/bin/env python3
"""
Setup script for the LangGraph-based cryptic crossword solver.
This script installs required dependencies for the LangGraph-based solver.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements."""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False
    return True

def check_environment():
    """Check environment configuration."""
    print("Checking environment configuration...")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"⚠ Warning: {env_file} not found. Creating example file...")
        with open(".env.example", "w") as f:
            f.write("""# Flask Configuration
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=5000

# LLM API Configuration
LLM_API_PROVIDER=openai
TEST_MODE=false

# LangGraph Configuration
USE_LANGGRAPH=true
MAX_SOLVER_ITERATIONS=3

# OpenAI API (required for LangGraph solver)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API (alternative)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Rate limiting (seconds between API calls)
API_RATE_LIMIT=5
""")
        print(f"✓ Created {env_file}.example - please copy to {env_file} and configure")
    else:
        print(f"✓ Found {env_file}")
    
    return True

def main():
    """Main setup function."""
    print("Setting up LangGraph-based Cryptic Crossword Solver")
    print("=" * 50)
    
    success = True
    success &= install_requirements()
    success &= check_environment()
    
    print("=" * 50)
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure your .env file with API keys")
        print("2. Run: python run.py")
    else:
        print("✗ Setup encountered errors. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
