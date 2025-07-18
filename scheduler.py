"""
Scheduler for automated meal planning tasks.
"""
import schedule
import time
import threading
from datetime import datetime, date, timedelta
from typing import Optional

from models import MealPlan
from database import db
from recipe_generator import recipe_generator
from config import config

class MealPlannerScheduler:
    """Scheduler for automated meal planning tasks."""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler in a separate thread."""
        if self.running:
            print("Scheduler is already running!")
            return
        
        self.running = True
        
        # Schedule morning meal plan (8:00 AM)
        schedule.every().day.at(config.schedule.breakfast_time).do(self._morning_meal_plan_task)
        
        # Schedule evening grocery list (9:00 PM)
        schedule.every().day.at(config.schedule.grocery_time).do(self._evening_grocery_task)
        
        # Start the scheduler in a separate thread
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        print(f"✅ Meal planner scheduler started!")
        print(f"📅 Meal plans will be displayed at {config.schedule.breakfast_time}")
        print(f"🛒 Grocery lists will be displayed at {config.schedule.grocery_time}")
        print("Press Ctrl+C to stop the scheduler")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        print("🛑 Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop with smart interval."""
        print("🔄 Scheduler loop started")
        while self.running:
            schedule.run_pending()
            
            # Smart interval: Check more frequently around scheduled times
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute
            
            # Only check frequently in the hour before scheduled times
            if (current_hour == 7 and current_minute >= 45) or \
               (current_hour == 11 and current_minute >= 45) or \
               (current_hour == 20 and current_minute >= 45):
                interval = 60  # Check every minute only in the 15 minutes before scheduled times
                print(f"⚡ High-frequency mode: checking again in {interval} seconds...")
            else:
                interval = config.schedule.check_interval  # Use configured interval (5 minutes)
                print(f"😴 Low-frequency mode: sleeping for {interval} seconds...")
            
            time.sleep(interval)
    
    def _morning_meal_plan_task(self):
        """Generate and display morning meal plan."""
        try:
            print(f"🌅 Generating meal plan for {datetime.now().date()}")
            
            # Generate meal plan for today
            target_date = datetime.now()
            meal_plan_recipes = recipe_generator.generate_meal_plan(target_date)
            
            # Create meal plan object
            meal_plan = MealPlan(
                date=target_date,
                breakfast=meal_plan_recipes.get('breakfast'),
                lunch=meal_plan_recipes.get('lunch'),
                dinner=meal_plan_recipes.get('dinner')
            )
            
            # Save to database
            db.save_meal_plan(meal_plan)
            
            # Display in terminal
            self._display_meal_plan(meal_plan)
            
            print(f"✅ Morning meal plan generated successfully for {target_date.date()}")
                
        except Exception as e:
            print(f"❌ Error in morning meal plan task: {e}")
    
    def _evening_grocery_task(self):
        """Generate and display evening grocery list."""
        try:
            print(f"🛒 Generating grocery list for {datetime.now().date()}")
            
            # Get meal plan for tomorrow
            tomorrow = datetime.now() + timedelta(days=1)
            meal_plan = db.get_meal_plan(tomorrow.date())
            
            if meal_plan:
                # Generate grocery list from meal plan
                ingredients = meal_plan.get_grocery_list()
                
                # Save grocery list
                db.save_grocery_list(tomorrow.date(), ingredients)
                
                # Display in terminal
                self._display_grocery_list(ingredients, tomorrow.date())
                
                print(f"✅ Evening grocery list generated successfully for {tomorrow.date()}")
            else:
                print(f"⚠️ No meal plan found for {tomorrow.date()}, generating one now...")
                
                # Generate meal plan for tomorrow if not exists
                meal_plan_recipes = recipe_generator.generate_meal_plan(tomorrow)
                
                meal_plan = MealPlan(
                    date=tomorrow,
                    breakfast=meal_plan_recipes.get('breakfast'),
                    lunch=meal_plan_recipes.get('lunch'),
                    dinner=meal_plan_recipes.get('dinner')
                )
                
                # Save meal plan
                db.save_meal_plan(meal_plan)
                
                # Generate and display grocery list
                ingredients = meal_plan.get_grocery_list()
                db.save_grocery_list(tomorrow.date(), ingredients)
                
                self._display_grocery_list(ingredients, tomorrow.date())
                
                print(f"✅ Evening grocery list generated successfully for {tomorrow.date()}")
                
        except Exception as e:
            print(f"❌ Error in evening grocery task: {e}")
    
    def _display_meal_plan(self, meal_plan: MealPlan):
        """Display meal plan in terminal."""
        print("\n" + "="*60)
        print(f"🍽️ MEAL PLAN FOR {meal_plan.date.strftime('%A, %B %d, %Y').upper()}")
        print("="*60)
        
        # Display breakfast
        if meal_plan.breakfast:
            print(f"\n🌅 BREAKFAST: {meal_plan.breakfast.name}")
            print(f"   ⏱️ Prep: {meal_plan.breakfast.prep_time}min | Cook: {meal_plan.breakfast.cook_time}min")
            print(f"   📊 {meal_plan.breakfast.nutrition.calories} kcal | P: {meal_plan.breakfast.nutrition.protein}g | C: {meal_plan.breakfast.nutrition.carbs}g | F: {meal_plan.breakfast.nutrition.fat}g")
            
            print("   📝 Ingredients:")
            for i, ingredient in enumerate(meal_plan.breakfast.ingredients[:5], 1):
                print(f"      {i}. {ingredient}")
            if len(meal_plan.breakfast.ingredients) > 5:
                print(f"      ... and {len(meal_plan.breakfast.ingredients) - 5} more")
        
        # Display lunch
        if meal_plan.lunch:
            print(f"\n☀️ LUNCH: {meal_plan.lunch.name}")
            print(f"   ⏱️ Prep: {meal_plan.lunch.prep_time}min | Cook: {meal_plan.lunch.cook_time}min")
            print(f"   📊 {meal_plan.lunch.nutrition.calories} kcal | P: {meal_plan.lunch.nutrition.protein}g | C: {meal_plan.lunch.nutrition.carbs}g | F: {meal_plan.lunch.nutrition.fat}g")
            
            print("   📝 Ingredients:")
            for i, ingredient in enumerate(meal_plan.lunch.ingredients[:5], 1):
                print(f"      {i}. {ingredient}")
            if len(meal_plan.lunch.ingredients) > 5:
                print(f"      ... and {len(meal_plan.lunch.ingredients) - 5} more")
        
        # Display dinner
        if meal_plan.dinner:
            print(f"\n🌙 DINNER: {meal_plan.dinner.name}")
            print(f"   ⏱️ Prep: {meal_plan.dinner.prep_time}min | Cook: {meal_plan.dinner.cook_time}min")
            print(f"   📊 {meal_plan.dinner.nutrition.calories} kcal | P: {meal_plan.dinner.nutrition.protein}g | C: {meal_plan.dinner.nutrition.carbs}g | F: {meal_plan.dinner.nutrition.fat}g")
            
            print("   📝 Ingredients:")
            for i, ingredient in enumerate(meal_plan.dinner.ingredients[:5], 1):
                print(f"      {i}. {ingredient}")
            if len(meal_plan.dinner.ingredients) > 5:
                print(f"      ... and {len(meal_plan.dinner.ingredients) - 5} more")
        
        # Display nutrition summary
        total_nutrition = meal_plan.get_total_nutrition()
        print(f"\n📊 DAILY NUTRITION SUMMARY:")
        print(f"   • Calories: {total_nutrition.calories} kcal")
        print(f"   • Protein: {total_nutrition.protein}g")
        print(f"   • Carbs: {total_nutrition.carbs}g")
        print(f"   • Fat: {total_nutrition.fat}g")
        
        print(f"\n⏰ Total Prep Time: {sum(r.total_time for r in meal_plan.get_all_recipes())} minutes")
        print("="*60)
    
    def _display_grocery_list(self, ingredients, target_date: date):
        """Display grocery list in terminal."""
        print("\n" + "="*60)
        print(f"🛒 GROCERY LIST FOR {target_date.strftime('%A, %B %d, %Y').upper()}")
        print("="*60)
        
        # Group ingredients by category
        categories = {}
        for ingredient in ingredients:
            category = ingredient.category or "Other"
            if category not in categories:
                categories[category] = []
            categories[category].append(ingredient)
        
        # Display ingredients by category
        for category, items in categories.items():
            print(f"\n📦 {category.upper()}:")
            for i, ingredient in enumerate(items, 1):
                print(f"   {i}. {ingredient}")
        
        # Display summary
        total_items = len(ingredients)
        print(f"\n📋 Total Items: {total_items}")
        print(f"💰 Estimated Cost: ${total_items * 2:.2f} - ${total_items * 4:.2f}")
        print(f"⏰ Shopping Time: ~{max(15, total_items * 2)} minutes")
        
        print("\n💡 Tips:")
        print("   • Check your pantry first")
        print("   • Buy fresh ingredients last")
        print("   • Consider meal prep containers")
        print("="*60)
    
    def run_manual_task(self, task_type: str, target_date: Optional[date] = None):
        """Run a task manually."""
        if task_type == "meal_plan":
            if target_date is None:
                target_date = datetime.now().date()
            
            print(f"🍽️ Manually generating meal plan for {target_date}")
            
            # Generate meal plan
            meal_plan_recipes = recipe_generator.generate_meal_plan(
                datetime.combine(target_date, datetime.min.time())
            )
            
            meal_plan = MealPlan(
                date=datetime.combine(target_date, datetime.min.time()),
                breakfast=meal_plan_recipes.get('breakfast'),
                lunch=meal_plan_recipes.get('lunch'),
                dinner=meal_plan_recipes.get('dinner')
            )
            
            # Save and display
            db.save_meal_plan(meal_plan)
            self._display_meal_plan(meal_plan)
            
            print(f"✅ Manual meal plan generated successfully for {target_date}")
        
        elif task_type == "grocery_list":
            if target_date is None:
                target_date = (datetime.now() + timedelta(days=1)).date()
            
            print(f"🛒 Manually generating grocery list for {target_date}")
            
            # Get or generate meal plan
            meal_plan = db.get_meal_plan(target_date)
            
            if not meal_plan:
                # Generate meal plan first
                meal_plan_recipes = recipe_generator.generate_meal_plan(
                    datetime.combine(target_date, datetime.min.time())
                )
                
                meal_plan = MealPlan(
                    date=datetime.combine(target_date, datetime.min.time()),
                    breakfast=meal_plan_recipes.get('breakfast'),
                    lunch=meal_plan_recipes.get('lunch'),
                    dinner=meal_plan_recipes.get('dinner')
                )
                
                db.save_meal_plan(meal_plan)
            
            # Generate and display grocery list
            ingredients = meal_plan.get_grocery_list()
            db.save_grocery_list(target_date, ingredients)
            
            self._display_grocery_list(ingredients, target_date)
            
            print(f"✅ Manual grocery list generated successfully for {target_date}")
        
        else:
            print(f"❌ Unknown task type: {task_type}")
    
    def get_next_run_times(self):
        """Get the next scheduled run times."""
        next_runs = []
        
        for job in schedule.jobs:
            next_runs.append({
                "task": job.job_func.__name__,
                "next_run": job.next_run
            })
        
        return next_runs

# Global scheduler instance
scheduler = MealPlannerScheduler() 