import streamlit as st
from dotenv import load_dotenv
import anthropic

load_dotenv()

from models.user_profile import UserProfile
from agents import onboarding_agent, orchestrator
from components import render_metrics_card, render_diet_plan, render_fitness_plan
from utils.prompts import FOLLOWUP_SYSTEM_PROMPT

# ── Helper functions ───────────────────────────────────────────────────────────
def _stream_followup(client, context: str, messages: list[dict]):
    system = FOLLOWUP_SYSTEM_PROMPT + f"\n\n{context}"
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text


def _render_followup_chat(plans: dict, profile):
    st.markdown("### Ask Your AI Coach")
    st.caption("Ask anything about your plan — swap a meal, modify an exercise, explain a concept...")

    for msg in st.session_state.followup_messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑"):
            st.markdown(msg["content"])

    if question := st.chat_input("Ask a follow-up question...", key="followup_input"):
        with st.chat_message("user", avatar="🧑"):
            st.markdown(question)
        st.session_state.followup_messages.append({"role": "user", "content": question})

        context = f"""
User Profile:
{profile.to_summary()}

Calculated Metrics:
- BMI: {plans['metrics']['bmi']} ({plans['metrics']['bmi_category']})
- Daily Calories: {plans['metrics']['daily_calories']} kcal
- Protein: {plans['metrics']['protein_g']}g | Carbs: {plans['metrics']['carbs_g']}g | Fat: {plans['metrics']['fat_g']}g

Diet Plan:
{plans['diet_plan']}

Fitness Plan:
{plans['fitness_plan']}
""".strip()

        messages = st.session_state.followup_messages[:]
        client = anthropic.Anthropic()

        with st.chat_message("assistant", avatar="🤖"):
            response_text = st.write_stream(
                _stream_followup(client, context, messages)
            )

        st.session_state.followup_messages.append({"role": "assistant", "content": response_text})


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Health & Fitness Planner",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ─────────────────────────────────────────────────────────
def _init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []          # [{role, content}]
    if "profile" not in st.session_state:
        st.session_state.profile = UserProfile()
    if "phase" not in st.session_state:
        st.session_state.phase = "onboarding"   # onboarding | generating | dashboard
    if "plans" not in st.session_state:
        st.session_state.plans = {}             # metrics, diet_plan, fitness_plan
    if "followup_messages" not in st.session_state:
        st.session_state.followup_messages = [] # [{role, content}]
    if "greeted" not in st.session_state:
        st.session_state.greeted = False

_init_state()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💪 AI Fitness Planner")
    st.divider()

    if st.session_state.phase == "onboarding":
        st.markdown("### Profile Progress")
        profile = st.session_state.profile
        fields = {
            "Name": profile.name,
            "Age": profile.age,
            "Gender": profile.gender,
            "Weight": f"{profile.weight_kg} kg" if profile.weight_kg else None,
            "Height": f"{profile.height_cm} cm" if profile.height_cm else None,
            "Goal": profile.fitness_goal.replace("_", " ").title() if profile.fitness_goal else None,
            "Diet": profile.dietary_preference.replace("_", " ").title() if profile.dietary_preference else None,
            "Fitness Level": profile.fitness_level.title() if profile.fitness_level else None,
            "Workout Days": f"{profile.workout_days_per_week}/week" if profile.workout_days_per_week else None,
        }
        filled = sum(1 for v in fields.values() if v)
        total = len(fields)
        st.progress(filled / total, text=f"{filled}/{total} fields collected")

        for label, value in fields.items():
            if value:
                st.markdown(f"**{label}:** {value}")
            else:
                st.markdown(f"<span style='color:gray'>**{label}:** —</span>", unsafe_allow_html=True)

    elif st.session_state.phase == "dashboard":
        st.markdown("### Your Profile")
        st.markdown(st.session_state.profile.to_summary())
        st.divider()
        if st.button("Start Over", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.divider()
    st.caption("Powered by Claude claude-sonnet-4-6")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: ONBOARDING CHAT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "onboarding":
    st.markdown("## AI Health & Fitness Planner")
    st.markdown("Answer a few questions and get your personalized diet + workout plan.")
    st.divider()

    # Send greeting on first load
    if not st.session_state.greeted:
        with st.spinner(""):
            opening = onboarding_agent.get_opening_message()
        st.session_state.messages.append({"role": "assistant", "content": opening})
        st.session_state.greeted = True

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑"):
            st.markdown(msg["content"])

    # Profile complete — show confirmation and generate button
    profile = st.session_state.profile
    if profile.is_complete() and st.session_state.messages:
        last_msg = st.session_state.messages[-1]["content"]
        if onboarding_agent.is_complete(last_msg):
            st.divider()
            st.markdown("### Profile Summary")
            with st.expander("Review your details", expanded=True):
                st.markdown(profile.to_summary())

            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("Generate My Plan", type="primary", use_container_width=True):
                    st.session_state.phase = "generating"
                    st.rerun()
            with col2:
                if st.button("Edit Info", use_container_width=True):
                    # Allow more chat
                    pass

    # Chat input
    if user_input := st.chat_input("Type your answer here..."):
        # Show user message immediately
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Build history (exclude the current user message — already appended)
        history = st.session_state.messages[:-1]

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                reply, updated_profile = onboarding_agent.chat(
                    user_input, history, st.session_state.profile
                )
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.profile = updated_profile

        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: GENERATING PLANS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "generating":
    st.markdown("## Generating Your Personalized Plan")
    st.markdown("Our AI agents are working in parallel to craft your diet and fitness plan...")

    col1, col2 = st.columns(2)
    with col1:
        st.info("🥗 **Diet Agent** — Creating your 7-day meal plan...")
    with col2:
        st.info("🏋️ **Fitness Agent** — Building your workout schedule...")

    progress_bar = st.progress(0, text="Starting agents...")

    try:
        progress_bar.progress(10, text="Agents running in parallel...")
        plans = orchestrator.generate_plans(st.session_state.profile)
        progress_bar.progress(100, text="Complete!")

        st.session_state.plans = plans
        st.session_state.phase = "dashboard"
        st.rerun()

    except Exception as e:
        st.error(f"Something went wrong: {e}")
        if st.button("Try Again"):
            st.session_state.phase = "generating"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "dashboard":
    profile = st.session_state.profile
    plans = st.session_state.plans

    st.markdown(f"## Welcome, {profile.name}! Here's Your Personalized Plan")
    st.divider()

    # Metrics row
    render_metrics_card(plans["metrics"], profile)

    # Plan tabs
    tab_diet, tab_fitness, tab_qa = st.tabs(["🥗 Diet Plan", "🏋️ Fitness Plan", "💬 Ask Questions"])

    with tab_diet:
        render_diet_plan(plans["diet_plan"])

    with tab_fitness:
        render_fitness_plan(plans["fitness_plan"])

    with tab_qa:
        _render_followup_chat(plans, profile)
