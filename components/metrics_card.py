import streamlit as st


def render_metrics_card(metrics: dict, profile):
    """Render the top metrics row with BMI, calories, and macros."""
    st.markdown("### Your Health Metrics")

    bmi = metrics["bmi"]
    bmi_category = metrics["bmi_category"]

    # Color-code BMI
    if bmi < 18.5:
        bmi_color = "blue"
    elif bmi < 25:
        bmi_color = "green"
    elif bmi < 30:
        bmi_color = "orange"
    else:
        bmi_color = "red"

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(
            label="BMI",
            value=bmi,
            help=f"Category: {bmi_category}",
        )
        st.caption(f":{bmi_color}[{bmi_category}]")

    with col2:
        st.metric(
            label="TDEE",
            value=f"{metrics['tdee']} kcal",
            help="Total Daily Energy Expenditure — calories you burn at your activity level",
        )

    with col3:
        st.metric(
            label="Daily Target",
            value=f"{metrics['daily_calories']} kcal",
            delta=f"{metrics['daily_calories'] - metrics['tdee']:+d} from TDEE",
            help="Your adjusted daily calorie target based on your fitness goal",
        )

    with col4:
        st.metric(
            label="Protein",
            value=f"{metrics['protein_g']}g",
            help="Daily protein target (~1g per lb of bodyweight)",
        )

    with col5:
        st.metric(
            label="Carbs",
            value=f"{metrics['carbs_g']}g",
            help="Daily carbohydrate target",
        )

    with col6:
        st.metric(
            label="Fat",
            value=f"{metrics['fat_g']}g",
            help="Daily fat target (25% of total calories)",
        )

    st.divider()

    # Ideal weight range note
    ideal_min = metrics["ideal_weight_min_kg"]
    ideal_max = metrics["ideal_weight_max_kg"]
    current = profile.weight_kg
    if current < ideal_min:
        note = f"Your ideal weight range is **{ideal_min}–{ideal_max} kg**. You are **{round(ideal_min - current, 1)} kg below** the healthy range."
    elif current > ideal_max:
        note = f"Your ideal weight range is **{ideal_min}–{ideal_max} kg**. You are **{round(current - ideal_max, 1)} kg above** the healthy range."
    else:
        note = f"Your weight of **{current} kg** is within the healthy range of {ideal_min}–{ideal_max} kg."

    st.info(note)
