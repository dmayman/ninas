from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

PHOTO_DIR = "training_photos"
DOGS = ["Mila", "Nova"]

@app.route("/")
def index():
    # List all available dogs and their photo counts
    dog_folders = {dog: len(os.listdir(os.path.join(PHOTO_DIR, dog))) for dog in DOGS}
    return render_template("index.html", dogs=dog_folders)

@app.route("/photos/<dog>")
def photos(dog):
    if dog not in DOGS:
        return "Invalid dog name.", 404
    photo_dir = os.path.join(PHOTO_DIR, dog)
    photos = [f for f in os.listdir(photo_dir) if f.endswith(".jpg")]
    return render_template("photos.html", dog=dog, photos=photos)

@app.route("/delete/<dog>/<photo>")
def delete_photo(dog, photo):
    photo_path = os.path.join(PHOTO_DIR, dog, photo)
    if os.path.exists(photo_path):
        os.remove(photo_path)
        print(f"Deleted: {photo_path}")
    return redirect(url_for("photos", dog=dog))

if __name__ == "__main__":
    os.makedirs(PHOTO_DIR, exist_ok=True)
    for dog in DOGS:
        os.makedirs(os.path.join(PHOTO_DIR, dog), exist_ok=True)
    app.run(host="0.0.0.0", port=5000)