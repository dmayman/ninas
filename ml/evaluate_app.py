from flask import Flask, render_template
from tflite_support.task import vision, core, processor
import os
import cv2

# Paths for model and labels
MODEL_PATH = "tm_dog_model/efficientnet_lite0.tflite"
TEST_FOLDER = "test-photos/test-set-3"
MAX_RESULTS = 3  # Number of classification results to display
SCORE_THRESHOLD = 0.5  # Minimum confidence score for classifications

# Create the Flask app
app = Flask(__name__, static_folder=TEST_FOLDER)
app.config["TEST_FOLDER"] = TEST_FOLDER

# Initialize the TensorFlow Lite model
base_options = core.BaseOptions(
    file_name=MODEL_PATH,
    num_threads=4,
)
classification_options = processor.ClassificationOptions(
    max_results=MAX_RESULTS, score_threshold=SCORE_THRESHOLD
)
options = vision.ImageClassifierOptions(
    base_options=base_options, classification_options=classification_options
)
classifier = vision.ImageClassifier.create_from_options(options)


def preprocess_and_classify(image_path):
    """
    Preprocesses the input image and runs classification using TensorFlow Lite.
    """
    # Load and preprocess the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Image not found at {image_path}")
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Convert to TensorImage
    tensor_image = vision.TensorImage.create_from_array(rgb_image)

    # Perform classification
    results = classifier.classify(tensor_image)

    # Extract classification results
    classifications = results.classifications[0].categories
    classified_data = [
        {
            "class": category.category_name,
            "confidence": round(category.score * 100, 2),
        }
        for category in classifications
    ]

    # Return the top result and all classifications
    top_result = classified_data[0] if classified_data else {"class": "Unknown", "confidence": 0}
    return {"top_result": top_result, "all_results": classified_data}


@app.route("/")
def index():
    """
    Displays the images in the test folder grouped by predicted class.
    """
    grouped_images = {}

    # Iterate through test folder images
    for filename in os.listdir(TEST_FOLDER):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join(TEST_FOLDER, filename)

            try:
                result = preprocess_and_classify(image_path)
                top_class = result["top_result"]["class"]

                if top_class not in grouped_images:
                    grouped_images[top_class] = []

                grouped_images[top_class].append(
                    {
                        "filename": filename,
                        "confidence": result["top_result"]["confidence"],
                        "all_results": result["all_results"],
                    }
                )
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Render results in the template
    return render_template("index.html", grouped_images=grouped_images, folder=TEST_FOLDER)


if __name__ == "__main__":
    app.run(debug=True)