import datetime
from .base_widget import BaseWidget

class DateWidget(BaseWidget):
    """Displays the current date."""

    # Map for predefined format types to strftime strings
    DATE_FORMAT_MAP = {
        "dd_mon": "%d %b",       # 12 JAN
        "dd_month": "%d %B",     # 12 JANUARY
        "dd_mm": "%d/%m",        # 12/01
        "dd_mm_yy": "%d/%m/%y",  # 12/01/24
        "dd_mm_yyyy": "%d/%m/%Y" # 12/01/2024
    }

    def __init__(self, config: dict, global_context: dict = None):
        super().__init__(config, global_context)
        # Store the chosen format type, defaulting to 'dd_mm' (12/01)
        self.date_format_type = self.config.get('date_format_type', "dd_mm") 
        self.font_size = self.config.get('font_size', "medium")

    def reconfigure(self):
        super().reconfigure() # Call base class reconfigure
        # Re-apply DateWidget specific configurations
        self.date_format_type = self.config.get('date_format_type', "dd_mm")
        self.font_size = self.config.get('font_size', "medium")

    def get_content(self) -> str:
        """Returns the current date formatted based on the selected type."""
        now = self.global_context.get('now')
        if not now or not isinstance(now, datetime.datetime):
            # Potentially use self._log here if we want to log missing 'now' in context
            return "--/--"
        
        # Get the actual strftime format string from our map
        format_string = self.DATE_FORMAT_MAP.get(self.date_format_type, self.DATE_FORMAT_MAP["dd_mm"])
        return now.strftime(format_string)

    @staticmethod
    def get_config_options() -> list:
        options = BaseWidget.get_config_options() # Get base options including 'enable_logging'
        options.extend([
            {
                'name': 'date_format_type',
                'label': 'Date Format',
                'type': 'select',
                'default': 'dd_mm',
                'options': [
                    {'value': 'dd_mon', 'label': 'DD MON (e.g., 12 Jan)'},
                    {'value': 'dd_month', 'label': 'DD MONTH (e.g., 12 January)'},
                    {'value': 'dd_mm', 'label': 'DD/MM (e.g., 12/01)'},
                    {'value': 'dd_mm_yy', 'label': 'DD/MM/YY (e.g., 12/01/24)'},
                    {'value': 'dd_mm_yyyy', 'label': 'DD/MM/YYYY (e.g., 12/01/2024)'}
                ]
            },
            {
                'name': 'font_size',
                'label': 'Font Size',
                'type': 'select',
                'default': 'medium',
                'options': [
                    {'value': 'small', 'label': 'Small (3x5)'},
                    {'value': 'medium', 'label': 'Medium (5x7)'},
                    {'value': 'large', 'label': 'Large (7x9)'},
                    {'value': 'xl', 'label': 'Extra Large (9x13)'}
                ]
            }
            # The old free-text 'date_format' can be removed or deprecated if desired
            # For now, let's remove it to avoid confusion.
        ]) 
        return options 