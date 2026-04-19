import os
from dotenv import load_dotenv

# Load local environment variables if testing locally
load_dotenv()

# --- AI & LLM Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- Nutrition API Configuration ---
USDA_API_KEY = os.getenv("USDA_API_KEY")
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# --- Nutrition Constants ---
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9
}

GOAL_ADJUSTMENTS = {
    "lose_weight": -500,
    "maintain": 0,
    "gain_weight": 500,
    "build_muscle": 300
}