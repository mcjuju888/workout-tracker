from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import json
from datetime import date
from pathlib import Path

app = Flask(__name__)
app.secret_key = "dev-secret"

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "workouts.json"

DATE_FMT = "%Y-%m-%d"

def parse_date_or_none(s):
    try:
        return datetime.strptime(s, DATE_FMT).date()
    except Exception:
        return None


# ---------- Data helpers ----------

def load_workouts():
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            # migration: ensure every item has an integer id
            changed = False
            next_id = _next_id(data)
            for w in data:
                if "id" not in w:
                    w["id"] = next_id
                    next_id += 1
                    changed = True
            if changed:
                save_workouts(data)
            return data
    except json.JSONDecodeError:
        return []

def save_workouts(workouts):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(workouts, f, indent=4)

def _next_id(items):
    max_id = 0
    for w in items:
        try:
            max_id = max(max_id, int(w.get("id", 0)))
        except (TypeError, ValueError):
            pass
    return max_id + 1

def get_workout(workouts, wid):
    for w in workouts:
        if int(w["id"]) == int(wid):
            return w
    return None

# ---------- Routes ----------

@app.route("/")
def index():
    workouts = load_workouts()

    # ---- Query params ----
    q = (request.args.get("q") or "").strip().lower()
    start_str = (request.args.get("start") or "").strip()
    end_str = (request.args.get("end") or "").strip()

    start = parse_date_or_none(start_str) if start_str else None
    end = parse_date_or_none(end_str) if end_str else None

    # ---- Filtering ----
    def match(w):
        ok_ex = True
        if q:
            ok_ex = q in w["exercise"].lower()

        ok_start = True
        if start:
            ok_start = w["date"] >= start.strftime(DATE_FMT)

        ok_end = True
        if end:
            ok_end = w["date"] <= end.strftime(DATE_FMT)

        return ok_ex and ok_start and ok_end

    filtered = [w for w in workouts if match(w)]
    filtered.sort(key=lambda w: w["date"])

    return render_template(
        "index.html",
        workouts=filtered,
        q=q,
        start=start_str,
        end=end_str,
        total=len(filtered)
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        dt = request.form.get("date") or date.today().isoformat()
        exercise = (request.form.get("exercise") or "").strip()
        sets = request.form.get("sets") or "0"
        reps = request.form.get("reps") or "0"
        weight = request.form.get("weight") or "0"
        notes = (request.form.get("notes") or "").strip()

        if not exercise:
            flash("Exercise is required.", "error")
            return redirect(url_for("add"))

        try:
            sets = int(sets); reps = int(reps); weight = float(weight)
        except ValueError:
            flash("Sets/Reps must be integers and Weight must be a number.", "error")
            return redirect(url_for("add"))

        data = load_workouts()
        wid = _next_id(data)
        data.append({
            "id": wid,
            "date": dt,
            "exercise": exercise,
            "sets": sets,
            "reps": reps,
            "weight": weight,
            "notes": notes
        })
        save_workouts(data)
        flash("Workout added!", "success")
        return redirect(url_for("index"))

    return render_template("add.html", today=date.today().isoformat())

@app.route("/edit/<int:wid>", methods=["GET", "POST"])
def edit(wid):
    data = load_workouts()
    w = get_workout(data, wid)
    if not w:
        flash("Workout not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        dt = request.form.get("date") or w["date"]
        exercise = (request.form.get("exercise") or w["exercise"]).strip()
        sets = request.form.get("sets") or w["sets"]
        reps = request.form.get("reps") or w["reps"]
        weight = request.form.get("weight") or w["weight"]
        notes = (request.form.get("notes") or w["notes"]).strip()

        try:
            sets = int(sets); reps = int(reps); weight = float(weight)
        except ValueError:
            flash("Sets/Reps must be integers and Weight must be a number.", "error")
            return redirect(url_for("edit", wid=wid))

        w.update({
            "date": dt,
            "exercise": exercise,
            "sets": sets,
            "reps": reps,
            "weight": weight,
            "notes": notes
        })
        save_workouts(data)
        flash("Workout updated.", "success")
        return redirect(url_for("index"))

    return render_template("edit.html", w=w)

@app.route("/delete/<int:wid>", methods=["POST"])
def delete(wid):
    data = load_workouts()
    w = get_workout(data, wid)
    if not w:
        flash("Workout not found.", "error")
        return redirect(url_for("index"))

    data = [x for x in data if int(x["id"]) != int(wid)]
    save_workouts(data)
    flash("Workout deleted.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
