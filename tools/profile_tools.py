from langchain_core.tools import tool
from database import get_session, UserProfile
from config import ACTIVITY_MULTIPLIERS, GOAL_ADJUSTMENTS


def _calculate_bmr(weight_kg, height_cm, age, gender):
    # Mifflin-St Jeor Equation
    if gender.lower() == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def compute_targets(age, gender, height_cm, weight_kg, activity_level, goal):
    bmr = _calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    target_cal = tdee + GOAL_ADJUSTMENTS.get(goal, 0)

    # Macro split: protein 30%, carbs 40%, fat 30% (adjusted for muscle building)
    if goal == "build_muscle":
        p_ratio, c_ratio, f_ratio = 0.35, 0.40, 0.25
    elif goal == "lose_weight":
        p_ratio, c_ratio, f_ratio = 0.35, 0.35, 0.30
    else:
        p_ratio, c_ratio, f_ratio = 0.30, 0.40, 0.30

    return {
        "target_calories": round(target_cal),
        "target_protein": round((target_cal * p_ratio) / 4),
        "target_carbs": round((target_cal * c_ratio) / 4),
        "target_fat": round((target_cal * f_ratio) / 9),
        "bmr": round(bmr),
        "tdee": round(tdee),
    }


@tool
def get_user_profile() -> dict:
    """Retrieve the user's profile and nutritional targets."""
    session = get_session()
    try:
        p = session.query(UserProfile).first()
        if not p:
            return {"error": "No profile found. Please create one."}
        return {
            "name": p.name, "age": p.age, "gender": p.gender,
            "height_cm": p.height_cm, "weight_kg": p.weight_kg,
            "activity_level": p.activity_level, "goal": p.goal,
            "dietary_restrictions": p.dietary_restrictions,
            "allergies": p.allergies,
            "target_calories": p.target_calories,
            "target_protein": p.target_protein,
            "target_carbs": p.target_carbs,
            "target_fat": p.target_fat,
        }
    finally:
        session.close()


@tool
def update_user_profile(name: str, age: int, gender: str, height_cm: float,
                        weight_kg: float, activity_level: str, goal: str,
                        dietary_restrictions: str = "", allergies: str = "") -> dict:
    """Create or update the user's profile. activity_level: sedentary/light/moderate/active/very_active.
    goal: lose_weight/maintain/gain_weight/build_muscle."""
    session = get_session()
    try:
        targets = compute_targets(age, gender, height_cm, weight_kg, activity_level, goal)
        p = session.query(UserProfile).first()
        if not p:
            p = UserProfile()
            session.add(p)
        p.name = name
        p.age = age
        p.gender = gender
        p.height_cm = height_cm
        p.weight_kg = weight_kg
        p.activity_level = activity_level
        p.goal = goal
        p.dietary_restrictions = dietary_restrictions
        p.allergies = allergies
        p.target_calories = targets["target_calories"]
        p.target_protein = targets["target_protein"]
        p.target_carbs = targets["target_carbs"]
        p.target_fat = targets["target_fat"]
        session.commit()
        return {"status": "success", "targets": targets}
    finally:
        session.close()