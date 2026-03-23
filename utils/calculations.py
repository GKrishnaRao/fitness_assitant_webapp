from models.user_profile import UserProfile


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}

CALORIC_ADJUSTMENTS = {
    "lose_weight": -500,
    "gain_muscle": 300,
    "maintain": 0,
    "improve_endurance": 200,
    "general_health": 0,
}

BMI_CATEGORIES = [
    (0, 18.5, "Underweight"),
    (18.5, 25, "Normal weight"),
    (25, 30, "Overweight"),
    (30, 35, "Obese (Class I)"),
    (35, 40, "Obese (Class II)"),
    (40, float("inf"), "Obese (Class III)"),
]


def compute_metrics(profile: UserProfile) -> dict:
    h_m = profile.height_cm / 100
    bmi = round(profile.weight_kg / (h_m ** 2), 1)

    bmi_category = next(
        cat for lo, hi, cat in BMI_CATEGORIES if lo <= bmi < hi
    )

    # Mifflin-St Jeor BMR
    if profile.gender.lower() in ("male", "m"):
        bmr = (10 * profile.weight_kg) + (6.25 * profile.height_cm) - (5 * profile.age) + 5
    else:
        bmr = (10 * profile.weight_kg) + (6.25 * profile.height_cm) - (5 * profile.age) - 161

    multiplier = ACTIVITY_MULTIPLIERS.get(profile.activity_level, 1.375)
    tdee = bmr * multiplier

    adjustment = CALORIC_ADJUSTMENTS.get(profile.fitness_goal, 0)
    daily_calories = round(tdee + adjustment)

    # Macros
    protein_g = round(profile.weight_kg * 2.2)  # ~1g per lb bodyweight
    fat_g = round((daily_calories * 0.25) / 9)
    carbs_g = round((daily_calories - (protein_g * 4) - (fat_g * 9)) / 4)

    # Ideal weight range (BMI 18.5–24.9)
    ideal_weight_min = round(18.5 * (h_m ** 2), 1)
    ideal_weight_max = round(24.9 * (h_m ** 2), 1)

    return {
        "bmi": bmi,
        "bmi_category": bmi_category,
        "bmr": round(bmr),
        "tdee": round(tdee),
        "daily_calories": daily_calories,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
        "ideal_weight_min_kg": ideal_weight_min,
        "ideal_weight_max_kg": ideal_weight_max,
    }
