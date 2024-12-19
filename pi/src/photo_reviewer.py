from flask import Flask, render_template, request, redirect, url_for
import os
from pathlib import Path

app = Flask(__name__)

# Determine the absolute path to the shared photo directory
repo_root = Path(__file__).resolve().parent.parent  # Adjust based on repo structure
PHOTO_DIR = repo_root / "static" / "training_photos"

# List of dog names
DOGS = ["Mila", "Nova"]

@app.route("/")
def index():
    # List all available dogs and their photo counts
    dog_folders = {dog: len(os.listdir(PHOTO_DIR / dog)) for dog in DOGS}
    return render_template("index.html", dogs=dog_folders)

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