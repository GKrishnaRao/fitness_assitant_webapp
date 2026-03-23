import anthropic
from models.user_profile import UserProfile
from utils.prompts import DIET_SYSTEM_PROMPT
from utils.calculations import compute_metrics

_client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


def generate(profile: UserProfile) -> str:
    """Generate a personalized 7-day diet plan for the given profile."""
    metrics = compute_metrics(profile)

    user_message = f"""
Please create a personalized 7-day meal plan for this client:

{profile.to_summary()}

**Calculated Metrics:**
- BMI: {metrics['bmi']} ({metrics['bmi_category']})
- TDEE: {metrics['tdee']} kcal/day
- Daily Calorie Target: {metrics['daily_calories']} kcal
- Protein Target: {metrics['protein_g']}g
- Fat Target: {metrics['fat_g']}g
- Carbs Target: {metrics['carbs_g']}g
""".strip()

    response = _client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=DIET_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_stream(profile: UserProfile):
    """Generator that streams the diet plan token by token."""
    metrics = compute_metrics(profile)

    user_message = f"""
Please create a personalized 7-day meal plan for this client:

{profile.to_summary()}

**Calculated Metrics:**
- BMI: {metrics['bmi']} ({metrics['bmi_category']})
- TDEE: {metrics['tdee']} kcal/day
- Daily Calorie Target: {metrics['daily_calories']} kcal
- Protein Target: {metrics['protein_g']}g
- Fat Target: {metrics['fat_g']}g
- Carbs Target: {metrics['carbs_g']}g
""".strip()

    with _client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        system=DIET_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            yield text
