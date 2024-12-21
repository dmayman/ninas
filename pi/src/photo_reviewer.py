from flask import Flask, render_template, request, redirect, url_for
import os
from pathlib import Path

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
untagged_dir = photos_dir / "untagged"
mila_dir = photos_dir / "Mila"
nova_dir = photos_dir / "Nova"

# Ensure directories exist
for directory in [untagged_dir, mila_dir, nova_dir]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize Flask
app = Flask(__name__, static_folder=str(repo_root / "static"))

@app.route("/")
def index():
    # Prepare the dictionaries for all categories
    categories = {
        "Mila": mila_dir,
        "Nova": nova_dir,
        "Untagged": untagged_dir
    }

    dog_folders = {}
    dog_previews = {}

    for category, folder in categories.items():
        photos = [f for f in os.listdir(folder) if f.endswith(".jpg")]
        dog_folders[category] = len(photos)
        dog_previews[category] = photos[0] if photos else None

    return render_template("index.html", dogs=dog_folders, previews=dog_previews)

@app.route("/photos/<category>")
def photos(category):
    if category not in ["Untagged", "Mila", "Nova"]:
        return "Invalid category.", 404

    if category == "Untagged":
        photo_dir = untagged_dir
    elif category == "Mila":
        photo_dir = mila_dir
    elif category == "Nova":
        photo_dir = nova_dir

    photos = [f for f in os.listdir(photo_dir) if f.endswith(".jpg")]
    return render_template("photos.html", category=category, photos=photos)

@app.route("/label/<photo>/<label>")
def label_photo(photo, label):
    if label not in ["Mila", "Nova"]:
        return "Invalid label.", 404

    src = untagged_dir / photo
    if not src.exists():
        return "Photo not found.", 404

    dest = mila_dir / photo if label == "Mila" else nova_dir / photo
    src.rename(dest)
    return redirect(url_for("photos", category="Untagged"))

@app.route("/delete/<photo>")
def delete_photo(photo):
    src = untagged_dir / photo
    if not src.exists():
        return "Photo not found.", 404

    src.unlink()
    return redirect(url_for("photos", category="Untagged"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)