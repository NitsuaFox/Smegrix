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

DISPLAY_UPDATE_INTERVAL = 1 # seconds

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
            {"id": "date_default", "type": "date", "x": (MATRIX_WIDTH - 29) // 2, "y": ((MATRIX_HEIGHT - (2 * 7 + 3)) // 2) + 7 + 3, "enabled": True, "date_format_type": "dd_mm", "color": "#FFFFFF"}
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
    global screen_layouts
    if os.path.exists(SCREEN_LAYOUTS_FILE_PATH):
        try:
            with open(SCREEN_LAYOUTS_FILE_PATH, 'r') as f:
                loaded_layouts = json.load(f)
            print(f"Loaded screen layouts from {SCREEN_LAYOUTS_FILE_PATH}")
            
            if not isinstance(loaded_layouts, dict) or 'default' not in loaded_layouts:
                print("Warning: Invalid screen_layouts.json structure or default screen missing. Reverting to defaults.")
                screen_layouts = default_screen_layouts.copy()
                _save_layouts_to_file()
                return

            migrated_layouts = {}
            for screen_id, screen_config in loaded_layouts.items():
                if not isinstance(screen_config, dict):
                    print(f"Warning: Invalid configuration for screen '{screen_id}'. Skipping.")
                    continue
                if 'widgets' not in screen_config: 
                    screen_config['widgets'] = []
                if 'display_time_seconds' not in screen_config:
                    screen_config['display_time_seconds'] = DEFAULT_SCREEN_DISPLAY_TIME_S
                elif not isinstance(screen_config['display_time_seconds'], (int, float)) or screen_config['display_time_seconds'] <= 0:
                    screen_config['display_time_seconds'] = DEFAULT_SCREEN_DISPLAY_TIME_S
                migrated_layouts[screen_id] = screen_config
            
            screen_layouts = migrated_layouts
            if 'default' not in screen_layouts:
                 print("Critical: Default screen was lost during migration. Re-initializing default screen.")
                 screen_layouts['default'] = default_screen_layouts['default'].copy()
                 _save_layouts_to_file()

        except json.JSONDecodeError:
            print(f"Error decoding {SCREEN_LAYOUTS_FILE_PATH}. Using default layouts.")
            screen_layouts = default_screen_layouts.copy()
            _save_layouts_to_file()
        except Exception as e:
            print(f"Error loading {SCREEN_LAYOUTS_FILE_PATH}: {e}. Using default layouts.")
            screen_layouts = default_screen_layouts.copy()
            _save_layouts_to_file()
    else:
        print(f"{SCREEN_LAYOUTS_FILE_PATH} not found. Using default layouts and creating file.")
        screen_layouts = default_screen_layouts.copy()
        _save_layouts_to_file()

def _save_layouts_to_file():
    try:
        with open(SCREEN_LAYOUTS_FILE_PATH, 'w') as f:
            json.dump(screen_layouts, f, indent=4)
        print(f"Screen layouts saved to {SCREEN_LAYOUTS_FILE_PATH}")
        return True
    except Exception as e:
        print(f"Error saving screen layouts to {SCREEN_LAYOUTS_FILE_PATH}: {e}")
        return False

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
    widget_type_data = []
    for type_key, widget_class in AVAILABLE_WIDGETS.items():
        # Attempt to get a display name (e.g., from class docstring or a class variable)
        # For simplicity, we'll use the type_key capitalized for now, but this can be improved.
        display_name = widget_class.__name__.replace("Widget", "") # Simple name like "Time" or "NetworkSSID"
        # Make it more readable, e.g. NetworkSSID -> Network SSID
        display_name = re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', display_name).strip()
        
        widget_type_data.append({
            "type": type_key,
            "displayName": display_name,
            "configOptions": widget_class.get_config_options() # Get specific config options
        })
    return jsonify(widget_type_data)

@app.route('/api/get_screen_layouts', methods=['GET'])
def get_screen_layouts_route():
    return jsonify(screen_layouts)

@app.route('/api/save_screen_layouts', methods=['POST'])
def save_screen_layouts_route():
    global screen_layouts, active_widget_instances
    try:
        new_layouts = request.get_json()
        if not isinstance(new_layouts, dict):
            return jsonify(success=False, message="Invalid layout format: must be a dictionary."), 400
        with data_lock: # Protect write to screen_layouts
            screen_layouts = new_layouts
            active_widget_instances.clear() # Clear instances to force re-creation
            print("Cleared active_widget_instances due to layout save.")
            saved = _save_layouts_to_file()
        
        if saved:
            # update_display_content() # The background thread will handle updates
            return jsonify(success=True, message="Screen layouts saved successfully.")
        else:
            return jsonify(success=False, message="Failed to save screen layouts to file."), 500
    except Exception as e:
        return jsonify(success=False, message=f"Error processing request: {e}"), 400

@app.route('/api/add_screen', methods=['POST'])
def add_screen_route():
    global screen_layouts, active_widget_instances
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
            screen_layouts[new_screen_id] = {
                "name": new_screen_name,
                "widgets": [],
                "display_time_seconds": DEFAULT_SCREEN_DISPLAY_TIME_S
            }
            active_widget_instances.clear() # Clear instances as layout structure changed
            print("Cleared active_widget_instances due to adding screen.")
            saved = _save_layouts_to_file()

        if saved:
            return jsonify(success=True, message=f"Screen '{new_screen_name}' added successfully.", new_screen_id=new_screen_id)
        else:
            # Rollback if save failed, though _save_layouts_to_file failing is less common than the write itself
            with data_lock: 
                if new_screen_id in screen_layouts: del screen_layouts[new_screen_id]
            return jsonify(success=False, message="Failed to save updated layouts to file."), 500
    except Exception as e:
        return jsonify(success=False, message=f"Error adding screen: {e}"), 400

@app.route('/api/remove_screen/<string:screen_id_to_remove>', methods=['POST'])
def remove_screen_route(screen_id_to_remove):
    global screen_layouts, current_display_mode, active_widget_instances
    original_layouts_copy = None # For potential rollback if save fails
    try:
        if screen_id_to_remove == 'default':
            return jsonify(success=False, message="Cannot remove the default screen."), 400
        
        with data_lock:
            if screen_id_to_remove not in screen_layouts:
                return jsonify(success=False, message=f"Screen ID '{screen_id_to_remove}' not found."), 404
            original_layouts_copy = json.dumps(screen_layouts) # Deep copy for rollback
            removed_screen_name = screen_layouts[screen_id_to_remove].get('name', screen_id_to_remove)
            del screen_layouts[screen_id_to_remove]
            display_mode_changed = False
            if current_display_mode == screen_id_to_remove:
                current_display_mode = 'default' 
                display_mode_changed = True
                print(f"Current display mode was {screen_id_to_remove}, switched to default.")
            active_widget_instances.clear() # Clear instances as layout structure changed
            print("Cleared active_widget_instances due to removing screen.")
            saved = _save_layouts_to_file()

        if saved:
            # update_display_content() will be handled by the background thread
            return jsonify(success=True, message=f"Screen '{removed_screen_name}' removed successfully.", new_active_mode=current_display_mode if display_mode_changed else None)
        else:
            # Rollback
            if original_layouts_copy:
                with data_lock:
                    screen_layouts = json.loads(original_layouts_copy)
                    # We might also need to revert current_display_mode if it was changed and save failed
                    # but _save_layouts_to_file is less likely to fail here.
            return jsonify(success=False, message="Failed to save updated layouts to file after removing screen."), 500
    except Exception as e:
        return jsonify(success=False, message=f"Error removing screen: {e}"), 400

@app.route('/api/set_display_mode/<string:mode_name>', methods=['POST'])
def set_display_mode_route(mode_name):
    global current_display_mode
    with data_lock: # Protect read of screen_layouts and write to current_display_mode
        if mode_name in screen_layouts:
            current_display_mode = mode_name
            # update_display_content() # Let background thread handle this
            # Note: Changing mode doesn't necessarily need to clear all widget instances
            # if they could persist across screens, but current model is per-screen instances implicitly.
            # No, active_widget_instances are managed by update_display_content based on current screen.
            return jsonify(success=True, message=f"Display mode set to {mode_name}"), 200
        return jsonify(success=False, message=f"Invalid display mode: {mode_name}"), 400

def update_display_content(): 
    global active_widget_instances # Ensure we're using the global cache
    with data_lock: # Ensure exclusive access to shared resources
        matrix_display.clear() 
        now = datetime.datetime.now()
        
        current_screen_config = screen_layouts.get(current_display_mode)
        if not current_screen_config:
            print(f"Warning: Screen '{current_display_mode}' not found in screen_layouts. Cannot update display.")
            # Clean up instances if the screen config is gone
            # active_widget_instances.clear() # Or selectively remove only for this screen if it existed
            return

        widgets_on_current_screen_config = current_screen_config.get('widgets', [])
        current_widget_ids_on_screen = {wc['id'] for wc in widgets_on_current_screen_config if wc.get('enabled')}

        # Remove instances that are no longer on the current enabled screen
        ids_to_remove = set(active_widget_instances.keys()) - current_widget_ids_on_screen
        for widget_id in ids_to_remove:
            print(f"Removing instance for widget ID: {widget_id} (no longer on screen or disabled)")
            del active_widget_instances[widget_id]

        # Prepare global context (conditionally fetch network info)
        needs_net_info = any(
            widget_config.get('type') in AVAILABLE_WIDGETS and \
            (AVAILABLE_WIDGETS[widget_config.get('type')].__name__ in ['NetworkSSIDWidget', 'NetworkRSSIDWidget']) and \
            widget_config.get('enabled', False)
            for widget_config in widgets_on_current_screen_config
        )
        ssid_val, rssi_val = ("N/A", "N/A")
        if needs_net_info:
            ssid_val, rssi_val = get_network_info_macos()

        global_widget_context = {
            'now': now,
            'ssid': ssid_val,
            'rssi': rssi_val
        }

        if not widgets_on_current_screen_config:
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
                            # print(f"Reusing instance for {widget_id}") # Debug
                        else:
                            # Type mismatch, should re-create
                            print(f"Type mismatch for {widget_id}. Expected {WidgetClass.__name__}, found {type(active_widget_instances[widget_id]).__name__}. Recreating.")
                            del active_widget_instances[widget_id] # remove bad instance
                    
                    if instance is None: # Needs creation or re-creation
                        instance = WidgetClass(config=widget_config, global_context=global_widget_context)
                        active_widget_instances[widget_id] = instance
                        print(f"Created new instance for widget ID: {widget_id} of type {widget_type}")
                    
                    content = instance.get_content()
                    if content: 
                        rgb_color_tuple = hex_to_rgb(instance.color)
                        font_name_to_pass = None
                        if hasattr(instance, 'font_size'):
                            if instance.font_size == 'small': font_name_to_pass = '3x5'
                            elif instance.font_size == 'medium': font_name_to_pass = '5x7'
                            elif instance.font_size == 'large': font_name_to_pass = '7x9'
                            elif instance.font_size == 'xl': font_name_to_pass = 'xl'
                        matrix_display.draw_text(content, instance.x, instance.y, color_tuple=rgb_color_tuple, font_name=font_name_to_pass)
                except Exception as e:
                    print(f"Error processing widget '{widget_config.get('id', widget_type)}': {e}")
            else:
                print(f"Warning: Widget type '{widget_type}' not found in AVAILABLE_WIDGETS.")

@app.route('/api/matrix_data')
def get_matrix_data_route(): 
    with data_lock: # Ensure we read a consistent buffer
        pixels = matrix_display.get_buffer()
        mode = current_display_mode
    return jsonify({
        "pixels": pixels,
        "current_display_mode": mode
    })

def periodic_display_updater():
    """Periodically calls update_display_content in a background thread."""
    print("Starting periodic display updater thread...")
    while True:
        try:
            # print(f"Background thread: calling update_display_content() at {time.time()}") # Debug
            update_display_content() 
            time.sleep(DISPLAY_UPDATE_INTERVAL) 
        except Exception as e:
            print(f"Error in periodic_display_updater: {e}")
            # Avoid busy-looping on repeated errors in the updater itself
            time.sleep(5) # Sleep longer if there was an error in the update logic

if __name__ == '__main__':
    load_widget_classes()
    load_screen_layouts() # Initial load
    active_widget_instances.clear() # Ensure instances are fresh after initial load
    print("Cleared active_widget_instances after initial load_screen_layouts.")
    
    # Start the background thread for display updates
    update_thread = threading.Thread(target=periodic_display_updater, daemon=True)
    update_thread.start()
    
    # update_display_content() # Initial call, now handled by the thread almost immediately
    app.run(debug=True, host='0.0.0.0', port=5001) 