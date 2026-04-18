from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DB_PATH

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class UserProfile(Base):
    __tablename__ = "user_profile"
    id = Column(Integer, primary_key=True)
    name = Column(String, default="User")
    age = Column(Integer)
    gender = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    activity_level = Column(String)
    goal = Column(String)
    dietary_restrictions = Column(Text, default="")  # e.g. "vegetarian,gluten-free"
    allergies = Column(Text, default="")
    target_calories = Column(Float)
    target_protein = Column(Float)
    target_carbs = Column(Float)
    target_fat = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MealLog(Base):
    __tablename__ = "meal_log"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    meal_type = Column(String)  # breakfast/lunch/dinner/snack
    food_name = Column(String)
    quantity_g = Column(Float)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    fiber = Column(Float, default=0)
    notes = Column(Text, default="")


class WeightLog(Base):
    __tablename__ = "weight_log"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    weight_kg = Column(Float)


class ChatMemory(Base):
    __tablename__ = "chat_memory"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    role = Column(String)
    content = Column(Text)


class MealPlan(Base):
    __tablename__ = "meal_plan"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    plan_date = Column(String)  # YYYY-MM-DD
    plan_data = Column(JSON)    # full plan dict


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


init_db()