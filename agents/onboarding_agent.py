import json
import anthropic
from models.user_profile import UserProfile
from utils.prompts import ONBOARDING_SYSTEM_PROMPT, PROFILE_EXTRACTION_PROMPT

_client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"
COMPLETION_SIGNAL = "Great! I have everything I need. Let me generate your personalized plan!"


def chat(user_message: str, history: list[dict], profile: UserProfile) -> tuple[str, UserProfile]:
    """
    Send a user message to the onboarding agent.
    Returns (ai_reply, updated_profile).
    history: list of {role: "user"|"assistant", content: str}
    """
    messages = history + [{"role": "user", "content": user_message}]

    response = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=ONBOARDING_SYSTEM_PROMPT,
        messages=messages,
    )
    reply = response.content[0].text

    # Extract profile fields from full conversation so far
    updated_profile = _extract_profile(messages + [{"role": "assistant", "content": reply}], profile)

    return reply, updated_profile


def get_opening_message() -> str:
    """Generate the first greeting message from the assistant."""
    response = _client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=ONBOARDING_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": "Hello, I want to get a personalized fitness and diet plan.",
            }
        ],
    )
    return response.content[0].text


def is_complete(reply: str) -> bool:
    """Check if the onboarding agent has signaled completion."""
    return COMPLETION_SIGNAL.lower() in reply.lower()


def _extract_profile(messages: list[dict], existing_profile: UserProfile) -> UserProfile:
    """
    Run a secondary Claude call to extract structured profile data from the conversation.
    Merges results into the existing profile (only overwrites non-empty values).
    """
    conversation_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )

    prompt = PROFILE_EXTRACTION_PROMPT.format(conversation=conversation_text)

    try:
        response = _client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        extracted = json.loads(raw)
        return _merge_profile(existing_profile, extracted)

    except (json.JSONDecodeError, Exception):
        # If extraction fails, return the profile unchanged
        return existing_profile


def _merge_profile(profile: UserProfile, data: dict) -> UserProfile:
    """Merge extracted data into profile, only overwriting if new value is meaningful."""
    for key, value in data.items():
        if not hasattr(profile, key):
            continue
        if value is None or value == "" or value == []:
            continue
        setattr(profile, key, value)
    return profile
