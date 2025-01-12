# General settings
LOG_FILE = "logs/app.log"  # Path to the log file

# API settings
API_URL = "https://ninas.davidmayman.com/api/record_visit.php"
API_KEY_FILE = "api_key.txt"  # Path to the file containing the API key

# Model configuration
MODEL_PATH = "tm_dog_model/model3.tflite"  # Path to TensorFlow Lite model
CLASS_LABELS = ["Mila", "Nova", "None"]  # Model class labels
CONFIDENCE_THRESHOLD = 90  # Confidence threshold for valid detection
INPUT_SIZE = (224, 224)  # Image size expected by the model

# Motion detection settings
MOTION_DELAY_MS = 1  # Delay between frames in milliseconds
MOTION_THRESHOLD = 0.01  # Fraction of frame size required for motion detection
SWITCH_DETECTION_TIME = 1  # Time in seconds for rapid switching detection

# Evaluation and visit settings
VERIFY_TIMES = 2 # Number of times to verify dog detection
VISIT_TIMEOUT = 40  # Timeout in seconds for ending a visit

# Vibration control settings
ENABLE_VIBRATION = False  # Master override for enabling/disabling vibration
VIBRATE_GPIO_PIN = 17  # GPIO pin used for controlling the vibration
DETECTION_TIMEOUT = 2  # Timeout in seconds for deactivating vibration

# Buffer settings
SAFETY_BUFFER = 120  # Buffer time between Mila's detection and Nova's

# Paths for logs, reports, and test data
REPORT_DATA_DIR = "static/report-data"  # Directory for storing report images
TESTS_JSON_PATH = "report/tests.json"  # Path to test case JSON file
BUZZERS_JSON_PATH = "report/buzzers.json"  # Path to buzz events JSON file

# Test case thresholds
LOW_CONFIDENCE_THRESHOLD = 95  # Low confidence threshold
SECOND_THIRD_CONFIDENCE_THRESHOLD = 25  # Confidence threshold for 2nd/3rd class