from .base_widget import BaseWidget

class NetworkRSSIWidget(BaseWidget):
    """Displays the current network RSSI (signal strength)."""

    def get_content(self) -> str:
        """Returns the RSSI from the global context."""
        return str(self.global_context.get('rssi', "N/A")) # Ensure it's a string

    # No specific config options beyond base 