from flask import Flask, render_template, jsonify, request
import json
import subprocess 
import re 
from display import Display # Import the Display class
import datetime # For getting current time and date
import os
import importlib
import inspect
import time
import threading # For background updates
import logging # Added for custom log filter

# Import performance optimization modules
from performance_optimizer import optimizer
from performance_utils import RaspberryPiOptimizer, optimize_flask_app, get_app_optimizations

# Import rpi-rgb-led-matrix library
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    RGB_MATRIX_AVAILABLE = True
except ImportError:
    RGB_MATRIX_AVAILABLE = False
    print("WARNING: RGBMatrix library not found. Hardware display will not be available.")

# Import BaseWidget to check instance types, though specific widgets are loaded dynamically
from widgets.base_widget import BaseWidget 

app = Flask(__name__)

# Matrix dimensions
MATRIX_WIDTH = 64
MATRIX_HEIGHT = 64

# Create a single Display instance that will be used throughout the application
matrix_display = Display(width=MATRIX_WIDTH, height=MATRIX_HEIGHT)

# --- RGB Matrix Hardware Initialization ---
hardware_matrix = None
if RGB_MATRIX_AVAILABLE:
    try:
        print("INFO: Initializing RGB LED Matrix hardware...")
        options = RGBMatrixOptions()
        options.rows = MATRIX_HEIGHT
        options.cols = MATRIX_WIDTH
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'adafruit-hat' # Or 'adafruit-hat-pwm' if quality mode was used
        options.gpio_slowdown = 2 # Adjust as needed (1-4 typically)
        options.disable_hardware_pulsing = False # Usually False for Adafruit HAT/Bonnet
        # options.brightness = 50 # Optional: Set brightness (0-100)
        hardware_matrix = RGBMatrix(options=options)
        print("SUCCESS: RGB LED Matrix hardware initialized.")
    except Exception as e:
        print(f"ERROR: Failed to initialize RGB LED Matrix hardware: {e}")
        hardware_matrix = None # Ensure it's None if initialization fails
# --- End RGB Matrix Hardware Initialization ---

# Current display mode
current_display_mode = 'default' 
SCREEN_LAYOUTS_FILE_PATH = 'screen_layouts.json'

# Add these global variables near the top of the file with other globals
AUTO_SCREEN_ROTATION_ENABLED = False
last_screen_change_time = time.monotonic()
last_debug_log_time = time.monotonic()

# --- Widget Management ---
AVAILABLE_WIDGETS = {} # Stores loaded widget classes, e.g., {"time": TimeWidget, "text": TextWidget}
active_widget_instances = {} # Stores active widget instances: widget_id -> instance

# Lock for synchronizing access to shared resources like screen_layouts, current_display_mode, and matrix_display
data_lock = threading.Lock()

# Initialize Raspberry Pi optimizer
pi_optimizer = RaspberryPiOptimizer()

# Performance settings
app_optimizations = get_app_optimizations()
DISPLAY_UPDATE_INTERVAL = 0.1 if app_optimizations["reduce_update_frequency"] else 0.04  # Target ~25 FPS for normal, 10 FPS for reduced
SKIP_FRAMES_ON_SLOW = True  # Skip frames if processing is too slow
SKIP_FRAME_THRESHOLD = app_optimizations["skip_frame_threshold"]  # ms
MATRIX_DATA_LOGGING_ENABLED = True # Global flag for matrix_data route logging
current_frame_widget_dimensions = [] # Stores dimensions of widgets in the current frame

# Custom Log Filter for /api/matrix_data
class MatrixDataLogFilter(logging.Filter):
    def filter(self, record):
        # Check if the log message is for the /api/matrix_data endpoint
        # and if logging for this endpoint is globally disabled.
        # record.args is usually where the request details are for Werkzeug.
        # A common format is: "GET /api/matrix_data HTTP/1.1" 200 -
        is_matrix_data_req = False
        if isinstance(record.args, tuple) and len(record.args) > 0:
            request_line = str(record.args[0]) # e.g. "GET /api/matrix_data HTTP/1.1"
            if "/api/matrix_data" in request_line:
                is_matrix_data_req = True

        if is_matrix_data_req and not MATRIX_DATA_LOGGING_ENABLED:
            return 0  # Suppress log record
        return 1  # Allow log record

def load_widget_classes():
    """Dynamically loads widget classes from the 'widgets' directory."""
    global AVAILABLE_WIDGETS
    widgets_path = os.path.join(os.path.dirname(__file__), 'widgets')
    if not os.path.isdir(widgets_path):
        print(f"DEBUG: Widgets directory not found at {widgets_path}")
        return

    print("DEBUG: Starting widget class loading...")
    for filename in os.listdir(widgets_path):
        if filename.endswith('_widget.py'): # Convention: widget_type_widget.py
            module_name_full = f"widgets.{filename[:-3]}"
            widget_type_key = filename[:-10] # Extracts 'time' from 'time_widget.py'
            print(f"DEBUG: Attempting to load module: {module_name_full} for key: {widget_type_key}")
            try:
                module = importlib.import_module(module_name_full)
                print(f"DEBUG: Successfully imported module: {module_name_full}")
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    print(f"DEBUG: Checking class '{name}' in module '{module_name_full}'")
                    # Check if it's a subclass of BaseWidget and actually defined in this module (not imported)
                    if issubclass(cls, BaseWidget) and cls is not BaseWidget and cls.__module__ == module_name_full:
                        print(f"DEBUG: Found valid widget class '{name}' for key '{widget_type_key}'")
                        if widget_type_key in AVAILABLE_WIDGETS:
                            print(f"Warning: Duplicate widget type key '{widget_type_key}' found. Overwriting.")
                        AVAILABLE_WIDGETS[widget_type_key] = cls
                        print(f"Successfully loaded widget: {name} as type '{widget_type_key}'")
                        if widget_type_key == "news": # Specifically for news widget
                            print(f"DEBUG: NEWS WIDGET '{name}' SUCCESSFULLY REGISTERED AS '{widget_type_key}'")
            except ImportError as e:
                print(f"Error importing widget module {module_name_full}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while loading widget {module_name_full}: {e}")
    print(f"Available widgets: {list(AVAILABLE_WIDGETS.keys())}")

# --- Screen Layouts and Widget Instance Configuration System ---

def _get_all_widget_type_data():
    """Helper function to build the list of available widget types and their configurations."""
    widget_type_data = []
    for type_key, widget_class in AVAILABLE_WIDGETS.items():
        display_name = widget_class.__name__.replace("Widget", "")
        display_name = re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', display_name).strip()
        
        widget_type_data.append({
            "type": type_key,
            "displayName": display_name,
            "configOptions": widget_class.get_config_options()
        })
    return widget_type_data

# Helper function to convert hex color string to RGB tuple
def hex_to_rgb(hex_color_string):
    """Converts a hex color string (e.g., '#FF0000') to an (R, G, B) tuple."""
    hex_color = hex_color_string.lstrip('#')
    if len(hex_color) == 6:
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass # Invalid hex
    # Fallback to white if format is invalid
    print(f"Warning: Invalid hex color string '{hex_color_string}'. Defaulting to white.")
    return (255, 255, 255) 

# Default screen layouts (structure remains similar, but 'type' will map to loaded widget classes)
default_screen_layouts = {
    "default": {
        "name": "Home Screen",
        "widgets": [
            {"id": "time_default", "type": "time", "x": (MATRIX_WIDTH - 29) // 2, "y": (MATRIX_HEIGHT - (2 * 7 + 3)) // 2, "enabled": True, "time_format": "%H:%M", "color": "#61DAFB", "font_size": "medium"},
            {"id": "date_default", "type": "date", "x": (MATRIX_WIDTH - 29) // 2, "y": ((MATRIX_HEIGHT - (2 * 7 + 3)) // 2) + 7 + 3, "enabled": True, "date_format_type": "dd_mm", "color": "#FFFFFF", "font_size": "medium"}
        ],
        "display_time_seconds": 10
    },
    "net_config": {
        "name": "Network Info",
        "widgets": [
            {"id": "ncf_lbl_ssid", "type": "text", "text": "SSID:", "x": 1, "y": 1, "enabled": True, "color": "#FFFF00"},
            {"id": "ncf_val_ssid", "type": "network_stats", "stat_to_display": "ssid", "os_override": "auto", "font_size": "medium", "x": 1, "y": 1 + 7 + 2, "enabled": True, "color": "#FFFFFF"},
            {"id": "ncf_lbl_rssi", "type": "text", "text": "RSSI:", "x": 1, "y": 1 + 2*(7 + 2), "enabled": True, "color": "#FFFF00"},
            {"id": "ncf_val_rssi", "type": "network_stats", "stat_to_display": "rssi", "os_override": "auto", "font_size": "medium", "x": 1, "y": 1 + 3*(7 + 2), "enabled": True, "color": "#FFFFFF"}
        ],
        "display_time_seconds": 15
    }
}

screen_layouts = {} # Will be loaded or set to default
DEFAULT_SCREEN_DISPLAY_TIME_S = 10

def load_screen_layouts():
    global screen_layouts, MATRIX_DATA_LOGGING_ENABLED
    
    raw_loaded_data = {}

    if os.path.exists(SCREEN_LAYOUTS_FILE_PATH):
        try:
            with open(SCREEN_LAYOUTS_FILE_PATH, 'r') as f:
                raw_loaded_data = json.load(f)
            print(f"Loaded raw data from {SCREEN_LAYOUTS_FILE_PATH}")

            MATRIX_DATA_LOGGING_ENABLED = raw_loaded_data.get('matrix_data_logging_enabled', True)
            print(f"Matrix data logging state loaded/defaulted to: {MATRIX_DATA_LOGGING_ENABLED}")

            current_file_screen_layouts = {
                k: v for k, v in raw_loaded_data.items() if k != 'matrix_data_logging_enabled'
            }
            
            if not isinstance(current_file_screen_layouts, dict) or \
               ('default' not in current_file_screen_layouts and bool(current_file_screen_layouts)):
                print("Warning: Invalid screen_layouts structure or default screen missing. Reverting to defaults for screens.")
                screen_layouts = default_screen_layouts.copy()
                _save_layouts_to_file()
                return

            migrated_layouts = {}
            for screen_id, screen_config_item in current_file_screen_layouts.items(): # Renamed screen_config to screen_config_item
                if not isinstance(screen_config_item, dict): # Check item from loop
                    print(f"Warning: Invalid configuration for screen '{screen_id}'. Skipping item.")
                    continue
                
                # Make a mutable copy for modification
                current_screen_config = screen_config_item.copy()

                if 'widgets' not in current_screen_config: 
                    current_screen_config['widgets'] = []
                if 'display_time_seconds' not in current_screen_config:
                    current_screen_config['display_time_seconds'] = DEFAULT_SCREEN_DISPLAY_TIME_S
                elif not isinstance(current_screen_config['display_time_seconds'], (int, float)) or current_screen_config['display_time_seconds'] <= 0:
                    current_screen_config['display_time_seconds'] = DEFAULT_SCREEN_DISPLAY_TIME_S
                migrated_layouts[screen_id] = current_screen_config # Add modified copy
            
            screen_layouts = migrated_layouts
            if not screen_layouts: 
                 print("No screen configurations found after loading. Initializing with default screen(s).")
                 screen_layouts = default_screen_layouts.copy()
                 _save_layouts_to_file()
            elif 'default' not in screen_layouts: 
                 print("Critical: Default screen was lost or not found. Re-initializing default screen.")
                 screen_layouts['default'] = default_screen_layouts['default'].copy()
                 _save_layouts_to_file()

        except json.JSONDecodeError:
            print(f"Error decoding {SCREEN_LAYOUTS_FILE_PATH}. Using default layouts. Matrix logging defaults to True.")
            MATRIX_DATA_LOGGING_ENABLED = True
            screen_layouts = default_screen_layouts.copy()
            _save_layouts_to_file()
        except Exception as e:
            print(f"Error loading {SCREEN_LAYOUTS_FILE_PATH}: {e}. Using default layouts. Matrix logging defaults to True.")
            MATRIX_DATA_LOGGING_ENABLED = True
            screen_layouts = default_screen_layouts.copy()
            _save_layouts_to_file()
    else:
        print(f"{SCREEN_LAYOUTS_FILE_PATH} not found. Using default layouts and creating file. Matrix logging defaults to True.")
        MATRIX_DATA_LOGGING_ENABLED = True
        screen_layouts = default_screen_layouts.copy()
        _save_layouts_to_file()

def _save_layouts_to_file_threaded(): # Renamed for clarity
    global screen_layouts, MATRIX_DATA_LOGGING_ENABLED, data_lock 

    layouts_copy = {}
    logging_enabled_copy = False
    with data_lock: 
        # Make deep copies if screen_layouts contains mutable objects (like lists/dicts)
        # that could be modified elsewhere while the save is in progress.
        # json.loads(json.dumps(obj)) is a common way for deepish copy of JSON-serializable data.
        try:
            layouts_copy = json.loads(json.dumps(screen_layouts))
        except Exception as e:
            print(f"Error deep copying screen_layouts for threaded save: {e}. Falling back to shallow copy.")
            layouts_copy = screen_layouts.copy() # Fallback, might not be safe if nested dicts are modified
        logging_enabled_copy = MATRIX_DATA_LOGGING_ENABLED

    data_to_save = {'matrix_data_logging_enabled': logging_enabled_copy}
    data_to_save.update(layouts_copy)

    try:
        with open(SCREEN_LAYOUTS_FILE_PATH, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        print(f"Successfully saved screen layouts and settings to {SCREEN_LAYOUTS_FILE_PATH} in background thread.")
    except Exception as e:
        print(f"Error saving screen layouts to {SCREEN_LAYOUTS_FILE_PATH} in background thread: {e}")

def _update_and_save_screen_layouts(new_layouts_data):
    """Updates the global screen_layouts, clears active instances, and saves to file in a background thread."""
    global screen_layouts, active_widget_instances
    # The main route save_screen_layouts_route already holds data_lock for updating screen_layouts
    
    screen_layouts = new_layouts_data
    active_widget_instances.clear() 
    print("Cleared active_widget_instances due to layout save (triggered by _update_and_save_screen_layouts).")
    
    # Run the save operation in a new thread
    save_thread = threading.Thread(target=_save_layouts_to_file_threaded)
    save_thread.daemon = True # Ensure thread doesn't prevent app exit
    save_thread.start()
    
    return True # Return immediately (optimistic success)

def _add_new_screen(screen_id, screen_name):
    """Adds a new screen to the global screen_layouts and saves to file."""
    global screen_layouts, active_widget_instances
    # Assuming lock is handled by the caller (the route function) for screen_layouts modification

    screen_layouts[screen_id] = {
        "name": screen_name,
        "widgets": [],
        "display_time_seconds": DEFAULT_SCREEN_DISPLAY_TIME_S
    }
    active_widget_instances.clear()
    print(f"Cleared active_widget_instances due to adding screen: {screen_id}")
    
    # Run the save operation in a new thread
    save_thread = threading.Thread(target=_save_layouts_to_file_threaded)
    save_thread.daemon = True
    save_thread.start()
    return True # Optimistic success

def _remove_screen(screen_id_to_remove):
    """Removes a screen from global layouts, updates current_display_mode if needed, and saves."""
    global screen_layouts, current_display_mode, active_widget_instances
    # Assume screen_id_to_remove exists and is not 'default' (checked by caller/route)
    
    removed_screen_name = screen_layouts[screen_id_to_remove].get('name', screen_id_to_remove)
    del screen_layouts[screen_id_to_remove]
    
    display_mode_was_changed = False
    if current_display_mode == screen_id_to_remove:
        current_display_mode = 'default' 
        display_mode_was_changed = True
        print(f"Current display mode was {screen_id_to_remove}, switched to default following removal.")
        
    active_widget_instances.clear()
    print(f"Cleared active_widget_instances due to removing screen: {screen_id_to_remove}")
    
    # Run the save operation in a new thread
    save_thread = threading.Thread(target=_save_layouts_to_file_threaded)
    save_thread.daemon = True
    save_thread.start()
    return True, removed_screen_name, display_mode_was_changed # Optimistic success for save

def _set_active_display_mode(mode_name):
    """Sets the current_display_mode if the mode_name is valid."""
    global current_display_mode
    if mode_name in screen_layouts: # Check for existence within screen_layouts
        current_display_mode = mode_name
        return True # Successfully set
    return False # Mode not found

def _set_matrix_logging_enabled_and_save(status: bool):
    """Updates the global MATRIX_DATA_LOGGING_ENABLED flag and triggers saving all layouts."""
    global MATRIX_DATA_LOGGING_ENABLED
    MATRIX_DATA_LOGGING_ENABLED = status
    print(f"Matrix data route logging globally set to: {MATRIX_DATA_LOGGING_ENABLED}")
    
    # Run the save operation in a new thread
    save_thread = threading.Thread(target=_save_layouts_to_file_threaded)
    save_thread.daemon = True
    save_thread.start()
    return True # Optimistic success

def _prepare_global_widget_context(current_time, current_screen_widget_configs):
    """Prepares the global context dictionary for widgets."""
    return {
        'now': current_time,
        'get_text_dimensions': matrix_display.get_text_dimensions, # Pass the method itself
        'matrix_width': MATRIX_WIDTH
    }



# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def config_page():
    return render_template('config.html')

@app.route('/performance')
def performance_page():
    """Route for the performance monitoring page"""
    return render_template('performance.html')

@app.route('/api/get_widget_types', methods=['GET'])
def get_widget_types_route():
    """Returns a list of available widget types and their configurations."""
    widget_data = _get_all_widget_type_data()
    return jsonify(widget_data)

@app.route('/api/get_screen_layouts', methods=['GET'])
def get_screen_layouts_route():
    return jsonify(screen_layouts)

@app.route('/api/save_screen_layouts', methods=['POST'])
def save_screen_layouts_route():
    try:
        new_layouts = request.get_json()
        if not isinstance(new_layouts, dict):
            return jsonify(success=False, message="Invalid layout format: must be a dictionary."), 400
        
        with data_lock: 
            # _update_and_save_screen_layouts will be called, which now uses a thread for file I/O.
            # The modification of global screen_layouts and active_widget_instances happens under this lock.
            saved = _update_and_save_screen_layouts(new_layouts)
        
        if saved: # This now reflects the start of the save, not its completion
            return jsonify(success=True, message="Screen layouts update initiated and saving in background.")
        else:
            # This path might be less likely if _update_and_save_screen_layouts always returns True
            return jsonify(success=False, message="Failed to initiate screen layout save."), 500
    except Exception as e:
        return jsonify(success=False, message=f"Error processing request: {e}"), 400

@app.route('/api/add_screen', methods=['POST'])
def add_screen_route():
    try:
        data = request.get_json()
        new_screen_id = data.get('screen_id')
        new_screen_name = data.get('screen_name')

        if not new_screen_id or not new_screen_name:
            return jsonify(success=False, message="Screen ID and Name are required."), 400
        if not re.match(r"^[a-zA-Z0-9_\-]+$", new_screen_id):
            return jsonify(success=False, message="Screen ID can only contain letters, numbers, underscores, and hyphens."), 400
        
        with data_lock:
            if new_screen_id in screen_layouts: 
                return jsonify(success=False, message=f"Screen ID '{new_screen_id}' already exists."), 400
            
            # _add_new_screen now uses a thread for file I/O.
            # screen_layouts and active_widget_instances are modified under this lock.
            saved = _add_new_screen(new_screen_id, new_screen_name)

        if saved: # Reflects initiation of save
            return jsonify(success=True, message=f"Screen '{new_screen_name}' added, saving layouts in background.", new_screen_id=new_screen_id)
        else:
            # This part of the logic might need adjustment if _add_new_screen always returns True
            # and relies on background thread for actual save outcome.
            # For now, assuming 'saved' reflects successful initiation.
            # A robust rollback for in-memory changes if background save fails would be more complex.
            return jsonify(success=False, message="Failed to initiate screen add operation."), 500
    except Exception as e:
        return jsonify(success=False, message=f"Error adding screen: {e}"), 400

@app.route('/api/remove_screen/<string:screen_id_to_remove>', methods=['POST'])
def remove_screen_route(screen_id_to_remove):
    global current_display_mode # Declare usage of global for reading/writing after helper potentially changes it
    original_screen_config = None
    original_current_display_mode_snapshot = None # Unique name for the snapshot

    try:
        if screen_id_to_remove == 'default':
            return jsonify(success=False, message="Cannot remove the default screen."), 400
        
        with data_lock:
            if screen_id_to_remove not in screen_layouts:
                return jsonify(success=False, message=f"Screen ID '{screen_id_to_remove}' not found."), 404
            
            # Snapshot for potential rollback of in-memory changes if save fails
            original_screen_config = screen_layouts.get(screen_id_to_remove).copy()
            original_current_display_mode_snapshot = current_display_mode # Snapshot global before change by helper

            # _remove_screen now uses a thread for file I/O.
            # screen_layouts, active_widget_instances, and current_display_mode are modified under this lock.
            save_initiated, removed_name, mode_changed = _remove_screen(screen_id_to_remove)

        if save_initiated: # Reflects initiation of save
            new_active_mode_val = None
            if mode_changed:
                # current_display_mode (global) has been updated by _remove_screen to 'default'
                new_active_mode_val = current_display_mode 
            
            return jsonify(success=True, 
                           message=f"Screen '{removed_name}' removed, saving layouts in background.", 
                           new_active_mode=new_active_mode_val)
        else:
            # Rollback logic for in-memory changes if initiation fails (less likely with current optimistic return)
            # If background save fails, a more complex callback or status check mechanism would be needed for rollback.
            with data_lock:
                if original_screen_config:
                    screen_layouts[screen_id_to_remove] = original_screen_config # Restore deleted screen
                
                # If mode was changed by the helper (meaning global current_display_mode was set to 'default'),
                # revert it to its state before the helper call using the snapshot.
                if mode_changed: 
                    current_display_mode = original_current_display_mode_snapshot
                
                # active_widget_instances.clear() # Already cleared by _remove_screen
                print(f"Rollback of in-memory changes for screen '{screen_id_to_remove}' due to initiation failure.")
            return jsonify(success=False, message="Failed to initiate screen remove operation."), 500
    except Exception as e:
        return jsonify(success=False, message=f"Error removing screen: {e}"), 400

@app.route('/api/set_display_mode/<string:mode_name>', methods=['POST'])
def set_display_mode_route(mode_name):
    # global current_display_mode # Managed by helper
    with data_lock: # Protect read of screen_layouts and write to current_display_mode by helper
        success = _set_active_display_mode(mode_name)
    
    if success:
        return jsonify(success=True, message=f"Display mode set to {mode_name}"), 200
    else:
        return jsonify(success=False, message=f"Invalid display mode: {mode_name}"), 400

def update_display_content(): 
    global active_widget_instances, current_frame_widget_dimensions
    with data_lock:
        optimizer.start_timer("matrix_clear")
        matrix_display.clear() 
        optimizer.end_timer("matrix_clear")
        now = datetime.datetime.now()
        
        new_dimensions_this_frame = []

        current_screen_config = screen_layouts.get(current_display_mode)
        if not current_screen_config:
            print(f"Warning: Screen '{current_display_mode}' not found. Cannot update display.")
            return

        widgets_on_current_screen_config = current_screen_config.get('widgets', [])
        current_widget_ids_on_screen = {wc['id'] for wc in widgets_on_current_screen_config if wc.get('enabled')}

        optimizer.start_timer("widget_instance_management")
        ids_to_remove = set(active_widget_instances.keys()) - current_widget_ids_on_screen
        for widget_id in ids_to_remove:
            print(f"Removing instance for widget ID: {widget_id} (no longer on screen or disabled)")
            del active_widget_instances[widget_id]
        optimizer.end_timer("widget_instance_management")

        # Prepare global context using the new helper
        optimizer.start_timer("prepare_global_context")
        global_widget_context = _prepare_global_widget_context(now, widgets_on_current_screen_config)
        optimizer.end_timer("prepare_global_context")

        if not widgets_on_current_screen_config:
            current_frame_widget_dimensions = new_dimensions_this_frame # Ensure it's updated even if no widgets
            # Ensure overall widget processing timer is ended if we return early
            optimizer.end_timer("widget_processing_loop_overall") 
            return

        optimizer.start_timer("widget_processing_loop_overall") # Renamed from widget_processing_loop to be more specific
        for widget_config in widgets_on_current_screen_config:
            if not widget_config.get('enabled', False):
                continue

            widget_type = widget_config.get('type')
            widget_id = widget_config.get('id')
            WidgetClass = AVAILABLE_WIDGETS.get(widget_type)

            if WidgetClass:
                instance = None
                optimizer.start_timer(f"widget_{widget_id}_setup") # New Timer
                try:
                    if widget_id in active_widget_instances:
                        if isinstance(active_widget_instances[widget_id], WidgetClass):
                            instance = active_widget_instances[widget_id]
                            instance.config = widget_config 
                            instance.global_context = global_widget_context
                            instance.reconfigure() 
                        else:
                            print(f"Type mismatch for {widget_id}. Expected {WidgetClass.__name__}, found {type(active_widget_instances[widget_id]).__name__}. Recreating.")
                            del active_widget_instances[widget_id] # remove bad instance
                    
                    if instance is None: 
                        instance = WidgetClass(config=widget_config, global_context=global_widget_context)
                        active_widget_instances[widget_id] = instance
                        print(f"Created new instance for widget ID: {widget_id} of type {widget_type}")
                finally:
                    optimizer.end_timer(f"widget_{widget_id}_setup") # New Timer
                    
                if instance: # Ensure instance was successfully created/retrieved
                    try:
                        optimizer.start_timer(f"widget_{widget_id}_get_content")
                        # content can be a string (for text) or a dict (for pixel_map)
                        content = instance.get_content()
                        optimizer.end_timer(f"widget_{widget_id}_get_content")

                        final_draw_x = instance.x
                        final_draw_y = instance.y # y-coordinate of the widget

                        # Check if content is a dictionary and of type 'pixel_map'
                        if isinstance(content, dict) and content.get('type') == 'pixel_map':
                            pixel_data = content.get('data', [])
                            map_width = content.get('width', 0)
                            map_height = content.get('height', 0)
                            
                            # Add dimensions for this pixel_map widget
                            new_dimensions_this_frame.append({
                                'id': widget_id,
                                'width_cells': map_width,
                                'height_cells': map_height
                            })

                            optimizer.start_timer(f"widget_{widget_id}_draw_pixel_map")
                            if pixel_data and map_width > 0 and map_height > 0:
                                # OLD METHOD - Loop and set_pixel:
                                # for r_idx, row in enumerate(pixel_data):
                                #     if r_idx >= map_height: break # Respect map_height
                                #     for c_idx, color_tuple in enumerate(row):
                                #         if c_idx >= map_width: break # Respect map_width
                                #         if isinstance(color_tuple, tuple) and len(color_tuple) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in color_tuple):
                                #             abs_x = final_draw_x + c_idx
                                #             abs_y = final_draw_y + r_idx
                                #             if 0 <= abs_x < MATRIX_WIDTH and 0 <= abs_y < MATRIX_HEIGHT:
                                #                  matrix_display.set_pixel(abs_x, abs_y, color_tuple)
                                
                                # NEW METHOD - Use draw_pixel_map
                                matrix_display.draw_pixel_map(final_draw_x, final_draw_y, pixel_data)
                                         
                            optimizer.end_timer(f"widget_{widget_id}_draw_pixel_map")

                        # Else, assume it's text content (string)
                        elif isinstance(content, str) and content: 
                            text_to_draw = content
                            rgb_color_tuple = hex_to_rgb(instance.color)
                            font_name_to_pass = None
                            if hasattr(instance, 'font_size'):
                                # Re-map font_size string to actual font file name/key
                                if instance.font_size == 'small': font_name_to_pass = '3x5'
                                elif instance.font_size == 'medium': font_name_to_pass = '5x7'
                                elif instance.font_size == 'large': font_name_to_pass = '7x9'
                                elif instance.font_size == 'xl': font_name_to_pass = 'xl' 
                            
                            try:
                                # Calculate dimensions for text
                                width_cells, height_cells = matrix_display.get_text_dimensions(text_to_draw, font_name_to_pass)
                                new_dimensions_this_frame.append({
                                    'id': widget_id,
                                    'width_cells': width_cells,
                                    'height_cells': height_cells
                                })
                            except Exception as dim_error:
                                print(f"Error calculating dimensions for widget {widget_id} (text): {dim_error}")
                                # Provide default dimensions on error
                                new_dimensions_this_frame.append({
                                    'id': widget_id,
                                    'width_cells': 5, # Default width
                                    'height_cells': 7  # Default height (e.g. for medium font)
                                })
                            
                            optimizer.start_timer(f"widget_{widget_id}_draw_text")
                            matrix_display.draw_text(text_to_draw, final_draw_x, final_draw_y, rgb_color_tuple, font_name_to_pass)
                            optimizer.end_timer(f"widget_{widget_id}_draw_text")
                        # elif content: # If content is not None/empty string but not a handled type
                        #    instance._log("WARNING", f"Received unhandled content type from get_content(): {type(content)}")

                    except Exception as e:
                        print(f"Error processing widget '{widget_config.get('id', widget_type)}': {e}")
                        # Ensure individual widget processing timer is stopped in case of error within the loop
                        optimizer.end_timer(f"widget_{widget_id}_processing")
            else:
                print(f"Warning: Widget type '{widget_type}' not found in AVAILABLE_WIDGETS.")
        optimizer.end_timer("widget_processing_loop_overall") # Renamed
        
        current_frame_widget_dimensions = new_dimensions_this_frame

@app.route('/api/matrix_data')
def get_matrix_data_route(): 
    global current_frame_widget_dimensions # Access the global list
    with data_lock: # Ensure we read a consistent buffer and dimensions list
        pixels = matrix_display.get_buffer()
        mode = current_display_mode
        # Make a copy of the dimensions to avoid issues if it's modified during jsonify
        dimensions_to_send = list(current_frame_widget_dimensions) 
    return jsonify({
        "pixels": pixels,
        "current_display_mode": mode,
        "widgets_dimensions": dimensions_to_send
    })

@app.route('/api/get_matrix_logging_status', methods=['GET'])
def get_matrix_logging_status():
    global MATRIX_DATA_LOGGING_ENABLED
    return jsonify(enabled=MATRIX_DATA_LOGGING_ENABLED)

@app.route('/api/set_matrix_logging_status', methods=['POST'])
def set_matrix_logging_status():
    try:
        data = request.get_json()
        status = data.get('enabled', False)
        with data_lock:
            # _set_matrix_logging_enabled_and_save now uses a thread for file I/O.
            # MATRIX_DATA_LOGGING_ENABLED is modified under this lock.
            if _set_matrix_logging_enabled_and_save(status):
                return jsonify(success=True, message=f"Matrix data logging status update initiated, saving in background.")
            else:
                return jsonify(success=False, message="Failed to initiate matrix logging status update.")
    except Exception as e:
        return jsonify(success=False, message=f"Error setting matrix logging status: {str(e)}"), 400

def periodic_display_updater():
    """Periodically calls update_display_content in a background thread."""
    print("Starting periodic display updater thread...")
    global current_display_mode, last_screen_change_time, last_debug_log_time
    
    # Initialize offscreen_canvas for the hardware matrix if available
    thread_local_offscreen_canvas = None
    if hardware_matrix:
        try:
            thread_local_offscreen_canvas = hardware_matrix.CreateFrameCanvas()
            print("INFO: Hardware matrix offscreen canvas created successfully for the updater thread.")
        except Exception as e:
            print(f"ERROR: Failed to create hardware matrix offscreen canvas in updater thread: {e}")
            # If canvas creation fails, we won't be able to use the hardware matrix.
            # The 'if hardware_matrix and thread_local_offscreen_canvas:' check later will handle this.

    last_loop_finish_time = time.monotonic()
    frame_count = 0
    skip_count = 0
    last_stats_time = time.monotonic()
    log_save_counter = 0 # New counter for saving logs
    LOG_SAVE_INTERVAL = 6 # Save log every 6*10 = 60 seconds
    
    while True:
        loop_start_time = time.monotonic()
        
        # Adaptive update interval based on performance
        current_interval = optimizer.get_update_interval(DISPLAY_UPDATE_INTERVAL)
        
        # Decide if we should skip this frame based on performance
        should_skip = optimizer.should_skip_frame()
        
        optimizer.start_timer("pdu_auto_screen_rotation") # New Timer Start
        # Auto Screen Rotation - Check if it's time to change screens
        current_time = time.monotonic()
        
        with data_lock:
            if AUTO_SCREEN_ROTATION_ENABLED and len(screen_layouts) > 1:
                current_screen = screen_layouts.get(current_display_mode)
                display_time = current_screen.get('display_time_seconds', DEFAULT_SCREEN_DISPLAY_TIME_S) if current_screen else DEFAULT_SCREEN_DISPLAY_TIME_S
                
                # Debug print to track time - only print once every 30 seconds to reduce noise
                elapsed_time = current_time - last_screen_change_time
                if current_time - last_debug_log_time > 30:  # Limit to every 30 seconds
                    print(f"[AUTO_ROTATE_DEBUG] Enabled: {AUTO_SCREEN_ROTATION_ENABLED}, Current: '{current_display_mode}', "
                          f"Time elapsed: {elapsed_time:.1f}s, Display time: {display_time}s, "
                          f"Available screens: {list(screen_layouts.keys())}")
                    last_debug_log_time = current_time
                
                if current_time - last_screen_change_time >= display_time:
                    # Get the list of screen IDs
                    screen_ids = list(screen_layouts.keys())
                    current_index = screen_ids.index(current_display_mode) if current_display_mode in screen_ids else 0
                    next_index = (current_index + 1) % len(screen_ids)
                    next_screen_id = screen_ids[next_index]
                    
                    # Change to the next screen
                    current_display_mode = next_screen_id
                    last_screen_change_time = current_time
                    print(f"[AUTO_ROTATE] Changing screen to '{next_screen_id}' (from '{screen_ids[current_index]}')")
            elif AUTO_SCREEN_ROTATION_ENABLED:
                # Only log this message once per minute to reduce noise
                if current_time - last_debug_log_time > 60:
                    print(f"[AUTO_ROTATE_DEBUG] Auto-rotation enabled but need at least 2 screens. "
                          f"Currently have {len(screen_layouts)} screens available.")
                    last_debug_log_time = current_time
        optimizer.end_timer("pdu_auto_screen_rotation") # New Timer End
        
        # Track frame stats
        frame_count += 1
        actual_cycle_time_ms = (loop_start_time - last_loop_finish_time) * 1000
        
        # Performance tracking
        optimizer.start_timer("display_update_cycle")

        try:
            # Only update display if we're not skipping this frame
            if not should_skip:
                # Time the actual display update
                optimizer.start_timer("update_display_content")
                update_display_content() 
                update_time_ms = optimizer.end_timer("update_display_content")

                # --- BEGIN NEW MATRIX HARDWARE UPDATE CODE ---
                if hardware_matrix and thread_local_offscreen_canvas: # Check if matrix and its canvas were initialized successfully
                    optimizer.start_timer("hardware_matrix_update")
                    try:
                        # Get the app's pixel buffer. 
                        with data_lock:
                            current_app_buffer = matrix_display.get_buffer()
                        
                        if current_app_buffer: # Ensure buffer is not None
                            # REUSE thread_local_offscreen_canvas. 
                            # Pixels are set directly, effectively clearing/overwriting previous frame content.
                            for y, row in enumerate(current_app_buffer):
                                if y >= MATRIX_HEIGHT: break # Boundary check
                                for x, color_tuple in enumerate(row):
                                    if x >= MATRIX_WIDTH: break # Boundary check
                                    if color_tuple and len(color_tuple) == 3:
                                        thread_local_offscreen_canvas.SetPixel(x, y, color_tuple[0], color_tuple[1], color_tuple[2])
                                    else:
                                        # Default to black if color_tuple is invalid or None
                                        thread_local_offscreen_canvas.SetPixel(x, y, 0, 0, 0)
                                        if color_tuple is not None:
                                            print(f"DEBUG: Invalid color_tuple {color_tuple} at ({x},{y}). Defaulted to black.")
                            
                            # Swap the canvas to the physical display
                            hardware_matrix.SwapOnVSync(thread_local_offscreen_canvas)
                            # print(f"DEBUG: Hardware matrix updated at {time.monotonic():.2f}") # Optional: for frequent debug
                    except Exception as e:
                        print(f"ERROR: Failed to update hardware matrix: {e}")
                        # import traceback
                        # traceback.print_exc() # For more detailed error logging if needed
                    finally:
                        optimizer.end_timer("hardware_matrix_update")
                # --- END NEW MATRIX HARDWARE UPDATE CODE ---
                
                # Decide if we should skip the next frame if this one was slow
                if SKIP_FRAMES_ON_SLOW and update_time_ms > SKIP_FRAME_THRESHOLD:
                    optimizer.update_settings({"skip_frame_rendering": True})
                    skip_count += 1
                else:
                    optimizer.update_settings({"skip_frame_rendering": False})
            else:
                skip_count += 1
                # Reset skip flag after skipping one frame
                optimizer.update_settings({"skip_frame_rendering": False})
            
            # Calculate sleep time (adaptive based on performance)
            processing_time = time.monotonic() - loop_start_time
            sleep_duration = max(0, current_interval - processing_time)
            
            if processing_time > current_interval:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [PERF_WARNING] Display update took {processing_time*1000:.2f}ms, exceeding interval of {current_interval*1000:.2f}ms.")
            
            time.sleep(sleep_duration) 
            
            # Record loop finish time
            last_loop_finish_time = time.monotonic()
            
            optimizer.start_timer("pdu_periodic_stats_log") # New Timer Start
            # Log performance stats periodically
            if time.monotonic() - last_stats_time > 10:  # Every 10 seconds
                total_time = time.monotonic() - last_stats_time
                fps = frame_count / total_time
                skip_percent = (skip_count / frame_count) * 100 if frame_count > 0 else 0
                print(f"[PERF_STATS] FPS: {fps:.1f}, Frames: {frame_count}, Skipped: {skip_count} ({skip_percent:.1f}%)")
                
                # Get and log system stats if on Raspberry Pi
                if pi_optimizer.is_raspberry_pi:
                    sys_stats = pi_optimizer.get_system_stats()
                    print(f"[SYS_STATS] CPU: {sys_stats['cpu_percent']}%, Memory: {sys_stats['memory_percent']}%, Temp: {sys_stats['temperature']}")
                
                # Reset counters
                frame_count = 0
                skip_count = 0
                last_stats_time = time.monotonic()
                
                log_save_counter += 1
                if log_save_counter >= LOG_SAVE_INTERVAL:
                    optimizer.save_log()
                    log_save_counter = 0 # Reset counter
                    print("[PERF_STATS] Performance log saved.")

            optimizer.end_timer("pdu_periodic_stats_log") # New Timer End
                
        except Exception as e:
            print(f"Error in periodic_display_updater: {e}")
            time.sleep(5) 
            last_loop_finish_time = time.monotonic()
        
        # Complete performance timing for this cycle
        optimizer.end_timer("display_update_cycle")

# Add route to get performance data
@app.route('/api/performance_stats', methods=['GET'])
def get_performance_stats():
    """Return performance statistics"""
    return jsonify(optimizer.get_performance_summary())

# Add route to update performance settings
@app.route('/api/performance_settings', methods=['POST'])
def update_performance_settings():
    """Update performance optimization settings"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid request data"})
        
    success = optimizer.update_settings(data)
    return jsonify({"success": success, "settings": optimizer.get_settings()})

# Add route to get system stats
@app.route('/api/system_stats', methods=['GET'])
def get_system_stats():
    """Get system statistics (CPU, memory, temperature)"""
    return jsonify(pi_optimizer.get_system_stats())

# Add route to get auto rotation status
@app.route('/api/get_auto_rotation_status', methods=['GET'])
def get_auto_rotation_status():
    """Get the current state of auto screen rotation"""
    global AUTO_SCREEN_ROTATION_ENABLED
    return jsonify(enabled=AUTO_SCREEN_ROTATION_ENABLED)

# Add route to set auto rotation status
@app.route('/api/set_auto_rotation_status', methods=['POST'])
def set_auto_rotation_status():
    """Enable or disable auto screen rotation"""
    global AUTO_SCREEN_ROTATION_ENABLED, last_screen_change_time
    
    data = request.get_json()
    if data is None or 'enabled' not in data or not isinstance(data['enabled'], bool):
        return jsonify(success=False, message="Invalid request. 'enabled' (boolean) is required."), 400
    
    # Update auto rotation status
    with data_lock:
        AUTO_SCREEN_ROTATION_ENABLED = data['enabled']
        if AUTO_SCREEN_ROTATION_ENABLED:
            # Reset timer when enabling
            last_screen_change_time = time.monotonic()
            print(f"[AUTO_ROTATE] Auto screen rotation enabled, starting with current screen '{current_display_mode}'")
        else:
            print(f"[AUTO_ROTATE] Auto screen rotation disabled")
    
    return jsonify(success=True, enabled=AUTO_SCREEN_ROTATION_ENABLED)

if __name__ == '__main__':
    # Apply performance optimizations
    print("Initializing performance optimizations...")
    
    # Configure app based on Raspberry Pi detection
    flask_options = optimize_flask_app()
    
    # Update default settings based on environment
    if pi_optimizer.is_raspberry_pi:
        print("Running on Raspberry Pi - applying specific optimizations")
        optimizer.update_settings({
            "update_interval_multiplier": 20.0,
            "minimize_logging": True
        })
    
    load_widget_classes()
    load_screen_layouts() # Initial load
    active_widget_instances.clear() # Ensure instances are fresh after initial load
    print("Cleared active_widget_instances after initial load_screen_layouts.")
    
    # Add custom log filter to Werkzeug logger to control /api/matrix_data logs
    werkzeug_logger = logging.getLogger('werkzeug')
    if werkzeug_logger:
        # Check if the filter is already added to prevent duplicates during reloads with Flask debug mode
        already_added = False
        for f in werkzeug_logger.filters:
            if isinstance(f, MatrixDataLogFilter):
                already_added = True
                break
        if not already_added:
            werkzeug_logger.addFilter(MatrixDataLogFilter())
            print("MatrixDataLogFilter added to Werkzeug logger.")
        else:
            print("MatrixDataLogFilter already present in Werkzeug logger.")

    else:
        print("Warning: Could not get Werkzeug logger to add MatrixDataLogFilter.")

    # Start the background thread for display updates
    update_thread = threading.Thread(target=periodic_display_updater, daemon=True)
    update_thread.start()
    
    # Start Flask app with optimized settings
    app.run(
        debug=flask_options["debug"], 
        host=flask_options["host"], 
        port=flask_options["port"],
        threaded=flask_options["threaded"]
    ) 