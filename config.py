"""
Configuration settings for the meal planning automation system.
"""
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class MacroGoals:
    """Daily macro goals for meal planning."""
    calories: int = 2000
    protein: int = 150  # grams
    carbs: int = 180    # grams
    fat: int = 60       # grams

@dataclass
class UserPreferences:
    """User preferences for meal planning."""
    cuisine: str = "Indian"
    preferred_protein: str = "chicken"
    max_prep_time: int = 30  # minutes
    dietary_restrictions: list = None
    
    def __post_init__(self):
        if self.dietary_restrictions is None:
            self.dietary_restrictions = []

@dataclass
class ScheduleConfig:
    """Schedule configuration for automation."""
    breakfast_time: str = "12:03"
    grocery_time: str = "21:00"
    timezone: str = "local"
    check_interval: int = 300  # Check every 5 minutes (300 seconds)

class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.macro_goals = MacroGoals()
        self.user_preferences = UserPreferences()
        self.schedule = ScheduleConfig()
        
        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        
        # Database configuration
        self.db_path = os.getenv("DB_PATH", "meal_planner.db")
        
        # Recipe storage
        self.recipes_dir = os.getenv("RECIPES_DIR", "recipes")
        
    def get_meal_distribution(self) -> Dict[str, Dict[str, int]]:
        """Get macro distribution across meals."""
        return {
            "breakfast": {
                "calories": int(self.macro_goals.calories * 0.25),
                "protein": int(self.macro_goals.protein * 0.25),
                "carbs": int(self.macro_goals.carbs * 0.25),
                "fat": int(self.macro_goals.fat * 0.25)
            },
            "lunch": {
                "calories": int(self.macro_goals.calories * 0.35),
                "protein": int(self.macro_goals.protein * 0.35),
                "carbs": int(self.macro_goals.carbs * 0.35),
                "fat": int(self.macro_goals.fat * 0.35)
            },
            "dinner": {
                "calories": int(self.macro_goals.calories * 0.40),
                "protein": int(self.macro_goals.protein * 0.40),
                "carbs": int(self.macro_goals.carbs * 0.40),
                "fat": int(self.macro_goals.fat * 0.40)
            }
        }

# Global configuration instance
config = Config() 