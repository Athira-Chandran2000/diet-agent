# tools/profile_tools.py
import os
from langchain_core.tools import tool
from database import get_session, UserProfile
from config import ACTIVITY_MULTIPLIERS, GOAL_ADJUSTMENTS

def compute_targets(age: int, gender: str, height_cm: float, weight_kg: float, activity_level: str, goal: str):
    """Calculate BMR, TDEE, and Macros."""
    if gender.lower() == 'male':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.2)
    target_calories = int(tdee + GOAL_ADJUSTMENTS.get(goal.lower(), 0))
    
    protein = int(weight_kg * 2.2)
    fat = int((target_calories * 0.25) / 9)
    carbs = int((target_calories - (protein * 4) - (fat * 9)) / 4)
    
    return {
        "target_calories": target_calories,
        "target_protein": protein,
        "target_fat": fat,
        "target_carbs": carbs
    }

@tool
def get_user_profile() -> dict:
    """Retrieve the user's profile and nutritional targets."""
    session = get_session()
    try:
        username = os.environ.get("CURRENT_USERNAME", "default")
        p = session.query(UserProfile).filter_by(name=username).first()
        if not p:
            return {"error": "No profile found. Please create one."}
        return {
            "name": p.name, "age": p.age, "gender": p.gender,
            "weight_kg": p.weight_kg, "height_cm": p.height_cm,
            "goal": p.goal, "activity_level": p.activity_level,
            "dietary_restrictions": p.dietary_restrictions,
            "allergies": p.allergies,
            "targets": {
                "calories": p.target_calories, "protein": p.target_protein,
                "carbs": p.target_carbs, "fat": p.target_fat
            }
        }
    finally:
        session.close()

@tool
def update_user_profile(name: str, age: int, gender: str, height_cm: float, 
                        weight_kg: float, activity_level: str, goal: str, 
                        restrictions: str = "", allergies: str = "") -> str:
    """Update or create the user profile. Calculates daily targets automatically."""
    session = get_session()
    try:
        username = os.environ.get("CURRENT_USERNAME", "default")
        targets = compute_targets(age, gender, height_cm, weight_kg, activity_level, goal)
        p = session.query(UserProfile).filter_by(name=username).first()
        if not p:
            p = UserProfile(name=username)
            session.add(p)
            
        p.age = age
        p.gender = gender
        p.height_cm = height_cm
        p.weight_kg = weight_kg
        p.activity_level = activity_level
        p.goal = goal
        p.dietary_restrictions = restrictions
        p.allergies = allergies
        p.target_calories = targets['target_calories']
        p.target_protein = targets['target_protein']
        p.target_carbs = targets['target_carbs']
        p.target_fat = targets['target_fat']
        
        session.commit()
        return f"Profile updated. New daily targets: {targets['target_calories']} kcal, {targets['target_protein']}g Protein."
    except Exception as e:
        session.rollback()
        return f"Failed to update profile: {str(e)}"
    finally:
        session.close()