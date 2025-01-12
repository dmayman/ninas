
class AppState:
    def __init__(self):
        # Camera state
        self.cap = None  # VideoCapture object
        
        # Frame data
        self.curr_frame = None  # Current frame from the camera
        self.prev_frame = None  # Previous frame for motion detection

        # Simulation settings
        self.use_dummy_images = False  # Flag to use dummy images
        self.active_dummy_images = []  # List of loaded dummy images
        self.current_image_index = 0  # Index for dummy image set
        self.current_buzz_event = None  # Current buzz event data

        # Visit event tracking
        self.last_mila_end_time = None  # Last time Mila's visit ended for safety buffer
        self.safety_buffer_active = False # Flag to suppress Nova detection
        self.current_visit = {"dog": None, "start_time": None, "end_time": None}  # Active visit data

        # GPIO state
        self.gpio = None  # GPIO object (for vibration control)

        

app_state = AppState()  # Singleton instance