from flask import Flask, render_template, request, redirect, url_for
import os
from pathlib import Path

# Determine the absolute path to the shared photo directory
def find_repo_root(start_path):
    current_path = Path(start_path).resolve()
    while not (current_path / ".repo_root").exists():
        if current_path.parent == current_path:
            raise FileNotFoundError("Could not locate repo root marker (.repo_root)")
        current_path = current_path.parent
    return current_path

repo_root = find_repo_root(__file__)

PHOTO_DIR = repo_root / "static" / "training_photos"


# Initialize Flask
app = Flask(__name__, static_folder=str(repo_root / "static"))

# List of dog names
DOGS = ["Mila", "Nova"]

@app.route("/")
def index():
    dog_folders = {}
    dog_previews = {}

    for dog in DOGS:
        photo_dir = PHOTO_DIR / dog
        photos = [f for f in os.listdir(photo_dir) if f.endswith(".jpg")]
        dog_folders[dog] = len(photos)

        # Get the first photo or set to None if no photos exist
        dog_previews[dog] = photos[0] if photos else None

    return render_template("index.html", dogs=dog_folders, previews=dog_previews)

@app.route("/photos/<dog>")
def photos(dog):
    if dog not in DOGS:
        return "Invalid dog name.", 404
    photo_dir = PHOTO_DIR / dog
    photos = [f for f in os.listdir(photo_dir) if f.endswith(".jpg")]
    return render_template("photos.html", dog=dog, photos=photos)

@app.route("/delete/<dog>/<photo>")
def delete_photo(dog, photo):
    photo_path = PHOTO_DIR / dog / photo
    if photo_path.exists():
        photo_path.unlink()  # Delete the photo
        print(f"Deleted: {photo_path}")
    return redirect(url_for("photos", dog=dog))

if __name__ == "__main__":
    # Ensure directories for each dog exist
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    for dog in DOGS:
        (PHOTO_DIR / dog).mkdir(parents=True, exist_ok=True)

    # Run the Flask app
    app.run(host="0.0.0.0", port=5000)