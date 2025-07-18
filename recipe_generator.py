"""
Recipe generator using Ollama for local AI-powered recipe creation.
"""
import json
import re
from typing import List, Dict, Optional
import ollama
from datetime import datetime

from models import Recipe, Ingredient, NutritionInfo
from config import config

class RecipeGenerator:
    """Generate recipes using Ollama local LLM."""
    
    def __init__(self):
        self.client = ollama.Client(host=config.ollama_url)
        self.model = config.ollama_model
    
    def generate_recipe(self, meal_type: str, cuisine: str, preferred_protein: str, 
                       macro_goals: Dict[str, int], max_prep_time: int = 30) -> Recipe:
        """Generate a recipe using Ollama."""
        
        prompt = self._create_recipe_prompt(
            meal_type=meal_type,
            cuisine=cuisine,
            preferred_protein=preferred_protein,
            macro_goals=macro_goals,
            max_prep_time=max_prep_time
        )
        
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            )
            
            recipe_data = self._parse_recipe_response(response['response'])
            return self._create_recipe_object(recipe_data, meal_type, cuisine)
            
        except Exception as e:
            print(f"Error generating recipe: {e}")
            # Return a fallback recipe
            return self._create_fallback_recipe(meal_type, cuisine, preferred_protein, macro_goals)
    
    def _create_recipe_prompt(self, meal_type: str, cuisine: str, preferred_protein: str,
                            macro_goals: Dict[str, int], max_prep_time: int) -> str:
        """Create a detailed prompt for recipe generation."""
        
        return f"""
You are a professional chef and nutritionist. Create a detailed recipe in JSON format for a {meal_type} meal.

Requirements:
- Cuisine: {cuisine}
- Preferred protein: {preferred_protein}
- Maximum preparation time: {max_prep_time} minutes
- Nutritional goals: {macro_goals['calories']} calories, {macro_goals['protein']}g protein, {macro_goals['carbs']}g carbs, {macro_goals['fat']}g fat
- Must be healthy and balanced
- Include detailed step-by-step instructions
- List all ingredients with exact amounts and units

Return ONLY a valid JSON object with this exact structure:
{{
    "name": "Recipe Name",
    "prep_time": 15,
    "cook_time": 20,
    "servings": 1,
    "ingredients": [
        {{"name": "ingredient name", "amount": 1.0, "unit": "cup", "category": "protein"}}
    ],
    "instructions": [
        "Step 1: ...",
        "Step 2: ..."
    ],
    "nutrition": {{
        "calories": 500,
        "protein": 25.0,
        "carbs": 45.0,
        "fat": 20.0
    }}
}}

Make sure the recipe is authentic to {cuisine} cuisine and uses {preferred_protein} as the main protein source.
"""
    
    def _parse_recipe_response(self, response: str) -> Dict:
        """Parse the Ollama response into a structured recipe."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                
                # Fix common issues
                json_str = re.sub(r':\s*(\d+[a-zA-Z]+)', r': "\1"', json_str)  # Fix 100g -> "100g"
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # Remove trailing commas
                
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            print(f"Error parsing recipe response: {e}")
            print("Using fallback recipe...")
            raise

    def _clean_json_string(self, json_str: str) -> str:
        """Clean up common JSON formatting issues."""
        # Fix unquoted values (like 100g, 50g, etc.)
        json_str = re.sub(r':\s*(\d+[a-zA-Z]+)', r': "\1"', json_str)
        
        # Fix unquoted decimal values
        json_str = re.sub(r':\s*(\d+\.\d+[a-zA-Z]+)', r': "\1"', json_str)
        
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix missing quotes around keys
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')
        
        # Remove any comments
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        return json_str

    def _manual_parse_recipe(self, json_str: str) -> Dict:
        """Manually parse recipe when JSON parsing fails completely."""
        print("Attempting manual parsing...")
        
        recipe_data = {
            "name": "AI Generated Recipe",
            "prep_time": 15,
            "cook_time": 20,
            "servings": 1,
            "ingredients": [],
            "instructions": [],
            "nutrition": {
                "calories": 500,
                "protein": 25.0,
                "carbs": 45.0,
                "fat": 20.0
            }
        }
        
        # Extract recipe name
        name_match = re.search(r'"name":\s*"([^"]+)"', json_str)
        if name_match:
            recipe_data["name"] = name_match.group(1)
        
        # Extract times
        prep_match = re.search(r'"prep_time":\s*(\d+)', json_str)
        if prep_match:
            recipe_data["prep_time"] = int(prep_match.group(1))
        
        cook_match = re.search(r'"cook_time":\s*(\d+)', json_str)
        if cook_match:
            recipe_data["cook_time"] = int(cook_match.group(1))
        
        # Extract ingredients using regex
        ingredients_section = re.search(r'"ingredients":\s*\[(.*?)\]', json_str, re.DOTALL)
        if ingredients_section:
            ingredients_text = ingredients_section.group(1)
            # Find each ingredient object
            ingredient_objects = re.findall(r'\{[^}]+\}', ingredients_text)
            for ing_obj in ingredient_objects:
                try:
                    # Clean and parse individual ingredient
                    ing_obj = self._clean_json_string(ing_obj)
                    ing_data = json.loads(ing_obj)
                    recipe_data["ingredients"].append(ing_data)
                except:
                    # Skip malformed ingredients
                    continue
        
        # Extract instructions
        instructions_section = re.search(r'"instructions":\s*\[(.*?)\]', json_str, re.DOTALL)
        if instructions_section:
            instructions_text = instructions_section.group(1)
            # Find quoted strings
            instructions = re.findall(r'"([^"]+)"', instructions_text)
            recipe_data["instructions"] = instructions
        
        # Extract nutrition
        nutrition_section = re.search(r'"nutrition":\s*\{([^}]+)\}', json_str)
        if nutrition_section:
            nutrition_text = nutrition_section.group(1)
            
            calories_match = re.search(r'"calories":\s*(\d+)', nutrition_text)
            if calories_match:
                recipe_data["nutrition"]["calories"] = int(calories_match.group(1))
            
            protein_match = re.search(r'"protein":\s*([\d.]+)', nutrition_text)
            if protein_match:
                recipe_data["nutrition"]["protein"] = float(protein_match.group(1))
            
            carbs_match = re.search(r'"carbs":\s*([\d.]+)', nutrition_text)
            if carbs_match:
                recipe_data["nutrition"]["carbs"] = float(carbs_match.group(1))
            
            fat_match = re.search(r'"fat":\s*([\d.]+)', nutrition_text)
            if fat_match:
                recipe_data["nutrition"]["fat"] = float(fat_match.group(1))
        
        return recipe_data
    
    def _create_recipe_object(self, recipe_data: Dict, meal_type: str, cuisine: str) -> Recipe:
        """Create a Recipe object from parsed data."""
        
        # Convert ingredients
        ingredients = []
        for ing_data in recipe_data.get('ingredients', []):
            ingredient = Ingredient(
                name=ing_data['name'],
                amount=float(ing_data['amount']),
                unit=ing_data['unit'],
                category=ing_data.get('category', '')
            )
            ingredients.append(ingredient)
        
        # Convert nutrition
        nutrition_data = recipe_data.get('nutrition', {})
        nutrition = NutritionInfo(
            calories=int(nutrition_data.get('calories', 0)),
            protein=float(nutrition_data.get('protein', 0)),
            carbs=float(nutrition_data.get('carbs', 0)),
            fat=float(nutrition_data.get('fat', 0))
        )
        
        return Recipe(
            name=recipe_data.get('name', f"{cuisine} {meal_type}"),
            cuisine=cuisine,
            meal_type=meal_type,
            prep_time=int(recipe_data.get('prep_time', 15)),
            cook_time=int(recipe_data.get('cook_time', 15)),
            servings=int(recipe_data.get('servings', 1)),
            ingredients=ingredients,
            instructions=recipe_data.get('instructions', []),
            nutrition=nutrition,
            tags=[cuisine, meal_type, "ai-generated"]
        )
    
    def _create_fallback_recipe(self, meal_type: str, cuisine: str, 
                              preferred_protein: str, macro_goals: Dict[str, int]) -> Recipe:
        """Create a fallback recipe when AI generation fails."""
        
        # Simple fallback recipes based on cuisine and meal type
        fallback_recipes = {
            "breakfast": {
                "Indian": {
                    "name": "Masala Omelette with Toast",
                    "ingredients": [
                        {"name": "eggs", "amount": 2, "unit": "pieces", "category": "protein"},
                        {"name": "onion", "amount": 0.25, "unit": "cup", "category": "vegetable"},
                        {"name": "tomato", "amount": 0.25, "unit": "cup", "category": "vegetable"},
                        {"name": "bread", "amount": 2, "unit": "slices", "category": "grain"},
                        {"name": "oil", "amount": 1, "unit": "tbsp", "category": "fat"}
                    ],
                    "instructions": [
                        "Chop onion and tomato finely",
                        "Beat eggs with salt and pepper",
                        "Heat oil in pan, sauté onions and tomatoes",
                        "Pour beaten eggs and cook until set",
                        "Serve with toasted bread"
                    ],
                    "nutrition": {"calories": 350, "protein": 20, "carbs": 25, "fat": 15}
                }
            },
            "lunch": {
                "Indian": {
                    "name": f"{preferred_protein.title()} Curry with Rice",
                    "ingredients": [
                        {"name": preferred_protein, "amount": 150, "unit": "grams", "category": "protein"},
                        {"name": "onion", "amount": 0.5, "unit": "cup", "category": "vegetable"},
                        {"name": "tomato", "amount": 0.5, "unit": "cup", "category": "vegetable"},
                        {"name": "rice", "amount": 0.75, "unit": "cup", "category": "grain"},
                        {"name": "oil", "amount": 2, "unit": "tbsp", "category": "fat"}
                    ],
                    "instructions": [
                        "Cook rice according to package instructions",
                        "Heat oil and sauté onions until golden",
                        f"Add {preferred_protein} and cook until browned",
                        "Add tomatoes and spices, cook until soft",
                        "Serve hot with rice"
                    ],
                    "nutrition": {"calories": 600, "protein": 35, "carbs": 55, "fat": 25}
                }
            },
            "dinner": {
                "Indian": {
                    "name": f"{preferred_protein.title()} Tikka with Roti",
                    "ingredients": [
                        {"name": preferred_protein, "amount": 120, "unit": "grams", "category": "protein"},
                        {"name": "yogurt", "amount": 0.25, "unit": "cup", "category": "dairy"},
                        {"name": "roti", "amount": 2, "unit": "pieces", "category": "grain"},
                        {"name": "cucumber", "amount": 0.5, "unit": "cup", "category": "vegetable"}
                    ],
                    "instructions": [
                        "Marinate protein in yogurt and spices for 30 minutes",
                        "Grill or pan-fry until cooked through",
                        "Warm roti on a hot pan",
                        "Serve with fresh cucumber salad"
                    ],
                    "nutrition": {"calories": 450, "protein": 30, "carbs": 40, "fat": 20}
                }
            }
        }
        
        fallback = fallback_recipes.get(meal_type, {}).get(cuisine, {})
        
        ingredients = [Ingredient(**ing) for ing in fallback.get('ingredients', [])]
        nutrition = NutritionInfo(**fallback.get('nutrition', {}))
        
        return Recipe(
            name=fallback.get('name', f"{cuisine} {meal_type}"),
            cuisine=cuisine,
            meal_type=meal_type,
            prep_time=15,
            cook_time=20,
            servings=1,
            ingredients=ingredients,
            instructions=fallback.get('instructions', []),
            nutrition=nutrition,
            tags=[cuisine, meal_type, "fallback"]
        )
    
    def generate_meal_plan(self, target_date: datetime) -> Dict[str, Recipe]:
        """Generate a complete meal plan for a day."""
        meal_distribution = config.get_meal_distribution()
        
        meal_plan = {}
        
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            macro_goals = meal_distribution[meal_type]
            
            recipe = self.generate_recipe(
                meal_type=meal_type,
                cuisine=config.user_preferences.cuisine,
                preferred_protein=config.user_preferences.preferred_protein,
                macro_goals=macro_goals,
                max_prep_time=config.user_preferences.max_prep_time
            )
            
            meal_plan[meal_type] = recipe
        
        return meal_plan

# Global recipe generator instance
recipe_generator = RecipeGenerator() 