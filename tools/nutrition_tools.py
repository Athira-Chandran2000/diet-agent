import requests
from langchain_core.tools import tool
from datetime import datetime, timedelta
from database import get_session, MealLog, UserProfile, WeightLog
from config import USDA_API_KEY
import functools


@tool
@functools.lru_cache(maxsize=100)
def search_food_nutrition(food_query: str, quantity_g: float = 100.0) -> dict:
    """Search the USDA FoodData Central for nutritional data of a food item.
    Returns calories, protein, carbs, fat, fiber per given quantity in grams."""
    try:
        url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {"query": food_query, "api_key": USDA_API_KEY, "pageSize": 1,
                  "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"]}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data.get("foods"):
            return {"error": f"No food found for '{food_query}'"}

        food = data["foods"][0]
        nutrients = {n["nutrientName"]: n.get("value", 0) for n in food.get("foodNutrients", [])}
        factor = quantity_g / 100.0
        return {
            "food_name": food.get("description", food_query),
            "quantity_g": quantity_g,
            "calories": round(nutrients.get("Energy", 0) * factor, 1),
            "protein": round(nutrients.get("Protein", 0) * factor, 1),
            "carbs": round(nutrients.get("Carbohydrate, by difference", 0) * factor, 1),
            "fat": round(nutrients.get("Total lipid (fat)", 0) * factor, 1),
            "fiber": round(nutrients.get("Fiber, total dietary", 0) * factor, 1),
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def log_meal(meal_type: str, food_name: str, quantity_g: float,
             calories: float, protein: float, carbs: float, fat: float,
             fiber: float = 0, notes: str = "") -> str:
    """Log a meal into the user's food diary. meal_type must be breakfast, lunch, dinner, or snack."""
    session = get_session()
    try:
        entry = MealLog(
            meal_type=meal_type, food_name=food_name, quantity_g=quantity_g,
            calories=calories, protein=protein, carbs=carbs, fat=fat,
            fiber=fiber, notes=notes
        )
        session.add(entry)
        session.commit()
        return f"✅ Logged {food_name} ({quantity_g}g, {calories} kcal) as {meal_type}."
    finally:
        session.close()


@tool
def get_daily_intake(days_ago: int = 0) -> dict:
    """Get aggregated nutritional intake for a specific day. days_ago=0 means today."""
    session = get_session()
    try:
        target_date = datetime.utcnow().date() - timedelta(days=days_ago)
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)
        meals = session.query(MealLog).filter(
            MealLog.date >= start, MealLog.date < end
        ).all()

        totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
        meal_list = []
        for m in meals:
            totals["calories"] += m.calories
            totals["protein"] += m.protein
            totals["carbs"] += m.carbs
            totals["fat"] += m.fat
            totals["fiber"] += m.fiber
            meal_list.append({
                "meal_type": m.meal_type, "food": m.food_name,
                "qty_g": m.quantity_g, "kcal": m.calories
            })
        return {"date": str(target_date), "totals": totals, "meals": meal_list}
    finally:
        session.close()


@tool
def get_weekly_summary() -> dict:
    """Get a 7-day rolling summary of daily calories and macros."""
    session = get_session()
    try:
        summary = []
        for d in range(6, -1, -1):
            target = datetime.utcnow().date() - timedelta(days=d)
            start = datetime.combine(target, datetime.min.time())
            end = start + timedelta(days=1)
            meals = session.query(MealLog).filter(
                MealLog.date >= start, MealLog.date < end
            ).all()
            totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
            for m in meals:
                totals["calories"] += m.calories
                totals["protein"] += m.protein
                totals["carbs"] += m.carbs
                totals["fat"] += m.fat
            summary.append({"date": str(target), **totals})
        return {"week": summary}
    finally:
        session.close()


@tool
def log_weight(weight_kg: float) -> str:
    """Log the user's current weight (kg) into the progress tracker."""
    session = get_session()
    try:
        session.add(WeightLog(weight_kg=weight_kg))
        # Also update the profile
        profile = session.query(UserProfile).first()
        if profile:
            profile.weight_kg = weight_kg
        session.commit()
        return f"✅ Weight logged: {weight_kg} kg"
    finally:
        session.close()