import anthropic
from models.user_profile import UserProfile
from utils.prompts import FITNESS_SYSTEM_PROMPT
from utils.calculations import compute_metrics

_client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


def generate(profile: UserProfile) -> str:
    """Generate a personalized weekly fitness plan for the given profile."""
    metrics = compute_metrics(profile)

    user_message = f"""
Please create a personalized weekly fitness plan for this client:

{profile.to_summary()}

**Calculated Metrics:**
- BMI: {metrics['bmi']} ({metrics['bmi_category']})
- Daily Calorie Target: {metrics['daily_calories']} kcal
- Protein Target: {metrics['protein_g']}g (important for muscle recovery)
""".strip()

    response = _client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=FITNESS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def generate_stream(profile: UserProfile):
    """Generator that streams the fitness plan token by token."""
    metrics = compute_metrics(profile)

    user_message = f"""
Please create a personalized weekly fitness plan for this client:

{profile.to_summary()}

**Calculated Metrics:**
- BMI: {metrics['bmi']} ({metrics['bmi_category']})
- Daily Calorie Target: {metrics['daily_calories']} kcal
- Protein Target: {metrics['protein_g']}g (important for muscle recovery)
""".strip()

    with _client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        system=FITNESS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            yield text
