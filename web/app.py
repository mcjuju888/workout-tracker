from flask import Flask, render_template, request, redirect, url_for, flash
import json, os
from datetime import date
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
DATA_FILE = APP_ROOT.parent / "workouts.json"

app = Flask(__name__)
app.secret_key = "dev-secret"  # replace later

def load_workouts():
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_workouts(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/")
def index():
    workouts = sorted(load_workouts(), key=lambda w: w["date"])
    return render_template("index.html", workouts=workouts)

@app.route("/add", methods=["GET","POST"])
def add():
    if request.method == "POST":
        dt = request.form.get("date") or date.today().isoformat()
        exercise = request.form.get("exercise","").strip()
        sets = request.form.get("sets","0")
        reps = request.form.get("reps","0")
        weight = request.form.get("weight","0")
        notes = request.form.get("notes","").strip()

        try:
            sets = int(sets); reps = int(reps); weight = float(weight)
        except ValueError:
            flash("Sets/Reps must be integers and Weight must be a number.", "error")
            return redirect(url_for("add"))

        if not exercise:
            flash("Exercise is required.", "error")
            return redirect(url_for("add"))

        data = load_workouts()
        data.append({
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

if __name__ == "__main__":
    app.run(debug=True)
