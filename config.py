import os
from dotenv import load_dotenv

# Load local environment variables if testing on your computer
load_dotenv()

# --- API Configuration ---
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