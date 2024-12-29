from flask import Flask, render_template, request, redirect, url_for
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz  # Import pytz for time zone handling
import json
import shutil  # For copying files

# Determine the absolute path to the shared folder
def find_repo_root(start_path):
    current_path = Path(start_path).resolve()
    while not (current_path / ".repo_root").exists():
        if current_path.parent == current_path:
            raise FileNotFoundError("Could not locate repo root marker (.repo_root)")
        current_path = current_path.parent
    return current_path

repo_root = find_repo_root(__file__)
photos_dir = repo_root / "static" / "training_photos"
report_dir = repo_root / "static" / "report-data"  # Updated path for report-data
untagged_dir = photos_dir / "untagged"
mila_dir = photos_dir / "Mila"
nova_dir = photos_dir / "Nova"
none_dir = photos_dir / "None"  # New "None" category
test_cases_json = report_dir / "tests.json"  # Path to the tests.json file

# Ensure directories exist
for directory in [untagged_dir, mila_dir, nova_dir, none_dir, report_dir]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize Flask
app = Flask(__name__, static_folder=str(repo_root / "static"))

@app.route("/")
def index():
    # Prepare the dictionaries for all categories
    categories = {
        "Mila": mila_dir,
        "Nova": nova_dir,
        "None": none_dir,
        "untagged": untagged_dir,
        "test_cases": test_cases_json
    }

    dog_folders = {}
    dog_previews = {}

    for category, folder in categories.items():
        if category == "test_cases":
            # Count JSON entries
            if test_cases_json.exists():
                with open(test_cases_json, "r") as f:
                    data = json.load(f)
                dog_folders[category] = len(data)
                dog_previews[category] = data[0]["file_path"] if data else None
        else:
            photos = [f for f in os.listdir(folder) if f.endswith(".jpg")]
            dog_folders[category] = len(photos)
            dog_previews[category] = photos[0] if photos else None

    return render_template("index.html", dogs=dog_folders, previews=dog_previews)

@app.route("/test_cases")
def test_cases():
    # Load test cases from JSON
    if not test_cases_json.exists():
        return "No test cases found.", 404

    with open(test_cases_json, "r") as f:
        data = json.load(f)

    return render_template("test_cases.html", test_cases=data)

@app.route("/copy_to/<photo>/<label>")
def copy_photo(photo, label):
    valid_categories = {"Mila": mila_dir, "Nova": nova_dir, "None": none_dir}

    if label not in valid_categories:
        return "Invalid label.", 404

    # Locate the photo from tests.json
    with open(test_cases_json, "r+") as f:
        data = json.load(f)
        photo_entry = next((entry for entry in data if entry["file_path"].endswith(photo)), None)

        if not photo_entry:
            return "Photo not found in test cases.", 404

        # Copy the photo to the target directory
        src_path = Path(photo_entry["file_path"])
        dest_dir = valid_categories[label]
        dest_path = dest_dir / src_path.name

        shutil.copy(src_path, dest_path)

        # Append copy details to the JSON entry
        photo_entry["copied_to"] = str(dest_path)

        # Update the JSON file
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

    return redirect(url_for("test_cases"))

@app.route("/photos/<category>")
def photos(category):
    valid_categories = {"Mila": mila_dir, "Nova": nova_dir, "None": none_dir, "untagged": untagged_dir}

    if category not in valid_categories:
        return "Invalid category.", 404

    photo_dir = valid_categories[category]
    photos = {}

    # Use Los Angeles timezone
    la_tz = pytz.timezone("America/Los_Angeles")
    now = datetime.now(tz=la_tz)

    all_photos = [
        (photo, datetime.fromtimestamp((photo_dir / photo).stat().st_mtime, tz=la_tz))
        for photo in os.listdir(photo_dir) if photo.endswith(".jpg")
    ]
    sorted_photos = sorted(all_photos, key=lambda x: x[1], reverse=True)

    for photo, photo_time in sorted_photos:
        # Calculate relative time
        delta = now - photo_time
        if delta < timedelta(minutes=1):
            relative = f"{int(delta.total_seconds())}s ago"
        elif delta < timedelta(hours=1):
            relative = f"{int(delta.total_seconds() // 60)}m ago"
        elif delta < timedelta(days=1):
            relative = f"{int(delta.total_seconds() // 3600)}hr ago"
        else:
            relative = f"{int(delta.days)}d ago"

        # Format absolute time
        absolute = photo_time.strftime("%a %m/%d, %-I:%M%p")

        photos[photo] = {"relative": relative, "absolute": absolute}

    return render_template("photos.html", category=category, photos=photos)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)