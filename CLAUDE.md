# AI Health & Fitness Planner

## Project Overview

A personalized health and fitness web application built with **Python + Streamlit**, powered by Claude AI agents. The app collects user profile information through a conversational chatbot interface, then generates tailored dietary and fitness plans using a multi-agent architecture.

## Core Concept

The application uses a **two-phase flow**:
1. **Onboarding Chat** — A guided conversation collecting user health profile data
2. **Plan Generation** — Specialized AI agents produce personalized diet and fitness plans

---

## Tech Stack

- **UI Framework**: Streamlit
- **Language**: Python 3.11+
- **AI**: Anthropic Claude API (`claude-sonnet-4-6`) via `anthropic` Python SDK
- **Multi-agent**: Two specialized Claude agents (Diet Agent + Fitness Agent) coordinated by an Orchestrator, plus an Onboarding Agent
- **State**: `st.session_state` for all app state and conversation history
- **Streaming**: Streamlit `st.write_stream` with Claude streaming responses
- **Async**: `asyncio` + `concurrent.futures` for parallel agent calls
- **Config**: `python-dotenv` for environment variables

---

## Project Structure

```
fitness_webapp/
├── app.py                     # Main Streamlit entry point
├── agents/
│   ├── __init__.py
│   ├── onboarding_agent.py    # Conversational profile collector
│   ├── diet_agent.py          # Diet & nutrition specialist
│   ├── fitness_agent.py       # Workout & exercise specialist
│   └── orchestrator.py        # Coordinates diet + fitness agents in parallel
├── utils/
│   ├── __init__.py
│   ├── calculations.py        # BMI, TDEE, macro calculations
│   └── prompts.py             # System prompt templates
├── components/
│   ├── __init__.py
│   ├── chat_ui.py             # Chat bubble rendering helpers
│   ├── metrics_card.py        # BMI / TDEE / macro display
│   ├── diet_plan_view.py      # Diet plan tab rendering
│   └── fitness_plan_view.py   # Fitness plan tab rendering
├── models/
│   ├── __init__.py
│   └── user_profile.py        # UserProfile dataclass
├── .env                       # ANTHROPIC_API_KEY (gitignored)
├── requirements.txt
└── CLAUDE.md
```

---

## User Profile Data Model

`models/user_profile.py` — collected during onboarding chat:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class UserProfile:
    # Basic Info
    name: str = ""
    age: Optional[int] = None
    gender: str = ""                # male | female | other

    # Physical Metrics
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None

    # Lifestyle
    activity_level: str = ""        # sedentary | lightly_active | moderately_active | very_active | extra_active

    # Goals
    fitness_goal: str = ""          # lose_weight | gain_muscle | maintain | improve_endurance | general_health
    target_weight_kg: Optional[float] = None
    timeline_weeks: Optional[int] = None

    # Diet
    dietary_preference: str = "none"  # none | vegetarian | vegan | keto | low_carb | mediterranean | paleo
    food_allergies: list[str] = field(default_factory=list)
    meals_per_day: int = 3

    # Health
    medical_conditions: list[str] = field(default_factory=list)
    injuries_or_limitations: str = ""

    # Fitness Background
    fitness_level: str = ""         # beginner | intermediate | advanced
    available_equipment: list[str] = field(default_factory=list)
    workout_days_per_week: int = 3
    workout_duration_minutes: int = 45

    def is_complete(self) -> bool:
        required = [self.name, self.age, self.gender, self.weight_kg,
                    self.height_cm, self.activity_level, self.fitness_goal,
                    self.fitness_level, self.workout_days_per_week]
        return all(required)
```

---

## Multi-Agent System

### Onboarding Agent (`agents/onboarding_agent.py`)
- Uses Claude with structured system prompt to act as a friendly health coach
- Sends/receives messages using full conversation history from `st.session_state`
- Extracts profile fields from conversation using a secondary Claude call that returns JSON
- Calls `profile.is_complete()` to detect when to stop asking questions
- Does NOT generate plans

```python
def chat(user_message: str, history: list, profile: UserProfile) -> tuple[str, UserProfile]:
    """Returns (ai_reply, updated_profile)"""
```

### Orchestrator (`agents/orchestrator.py`)
- Receives completed `UserProfile`
- Calls `diet_agent.generate()` and `fitness_agent.generate()` concurrently using `ThreadPoolExecutor`
- Also calls `calculations.compute_metrics()` for BMI/TDEE/macros
- Returns `dict` with keys: `metrics`, `diet_plan`, `fitness_plan`

```python
def generate_plans(profile: UserProfile) -> dict:
    with ThreadPoolExecutor(max_workers=2) as executor:
        diet_future = executor.submit(diet_agent.generate, profile)
        fitness_future = executor.submit(fitness_agent.generate, profile)
    return {
        "metrics": compute_metrics(profile),
        "diet_plan": diet_future.result(),
        "fitness_plan": fitness_future.result(),
    }
```

### Diet Agent (`agents/diet_agent.py`)
System prompt persona: Registered Dietitian
Generates:
- 7-day meal plan (breakfast, lunch, dinner, snacks)
- Calorie + macro breakdown per meal
- Hydration targets, fiber and electrolyte notes
- Weekly grocery list
- Adjusts for dietary preference, allergies, caloric target

### Fitness Agent (`agents/fitness_agent.py`)
System prompt persona: Certified Personal Trainer
Generates:
- Weekly workout schedule matching `workout_days_per_week`
- Each session: warm-up → main workout → cool-down
- Sets, reps, rest periods per exercise
- Scaled to equipment and fitness level
- 4-week and 8-week progress milestones
- Modifications for any injuries/limitations

---

## Streamlit App Flow (`app.py`)

### Session State Keys
```python
st.session_state.messages        # list[dict] — chat history {role, content}
st.session_state.profile         # UserProfile instance
st.session_state.phase           # "onboarding" | "generating" | "dashboard"
st.session_state.plans           # dict with metrics, diet_plan, fitness_plan
```

### Page Routing
```
phase == "onboarding"  →  show Chat UI (chatbot interface)
phase == "generating"  →  show spinner + progress while agents run
phase == "dashboard"   →  show Metrics Card + Diet Plan tab + Fitness Plan tab
                          + Follow-up Q&A chat at bottom
```

### Onboarding Chat UI
- Render all messages from `st.session_state.messages` as chat bubbles using `st.chat_message`
- `st.chat_input` at bottom for user input
- On submit: call `onboarding_agent.chat()`, append both messages to history
- When `profile.is_complete()`: show confirmation summary, "Generate My Plan" button
- On button click: set `phase = "generating"`, call `orchestrator.generate_plans()`

### Dashboard UI
- `st.metric` row: BMI, Daily Calories, Protein, Carbs, Fat
- `st.tabs(["Diet Plan", "Fitness Plan"])` for plan content
- Plans rendered as markdown inside `st.container` with `st.markdown`
- Follow-up Q&A: second `st.chat_input` that sends questions to a general Claude call with plan context

---

## Calculated Metrics (`utils/calculations.py`)

```python
def compute_metrics(profile: UserProfile) -> dict:
    h_m = profile.height_cm / 100
    bmi = round(profile.weight_kg / (h_m ** 2), 1)

    # Mifflin-St Jeor BMR
    if profile.gender == "male":
        bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
    else:
        bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161

    multipliers = {
        "sedentary": 1.2, "lightly_active": 1.375,
        "moderately_active": 1.55, "very_active": 1.725, "extra_active": 1.9,
    }
    tdee = bmr * multipliers[profile.activity_level]

    adjustments = {
        "lose_weight": -500, "gain_muscle": +300, "maintain": 0,
        "improve_endurance": +200, "general_health": 0,
    }
    calories = round(tdee + adjustments[profile.fitness_goal])

    protein_g = round(profile.weight_kg * 2.2)
    fat_g = round((calories * 0.25) / 9)
    carbs_g = round((calories - protein_g * 4 - fat_g * 9) / 4)

    return {
        "bmi": bmi,
        "tdee": round(tdee),
        "daily_calories": calories,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
    }
```

---

## Onboarding Chat Flow

The onboarding agent asks questions in this sequence:

**Phase 1 — Personal Info**
1. "Hi! I'm your AI fitness coach. What's your name?"
2. "Nice to meet you, [name]! How old are you?"
3. "What's your gender? (male / female / other)"
4. "What's your current weight? (e.g. 70 kg or 154 lbs)"
5. "What's your height? (e.g. 175 cm or 5'9\")"

**Phase 2 — Goals**
6. "What's your primary fitness goal?" (lose weight / gain muscle / maintain / improve endurance / general health)
7. "Do you have a target weight and timeline in mind?"
8. "How would you rate your current fitness level?" (beginner / intermediate / advanced)

**Phase 3 — Diet**
9. "Do you follow any specific diet?" (none / vegetarian / vegan / keto / low carb / mediterranean / paleo)
10. "Any food allergies or foods you avoid?"
11. "How many meals do you prefer per day?"

**Phase 4 — Fitness**
12. "How many days per week can you commit to working out?"
13. "How long can each session be? (in minutes)"
14. "What equipment do you have access to?" (gym / dumbbells / resistance bands / bodyweight only)
15. "Any injuries or physical limitations I should know about?"

**Phase 5 — Confirmation**
- Show profile summary table
- "Generate My Plan" button triggers orchestrator

---

## Key Implementation Notes

### Claude API Usage
```python
import anthropic
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

# Standard call
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=system_prompt,
    messages=conversation_history,
)

# Streaming (for plan display)
with client.messages.stream(model="claude-sonnet-4-6", ...) as stream:
    for text in stream.text_stream:
        yield text
```

### Onboarding Profile Extraction
After each user message, run a secondary lightweight Claude call:
```python
# Extract structured data from conversation so far
extraction_prompt = f"""
Given this conversation, extract any health profile fields mentioned.
Return ONLY valid JSON matching this schema: {profile_schema}
If a field wasn't mentioned, omit it.
Conversation: {conversation_text}
"""
```

### Streamlit Streaming
Use `st.write_stream` with a generator for live plan output:
```python
def stream_plan(profile):
    with client.messages.stream(...) as stream:
        for text in stream.text_stream:
            yield text

st.write_stream(stream_plan(profile))
```

### Environment Variables
```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Requirements (`requirements.txt`)

```
streamlit>=1.35.0
anthropic>=0.28.0
python-dotenv>=1.0.0
```

---

## Development Commands

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Add API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Run app
streamlit run app.py
```

---

## UI/UX Guidelines

- **Chat interface**: use `st.chat_message("user")` and `st.chat_message("assistant")` for native Streamlit chat bubbles
- **Sidebar**: show profile summary as it fills in during onboarding
- **Metrics row**: use `st.columns(5)` with `st.metric()` for BMI, calories, protein, carbs, fat
- **Plans**: use `st.tabs(["Diet Plan", "Fitness Plan"])` — render content as `st.markdown`
- **Color theme**: set via `.streamlit/config.toml` — use a clean green/teal primary color
- **Spinner**: `st.spinner("Generating your personalized plan...")` during agent calls

---

## Out of Scope (v1)

- User authentication / accounts
- Saving/loading historical plans
- Integration with wearables or fitness trackers
- Calorie tracking / food logging
- Video exercise demonstrations
- Payment / premium tiers
