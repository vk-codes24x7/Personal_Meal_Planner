"""
Data models for the meal planning automation system.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Ingredient(BaseModel):
    """Model for recipe ingredients."""
    name: str
    amount: float
    unit: str
    category: str = Field(default="", description="Category like 'protein', 'vegetable', 'spice'")
    
    def __str__(self):
        return f"{self.amount} {self.unit} {self.name}"

class NutritionInfo(BaseModel):
    """Model for nutritional information."""
    calories: int
    protein: float  # grams
    carbs: float    # grams
    fat: float      # grams
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None

class Recipe(BaseModel):
    """Model for a complete recipe."""
    name: str
    cuisine: str
    meal_type: str  # breakfast, lunch, dinner
    prep_time: int  # minutes
    cook_time: int  # minutes
    servings: int = 1
    ingredients: List[Ingredient]
    instructions: List[str]
    nutrition: NutritionInfo
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def total_time(self) -> int:
        """Total time including prep and cook time."""
        return self.prep_time + self.cook_time
    
    def get_ingredients_for_servings(self, num_servings: int) -> List[Ingredient]:
        """Get ingredients scaled for a specific number of servings."""
        scaled_ingredients = []
        for ingredient in self.ingredients:
            scaled_amount = (ingredient.amount / self.servings) * num_servings
            scaled_ingredients.append(Ingredient(
                name=ingredient.name,
                amount=scaled_amount,
                unit=ingredient.unit,
                category=ingredient.category
            ))
        return scaled_ingredients

class MealPlan(BaseModel):
    """Model for a daily meal plan."""
    date: datetime
    breakfast: Optional[Recipe] = None
    lunch: Optional[Recipe] = None
    dinner: Optional[Recipe] = None
    
    def get_all_recipes(self) -> List[Recipe]:
        """Get all recipes in the meal plan."""
        recipes = []
        if self.breakfast:
            recipes.append(self.breakfast)
        if self.lunch:
            recipes.append(self.lunch)
        if self.dinner:
            recipes.append(self.dinner)
        return recipes
    
    def get_total_nutrition(self) -> NutritionInfo:
        """Calculate total nutrition for the day."""
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for recipe in self.get_all_recipes():
            total_calories += recipe.nutrition.calories
            total_protein += recipe.nutrition.protein
            total_carbs += recipe.nutrition.carbs
            total_fat += recipe.nutrition.fat
        
        return NutritionInfo(
            calories=total_calories,
            protein=total_protein,
            carbs=total_carbs,
            fat=total_fat
        )
    
    def get_grocery_list(self) -> List[Ingredient]:
        """Generate a consolidated grocery list for all meals."""
        all_ingredients = []
        
        for recipe in self.get_all_recipes():
            all_ingredients.extend(recipe.ingredients)
        
        # Consolidate ingredients by name
        consolidated = {}
        for ingredient in all_ingredients:
            key = f"{ingredient.name}_{ingredient.unit}"
            if key in consolidated:
                consolidated[key].amount += ingredient.amount
            else:
                consolidated[key] = ingredient
        
        return list(consolidated.values())

class GroceryItem(BaseModel):
    """Model for grocery list items."""
    name: str
    amount: float
    unit: str
    category: str
    checked: bool = False
    priority: int = 1  # 1=low, 2=medium, 3=high
    
    def __str__(self):
        return f"{self.amount} {self.unit} {self.name} ({self.category})" 