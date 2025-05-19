from .base_widget import BaseWidget

class TextWidget(BaseWidget):
    """Displays a static or configured block of text."""

    def __init__(self, config: dict, global_context: dict = None):
        super().__init__(config, global_context)
        # The 'text' for this widget is part of its instance configuration (self.config)
        self.display_text = self.config.get('text', '') 

    def get_content(self) -> str:
        """Returns the configured text."""
        return self.display_text

    @staticmethod
    def get_config_options() -> list:
        """
        Defines the specific configuration fields for the TextWidget.
        The 'text' field itself is already handled by the core config mechanism 
        if we ensure it's saved as part of the widget's instance data.
        However, explicitly defining it here makes it discoverable by the config UI.
        """
        return [
            {
                'name': 'text', # This key must match the key used in self.config.get('text', '')
                'label': 'Display Text',
                'type': 'text',
                'default': 'Hello!',
                'placeholder': 'Enter text to display'
            }
        ] 