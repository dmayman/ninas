from flask import Flask, render_template
import os
import json
from datetime import datetime, timedelta
import pytz

# Determine the absolute path to the shared folder
def find_repo_root(start_path):
    current_path = Path(start_path).resolve()
    while not (current_path / ".repo_root").exists():
        if current_path.parent == current_path:
            raise FileNotFoundError("Could not locate repo root marker (.repo_root)")
        current_path = current_path.parent
    return current_path

repo_root = find_repo_root(__file__)

# Configuration
JSON_REPORT_PATH = "report/report.json"
REPORT_DATA_DIR = "report/report-data"

# Flask App
app = Flask(__name__, static_folder=str(repo_root / "pi" / "src" / REPORT_DATA_DIR))

def load_reports():
    """
    Loads the JSON report file and dynamically calculates relative and absolute timestamps.
    """
    if not os.path.exists(JSON_REPORT_PATH):
        return []

    with open(JSON_REPORT_PATH, "r") as f:
        reports = json.load(f)

    # Use Los Angeles timezone
    la_tz = pytz.timezone("America/Los_Angeles")
    now = datetime.now(tz=la_tz)

    # Calculate relative and absolute timestamps for each report
    for report in reports:
        timestamp = datetime.fromtimestamp(report["timestamp"], tz=la_tz)
        delta = now - timestamp

        # Relative time calculation
        if delta < timedelta(minutes=1):
            relative = f"{int(delta.total_seconds())}s ago"
        elif delta < timedelta(hours=1):
            relative = f"{int(delta.total_seconds() // 60)}m ago"
        elif delta < timedelta(days=1):
            relative = f"{int(delta.total_seconds() // 3600)}hr ago"
        else:
            relative = f"{delta.days}d ago"

        # Format absolute time
        absolute = timestamp.strftime("%a %m/%d, %-I:%M%p")

        # Add relative and absolute times to the report
        report["timestamp_relative"] = relative
        report["timestamp_absolute"] = absolute

    return reports

@app.route("/")
def index():
    """
    Displays the surveillance reports with relative and absolute timestamps.
    """
    reports = load_reports()
    return render_template("index.html", reports=reports)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)