from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///diet_agent.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profile"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # Using existing name as the unique username
    age = Column(Integer)
    gender = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    activity_level = Column(String)
    goal = Column(String)
    dietary_restrictions = Column(String, nullable=True)
    allergies = Column(String, nullable=True)
    target_calories = Column(Integer)
    target_protein = Column(Integer)
    target_carbs = Column(Integer)
    target_fat = Column(Integer)

class MealLog(Base):
    __tablename__ = "meal_log"
    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    meal_type = Column(String)  # breakfast/lunch/dinner/snack
    food_name = Column(String)
    quantity_g = Column(Float)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    fiber = Column(Float, nullable=True)
    notes = Column(String, nullable=True)

class WeightLog(Base):
    __tablename__ = "weight_log"
    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    weight_kg = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()