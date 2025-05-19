from .base_widget import BaseWidget

class NetworkSSIDWidget(BaseWidget):
    """Displays the current network SSID."""

    def get_content(self) -> str:
        """Returns the SSID from the global context."""
        return self.global_context.get('ssid', "N/A")

    # No specific config options beyond base (x, y, enabled, id, type)
    # So, it inherits the default get_config_options() which returns [] 