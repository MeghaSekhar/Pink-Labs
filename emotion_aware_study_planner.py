# emotion_aware_study_planner.py
import json
import os
import calendar
import random
from datetime import datetime, date

DATA_FILE = "planner_data.json"

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
TECHNIQUES = {
    "pomodoro": {
        "name": "Pomodoro (focus sprints)",
        "how": "Study 25–30 minutes, then 5-minute breaks; after 3–4 rounds, take a longer 20–30 minute break."
    },
    "active_recall": {
        "name": "Active Recall",
        "how": "Test yourself from memory before checking notes."
    },
    "spaced_repetition": {
        "name": "Spaced Repetition",
        "how": "Review material over increasing intervals instead of cramming."
    },
    "interleaving": {
        "name": "Interleaving",
        "how": "Mix related topics instead of studying one type only."
    },
}

MOTIVATION_LINES = [
    "Tiny consistent sessions beat random all-nighters.",
    "You don’t need a perfect day, just one honest study block.",
    "Rest is part of the plan, not outside it.",
    "Start small. Momentum will take care of the rest.",
    "You’re building a system, not chasing a mood.",
]

# ---------------------------------------------------------
# DATA
# ---------------------------------------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "tasks": [],
            "logs": [],
            "technique_stats": {},
            "journals": [],
            "achievements": [],
        }
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    for key in ["tasks", "logs", "journals", "achievements"]:
        data.setdefault(key, [])
    data.setdefault("technique_stats", {})
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def generate_task_id(data):
    return max((t["id"] for t in data["tasks"]), default=0) + 1

def safe_parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return date.max

def get_task_deadline_info(task):
    try:
        due = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
    except Exception:
        return None, "no due date"

    today = date.today()
    delta = (due - today).days
    if delta < 0:
        return delta, f"{abs(delta)} day(s) overdue"
    if delta == 0:
        return delta, "today"
    if delta == 1:
        return delta, "in 1 day"
    return delta, f"in {delta} days"

def pick_motivation_line():
    return random.choice(MOTIVATION_LINES)

# ---------------------------------------------------------
# CORE PLANNING LOGIC
# ---------------------------------------------------------
def get_daily_budget(mood, energy, sleep_hours):
    score = mood + energy
    if sleep_hours < 5:
        return 45
    if score <= 4:
        return 60
    if score <= 6:
        return 90
    if score <= 8:
        return 120
    return 180

def allowed_difficulties(mood, energy, sleep_hours):
    if sleep_hours < 5 or mood <= 2 or energy <= 2:
        return ["easy"]
    if mood == 3 or energy == 3:
        return ["easy", "medium"]
    return ["easy", "medium", "hard"]

def plan_today_for_app(mood, energy, sleep_hours):
    data = load_data()
    messages = []

    budget = get_daily_budget(mood, energy, sleep_hours)
    allowed = allowed_difficulties(mood, energy, sleep_hours)

    pending = [
        t for t in data["tasks"]
        if not t["completed"] and t["difficulty"] in allowed
    ]

    if not pending:
        return {
            "budget": budget,
            "tasks": [],
            "messages": ["No suitable tasks today. Rest is allowed."],
            "max_difficulty": 0,
        }

    pending.sort(key=lambda t: (safe_parse_date(t["due_date"]), t["estimated_minutes"]))

    chosen, total = [], 0
    for t in pending:
        if total + t["estimated_minutes"] <= budget:
            chosen.append(t)
            total += t["estimated_minutes"]

    if not chosen:
        chosen = [pending[0]]

    messages.append(f"Today's budget: ~{budget} minutes.")

    diff_map = {"easy": 1, "medium": 2, "hard": 3}
    max_diff = max(diff_map.get(t["difficulty"], 1) for t in chosen)

    data["logs"].append({
        "date": date.today().isoformat(),
        "mood": mood,
        "energy": energy,
        "sleep_hours": sleep_hours,
        "planned_task_ids": [t["id"] for t in chosen],
        "completed_task_ids": [],
        "technique_used": None,
    })
    save_data(data)

    return {
        "budget": budget,
        "tasks": chosen,
        "messages": messages,
        "max_difficulty": max_diff,
    }

# ---------------------------------------------------------
# STREAMLIT APP HELPERS
# ---------------------------------------------------------
def get_tasks_for_app():
    return load_data()["tasks"]

def add_task_from_app(subject, topic, difficulty, est_minutes, due_str, planned_time=None):
    data = load_data()
    task = {
        "id": generate_task_id(data),
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "estimated_minutes": int(est_minutes),
        "due_date": due_str,
        "planned_time": planned_time,
        "completed": False,
    }
    data["tasks"].append(task)
    save_data(data)
    return task

def delete_task_from_app(task_id):
    data = load_data()
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_data(data)
    return True

def set_task_completed_from_app(task_id, completed):
    data = load_data()
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["completed"] = completed
    save_data(data)

def get_motivation_for_app():
    return pick_motivation_line()

def get_techniques_for_app():
    return [
        {"code": k, "name": v["name"], "how": v["how"]}
        for k, v in TECHNIQUES.items()
    ]

def suggest_technique_for_app(mood, energy, max_difficulty):
    if mood <= 2 or energy <= 2:
        code = "pomodoro"
    elif max_difficulty >= 3:
        code = random.choice(["active_recall", "interleaving"])
    else:
        code = random.choice(list(TECHNIQUES.keys()))

    tech = TECHNIQUES[code]
    return {"code": code, "name": tech["name"], "how": tech["how"]}

def save_technique_usage_from_app(code):
    data = load_data()
    stats = data.setdefault("technique_stats", {})
    stats[code] = stats.get(code, 0) + 1
    save_data(data)

def get_technique_stats_for_app():
    data = load_data()
    return [
        {"code": c, "name": TECHNIQUES[c]["name"], "count": n}
        for c, n in data.get("technique_stats", {}).items()
    ]
