# Smegtrix - LED Matrix Display Simulator & Controller

Smegtrix is a Python-based simulator and controller for a 64x64 LED matrix display. It features a Flask web backend, a dynamic HTML/CSS/JavaScript frontend for simulation and configuration, and a modular widget-based system for displaying various information.

## Core Features

*   **Web-Based Simulator**: Visualize the 64x64 LED matrix in your browser (`/`).
*   **Dynamic Configuration UI**: A dedicated web page (`/config`) to manage screens and widgets with features like:
    *   Screen creation, deletion, and naming.
    *   Widget addition, deletion, and reordering within screens.
    *   Drag & Drop for widget positioning (visualized on a grid, coordinates saved).
    *   Expandable/collapsible cards for each widget's settings.
    *   Clear display of Widget ID and Type on each configuration card.
    *   Support for various input types for widget-specific options (text, number, select, checkbox).
*   **Flask Backend**: Manages display logic, data, and configuration via API endpoints.
*   **Screen Management**:
    *   Create, configure, and switch between multiple virtual screens.
    *   Per-screen settings for display duration in the rotation sequence.
    *   Auto Screen Rotation: Screens can automatically cycle based on their configured display times.
*   **Modular Widget System**:
    *   Dynamically loaded widgets (time, date, text, weather, network info, etc.).
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
*   **Persistent Configuration**: Screen layouts and widget settings are saved in `screen_layouts.json`.
*   **Logging Control**: Toggle verbose logging for matrix data requests via the UI (`/config`).

## Tech Stack

*   **Backend**: Python, Flask
*   **Frontend**: HTML, CSS, JavaScript (vanilla)
*   **Data Storage**: JSON file (`screen_layouts.json`) for configurations.

## Project Structure

```
.Smegrix/
├── app.py                  # Main Flask application, API endpoints, display logic, widget loading, screen rotation
├── display.py              # Display class, font data (3x5, 5x7, 7x9, 9x13/XL), drawing utilities
├── screen_layouts.json     # Stores screen and widget configurations
├── widgets/                # Directory for widget modules
│   ├── base_widget.py      # Abstract BaseWidget class
│   ├── time_widget.py      # Displays current time, configurable format & font
│   ├── date_widget.py      # Displays current date, configurable format & font
│   ├── text_widget.py      # Displays static text
│   ├── weather_widget.py   # Displays weather forecast with advanced formatting
│   ├── network_ssid_widget.py # Displays network SSID (macOS specific)
│   ├── network_rssi_widget.py # Displays network RSSI (macOS specific)
│   └── ...                 # Other widget modules
├── static/                 # Static assets (CSS, JS - currently minimal)
│   └── style.css           # Basic styles (most styling is in HTML templates)
├── templates/
│   ├── index.html          # Main simulator page
│   └── config.html         # Configuration page for screens and widgets
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

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
    *   **Configuration**: Navigate to `http://127.0.0.1:5001/config`.

## Widget System Architecture

The widget system is designed to be modular and extensible.

*   **Widget Directory**: Widgets are defined as Python classes in separate files within the `widgets/` directory (e.g., `time_widget.py`, `weather_widget.py`).
*   **Base Class**: All widgets must inherit from `widgets.base_widget.BaseWidget`. This base class defines a common interface:
    *   `__init__(self, config, global_context)`: Initializes the widget with its specific configuration and a global context (e.g., current time via `global_context['now']`).
    *   `get_content(self) -> str`: Returns the string content the widget should display. For widgets using format strings, this method typically prepares data and then uses `string.format_map(data_dict)` for substitution.
    *   `get_config_options() -> list` (static method): Returns a list of dictionaries defining specific configuration options for the widget type (e.g., text fields, select dropdowns, number inputs, checkboxes). These are used to dynamically generate the configuration UI in `config.html`. The base implementation includes an `enable_logging` checkbox.
*   **Dynamic Loading**: At startup, `app.py` dynamically imports all `*_widget.py` modules from the `widgets/` directory and registers any class that subclasses `BaseWidget`.
*   **Configuration (`config.html`)**:
    *   The configuration page fetches available widget types and their specific options via the `/api/get_widget_types` endpoint.
    *   When a widget is added or configured, its specific options (e.g., `font_size`, `color`, `display_format`) are rendered dynamically.
*   **Rendering**: `app.py` instantiates the required widget classes for the active screen, passes them their configuration and global context, calls `get_content()`, and then uses `display.py` to draw the text using the widget's specified position, color, and font (if applicable and configured).

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

## Widget Configuration Placeholders

Several widgets utilize format strings with placeholders. Here are some common ones:

### Weather Widgetdd (`weather_widget.py`)
Uses `display_format` option. Example: `"{dow_1}: {temp_max_1}{unit_symbol} / {temp_min_1}{unit_symbol}"`
*   `{temp}`: Current temperature.
*   `{unit_symbol}`: 'C' or 'F'.
*   `{sunrise_time}`: Today's sunrise time (formatted by `time_display_format`).
*   `{sunset_time}`: Today's sunset time (formatted by `time_display_format`).
*   `{wind_speed}`: Current wind speed.
*   `{wind_unit}`: 'km/h' or 'mph'.
*   `{weather_desc}`: Current weather description (e.g., "Clear", "Partly Cloudy").
*   **Forecast Placeholders (N = day index, 0 for today, 1 for tomorrow, etc.):**
    *   `{temp_max_N}`: Max temperature for day N.
    *   `{temp_min_N}`: Min temperature for day N.
    *   `{weather_desc_N}`: Weather description for day N.
    *   `{dow_N}`: Day of the week for day N (e.g., "MON", "TUE").
*   Legacy (Day 0 only): `{temp_max}`, `{temp_min}`, `{daily_weather_desc}` are aliases for their `_0` counterparts.

### Time Widget (`time_widget.py`)
Uses `time_format` option, which accepts standard `strftime` codes.
*   Example: `"%H:%M:%S"` for "14:35:02"
*   Example: `"%I:%M %p"` for "02:35 PM"

### Date Widget (`date_widget.py`)
Uses `date_format_type` (select dropdown) or `custom_date_format` (text input for `strftime`).
*   Predefined `date_format_type` options map to `strftime` codes like `"%d/%m/%Y"`, `"%m/%d/%Y"`, etc.
*   If `custom_date_format` is provided, it overrides `date_format_type`. Example: `"%A, %b %d"` for "Monday, Jul 08".

## Configuration

*   **Screen Layouts & Widget Settings**: All screen and widget configurations are managed through the `/config` web page. This includes widget type, position (X, Y), color, enabled state, and widget-specific settings.
*   **Data Persistence**: Changes made in the configuration UI are saved to `screen_layouts.json`.
*   **Initial Configuration**: If `screen_layouts.json` is missing or invalid, it will be created with default screens.

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
