from concurrent.futures import ThreadPoolExecutor, as_completed
from models.user_profile import UserProfile
from utils.calculations import compute_metrics
from agents import diet_agent, fitness_agent


def generate_plans(profile: UserProfile) -> dict:
    """
    Run diet and fitness agents in parallel.
    Returns dict with keys: metrics, diet_plan, fitness_plan.
    """
    metrics = compute_metrics(profile)

    with ThreadPoolExecutor(max_workers=2) as executor:
        diet_future = executor.submit(diet_agent.generate, profile)
        fitness_future = executor.submit(fitness_agent.generate, profile)

        results = {}
        for future in as_completed([diet_future, fitness_future]):
            if future is diet_future:
                results["diet_plan"] = future.result()
            else:
                results["fitness_plan"] = future.result()

    return {
        "metrics": metrics,
        "diet_plan": results["diet_plan"],
        "fitness_plan": results["fitness_plan"],
    }
