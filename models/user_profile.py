from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserProfile:
    # Basic Info
    name: str = ""
    age: Optional[int] = None
    gender: str = ""  # male | female | other

    # Physical Metrics
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None

    # Lifestyle
    activity_level: str = ""  # sedentary | lightly_active | moderately_active | very_active | extra_active

    # Goals
    fitness_goal: str = ""  # lose_weight | gain_muscle | maintain | improve_endurance | general_health
    target_weight_kg: Optional[float] = None
    timeline_weeks: Optional[int] = None

    # Diet
    dietary_preference: str = "none"  # none | vegetarian | vegan | keto | low_carb | mediterranean | paleo
    food_allergies: list = field(default_factory=list)
    meals_per_day: int = 3

    # Health
    medical_conditions: list = field(default_factory=list)
    injuries_or_limitations: str = ""

    # Fitness Background
    fitness_level: str = ""  # beginner | intermediate | advanced
    available_equipment: list = field(default_factory=list)
    workout_days_per_week: int = 3
    workout_duration_minutes: int = 45

    def is_complete(self) -> bool:
        required = [
            self.name,
            self.age,
            self.gender,
            self.weight_kg,
            self.height_cm,
            self.activity_level,
            self.fitness_goal,
            self.fitness_level,
            self.workout_days_per_week,
        ]
        return all(v is not None and v != "" and v != 0 for v in required)

    def to_summary(self) -> str:
        """Human-readable summary for display and agent context."""
        allergies = ", ".join(self.food_allergies) if self.food_allergies else "None"
        equipment = ", ".join(self.available_equipment) if self.available_equipment else "Bodyweight only"
        conditions = ", ".join(self.medical_conditions) if self.medical_conditions else "None"

        return f"""
**Personal Info**
- Name: {self.name}
- Age: {self.age}
- Gender: {self.gender}

**Physical Metrics**
- Weight: {self.weight_kg} kg
- Height: {self.height_cm} cm

**Lifestyle & Goals**
- Activity Level: {self.activity_level.replace("_", " ").title()}
- Fitness Goal: {self.fitness_goal.replace("_", " ").title()}
- Target Weight: {f"{self.target_weight_kg} kg" if self.target_weight_kg else "Not specified"}
- Timeline: {f"{self.timeline_weeks} weeks" if self.timeline_weeks else "Not specified"}

**Diet**
- Dietary Preference: {self.dietary_preference.replace("_", " ").title()}
- Food Allergies: {allergies}
- Meals Per Day: {self.meals_per_day}

**Health**
- Medical Conditions: {conditions}
- Injuries / Limitations: {self.injuries_or_limitations or "None"}

**Fitness Background**
- Fitness Level: {self.fitness_level.title()}
- Available Equipment: {equipment}
- Workout Days/Week: {self.workout_days_per_week}
- Session Duration: {self.workout_duration_minutes} minutes
""".strip()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "activity_level": self.activity_level,
            "fitness_goal": self.fitness_goal,
            "target_weight_kg": self.target_weight_kg,
            "timeline_weeks": self.timeline_weeks,
            "dietary_preference": self.dietary_preference,
            "food_allergies": self.food_allergies,
            "meals_per_day": self.meals_per_day,
            "medical_conditions": self.medical_conditions,
            "injuries_or_limitations": self.injuries_or_limitations,
            "fitness_level": self.fitness_level,
            "available_equipment": self.available_equipment,
            "workout_days_per_week": self.workout_days_per_week,
            "workout_duration_minutes": self.workout_duration_minutes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        profile = cls()
        for key, value in data.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        return profile
