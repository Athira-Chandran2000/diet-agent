# tools/nutrition_tools.py
import os
import requests
import functools
from langchain_core.tools import tool
from datetime import datetime, timedelta
from database import get_session, MealLog, UserProfile, WeightLog
from config import USDA_API_KEY, USDA_BASE_URL

@tool
@functools.lru_cache(maxsize=100)
def search_food_nutrition(food_query: str, quantity_g: float = 100.0) -> dict:
    """Search USDA database for food nutrition. Use this BEFORE logging a meal."""
    url = f"{USDA_BASE_URL}?api_key={USDA_API_KEY}&query={food_query}&pageSize=1"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if "foods" in data and len(data["foods"]) > 0:
            food = data["foods"][0]
            nutrients = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}
            
            factor = quantity_g / 100.0
            return {
                "food_name": food.get("description", food_query),
                "quantity_g": quantity_g,
                "calories": round(nutrients.get("Energy", 0) * factor, 1),
                "protein": round(nutrients.get("Protein", 0) * factor, 1),
                "carbs": round(nutrients.get("Carbohydrate, by difference", 0) * factor, 1),
                "fat": round(nutrients.get("Total lipid (fat)", 0) * factor, 1),
                "fiber": round(nutrients.get("Fiber, total dietary", 0) * factor, 1)
            }
    return {"error": f"Could not find exact data for {food_query}. Please estimate."}


@tool
def log_meal(food_name: str, meal_type: str = "snack", quantity_g: float = 100.0, 
             calories: float = None, protein: float = None, carbs: float = None, fat: float = None, 
             fiber: float = 0.0, notes: str = "") -> str:
    """Log a meal into the user's database. If you don't know the exact macros, ONLY provide food_name, meal_type, and quantity_g, and the system will automatically search the USDA database to calculate them."""
    import os
    import requests
    from config import USDA_API_KEY, USDA_BASE_URL
    
    session = get_session()
    try:
        username = os.environ.get("CURRENT_USERNAME", "default")

        # If the AI didn't provide macros, fetch them automatically!
        if calories is None or protein is None or carbs is None or fat is None:
            url = f"{USDA_BASE_URL}?api_key={USDA_API_KEY}&query={food_name}&pageSize=1"
            response = requests.get(url)
            
            if response.status_code == 200 and len(response.json().get("foods", [])) > 0:
                food = response.json()["foods"][0]
                nutrients = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}
                factor = quantity_g / 100.0
                
                # Auto-calculate macros
                calories = round(nutrients.get("Energy", 0) * factor, 1)
                protein = round(nutrients.get("Protein", 0) * factor, 1)
                carbs = round(nutrients.get("Carbohydrate, by difference", 0) * factor, 1)
                fat = round(nutrients.get("Total lipid (fat)", 0) * factor, 1)
                fiber = round(nutrients.get("Fiber, total dietary", 0) * factor, 1)
                food_name = food.get("description", food_name) # Use the official USDA name
            else:
                return f"Could not find USDA data for {food_name}. Please ask the user to specify calories manually."

        # Save to database
        entry = MealLog(
            username=username,
            meal_type=meal_type, food_name=food_name, quantity_g=quantity_g,
            calories=calories, protein=protein, carbs=carbs, fat=fat,
            fiber=fiber, notes=notes
        )
        session.add(entry)
        session.commit()
        return f"Successfully logged {quantity_g}g of {food_name} ({calories} kcal) for {meal_type}."
        
    except Exception as e:
        session.rollback()
        return f"Error logging meal: {str(e)}"
    finally:
        session.close()


@tool
def get_daily_intake(days_ago: int = 0) -> dict:
    """Get the total nutritional intake for a specific day (0 = today)."""
    session = get_session()
    try:
        username = os.environ.get("CURRENT_USERNAME", "default")
        target_date = datetime.utcnow().date() - timedelta(days=days_ago)
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)
        meals = session.query(MealLog).filter(
            MealLog.username == username,
            MealLog.date >= start, MealLog.date < end
        ).all()
        
        totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        for m in meals:
            totals["calories"] += m.calories
            totals["protein"] += m.protein
            totals["carbs"] += m.carbs
            totals["fat"] += m.fat
            
        return {"date": str(target_date), "totals": totals, "meal_count": len(meals)}
    finally:
        session.close()


@tool
def get_weekly_summary() -> dict:
    """Get daily nutritional totals for the last 7 days."""
    session = get_session()
    try:
        username = os.environ.get("CURRENT_USERNAME", "default")
        summary = {}
        for d in range(7):
            target = datetime.utcnow().date() - timedelta(days=d)
            start = datetime.combine(target, datetime.min.time())
            end = start + timedelta(days=1)
            meals = session.query(MealLog).filter(
                MealLog.username == username,
                MealLog.date >= start, MealLog.date < end
            ).all()
            totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
            for m in meals:
                totals["calories"] += m.calories
                totals["protein"] += m.protein
                totals["carbs"] += m.carbs
                totals["fat"] += m.fat
            summary[str(target)] = totals
        return summary
    finally:
        session.close()


@tool
def log_weight(weight_kg: float) -> str:
    """Log the user's current weight (kg) into the progress tracker."""
    session = get_session()
    try:
        username = os.environ.get("CURRENT_USERNAME", "default")
        session.add(WeightLog(weight_kg=weight_kg, username=username))
        profile = session.query(UserProfile).filter_by(name=username).first()
        if profile:
            profile.weight_kg = weight_kg
        session.commit()
        return f"Successfully logged weight: {weight_kg} kg."
    except Exception as e:
        session.rollback()
        return f"Error logging weight: {str(e)}"
    finally:
        session.close()