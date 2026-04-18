import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")

# LLM Provider selection
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Model names per provider
GROQ_MODEL = "llama-3.3-70b-versatile"   # Best free model
GEMINI_MODEL = "gemini-2.0-flash-exp"    # Fast, free backup
OLLAMA_MODEL = "llama3.2"                # Local fallback

# Database
DB_PATH = "diet_agent.db"

# Activity multipliers for TDEE
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENTS = {
    "lose_weight": -500,
    "maintain": 0,
    "gain_weight": 300,
    "build_muscle": 250,
}