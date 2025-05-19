# Smegtrix - LED Matrix Display Simulator & Controller

Smegtrix is a Python-based simulator and controller for a 64x64 LED matrix display. It features a Flask web backend, a dynamic HTML/CSS/JavaScript frontend for simulation and configuration, and a modular widget-based system for displaying various information.

## Core Features

*   **Web-Based Simulator**: Visualize the 64x64 LED matrix in your browser.
*   **Flask Backend**: Manages display logic, data, and configuration via API endpoints.
*   **Screen Management**: Create, configure, and switch between multiple virtual screens.
*   **Modular Widget System**: Dynamically loaded widgets (time, date, text, network info, etc.) can be added, removed, and positioned on each screen. Each widget can have its own specific configuration options (e.g., font sizes, date/time formats, colors).
*   **Drag & Drop Configuration**: Easily arrange widgets on the simulator grid.
*   **Per-Screen Settings**: Customize display time for each screen.
*   **Auto Screen Rotation**: Screens can automatically cycle based on their configured display times.
*   **Dynamic Configuration UI**: A dedicated web page (`/config`) to manage screens and widgets.
*   **Persistent Configuration**: Screen layouts and widget settings are saved in `screen_layouts.json`.
*   **Multiple Font Sizes**: Some widgets (like the Time widget) support multiple font sizes (e.g., 3x5, 5x7, 7x9, 9x13).

## Tech Stack

*   **Backend**: Python, Flask
*   **Frontend**: HTML, CSS, JavaScript (vanilla)
*   **Data Storage**: JSON file (`screen_layouts.json`) for configurations.

## Project Structure

```
.Smegrix/
├── app.py                  # Main Flask application, API endpoints, display logic, widget loading
├── display.py              # Display class, font data (including 3x5, 5x7, 7x9, 9x13), drawing utilities
├── screen_layouts.json     # Stores screen and widget configurations
├── widgets/                # Directory for widget modules
│   ├── base_widget.py      # Abstract BaseWidget class
│   ├── time_widget.py      # Example: Time widget implementation
│   └── ...                 # Other widget modules (date_widget.py, text_widget.py, etc.)
├── static/                 # (Currently not used, but available for static assets)
│   └── style.css
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

*   **Widget Directory**: Widgets are defined as Python classes in separate files within the `widgets/` directory (e.g., `time_widget.py`, `text_widget.py`).
*   **Base Class**: All widgets must inherit from `widgets.base_widget.BaseWidget`. This base class defines a common interface:
    *   `__init__(self, config, global_context)`: Initializes the widget with its specific configuration and a global context (e.g., current time).
    *   `get_content(self) -> str`: Returns the string content the widget should display.
    *   `get_config_options() -> list` (static method): Returns a list of dictionaries defining specific configuration options for the widget type (e.g., text fields, select dropdowns, number inputs). These are used to dynamically generate the configuration UI in `config.html`.
*   **Dynamic Loading**: At startup, `app.py` dynamically imports all `*_widget.py` modules from the `widgets/` directory and registers any class that subclasses `BaseWidget`.
*   **Configuration (`config.html`)**: 
    *   The configuration page fetches available widget types and their specific options via the `/api/get_widget_types` endpoint.
    *   When a widget is added or configured, its specific options (e.g., `font_size` for `TimeWidget`, `date_format_type` for `DateWidget`, `color` for all widgets) are rendered dynamically.
*   **Rendering**: `app.py` instantiates the required widget classes for the active screen, passes them their configuration and global context, calls `get_content()`, and then uses `display.py` to draw the text using the widget's specified position, color, and font (if applicable).

### Creating a New Widget

1.  **Create a Python file** in the `widgets/` directory, e.g., `my_new_widget.py`.
2.  **Define a class** that inherits from `BaseWidget`:
    ```python
    from .base_widget import BaseWidget

    class MyNewWidget(BaseWidget):
        def __init__(self, config: dict, global_context: dict = None):
            super().__init__(config, global_context)
            # Your widget-specific initialization
            self.my_option = config.get('my_option', 'default_value')

        def get_content(self) -> str:
            # Logic to generate display string based on self.my_option and global_context
            return f"My Widget: {self.my_option}"

        @staticmethod
        def get_config_options() -> list:
            return [
                {
                    'name': 'my_option',
                    'label': 'My Custom Option',
                    'type': 'text', # or 'number', 'select', 'checkbox'
                    'default': 'default_value',
                    'placeholder': 'Enter something'
                }
                # Add more options as needed
            ]
    ```
3.  The application will automatically pick up the new widget type upon restart.
4.  The configuration UI (`/config`) will show "My New" (derived from class name) in the "Add New Widget" modal, and its custom options will be available when configuring an instance of it.

## Configuration

*   **Screen Layouts & Widget Settings**: All screen and widget configurations are managed through the `/config` web page. This includes widget type, position (X, Y), color, enabled state, and widget-specific settings (like font sizes or date formats).
*   **Data Persistence**: Changes made in the configuration UI are saved to `screen_layouts.json`.
*   **Initial Configuration**: If `screen_layouts.json` is missing or invalid, it will be created with default screens (Home, Network Info).

## Future Development & Best Practices

To ensure the project remains scalable and modular, consider the following guidelines:

### 1. Backend (Flask/Python - `app.py`, `display.py`)

*   **Blueprints for Routes**: As the number of API endpoints grows, organize them into Flask Blueprints.
*   **Service Layer**: Abstract business logic away from route handlers.
*   **Error Handling**: Implement robust error handling and logging.
*   **Configuration Management**: For settings beyond screen layouts, use a dedicated configuration file or environment variables.
*   **Asynchronous Operations**: For long-running tasks, consider asynchronous tasks.

### 2. Frontend (HTML/CSS/JavaScript - `templates/`)

*   **JavaScript Modules**: Refactor JavaScript into ES6 modules.
*   **Component-Based UI**: Think in terms of reusable UI components.
*   **CSS Organization**: Consider methodologies like BEM or a CSS preprocessor.
*   **API Client**: Create a dedicated JavaScript module for making API calls.

### 3. Widget System (Enhancements)

*   The current widget system is quite flexible. Future enhancements could include:
    *   **More Widget Types**: Weather, stocks, custom API data, etc.
    *   **Live Preview in Config**: Show a live preview of the widget directly in the configuration form as options are changed.
    *   **Advanced Styling**: More granular control over background colors, text alignment within a widget's bounds (if widgets can have their own dimensions).
    *   **Widget Dimensions**: Allow widgets to define their own width/height instead of just being single lines of text.

### 4. General Practices

*   **Modularity in `display.py`**: The `Display` class is a good abstraction. Ensure it remains focused on low-level pixel manipulation and font rendering. Its font capabilities have been expanded to include 3x5, 5x7, 7x9, and 9x13 sizes, with `FONT_5X7` now containing a full A-Z character set.
*   **Testing**: Introduce unit tests for backend logic and potentially integration tests for API endpoints.
*   **Code Style & Linting**: Use a consistent code style and linters.
*   **Documentation**: Keep this README updated. Add comments to complex code sections.
*   **Version Control**: Continue using Git effectively.

## Hardware Integration (Raspberry Pi)

The target hardware setup is a Raspberry Pi connected to a 64x64 RGB LED Matrix Panel via an Adafruit RGB Matrix Bonnet or similar interface.

*   **Library**: The [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) library by Henner Zeller is the primary target for driving the physical matrix.
*   **Transition Strategy**:
    1.  The core application logic in `app.py` (managing screens, widgets, data) will remain.
    2.  The `Display` class in `display.py` will be adapted. Its methods will be modified or extended to call the `rpi-rgb-led-matrix` library functions to send the pixel buffer to the physical LED matrix, in addition to maintaining the buffer for the web simulator.
    3.  The web server component can remain for remote configuration, control, and simulation even when the hardware is active.

By following these guidelines, Smegtrix can evolve into a more robust, feature-rich, and maintainable application.
