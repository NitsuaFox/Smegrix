# Smegtrix - LED Matrix Display Simulator & Controller

Smegtrix is a Python-based simulator and controller for a 64x64 LED matrix display. It features a Flask web backend, a dynamic HTML/CSS/JavaScript frontend for simulation and configuration, and a modular widget-based system for displaying various information.

## Core Features

*   **Web-Based Simulator**: Visualize the 64x64 LED matrix in your browser (`/`). Includes a **Live Edit Mode** for dragging and positioning widgets directly on the simulator grid, with visual centering guides.
*   **Dynamic Configuration UI**: A dedicated web page (`/config`) to manage screens and widgets with features like:
    *   Screen creation, deletion, naming, and per-screen display duration for rotation.
    *   Widget addition, deletion, and reordering within screens.
    *   Configuration of widget-specific settings using dynamically generated forms.
    *   Expandable/collapsible cards for each widget's settings for better UI management.
    *   Clear display of Widget ID and Type on each configuration card.
    *   Support for various input types for widget-specific options (text, number, select, checkbox).
*   **Flask Backend**: Manages display logic, data, and configuration via API endpoints.
*   **Screen Management**:
    *   Create, configure, and switch between multiple virtual screens.
    *   Per-screen settings for display duration in the rotation sequence.
    *   **Auto Screen Rotation**: Screens can automatically cycle based on their configured display times. This can be toggled on/off from the simulator page.
*   **Modular Widget System**:
    *   Dynamically loaded widgets (time, date, text, weather, network stats, network RSSI).
    *   Widgets can be added, removed, and positioned on each screen.
    *   Each widget has its own specific configuration options (e.g., font sizes, date/time formats, colors, API keys, display formats).
*   **Advanced Font System (`display.py`)**:
    *   Multiple font sizes available:
        *   `3x5` (Compact, A-Z, 0-9)
        *   `5x7` (Standard, A-Z, 0-9, common symbols)
        *   `7x9` ("Large", A-Z, 0-9, common symbols)
        *   `xl` (mapped to `9x13`, "Extra Large", currently 0-9 and limited symbols)
    *   Widgets can offer font size selection through their configuration.
*   **Weather Widget Enhancements**:
    *   Flexible display format string using placeholders.
    *   Support for multi-day forecasts: `{temp_max_N}`, `{temp_min_N}`, `{weather_desc_N}` (where N is day index, 0 for today).
    *   Support for day of the week: `{dow_N}` (e.g., "MON", "TUE").
*   **Persistent Configuration**: Screen layouts and widget settings are saved in `screen_layouts.json`. Global settings like matrix data request logging are also stored here.
*   **Logging Control**: Toggle verbose logging for matrix data requests via the UI (`/config` for persistence, and a temporary toggle in the debug panel on `/`).

## Tech Stack

*   **Backend**: Python, Flask
*   **Frontend**: HTML, CSS, JavaScript (vanilla)
*   **Data Storage**: JSON file (`screen_layouts.json`) for all screen and widget configurations.
*   **Key Python Libraries**: `Flask`, `requests`, `ntplib`.

## Project Structure

```
.Smegrix/
├── app.py                  # Main Flask application, API endpoints, display logic, widget loading, screen rotation
├── display.py              # Display class, font data (3x5, 5x7, 7x9, 9x13/XL), drawing utilities
├── screen_layouts.json     # Stores screen, widget configurations, and global settings
├── widgets/                # Directory for widget modules
│   ├── base_widget.py      # Abstract BaseWidget class
│   ├── time_widget.py      # Displays current time, configurable format, font, and NTP sync
│   ├── date_widget.py      # Displays current date, configurable format & font
│   ├── text_widget.py      # Displays static text
│   ├── weather_widget.py   # Displays weather forecast with advanced formatting (Open-Meteo)
│   ├── network_stats_widget.py # Displays network SSID or IP (macOS, Linux)
│   ├── network_rssi_widget.py # Displays network RSSI (macOS specific via global context)
│   └── __init__.py         # Makes 'widgets' a Python package
├── static/                 # Static assets
│   └── css/  
│       └── style.css       # Basic styles (most UI styling is in HTML templates or inline)
├── templates/
│   ├── index.html          # Main simulator page with live edit mode and screen rotation controls
│   └── config.html         # Configuration page for screens and widgets
├── requirements.txt        # Python dependencies (Flask, requests, ntplib)
├── README.md               # This file
├── .gitignore              # Specifies intentionally untracked files
└── .venv/                  # Python virtual environment (example)
```

(Note: `widget_configs.json` might be present but `screen_layouts.json` is the primary configuration file used by the application.)

## Setup and Running

1.  **Prerequisites**:
    *   Python 3.x
2.  **Clone the repository** (if applicable) or ensure all project files are in a single directory.
3.  **Create and activate a Python virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
    (On Windows, activation is `.venv\Scripts\activate`)
4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Run the Flask application**:
    ```bash
    python app.py
    ```
6.  **Access the application**:
    *   **Simulator**: Open your web browser to `http://127.0.0.1:5001` (or the configured host/port).
        *   Use the "LIVE Mode" / "EDIT Mode" button to toggle widget dragging.
        *   Use the "Active Screen" dropdown to switch screens manually.
        *   Use the "Enable Auto Screen Rotation" checkbox to cycle through screens.
        *   A debug panel allows toggling of `/api/matrix_data` request logging.
    *   **Configuration**: Navigate to `http://127.0.0.1:5001/config`.

## Widget System Architecture

The widget system is designed to be modular and extensible.

*   **Widget Directory**: Widgets are defined as Python classes in separate files within the `widgets/` directory (e.g., `time_widget.py`, `weather_widget.py`).
*   **Base Class**: All widgets must inherit from `widgets.base_widget.BaseWidget`. This base class defines a common interface:
    *   `__init__(self, config, global_context)`: Initializes the widget with its specific configuration (ID, type, x, y, color, enabled, custom options) and a global context (e.g., current time via `global_context['now']`, network info like `global_context['ssid']`, `global_context['rssi']`).
    *   `get_content(self) -> str`: Returns the string content the widget should display.
    *   `get_config_options() -> list` (static method): Returns a list of dictionaries defining specific configuration options for the widget type. These are used to dynamically generate the configuration UI in `config.html`. The base implementation includes an `enable_logging` checkbox for widget-specific console logging.
*   **Dynamic Loading**: At startup, `app.py` dynamically imports all `*_widget.py` modules from the `widgets/` directory.
*   **Configuration (`config.html`)**:
    *   The configuration page fetches available widget types and their specific options via the `/api/get_widget_types` endpoint.
    *   When a widget is added or configured, its specific options (e.g., `font_size`, `color`, `display_format`, `enable_ntp`) are rendered dynamically based on its `get_config_options()` definition.
    *   Widget cards are collapsible for easier management of multiple widgets.
*   **Rendering**: `app.py` instantiates the required widget classes for the active screen, passes them their configuration and global context, calls `get_content()`, and then uses `display.py` to draw the text using the widget's specified position, color, and font. Widget dimensions are calculated for accurate placement and for the drag-and-drop interface on `index.html`.

### Creating a New Widget

1.  **Create a Python file** in the `widgets/` directory, e.g., `my_new_widget.py`.
2.  **Define a class** that inherits from `BaseWidget`:
    ```python
    from .base_widget import BaseWidget
    import datetime # Example import

    class MyNewWidget(BaseWidget):
        def __init__(self, config: dict, global_context: dict = None):
            super().__init__(config, global_context)
            # Your widget-specific initialization using self.config
            self.my_message = self.config.get('my_message', 'Default Message')
            self.show_time = self.config.get('show_current_time', False)

        def get_content(self) -> str:
            # Logic to generate display string
            content = self.my_message
            if self.show_time and self.global_context and 'now' in self.global_context:
                current_time_str = self.global_context['now'].strftime('%H:%M:%S')
                content += f" ({current_time_str})"
            return content

        @staticmethod
        def get_config_options() -> list:
            # Start with base options (like 'enable_logging')
            options = BaseWidget.get_config_options()
            options.extend([
                {
                    'name': 'my_message',
                    'label': 'Custom Message',
                    'type': 'text',
                    'default': 'Hello from My Widget!',
                    'placeholder': 'Enter message to display'
                },
                {
                    'name': 'show_current_time',
                    'label': 'Show Current Time with Message',
                    'type': 'checkbox',
                    'default': False
                },
                # Example of a select option
                {
                    'name': 'font_size', # Common option name
                    'label': 'Font Size',
                    'type': 'select',
                    'default': 'medium', # Corresponds to a key in Display.fonts
                    'options': [
                        {'value': 'small', 'label': 'Small (3x5)'},
                        {'value': 'medium', 'label': 'Medium (5x7)'},
                        {'value': 'large', 'label': 'Large (7x9)'},
                        {'value': 'xl', 'label': 'Extra Large (9x13)'}
                    ]
                }
            ])
            return options
    ```
3.  The application will automatically pick up the new widget type upon restart.
4.  The configuration UI (`/config`) will show "My New" (derived from class name `MyNewWidget`) in the "Add New Widget" modal, and its custom options will be available when configuring an instance of it.

## Widget Configuration Placeholders & Specifics

This section details notable configuration options and placeholders for specific widgets. Common options like `x`, `y`, `color`, `enabled`, `font_size` (for relevant widgets), and `enable_logging` (for verbose terminal output from a widget instance) are generally available.

### Time Widget (`time_widget.py`)
*   `time_format`: `strftime` string for time display (e.g., `"%H:%M:%S"`).
*   `font_size`: Select from available font sizes.
*   `enable_ntp`: Boolean, true to enable NTP time synchronization.
*   `ntp_server_address`: String, NTP server address (e.g., `pool.ntp.org`).
*   `ntp_timeout`: Number, seconds to wait for NTP server response.
*   `ntp_resync_interval_hours`: Number, how often to resynchronize with the NTP server.

### Date Widget (`date_widget.py`)
*   `date_format_type`: Select from predefined formats (e.g., "DD MON", "DD/MM/YYYY").
*   `font_size`: Select from available font sizes.
    *   (The old `custom_date_format` allowing raw `strftime` codes has been removed in favor of `date_format_type` for simplicity in the UI, but `app.py` logic for custom formats might still exist if `date_format_type` is bypassed).

### Weather Widget (`weather_widget.py`)
Uses Open-Meteo API. No API key required for basic forecast.
*   `location_name`: Text, display name for location (actual coordinates used for fetch).
*   `latitude`, `longitude`: Numbers, geographic coordinates.
*   `units`: Select "metric" (Celsius, km/h) or "imperial" (Fahrenheit, mph).
*   `time_display_format`: `strftime` string for sunrise/sunset times (e.g., `"%H:%M"`).
*   `display_format`: A flexible string with placeholders.
    *   Current weather: `{temp}`, `{unit_symbol}`, `{sunrise_time}`, `{sunset_time}`, `{wind_speed}`, `{wind_unit}`, `{weather_desc}`.
    *   Forecast (N = day index, 0 for today, 1 for tomorrow, etc., up to ~6 days typically):
        *   `{temp_max_N}`, `{temp_min_N}`: Max/Min temperature for day N.
        *   `{weather_desc_N}`: Weather description for day N.
        *   `{dow_N}`: Day of the week for day N (e.g., "MON", "TUE").
    *   Example: `"{dow_1}: {temp_max_1}{unit_symbol} / {temp_min_1}{unit_symbol}"`
*   `update_interval_minutes`: Number, how often to fetch new weather data (e.g., 30). Caches data between fetches.
*   `font_size`: Select from available font sizes.

### Network Stats Widget (`network_stats_widget.py`)
Displays network information. Data is cached.
*   `stat_to_display`: Select "ssid" (network name), "ip" (IP address), or "uptime" (system uptime).
*   `os_override`: Select "auto-detect", "macos", "linux". (Windows support is placeholder).
*   `font_size`: Select from available font sizes.

### Network RSSI Widget (`network_rssi_widget.py`)
Displays Wi-Fi signal strength (RSSI).
*   Relies on `rssi` value being present in the `global_context` provided by `app.py` (currently specific to macOS `airport` command).
*   No specific configuration options beyond base settings (position, color, etc.). `font_size` is not explicitly listed in its `get_config_options` but might be added if desired.

### Text Widget (`text_widget.py`)
*   `text`: The static text string to display.
*   `font_size`: Not explicitly a config option, but text widget will use default font or could be extended to support font_size.

## Configuration

*   **Screen Layouts & Widget Settings**: All screen and widget configurations are managed through the `/config` web page. This includes widget type, position (X, Y), color, enabled state, font size (where applicable), and widget-specific settings like time formats or weather location.
*   **Data Persistence**: Changes made in the configuration UI are saved to `screen_layouts.json` when the "Save All Layouts" button is clicked.
*   **Global Settings**: `screen_layouts.json` also stores the global `matrix_data_logging_enabled` flag.

## Key API Endpoints

The Flask backend provides several API endpoints to support the frontend UI and display logic:

*   `/api/matrix_data`: (GET) Provides the pixel data for the current screen's rendered widgets, the current display mode ID, and widget dimensions. Used by the simulator.
*   `/api/get_screen_layouts`: (GET) Returns the entire `screen_layouts.json` content.
*   `/api/save_screen_layouts`: (POST) Receives a JSON object to overwrite `screen_layouts.json`.
*   `/api/get_widget_types`: (GET) Returns a list of available widget types and their `get_config_options()` definitions for the UI.
*   `/api/add_screen`: (POST) Adds a new screen configuration. Expects `{"screen_id": "...", "screen_name": "..."}`.
*   `/api/remove_screen/<string:screen_id_to_remove>`: (POST) Removes a screen configuration.
*   `/api/set_display_mode/<string:mode_name>`: (POST) Sets the active screen to be displayed.
*   `/api/get_matrix_logging_status`: (GET) Returns the current status of matrix data request logging.
*   `/api/set_matrix_logging_status`: (POST) Sets the status of matrix data request logging. Expects `{"enabled": true/false}`.

(This is not an exhaustive list but covers the main interactions.)

## Future Development & Best Practices (Review)

The project has evolved. Many of the initial "Future Development" points are now implemented or part of the core design.

*   **Font System**: The `display.py` now centrally manages multiple fonts (3x5, 5x7, 7x9, 9x13/XL) with expanding character sets.
*   **Widget Enhancements**: Many widgets now have font size options, and the weather widget is significantly more advanced.
*   **UI Improvements**: The `/config` page is more dynamic and user-friendly with expandable cards.

Remaining areas for improvement:
*   **Backend**: Consider Flask Blueprints for better route organization as complexity grows. Abstracting business logic into a service layer could be beneficial.
*   **Frontend**: Refactoring JavaScript into ES6 modules.
*   **Widget System**:
    *   **Live Preview in Config**: This remains a valuable future goal.
    *   **Widget Dimensions**: Currently, widgets are single lines of text. Allowing widgets to define their own width/height and render multi-line content within those bounds would be a major upgrade.
*   **Testing**: Introduce unit tests for backend logic and widget functionality.
*   **Hardware Integration**: Adapting `display.py` to drive a physical Raspberry Pi LED matrix (e.g., using `rpi-rgb-led-matrix`) is still a key long-term goal.

## Hardware Integration Target (Raspberry Pi)

The target hardware setup is a Raspberry Pi connected to a 64x64 RGB LED Matrix Panel via an Adafruit RGB Matrix Bonnet or similar interface.

*   **Library**: The [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) library by Henner Zeller is the primary target for driving the physical matrix.
*   **Transition Strategy**:
    1.  The core application logic in `app.py` (managing screens, widgets, data) will remain largely unchanged.
    2.  The `Display` class in `display.py` will be adapted. Its `set_pixel` method (or a new `update_physical_matrix` method) would call the `rpi-rgb-led-matrix` library functions to send the `pixel_buffer` to the physical LED matrix.
    3.  The web server component can remain for remote configuration, control, and simulation even when the hardware is active.
