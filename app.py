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

# Import BaseWidget to check instance types, though specific widgets are loaded dynamically
from widgets.base_widget import BaseWidget 

app = Flask(__name__)

# Matrix dimensions
MATRIX_WIDTH = 64
MATRIX_HEIGHT = 64

# Create a single Display instance that will be used throughout the application
matrix_display = Display(width=MATRIX_WIDTH, height=MATRIX_HEIGHT)

# Current display mode
current_display_mode = 'default' 
SCREEN_LAYOUTS_FILE_PATH = 'screen_layouts.json'

# --- Widget Management ---
AVAILABLE_WIDGETS = {} # Stores loaded widget classes, e.g., {"time": TimeWidget, "text": TextWidget}
active_widget_instances = {} # Stores active widget instances: widget_id -> instance

# Lock for synchronizing access to shared resources like screen_layouts, current_display_mode, and matrix_display
data_lock = threading.Lock()

DISPLAY_UPDATE_INTERVAL = 0.05 # seconds - Increased for smoother animation (was 1.0)
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
        print(f"Warning: Widgets directory not found at {widgets_path}")
        return

    for filename in os.listdir(widgets_path):
        if filename.endswith('_widget.py'): # Convention: widget_type_widget.py
            module_name_full = f"widgets.{filename[:-3]}"
            widget_type_key = filename[:-10] # Extracts 'time' from 'time_widget.py'
            try:
                module = importlib.import_module(module_name_full)
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a subclass of BaseWidget and actually defined in this module (not imported)
                    if issubclass(cls, BaseWidget) and cls is not BaseWidget and cls.__module__ == module_name_full:
                        if widget_type_key in AVAILABLE_WIDGETS:
                            print(f"Warning: Duplicate widget type key '{widget_type_key}' found. Overwriting.")
                        AVAILABLE_WIDGETS[widget_type_key] = cls
                        print(f"Successfully loaded widget: {name} as type '{widget_type_key}'")
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
            {"id": "ncf_val_ssid", "type": "network_ssid", "x": 1, "y": 1 + 7 + 2, "enabled": True, "color": "#FFFFFF"},
            {"id": "ncf_lbl_rssi", "type": "text", "text": "RSSI:", "x": 1, "y": 1 + 2*(7 + 2), "enabled": True, "color": "#FFFF00"},
            {"id": "ncf_val_rssi", "type": "network_rssi", "x": 1, "y": 1 + 3*(7 + 2), "enabled": True, "color": "#FFFFFF"}
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

def _save_layouts_to_file():
    global screen_layouts, MATRIX_DATA_LOGGING_ENABLED
    try:
        data_to_save = {'matrix_data_logging_enabled': MATRIX_DATA_LOGGING_ENABLED}
        data_to_save.update(screen_layouts)

        with open(SCREEN_LAYOUTS_FILE_PATH, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        print(f"Screen layouts and global settings (matrix logging: {MATRIX_DATA_LOGGING_ENABLED}) saved to {SCREEN_LAYOUTS_FILE_PATH}")
        return True
    except Exception as e:
        print(f"Error saving screen layouts to {SCREEN_LAYOUTS_FILE_PATH}: {e}")
        return False

def _update_and_save_screen_layouts(new_layouts_data):
    """Updates the global screen_layouts, clears active instances, and saves to file."""
    global screen_layouts, active_widget_instances
    # No lock needed here if this function is always called within a lock from the route
    # or if the calling context is responsible for locking.
    # For now, assuming the route will handle the lock for atomicity of request processing.
    screen_layouts = new_layouts_data
    active_widget_instances.clear()
    print("Cleared active_widget_instances due to layout save.")
    return _save_layouts_to_file()

def _add_new_screen(screen_id, screen_name):
    """Adds a new screen to the global screen_layouts and saves to file."""
    global screen_layouts, active_widget_instances
    # Assuming lock is handled by the caller (the route function)
    if screen_id in screen_layouts:
        # This check is also in the route, but good for the helper to be safe if called elsewhere.
        # The route can return a specific error before calling this if ID exists.
        # For now, this makes the helper robust but might lead to a generic error if route doesn't pre-check.
        # Or, we can let the route do the pre-check and this helper assumes ID is new.
        # Let's assume the route does the pre-check for cleaner error messages from route.
        pass # Route should prevent this, but if called directly, this would be an issue. 
             # Decision: Route will do the pre-check. This func assumes ID is new for its context.

    screen_layouts[screen_id] = {
        "name": screen_name,
        "widgets": [],
        "display_time_seconds": DEFAULT_SCREEN_DISPLAY_TIME_S
    }
    active_widget_instances.clear()
    print(f"Cleared active_widget_instances due to adding screen: {screen_id}")
    return _save_layouts_to_file()

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
    
    saved_to_file = _save_layouts_to_file()
    return saved_to_file, removed_screen_name, display_mode_was_changed

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
    if _save_layouts_to_file():
        return True
    else:
        return False

def _prepare_global_widget_context(current_time, current_screen_widget_configs):
    """Prepares the global context dictionary for widgets, fetching network info if needed."""
    ssid_val, rssi_val = ("N/A", "N/A") # Defaults
    needs_net_info = any(
        widget_config.get('type') in AVAILABLE_WIDGETS and \
        (AVAILABLE_WIDGETS[widget_config.get('type')].__name__ in ['NetworkSSIDWidget', 'NetworkRSSIDWidget']) and \
        widget_config.get('enabled', False)
        for widget_config in current_screen_widget_configs
    )
    if needs_net_info:
        # Consider if get_network_info_macos() should be more generic or platform-dependent here
        ssid_val, rssi_val = get_network_info_macos() 

    return {
        'now': current_time,
        'ssid': ssid_val,
        'rssi': rssi_val,
        'get_text_dimensions': matrix_display.get_text_dimensions, # Pass the method itself
        'matrix_width': MATRIX_WIDTH
    }

def get_network_info_macos():
    ssid = "N/A"
    rssi = "N/A"
    try:
        process = subprocess.run(
            ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
            capture_output=True, text=True, check=True, timeout=5 
        )
        output = process.stdout
        ssid_match = re.search(r"^\s*SSID: (.+)$", output, re.MULTILINE)
        if ssid_match:
            ssid = ssid_match.group(1).strip()[:10]
        rssi_match = re.search(r"^\s*agrCtlRSSI: (.+)$", output, re.MULTILINE)
        if rssi_match:
            rssi = rssi_match.group(1).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"Error fetching network info: {e}")
    return ssid, rssi

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def config_page():
    return render_template('config.html')

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
    # global screen_layouts, active_widget_instances # No longer directly manipulating globals here
    try:
        new_layouts = request.get_json()
        if not isinstance(new_layouts, dict):
            return jsonify(success=False, message="Invalid layout format: must be a dictionary."), 400
        
        with data_lock: # Lock remains here to protect the overall operation triggered by the request
            saved = _update_and_save_screen_layouts(new_layouts)
        
        if saved:
            return jsonify(success=True, message="Screen layouts saved successfully.")
        else:
            return jsonify(success=False, message="Failed to save screen layouts to file."), 500
    except Exception as e:
        return jsonify(success=False, message=f"Error processing request: {e}"), 400

@app.route('/api/add_screen', methods=['POST'])
def add_screen_route():
    # global screen_layouts, active_widget_instances # No longer directly manipulating globals here
    try:
        data = request.get_json()
        new_screen_id = data.get('screen_id')
        new_screen_name = data.get('screen_name')

        if not new_screen_id or not new_screen_name:
            return jsonify(success=False, message="Screen ID and Name are required."), 400
        if not re.match(r"^[a-zA-Z0-9_\-]+$", new_screen_id):
            return jsonify(success=False, message="Screen ID can only contain letters, numbers, underscores, and hyphens."), 400
        
        with data_lock:
            if new_screen_id in screen_layouts: # Pre-check for existing ID before calling helper
                return jsonify(success=False, message=f"Screen ID '{new_screen_id}' already exists."), 400
            
            saved = _add_new_screen(new_screen_id, new_screen_name)

        if saved:
            return jsonify(success=True, message=f"Screen '{new_screen_name}' added successfully.", new_screen_id=new_screen_id)
        else:
            # Simplified rollback: if save failed, the in-memory change might persist until next load
            # or we could attempt to remove it. For now, error is reported.
            # A more robust rollback would explicitly remove new_screen_id from screen_layouts here if save failed.
            with data_lock: # Ensure thread safety if we decide to revert the in-memory change
                if new_screen_id in screen_layouts: # If it was added and save failed
                    del screen_layouts[new_screen_id] # Revert in-memory addition
                    print(f"Rolled back addition of screen '{new_screen_id}' due to save failure.")
            return jsonify(success=False, message="Failed to save updated layouts to file after adding screen."), 500
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

            saved, removed_name, mode_changed = _remove_screen(screen_id_to_remove)

        if saved:
            new_active_mode_val = None
            if mode_changed:
                # current_display_mode (global) has been updated by _remove_screen to 'default'
                new_active_mode_val = current_display_mode 
            
            return jsonify(success=True, 
                           message=f"Screen '{removed_name}' removed successfully.", 
                           new_active_mode=new_active_mode_val)
        else:
            # Attempt to roll back in-memory changes if save failed
            with data_lock:
                if original_screen_config:
                    screen_layouts[screen_id_to_remove] = original_screen_config # Restore deleted screen
                
                # If mode was changed by the helper (meaning global current_display_mode was set to 'default'),
                # revert it to its state before the helper call using the snapshot.
                if mode_changed: 
                    current_display_mode = original_current_display_mode_snapshot
                
                active_widget_instances.clear() # Keep it simple: clear instances on failed save too.
                print(f"Rolled back in-memory changes for screen '{screen_id_to_remove}' due to save failure.")
            return jsonify(success=False, message="Failed to save updated layouts to file after removing screen."), 500
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
        matrix_display.clear() 
        now = datetime.datetime.now()
        
        new_dimensions_this_frame = []

        current_screen_config = screen_layouts.get(current_display_mode)
        if not current_screen_config:
            print(f"Warning: Screen '{current_display_mode}' not found. Cannot update display.")
            return

        widgets_on_current_screen_config = current_screen_config.get('widgets', [])
        current_widget_ids_on_screen = {wc['id'] for wc in widgets_on_current_screen_config if wc.get('enabled')}

        ids_to_remove = set(active_widget_instances.keys()) - current_widget_ids_on_screen
        for widget_id in ids_to_remove:
            print(f"Removing instance for widget ID: {widget_id} (no longer on screen or disabled)")
            del active_widget_instances[widget_id]

        # Prepare global context using the new helper
        global_widget_context = _prepare_global_widget_context(now, widgets_on_current_screen_config)

        if not widgets_on_current_screen_config:
            current_frame_widget_dimensions = new_dimensions_this_frame # Ensure it's updated even if no widgets
            return

        for widget_config in widgets_on_current_screen_config:
            if not widget_config.get('enabled', False):
                continue

            widget_type = widget_config.get('type')
            widget_id = widget_config.get('id')
            WidgetClass = AVAILABLE_WIDGETS.get(widget_type)

            if WidgetClass:
                instance = None
                try:
                    if widget_id in active_widget_instances:
                        # Check if the type matches, just in case config got weird
                        if isinstance(active_widget_instances[widget_id], WidgetClass):
                            instance = active_widget_instances[widget_id]
                            # Update config and context on existing instance
                            instance.config = widget_config 
                            instance.global_context = global_widget_context
                            instance.reconfigure() # Re-apply config to internal state
                            # print(f"Reusing instance for {widget_id}") # Debug
                        else:
                            # Type mismatch, should re-create
                            print(f"Type mismatch for {widget_id}. Expected {WidgetClass.__name__}, found {type(active_widget_instances[widget_id]).__name__}. Recreating.")
                            del active_widget_instances[widget_id] # remove bad instance
                    
                    if instance is None: # Needs creation or re-creation
                        instance = WidgetClass(config=widget_config, global_context=global_widget_context)
                        active_widget_instances[widget_id] = instance
                        print(f"Created new instance for widget ID: {widget_id} of type {widget_type}")
                    
                    # --- Determine text content and drawing parameters ---
                    # For NewsWidget, get_content() now handles updating scroll state 
                    # and returning the correctly clipped visible segment.
                    # The pixel offset is managed internally by the widget.
                    text_to_draw = instance.get_content()
                    final_draw_x = instance.x # Draw the returned segment at the widget's base x

                    if text_to_draw: 
                        rgb_color_tuple = hex_to_rgb(instance.color)
                        font_name_to_pass = None
                        if hasattr(instance, 'font_size'):
                            if instance.font_size == 'small': font_name_to_pass = '3x5'
                            elif instance.font_size == 'medium': font_name_to_pass = '5x7'
                            elif instance.font_size == 'large': font_name_to_pass = '7x9'
                            elif instance.font_size == 'xl': font_name_to_pass = 'xl' # Uses 9x13 in display.py
                        
                        # Calculate and store dimensions
                        try:
                            width_cells, height_cells = matrix_display.get_text_dimensions(text_to_draw, font_name_to_pass)
                            new_dimensions_this_frame.append({
                                'id': widget_id,
                                'width_cells': width_cells,
                                'height_cells': height_cells
                            })
                        except Exception as dim_error:
                            print(f"Error calculating dimensions for widget {widget_id}: {dim_error}")
                            # Add with default/fallback dimensions if calculation fails
                            new_dimensions_this_frame.append({
                                'id': widget_id,
                                'width_cells': 5, # Fallback width
                                'height_cells': 7  # Fallback height (e.g. for 5x7 font)
                            })

                        matrix_display.draw_text(text_to_draw, final_draw_x, instance.y, color_tuple=rgb_color_tuple, font_name=font_name_to_pass)
                except Exception as e:
                    print(f"Error processing widget '{widget_config.get('id', widget_type)}': {e}")
            else:
                print(f"Warning: Widget type '{widget_type}' not found in AVAILABLE_WIDGETS.")
        
        # Update the global dimensions list for the current frame
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
    # global MATRIX_DATA_LOGGING_ENABLED # This global is managed by the helper function
    data = request.get_json()
    if data is None or 'enabled' not in data or not isinstance(data['enabled'], bool):
        return jsonify(success=False, message="Invalid request. 'enabled' (boolean) is required."), 400
    
    requested_status = data['enabled']
    
    # The data_lock is important here because _set_matrix_logging_enabled_and_save calls 
    # _save_layouts_to_file, which reads screen_layouts (shared) and writes to the filesystem.
    with data_lock: 
        save_success = _set_matrix_logging_enabled_and_save(requested_status)
            
    if save_success:
        # Return the current status of MATRIX_DATA_LOGGING_ENABLED, which the helper updated.
        return jsonify(success=True, enabled=MATRIX_DATA_LOGGING_ENABLED)
    else:
        # If saving failed, the global MATRIX_DATA_LOGGING_ENABLED might have changed,
        # but its persistence failed. The user gets an error. 
        # The actual global MATRIX_DATA_LOGGING_ENABLED reflects the attempted state.
        return jsonify(success=False, 
                       message="Failed to save configuration after updating logging status.", 
                       enabled=MATRIX_DATA_LOGGING_ENABLED), 500

def periodic_display_updater():
    """Periodically calls update_display_content in a background thread."""
    print("Starting periodic display updater thread...")
    last_loop_finish_time = time.monotonic()
    while True:
        loop_start_time = time.monotonic()
        # Precise timing log
        now_for_log = datetime.datetime.now()
        actual_cycle_time_ms = (loop_start_time - last_loop_finish_time) * 1000
        # print(f"[{now_for_log.strftime('%H:%M:%S.%f')[:-3]}] Periodic_updater: cycle start. Actual time since last cycle finish: {actual_cycle_time_ms:.2f}ms")

        try:
            update_display_content() 
            
            processing_time = time.monotonic() - loop_start_time
            sleep_duration = DISPLAY_UPDATE_INTERVAL - processing_time
            
            if sleep_duration < 0:
                sleep_duration = 0 
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [PERF_WARNING] Display update took {processing_time*1000:.2f}ms, exceeding interval of {DISPLAY_UPDATE_INTERVAL*1000:.2f}ms.")

            # print(f"Display update processing: {processing_time*1000:.2f}ms, sleeping for: {sleep_duration*1000:.2f}ms") # Verbose
            time.sleep(sleep_duration) 
            last_loop_finish_time = time.monotonic()
        except Exception as e:
            print(f"Error in periodic_display_updater: {e}")
            time.sleep(5) 
            last_loop_finish_time = time.monotonic() # Update here too to avoid false long cycle time after error

if __name__ == '__main__':
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
    
    # update_display_content() # Initial call, now handled by the thread almost immediately
    app.run(debug=True, host='0.0.0.0', port=5001) 