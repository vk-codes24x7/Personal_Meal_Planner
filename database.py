"""
Database module for storing recipes, meal plans, and grocery lists.
"""
import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pathlib import Path

from models import Recipe, MealPlan, Ingredient, NutritionInfo
from config import config

class Database:
    """SQLite database manager for meal planning data."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.db_path
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Try to initialize with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with sqlite3.connect(self.db_path, timeout=60.0) as conn:
                    # Use basic settings for better compatibility
                    conn.execute("PRAGMA busy_timeout=30000")
                    
                    cursor = conn.cursor()
                    
                    # Recipes table
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS recipes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            cuisine TEXT NOT NULL,
                            meal_type TEXT NOT NULL,
                            prep_time INTEGER NOT NULL,
                            cook_time INTEGER NOT NULL,
                            servings INTEGER DEFAULT 1,
                            ingredients TEXT NOT NULL,
                            instructions TEXT NOT NULL,
                            nutrition TEXT NOT NULL,
                            tags TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Meal plans table
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS meal_plans (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date DATE NOT NULL UNIQUE,
                            breakfast_recipe_id INTEGER,
                            lunch_recipe_id INTEGER,
                            dinner_recipe_id INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (breakfast_recipe_id) REFERENCES recipes (id),
                            FOREIGN KEY (lunch_recipe_id) REFERENCES recipes (id),
                            FOREIGN KEY (dinner_recipe_id) REFERENCES recipes (id)
                        )
                    ''')
                    
                    # Grocery lists table
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS grocery_lists (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date DATE NOT NULL,
                            ingredients TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    conn.commit()
                    break  # Success, exit retry loop
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise e
        else:
            raise Exception("Failed to initialize database after multiple attempts")
    
    def _get_connection(self):
        """Get a database connection with proper settings."""
        conn = sqlite3.connect(self.db_path, timeout=60.0)
        conn.execute("PRAGMA busy_timeout=30000")
        return conn
    
    def save_recipe(self, recipe: Recipe) -> int:
        """Save a recipe to the database and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO recipes (name, cuisine, meal_type, prep_time, cook_time, 
                                   servings, ingredients, instructions, nutrition, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recipe.name,
                recipe.cuisine,
                recipe.meal_type,
                recipe.prep_time,
                recipe.cook_time,
                recipe.servings,
                json.dumps([ing.dict() for ing in recipe.ingredients]),
                json.dumps(recipe.instructions),
                json.dumps(recipe.nutrition.dict()),
                json.dumps(recipe.tags)
            ))
            
            return cursor.lastrowid
    
    def get_recipe(self, recipe_id: int) -> Optional[Recipe]:
        """Get a recipe by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_recipe(row)
            return None
    
    def get_recipes_by_criteria(self, cuisine: str = None, meal_type: str = None, 
                               max_prep_time: int = None) -> List[Recipe]:
        """Get recipes matching specific criteria."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM recipes WHERE 1=1'
            params = []
            
            if cuisine:
                query += ' AND cuisine = ?'
                params.append(cuisine)
            
            if meal_type:
                query += ' AND meal_type = ?'
                params.append(meal_type)
            
            if max_prep_time:
                query += ' AND prep_time <= ?'
                params.append(max_prep_time)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_recipe(row) for row in rows]
    
    def save_meal_plan(self, meal_plan: MealPlan) -> int:
        """Save a meal plan to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Save recipes first if they don't exist
            breakfast_id = None
            lunch_id = None
            dinner_id = None
            
            if meal_plan.breakfast:
                breakfast_id = self.save_recipe(meal_plan.breakfast)
            
            if meal_plan.lunch:
                lunch_id = self.save_recipe(meal_plan.lunch)
            
            if meal_plan.dinner:
                dinner_id = self.save_recipe(meal_plan.dinner)
            
            # Save meal plan
            cursor.execute('''
                INSERT OR REPLACE INTO meal_plans 
                (date, breakfast_recipe_id, lunch_recipe_id, dinner_recipe_id)
                VALUES (?, ?, ?, ?)
            ''', (
                meal_plan.date.date(),
                breakfast_id,
                lunch_id,
                dinner_id
            ))
            
            return cursor.lastrowid
    
    def get_meal_plan(self, target_date: date) -> Optional[MealPlan]:
        """Get meal plan for a specific date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT mp.*, 
                       b.name as breakfast_name, b.cuisine as breakfast_cuisine,
                       l.name as lunch_name, l.cuisine as lunch_cuisine,
                       d.name as dinner_name, d.cuisine as dinner_cuisine
                FROM meal_plans mp
                LEFT JOIN recipes b ON mp.breakfast_recipe_id = b.id
                LEFT JOIN recipes l ON mp.lunch_recipe_id = l.id
                LEFT JOIN recipes d ON mp.dinner_recipe_id = d.id
                WHERE mp.date = ?
            ''', (target_date,))
            
            row = cursor.fetchone()
            
            if row:
                return self._row_to_meal_plan(row)
            return None
    
    def save_grocery_list(self, target_date: date, ingredients: List[Ingredient]):
        """Save grocery list for a specific date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO grocery_lists (date, ingredients)
                VALUES (?, ?)
            ''', (
                target_date,
                json.dumps([ing.dict() for ing in ingredients])
            ))
            
            conn.commit()
    
    def get_grocery_list(self, target_date: date) -> List[Ingredient]:
        """Get grocery list for a specific date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT ingredients FROM grocery_lists WHERE date = ?', (target_date,))
            row = cursor.fetchone()
            
            if row:
                ingredients_data = json.loads(row[0])
                return [Ingredient(**ing) for ing in ingredients_data]
            return []
    
    def _row_to_recipe(self, row) -> Recipe:
        """Convert database row to Recipe object."""
        ingredients_data = json.loads(row[7])
        instructions = json.loads(row[8])
        nutrition_data = json.loads(row[9])
        tags = json.loads(row[10]) if row[10] else []
        
        ingredients = [Ingredient(**ing) for ing in ingredients_data]
        nutrition = NutritionInfo(**nutrition_data)
        
        return Recipe(
            name=row[1],
            cuisine=row[2],
            meal_type=row[3],
            prep_time=row[4],
            cook_time=row[5],
            servings=row[6],
            ingredients=ingredients,
            instructions=instructions,
            nutrition=nutrition,
            tags=tags,
            created_at=datetime.fromisoformat(row[11])
        )
    
    def _row_to_meal_plan(self, row) -> MealPlan:
        """Convert database row to MealPlan object."""
        # This is a simplified version - in practice, you'd need to load the full recipes
        meal_plan = MealPlan(date=datetime.combine(row[1], datetime.min.time()))
        
        if row[2]:  # breakfast_recipe_id
            meal_plan.breakfast = self.get_recipe(row[2])
        
        if row[3]:  # lunch_recipe_id
            meal_plan.lunch = self.get_recipe(row[3])
        
        if row[4]:  # dinner_recipe_id
            meal_plan.dinner = self.get_recipe(row[4])
        
        return meal_plan

# Global database instance
db = Database() 