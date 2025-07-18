#!/usr/bin/env python3
"""
Main entry point for the Meal Planning Automation System.
"""
import typer
import signal
import sys
from datetime import datetime, date, timedelta
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from config import config
from scheduler import scheduler
from database import db
from recipe_generator import recipe_generator

app = typer.Typer(help="AI-Powered Meal Planning Automation System")
console = Console()

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    console.print("\n🛑 Shutting down meal planner...", style="red")
    scheduler.stop()
    sys.exit(0)

@app.command()
def start():
    """Start the automated meal planning scheduler."""
    console.print(Panel.fit(
        "🍽️ Meal Planning Automation System",
        style="bold blue"
    ))
    
    # Check configuration
    console.print("🔧 Checking configuration...")
    
    # Test Ollama connection
    try:
        import ollama
        client = ollama.Client(host=config.ollama_url)
        models = client.list()
        console.print(f"✅ Ollama connected. Available models: {[m['name'] for m in models['models']]}")
    except Exception as e:
        console.print(f"❌ Ollama connection failed: {e}", style="red")
        console.print("Please make sure Ollama is running and the model is available.", style="yellow")
        return
    
    # Start scheduler
    console.print("\n🚀 Starting scheduler...")
    scheduler.start()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Keep the main thread alive
        while scheduler.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

@app.command()
def test():
    """Test the system components."""
    console.print("🧪 Testing system components...")
    
    # Test recipe generation
    console.print("\n🍳 Testing recipe generation...")
    try:
        recipe = recipe_generator.generate_recipe(
            meal_type="breakfast",
            cuisine=config.user_preferences.cuisine,
            preferred_protein=config.user_preferences.preferred_protein,
            macro_goals={"calories": 500, "protein": 25, "carbs": 45, "fat": 20}
        )
        console.print(f"✅ Recipe generated: {recipe.name}")
    except Exception as e:
        console.print(f"❌ Recipe generation failed: {e}", style="red")
    
    # Test database
    console.print("\n💾 Testing database...")
    try:
        db.init_database()
        console.print("✅ Database initialized successfully")
    except Exception as e:
        console.print(f"❌ Database test failed: {e}", style="red")

@app.command()
def meal_plan(
    target_date: Optional[str] = typer.Option(
        None, 
        "--date", 
        "-d", 
        help="Target date (YYYY-MM-DD). Defaults to today."
    )
):
    """Generate and display a meal plan manually."""
    if target_date:
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            console.print("❌ Invalid date format. Use YYYY-MM-DD", style="red")
            return
    else:
        target_date = datetime.now().date()
    
    console.print(f"🍽️ Generating meal plan for {target_date}...")
    scheduler.run_manual_task("meal_plan", target_date)

@app.command()
def grocery_list(
    target_date: Optional[str] = typer.Option(
        None, 
        "--date", 
        "-d", 
        help="Target date (YYYY-MM-DD). Defaults to tomorrow."
    )
):
    """Generate and display a grocery list manually."""
    if target_date:
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            console.print("❌ Invalid date format. Use YYYY-MM-DD", style="red")
            return
    else:
        target_date = (datetime.now().date() + timedelta(days=1))
    
    console.print(f"🛒 Generating grocery list for {target_date}...")
    scheduler.run_manual_task("grocery_list", target_date)

@app.command()
def status():
    """Show system status and configuration."""
    console.print(Panel.fit("📊 System Status", style="bold blue"))
    
    # Configuration
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Cuisine", config.user_preferences.cuisine)
    table.add_row("Preferred Protein", config.user_preferences.preferred_protein)
    table.add_row("Max Prep Time", f"{config.user_preferences.max_prep_time} minutes")
    table.add_row("Daily Calories", str(config.macro_goals.calories))
    table.add_row("Daily Protein", f"{config.macro_goals.protein}g")
    table.add_row("Daily Carbs", f"{config.macro_goals.carbs}g")
    table.add_row("Daily Fat", f"{config.macro_goals.fat}g")
    table.add_row("Meal Plan Time", config.schedule.breakfast_time)
    table.add_row("Grocery List Time", config.schedule.grocery_time)
    table.add_row("Ollama URL", config.ollama_url)
    table.add_row("Ollama Model", config.ollama_model)
    
    console.print(table)
    
    # Scheduler status
    console.print(f"\n⏰ Scheduler Status: {'🟢 Running' if scheduler.running else '🔴 Stopped'}")
    
    if scheduler.running:
        next_runs = scheduler.get_next_run_times()
        if next_runs:
            console.print("\n📅 Next Scheduled Runs:")
            for run in next_runs:
                console.print(f"  • {run['task']}: {run['next_run']}")

@app.command()
def recipes():
    """Show saved recipes."""
    console.print("📚 Saved Recipes")
    
    # Get recipes from database
    recipes = db.get_recipes_by_criteria()
    
    if not recipes:
        console.print("No recipes found in database.", style="yellow")
        return
    
    table = Table(title="Saved Recipes")
    table.add_column("Name", style="cyan")
    table.add_column("Cuisine", style="green")
    table.add_column("Meal Type", style="yellow")
    table.add_column("Prep Time", style="magenta")
    table.add_column("Calories", style="blue")
    
    for recipe in recipes:
        table.add_row(
            recipe.name,
            recipe.cuisine,
            recipe.meal_type,
            f"{recipe.prep_time}min",
            str(recipe.nutrition.calories)
        )
    
    console.print(table)

@app.command()
def setup():
    """Interactive setup for the meal planning system."""
    console.print(Panel.fit("⚙️ Interactive Setup", style="bold blue"))
    
    console.print("Let's configure your meal planning preferences:")
    
    # Cuisine preference
    cuisine = typer.prompt(
        "What cuisine do you prefer?",
        default=config.user_preferences.cuisine
    )
    
    # Protein preference
    protein = typer.prompt(
        "What's your preferred protein?",
        default=config.user_preferences.preferred_protein
    )
    
    # Max prep time
    prep_time = typer.prompt(
        "Maximum preparation time per meal (minutes)?",
        default=config.user_preferences.max_prep_time,
        type=int
    )
    
    # Daily calories
    calories = typer.prompt(
        "Daily calorie goal?",
        default=config.macro_goals.calories,
        type=int
    )
    
    # Save configuration
    console.print("\n💾 Saving configuration...")
    
    # Update config
    config.user_preferences.cuisine = cuisine
    config.user_preferences.preferred_protein = protein
    config.user_preferences.max_prep_time = prep_time
    config.macro_goals.calories = calories
    
    console.print("✅ Configuration saved!")
    console.print("\nYou can now run 'python main.py start' to begin automated meal planning.")

if __name__ == "__main__":
    app() 