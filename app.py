import sqlite3
import random
from datetime import datetime, date, timedelta

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DATABASE = "planner.db"


# ---------- DATABASE HELPERS ----------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT,
            due_date TEXT,
            importance INTEGER,
            duration_hours REAL,
            notes TEXT
        );
        """
    )
    conn.commit()
    conn.close()


# ---------- WEB PAGES ----------

@app.route("/", methods=["GET", "POST"])
def index():
    # Handle "Add task" form
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        due_date = request.form.get("due_date", "").strip()
        importance = request.form.get("importance", "3").strip()
        duration_hours = request.form.get("duration_hours", "1").strip()
        notes = request.form.get("notes", "").strip()

        if title:
            # Convert to numbers safely
            try:
                importance_val = int(importance)
            except ValueError:
                importance_val = 0
            try:
                duration_val = float(duration_hours)
            except ValueError:
                duration_val = 1.0

            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO tasks (title, subject, due_date, importance, duration_hours, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (title, subject, due_date, importance_val, duration_val, notes),
            )
            conn.commit()
            conn.close()

    # Show all tasks
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY due_date").fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks)


# ---------- "AI" API (pure Python, no external model) ----------

@app.route("/api/plan", methods=["POST"])
def api_plan():
    """
    Generate a 7‑day study plan that *sounds* like an AI assistant,
    using only local Python logic (no paid APIs).
    """
    data = request.get_json(force=True)
    extra_info = data.get("extra_info", "").strip()

    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()

    if not tasks:
        return jsonify({"error": "No tasks available. Please add some tasks first."}), 400

    # Convert rows to dicts and parse dates
    task_list = []
    for t in tasks:
        d = dict(t)
        due_str = d.get("due_date") or ""
        try:
            d["due_parsed"] = datetime.strptime(due_str, "%Y-%m-%d").date()
        except Exception:
            d["due_parsed"] = date.max  # tasks without proper date go to the end
        if d.get("importance") is None:
            d["importance"] = 0
        if d.get("duration_hours") is None:
            d["duration_hours"] = 1.0
        task_list.append(d)

    # Sort: earliest due date first, then higher importance
    task_list.sort(key=lambda x: (x["due_parsed"], -x["importance"]))

    # Make 7 days starting from today
    today = date.today()
    days = [today + timedelta(days=i) for i in range(7)]
    plan_days = [{"date": d, "tasks": []} for d in days]

    # Simple distribution: put each task on the next day in a cycle
    idx = 0
    for t in task_list:
        plan_days[idx]["tasks"].append(t)
        idx = (idx + 1) % 7

    # Some AI‑style phrases and tips
    opening_lines = [
        "Here’s a focused 7‑day study plan I created from your tasks.",
        "I’ve looked at your tasks and built a balanced 7‑day schedule for you.",
        "Based on your deadlines and importance levels, here’s a realistic plan for the next week.",
    ]
    focus_tips = [
        "Keep sessions short (25–30 minutes) with 5‑minute breaks.",
        "Put your phone away and study at a clear desk to stay focused.",
        "Start with the most important or earliest‑due task each day.",
        "If you finish early, use the extra time to review or get ahead.",
        "Remember to drink water and take short breaks to avoid burnout.",
    ]

    lines = []
    lines.append(random.choice(opening_lines))
    if extra_info:
        lines.append("")
        lines.append(f"You mentioned about your schedule: {extra_info}")
    lines.append("")
    lines.append("Let’s break it down day by day:\n")

    for i, info in enumerate(plan_days, start=1):
        day_date = info["date"]
        day_name = day_date.strftime("%A")

        if i == 1:
            header = f"Day 1 – {day_name} (Today)"
        elif i == 2:
            header = f"Day 2 – {day_name} (Tomorrow)"
        else:
            header = f"Day {i} – {day_name}"

        lines.append(header + ":")

        if not info["tasks"]:
            lines.append("  • No heavy tasks today. Use this day to rest or lightly review your notes.")
        else:
            for t in info["tasks"]:
                title = t["title"]
                subject = t.get("subject") or "General"
                hrs = t.get("duration_hours") or 1
                due_str = t.get("due_date") or "no due date"
                notes = t.get("notes") or ""

                detail = (
                    f"  • Spend about {hrs} hour(s) on '{title}' ({subject}), "
                    f"due {due_str}."
                )
                if notes:
                    detail += f" Notes: {notes}"
                lines.append(detail)

        lines.append("  Tip: " + random.choice(focus_tips))
        lines.append("")

    lines.append(
        "This is a starting point—feel free to move tasks between days "
        "if your real schedule changes."
    )

    plan_text = "\n".join(lines)
    return jsonify({"plan": plan_text})


# ---------- ENTRY POINT ----------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)