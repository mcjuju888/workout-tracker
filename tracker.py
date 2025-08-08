import json
from datetime import date, datetime
from collections import defaultdict
import matplotlib.pyplot as plt
from colorama import init, Fore, Style

init(autoreset=True)

WORKOUT_FILE = "workouts.json"
DATE_FMT = "%Y-%m-%d"

# ---------- Utility ----------

def load_workouts():
    try:
        with open(WORKOUT_FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_workouts(workouts):
    with open(WORKOUT_FILE, "w") as f:
        json.dump(workouts, f, indent=4)

def parse_date(s: str) -> str:
    """Return ISO date string (YYYY-MM-DD). Accepts '' for today."""
    if not s.strip():
        return date.today().isoformat()
    try:
        return datetime.strptime(s.strip(), DATE_FMT).date().isoformat()
    except ValueError:
        warn("Invalid date. Use YYYY-MM-DD.")
        return parse_date(input("Enter date (YYYY-MM-DD) or press Enter for today: "))

def sort_by_date(entries):
    return sorted(entries, key=lambda w: w["date"])

def volume(w):
    return w["sets"] * w["reps"] * w["weight"]

def info(msg): print(Fore.CYAN + msg + Style.RESET_ALL)
def ok(msg): print(Fore.GREEN + msg + Style.RESET_ALL)
def warn(msg): print(Fore.YELLOW + msg + Style.RESET_ALL)
def err(msg): print(Fore.RED + msg + Style.RESET_ALL)
def title(msg): print(Fore.MAGENTA + Style.BRIGHT + msg + Style.RESET_ALL)

# ---------- Core actions ----------

def add_workout():
    title("\nAdd Workout")
    dt = parse_date(input("Date (YYYY-MM-DD, Enter for today): "))
    exercise = input("Exercise name: ").strip()
    try:
        sets = int(input("Sets: "))
        reps = int(input("Reps: "))
        weight = float(input("Weight (lbs): "))
    except ValueError:
        err("Numbers only for sets/reps/weight.")
        return
    notes = input("Notes (optional): ").strip()

    workout = {
        "date": dt,
        "exercise": exercise,
        "sets": sets,
        "reps": reps,
        "weight": weight,
        "notes": notes
    }
    workouts = load_workouts()
    workouts.append(workout)
    save_workouts(workouts)
    ok(f"Saved: {dt} • {exercise} {sets}x{reps} @ {weight} lbs")

def view_workouts():
    title("\nAll Workouts (sorted)")
    workouts = sort_by_date(load_workouts())
    if not workouts:
        warn("No workouts found.")
        return
    for i, w in enumerate(workouts, 1):
        print(f"{Fore.YELLOW}{i:>3}.{Style.RESET_ALL} {w['date']} • {w['exercise']} | "
              f"{w['sets']}x{w['reps']} @ {w['weight']} lbs "
              f"(Vol: {int(volume(w))}) | Notes: {w['notes']}")

def search_by_date():
    title("\nSearch by Date")
    dt = parse_date(input("Enter date (YYYY-MM-DD): "))
    results = [w for w in load_workouts() if w["date"] == dt]
    if not results:
        warn("No workouts found for that date.")
        return
    for w in sort_by_date(results):
        print(f"{w['date']} • {w['exercise']} | {w['sets']}x{w['reps']} @ {w['weight']} lbs (Vol: {int(volume(w))}) | {w['notes']}")

def search_by_exercise():
    title("\nSearch by Exercise")
    term = input("Exercise name: ").lower().strip()
    results = [w for w in load_workouts() if term in w["exercise"].lower()]
    if not results:
        warn("No workouts found for that exercise.")
        return
    for w in sort_by_date(results):
        print(f"{w['date']} • {w['exercise']} | {w['sets']}x{w['reps']} @ {w['weight']} lbs (Vol: {int(volume(w))}) | {w['notes']}")

def delete_workout():
    title("\nDelete Workout")
    workouts = sort_by_date(load_workouts())
    if not workouts:
        warn("No workouts to delete.")
        return
    for i, w in enumerate(workouts, 1):
        print(f"{i:>3}. {w['date']} • {w['exercise']} | {w['sets']}x{w['reps']} @ {w['weight']} lbs")
    try:
        idx = int(input("Choose number to delete: ")) - 1
        if 0 <= idx < len(workouts):
            removed = workouts.pop(idx)
            save_workouts(workouts)
            ok(f"Deleted: {removed['date']} • {removed['exercise']}")
        else:
            err("Invalid choice.")
    except ValueError:
        err("Enter a number.")

def edit_workout():
    title("\nEdit Workout")
    workouts = sort_by_date(load_workouts())
    if not workouts:
        warn("No workouts to edit.")
        return
    for i, w in enumerate(workouts, 1):
        print(f"{i:>3}. {w['date']} • {w['exercise']} | {w['sets']}x{w['reps']} @ {w['weight']} lbs")
    try:
        idx = int(input("Choose number to edit: ")) - 1
        if not (0 <= idx < len(workouts)):
            err("Invalid choice.")
            return
    except ValueError:
        err("Enter a number.")
        return

    w = workouts[idx]
    info("Press Enter to keep current value.")
    new_date = input(f"Date ({w['date']}): ")
    new_ex = input(f"Exercise ({w['exercise']}): ")
    new_sets = input(f"Sets ({w['sets']}): ")
    new_reps = input(f"Reps ({w['reps']}): ")
    new_weight = input(f"Weight ({w['weight']}): ")
    new_notes = input(f"Notes ({w['notes']}): ")

    if new_date.strip(): w["date"] = parse_date(new_date)
    if new_ex.strip(): w["exercise"] = new_ex.strip()
    if new_sets.strip():
        try: w["sets"] = int(new_sets)
        except ValueError: warn("Ignored invalid sets.")
    if new_reps.strip():
        try: w["reps"] = int(new_reps)
        except ValueError: warn("Ignored invalid reps.")
    if new_weight.strip():
        try: w["weight"] = float(new_weight)
        except ValueError: warn("Ignored invalid weight.")
    if new_notes.strip(): w["notes"] = new_notes.strip()

    workouts[idx] = w
    save_workouts(workouts)
    ok("Workout updated.")

def show_personal_bests():
    title("\nPersonal Bests")
    workouts = load_workouts()
    if not workouts:
        warn("No workouts found.")
        return
    pr = defaultdict(float)
    for w in workouts:
        pr[w["exercise"]] = max(pr[w["exercise"]], w["weight"])
    for ex, wt in sorted(pr.items()):
        print(f"{ex}: {wt} lbs")

def show_total_volume():
    title("\nTotal Training Volume")
    w = load_workouts()
    if not w:
        warn("No workouts found.")
        return
    total = sum(volume(x) for x in w)
    print(f"{int(total)} lbs")

def show_progress_graph():
    title("\nProgress Graph")
    term = input("Exercise name: ").lower().strip()
    filtered = [w for w in load_workouts() if term in w["exercise"].lower()]
    if not filtered:
        warn("No workouts found for that exercise.")
        return
    filtered = sort_by_date(filtered)
    dates = [w["date"] for w in filtered]
    weights = [w["weight"] for w in filtered]

    plt.plot(dates, weights, marker="o")
    plt.title(f"Progress for {filtered[0]['exercise']}")
    plt.xlabel("Date")
    plt.ylabel("Weight (lbs)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# ---------- Menu ----------

def menu():
    print("\n" + Fore.MAGENTA + Style.BRIGHT + "🏋️  Workout Tracker" + Style.RESET_ALL)
    print(f"{Fore.YELLOW}[A]{Style.RESET_ALL}dd   {Fore.YELLOW}[V]{Style.RESET_ALL}iew   "
          f"{Fore.YELLOW}[D]{Style.RESET_ALL}ate search   {Fore.YELLOW}[E]{Style.RESET_ALL}xercise search")
    print(f"{Fore.YELLOW}[R]{Style.RESET_ALL}eplace/Edit   {Fore.YELLOW}[X]{Style.RESET_ALL} Delete   "
          f"{Fore.YELLOW}[P]{Style.RESET_ALL} PRs   {Fore.YELLOW}[T]{Style.RESET_ALL} Total Vol   "
          f"{Fore.YELLOW}[G]{Style.RESET_ALL} Graph   {Fore.YELLOW}[Q]{Style.RESET_ALL} Quit")

def main():
    while True:
        menu()
        choice = input("> ").strip().lower()
        if choice in ("1","a","add"): add_workout()
        elif choice in ("2","v","view"): view_workouts()
        elif choice in ("3","d","date"): search_by_date()
        elif choice in ("4","e","exercise"): search_by_exercise()
        elif choice in ("5","r","edit","replace"): edit_workout()
        elif choice in ("6","x","del","delete"): delete_workout()
        elif choice in ("7","p","prs"): show_personal_bests()
        elif choice in ("8","t","total"): show_total_volume()
        elif choice in ("9","g","graph"): show_progress_graph()
        elif choice in ("10","q","quit","exit"):
            ok("Goodbye!")
            break
        else:
            warn("Unknown option. Try A/V/D/E/R/X/P/T/G/Q.")

if __name__ == "__main__":
    main()

