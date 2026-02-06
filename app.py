import streamlit as st
import time
from datetime import date

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Pink Focus Lab 💗📚",
    page_icon="💗",
    layout="wide",
)

# ---------------------------------------------------------
# STYLES
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            135deg,
            #FFB6F0 0%,
            #FFE6F7 35%,
            #FFC2EB 70%,
            #FFE6F7 100%
        );
        min-height: 100vh;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #C20063, #FF1493, #FF0066) !important;
        color: white !important;
    }

    h1, h2, h3 {
        color: #FF1493 !important;
        text-shadow: 0 0 6px rgba(255,182,240,0.9);
    }

    .stButton > button {
        background-color: #FF1493 !important;
        color: white !important;
        border-radius: 999px !important;
        font-weight: 700;
        border: 2px solid #FF8AD9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# IMPORT LOGIC
# ---------------------------------------------------------
from emotion_aware_study_planner import (
    plan_today_for_app,
    get_tasks_for_app,
    add_task_from_app,
    delete_task_from_app,
    set_task_completed_from_app,
    get_task_deadline_info,
    get_techniques_for_app,
    suggest_technique_for_app,
    save_technique_usage_from_app,
    get_technique_stats_for_app,
    get_motivation_for_app,
)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "timer_end" not in st.session_state:
    st.session_state.timer_end = None
if "timer_label" not in st.session_state:
    st.session_state.timer_label = None

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("Pink Focus Lab 💗📚")
st.caption("Soft productivity with emotional intelligence.")

page = st.sidebar.selectbox(
    "Section",
    ["Today's Plan", "Tasks", "Techniques"],
)

# ---------------------------------------------------------
# TODAY'S PLAN
# ---------------------------------------------------------
if page == "Today's Plan":
    st.header("Today's Plan 🧠")

    mood_map = {
        "Very low 🥺": 1,
        "Low 😞": 2,
        "Okay 🙂": 3,
        "Good 😊": 4,
        "Great 🤩": 5,
    }

    energy_map = {
        "Very low": 1,
        "Low": 2,
        "Medium": 3,
        "High": 4,
        "Very high": 5,
    }

    mood_label = st.selectbox("Mood 💭", mood_map.keys())
    energy_label = st.selectbox("Energy ⚡", energy_map.keys())
    sleep_hours = st.slider("Sleep last night (hours)", 0.0, 12.0, 7.0, 0.5)

    if st.button("Plan my study 💕"):
        plan = plan_today_for_app(
            mood_map[mood_label],
            energy_map[energy_label],
            sleep_hours,
        )

        st.subheader("Your plan for today")
        for msg in plan["messages"]:
            st.write(msg)

        if plan["tasks"]:
            st.markdown("**Suggested tasks:**")
            for t in plan["tasks"]:
                status = "✅" if t["completed"] else "⏳"
                _, label = get_task_deadline_info(t)
                st.write(
                    f"{status} **{t['subject']}** – {t['topic']} "
                    f"({t['difficulty']}, {t['estimated_minutes']} min, {label})"
                )

        st.markdown("---")
        st.subheader("Suggested study technique 🎯")
        tech = suggest_technique_for_app(
            mood_map[mood_label],
            energy_map[energy_label],
            plan["max_difficulty"],
        )

        if tech:
            st.markdown(f"**{tech['name']}**")
            st.write(tech["how"])
            if st.button("Use this technique today"):
                save_technique_usage_from_app(tech["code"])
                st.success("Technique saved 💗")

        st.markdown("---")
        st.subheader("Motivation 💌")
        st.write(get_motivation_for_app())

    # ---------------- TIMER ----------------
    st.subheader("Focus Timer ⏱️")

    label = st.text_input("Timer label", "Focus block")
    minutes = st.number_input("Minutes", 5, 180, 25, 5)

    if st.button("Start timer"):
        st.session_state.timer_end = time.time() + minutes * 60
        st.session_state.timer_label = label

    if st.session_state.timer_end:
        remaining = int(st.session_state.timer_end - time.time())
        if remaining <= 0:
            st.session_state.timer_end = None
            st.success("Time’s up! 🎉")
        else:
            m, s = divmod(remaining, 60)
            st.markdown(f"**{st.session_state.timer_label}:** {m:02d}:{s:02d}")
            time.sleep(1)
            st.rerun()

# ---------------------------------------------------------
# TASKS
# ---------------------------------------------------------
elif page == "Tasks":
    st.header("Tasks 📝")

    st.subheader("Add a task")
    subject = st.text_input("Subject")
    topic = st.text_input("Topic")
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
    est = st.number_input("Estimated minutes", 5, 300, 30, 5)
    due = st.date_input("Due date", value=date.today())

    if st.button("Add task ✨"):
        if subject and topic:
            add_task_from_app(
                subject,
                topic,
                difficulty,
                est,
                due.isoformat(),
            )
            st.success("Task added 💕")
            st.rerun()

    st.subheader("Your tasks")
    tasks = get_tasks_for_app()

    if not tasks:
        st.info("No tasks yet.")
    else:
        for t in tasks:
            col1, col2, col3 = st.columns([1, 6, 1])

            with col1:
                checked = st.checkbox(
                    "",
                    value=t["completed"],
                    key=f"chk_{t['id']}",
                )

            with col2:
                _, label = get_task_deadline_info(t)
                st.write(
                    f"**{t['subject']}** – {t['topic']} "
                    f"({t['difficulty']}, {t['estimated_minutes']} min, {label})"
                )

            with col3:
                if st.button("🗑️", key=f"del_{t['id']}"):
                    delete_task_from_app(t["id"])
                    st.rerun()

            if checked != t["completed"]:
                set_task_completed_from_app(t["id"], checked)

# ---------------------------------------------------------
# TECHNIQUES
# ---------------------------------------------------------
elif page == "Techniques":
    st.header("Study Techniques 🎯")

    techniques = get_techniques_for_app()
    labels = {f"{t['name']} ({t['code']})": t for t in techniques}

    if labels:
        chosen_label = st.selectbox("Choose a technique", labels.keys())
        chosen = labels[chosen_label]

        st.markdown(f"**{chosen['name']}**")
        st.write(chosen["how"])

        if st.button("Use this technique today"):
            save_technique_usage_from_app(chosen["code"])
            st.success("Technique logged 💗")

    st.subheader("Technique progress")
    stats = get_technique_stats_for_app()
    if not stats:
        st.info("No techniques used yet.")
    else:
        for s in stats:
            st.write(f"{s['name']}: used {s['count']} day(s)")


