from abc import ABC, abstractmethod

class BaseWidget(ABC):
    """
    Abstract base class for all widgets.
    Defines the common interface for widgets.
    """
    DEFAULT_ENABLE_LOGGING = True # Default for all widgets

    def __init__(self, config: dict, global_context: dict = None):
        """
        Initialize the widget.

        Args:
            config (dict): The specific configuration for this widget instance 
                           (e.g., {'id': 'my_time', 'type': 'time', 'x': 10, 'y': 20, 'enabled': True, 'color': '#FF0000', ...}).
            global_context (dict, optional): A dictionary containing global data that widgets might need,
                                             such as current time, network information, etc.
                                             Example: {'now': datetime_object, 'ssid': 'MyNetwork', 'rssi': -50}
        """
        self.widget_id = config.get('id', 'unknown_widget')
        self.widget_type = config.get('type', 'unknown_type')
        self.x = config.get('x', 0)
        self.y = config.get('y', 0)
        self.enabled = config.get('enabled', True)
        self.color = config.get('color', '#FFFFFF') # Default to white hex string
        
        # Logging configuration
        self.enable_logging = config.get('enable_logging', self.DEFAULT_ENABLE_LOGGING)

        self.config = config # Store the full config for widget-specific use
        self.global_context = global_context if global_context is not None else {}

    def reconfigure(self):
        """
        Re-apply configuration to an existing widget instance.
        This is useful when the widget's config is updated after instantiation.
        """
        # Re-read common properties from self.config
        self.widget_id = self.config.get('id', self.widget_id if hasattr(self, 'widget_id') else 'unknown_widget')
        self.widget_type = self.config.get('type', self.widget_type if hasattr(self, 'widget_type') else 'unknown_type')
        self.x = self.config.get('x', self.x if hasattr(self, 'x') else 0)
        self.y = self.config.get('y', self.y if hasattr(self, 'y') else 0)
        self.enabled = self.config.get('enabled', self.enabled if hasattr(self, 'enabled') else True)
        self.color = self.config.get('color', self.color if hasattr(self, 'color') else '#FFFFFF')
        self.enable_logging = self.config.get('enable_logging', self.DEFAULT_ENABLE_LOGGING)
        # Note: self.config itself is assumed to be updated by the caller before calling reconfigure.
        # self.global_context is also updated by the caller.

    def _log(self, level: str, message: str):
        """Helper method for logging. Prints if self.enable_logging is True."""
        if self.enable_logging:
            print(f"[{self.__class__.__name__}-{self.widget_id}] {level.upper()}: {message}")

    @abstractmethod
    def get_content(self) -> str:
        """
        Generate the display content for the widget.
        This method must be implemented by all concrete widget classes.

        Returns:
            str: The text content to be displayed by the widget.
                 Return an empty string if the widget should not display anything
                 (e.g., if required data is unavailable).
        """
        pass

    @staticmethod
    def get_config_options() -> list:
        """
        Returns a list of specific configuration options for this widget type.
        Each option should be a dictionary describing the field, e.g.:
        [
            {'name': 'text_content', 'label': 'Display Text', 'type': 'text', 'default': 'Hello'},
            {'name': 'update_interval', 'label': 'Update Interval (s)', 'type': 'number', 'default': 60}
        ]
        This helps the config UI to dynamically generate input fields.
        Base implementation includes the enable_logging option.
        """
        return [
            {
                'name': 'enable_logging',
                'label': 'Enable Terminal Logging',
                'type': 'checkbox',
                'default': BaseWidget.DEFAULT_ENABLE_LOGGING
            }
        ]

    def __repr__(self):
        return f"{self.__class__.__name__}(id='{self.widget_id}', type='{self.widget_type}', color='{self.color}', enabled={self.enabled})" 