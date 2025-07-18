# 🍽️ AI-Powered Meal Planning Automation System

An intelligent, CLI based local automation system that generates personalized meal plans and grocery lists using AI

## ✨ Features

- **🤖 AI-Powered Recipe Generation**: Uses Ollama (local LLM) to create personalized recipes
- **📅 Automated Scheduling**: Sends meal plans at 8:00 AM and grocery lists at 9:00 PM daily
- **🎯 Macro Tracking**: Recipes match your daily nutrition goals (2000 kcal, 150g protein, 180g carbs, 60g fat)
- **⏰ Quick Prep**: All meals take under 30 minutes to prepare
- **🏷️ Cuisine & Protein Preferences**: Customizable cuisine style and preferred protein sources
- **💾 Local Storage**: All recipes and meal plans stored locally in SQLite database
- **🔄 Smart Grocery Lists**: Automatically consolidates ingredients from all meals

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Ollama** installed and running locally


### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd Recipe_Automation
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install and start Ollama:**

   ```bash
   # Install Ollama (macOS)
   curl -fsSL https://ollama.ai/install.sh | sh

   # Start Ollama and pull a model
   ollama serve
   ollama pull llama2
   ```

4. **Configure the system:**

   ```bash
   python main.py setup
   ```

5. **Test the system:**

   ```bash
   python main.py test
   ```

6. **Start the automation:**
   ```bash
   python main.py start
   ```

## 📋 Configuration

### Environment Variables

Copy `env_example.txt` to `.env` and configure:

```bash
# WhatsApp API Configuration
WHATSAPP_API_URL=https://api.whatsapp.com/v1/messages
WHATSAPP_TOKEN=your_whatsapp_api_token_here
PHONE_NUMBER=+1234567890

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Database Configuration
DB_PATH=meal_planner.db
RECIPES_DIR=recipes
```

### User Preferences

Default settings (customizable via `config.py` or setup command):

- **Cuisine**: Indian
- **Preferred Protein**: Chicken
- **Max Prep Time**: 30 minutes
- **Daily Calories**: 2000
- **Daily Protein**: 150g
- **Daily Carbs**: 180g
- **Daily Fat**: 60g

## 🎮 Usage

### CLI Commands

```bash
# Start automated scheduling
python main.py start

# Test system components
python main.py test

# Generate meal plan manually
python main.py meal-plan
python main.py meal-plan --date 2024-01-15

# Generate grocery list manually
python main.py grocery-list
python main.py grocery-list --date 2024-01-16

# Show system status
python main.py status

# View saved recipes
python main.py recipes

# Interactive setup
python main.py setup
```

### Automated Schedule

- **8:00 AM**: Daily meal plan (breakfast, lunch, dinner)
- **9:00 PM**: Grocery list for next day's meals

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scheduler     │    │ Recipe Generator│    │   Database      │
│                 │    │                 │    │                 │
│ • Morning Task  │───▶│ • Ollama LLM    │───▶│ • SQLite        │
│ • Evening Task  │    │ • AI Recipes    │    │ • Local Storage │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ WhatsApp Sender │    │   Models        │    │   Config        │
│                 │    │                 │    │                 │
│ • Message Format│    │ • Recipe        │    │ • User Prefs    │
│ • API Integration│   │ • MealPlan      │    │ • Macro Goals   │
└─────────────────┘    │ • Ingredient    │    │ • Schedule      │
                       └─────────────────┘    └─────────────────┘
```

## 📊 Data Models

### Recipe

```python
{
    "name": "Chicken Tikka Masala",
    "cuisine": "Indian",
    "meal_type": "dinner",
    "prep_time": 15,
    "cook_time": 25,
    "ingredients": [...],
    "instructions": [...],
    "nutrition": {
        "calories": 450,
        "protein": 30,
        "carbs": 40,
        "fat": 20
    }
}
```

### Meal Plan

```python
{
    "date": "2024-01-15",
    "breakfast": Recipe(...),
    "lunch": Recipe(...),
    "dinner": Recipe(...)
}
```


## 🤖 Ollama Integration

The system uses Ollama for local AI recipe generation:

1. **Install Ollama**: Follow instructions at [ollama.ai](https://ollama.ai)
2. **Pull a model**: `ollama pull llama2` (or any other model)
3. **Configure**: Set `OLLAMA_MODEL` in your environment

### Supported Models

- llama2
- llama2:7b
- llama2:13b
- codellama
- mistral
- Any other Ollama-compatible model

## 📁 Project Structure

```
Recipe_Automation/
├── main.py              # CLI entry point
├── config.py            # Configuration management
├── models.py            # Data models
├── database.py          # SQLite database operations
├── recipe_generator.py  # AI recipe generation
├── whatsapp_sender.py   # WhatsApp integration
├── scheduler.py         # Automated scheduling
├── requirements.txt     # Python dependencies
├── env_example.txt      # Environment variables template
├── README.md           # This file
└── meal_planner.db     # SQLite database (created automatically)
```

## 🛠️ Development

### Adding New Features

1. **New Recipe Sources**: Extend `recipe_generator.py`
2. **New Data Models**: Add to `models.py`
3. **Database Changes**: Modify `database.py`

### Testing

```bash
# Test individual components
python main.py test

# Test recipe generation
python -c "from recipe_generator import recipe_generator; print(recipe_generator.generate_recipe('breakfast', 'Indian', 'chicken', {'calories': 500, 'protein': 25, 'carbs': 45, 'fat': 20}))"
```

## 🔒 Privacy & Security

- **Local Processing**: All AI processing happens locally via Ollama
- **No Cloud Dependencies**: No data sent to external services
- **Local Storage**: All data stored in local SQLite database
- **Optional WhatsApp**: Can run without WhatsApp integration

## 🐛 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**

   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags

   # Start Ollama if needed
   ollama serve
   ```


2. **Database Errors**
   ```bash
   # Reset database
   rm meal_planner.db
   python main.py test
   ```

### Logs

The system provides detailed logging:

- Recipe generation status
- Database operations
- Scheduler events

## 📈 Future Enhancements

- [ ] Recipe rating and feedback system
- [ ] Meal plan history and analytics
- [ ] Integration with grocery delivery services
- [ ] Nutritional goal tracking over time
- [ ] Recipe sharing and social features
- [ ] Mobile app companion
- [ ] Voice assistant integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local LLM capabilities
- [Pydantic](https://pydantic.dev) for data validation
- [Typer](https://typer.tiangolo.com) for CLI interface
- [Rich](https://rich.readthedocs.io) for beautiful terminal output

---

**Happy Meal Planning! 🍽️✨**
