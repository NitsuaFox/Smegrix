import datetime
import math # Added for analog clock calculations
from .base_widget import BaseWidget
import ntplib # Using ntplib for NTP communication
import socket # For specific socket errors
import time # For time.monotonic()

class TimeWidget(BaseWidget):
    """Displays the current time, with optional NTP sync."""

    # Default resync interval if not specified or invalid in config
    DEFAULT_NTP_RESYNC_INTERVAL_HOURS = 4
    DEFAULT_DISPLAY_MODE = "digital"
    DEFAULT_ANALOG_CLOCK_SIZE = "24x24"
    DEFAULT_ANALOG_HANDS_COLOR = "#FFFFFF" # White

    def __init__(self, config: dict, global_context: dict = None):
        super().__init__(config, global_context)
        # These are relatively static settings, can be set once if config object doesn't change
        # or re-evaluated if needed (as done for resync interval in get_content now)
        self.time_format = self.config.get('time_format', "%H:%M")
        self.font_size = self.config.get('font_size', "medium")
        self.display_mode = self.config.get('display_mode', self.DEFAULT_DISPLAY_MODE)
        self.analog_clock_size_str = self.config.get('analog_clock_size', self.DEFAULT_ANALOG_CLOCK_SIZE)
        self.analog_hands_color_hex = self.config.get('analog_hands_color', self.DEFAULT_ANALOG_HANDS_COLOR)
        
        self.analog_width, self.analog_height = self._parse_analog_size(self.analog_clock_size_str)
        self.analog_hands_rgb = self._hex_to_rgb(self.analog_hands_color_hex)

        self.enable_ntp = self.config.get('enable_ntp', False)
        self.ntp_server_address = self.config.get('ntp_server_address', 'pool.ntp.org')
        self.ntp_timeout = self.config.get('ntp_timeout', 5) 
        
        # NTP state attributes - these must persist across get_content calls for the same instance
        self.last_ntp_datetime_utc: datetime.datetime | None = None
        self.last_ntp_sync_monotonic_time: float | None = None
        
        self._log("INFO", f"TimeWidget initialized with display_mode: {self.display_mode}, analog_size: {self.analog_width}x{self.analog_height}, hands_color: {self.analog_hands_rgb}, font_size: {self.font_size}, NTP: {self.enable_ntp}")

    def _parse_analog_size(self, size_str: str) -> tuple[int, int]:
        try:
            parts = size_str.lower().split('x')
            if len(parts) == 2:
                w, h = int(parts[0]), int(parts[1])
                if w > 0 and h > 0:
                    return w, h
        except ValueError:
            pass
        self._log("WARNING", f"Invalid analog_clock_size '{size_str}'. Defaulting to 24x24.")
        return 24, 24 # Default size

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        try:
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            elif len(hex_color) == 3: # Shorthand e.g. #RGB
                return tuple(int(hex_color[i:i+1]*2, 16) for i in (0, 1, 2))
        except ValueError:
            pass
        self._log("WARNING", f"Invalid analog_hands_color '{hex_color}'. Defaulting to white (#FFFFFF).")
        return (255, 255, 255)

    def _draw_line_bresenham(self, pixel_map, x0, y0, x1, y1, color_rgb):
        """Draws a line from (x0,y0) to (x1,y1) on pixel_map using Bresenham's algorithm."""
        # Ensure coordinates are integers
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy  # error value e_xy

        map_height = len(pixel_map)
        map_width = len(pixel_map[0]) if map_height > 0 else 0

        while True:
            if 0 <= y0 < map_height and 0 <= x0 < map_width:
                pixel_map[y0][x0] = color_rgb
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:  # e_xy+e_x > 0
                err += dy
                x0 += sx
            if e2 <= dx:  # e_xy+e_y < 0
                err += dx
                y0 += sy

    def _fetch_ntp_time(self, server_address: str) -> datetime.datetime | None:
        """Fetches time from an NTP server using ntplib and updates sync state."""
        client = ntplib.NTPClient()
        try:
            # print(f"[TimeWidget-{self.widget_id}] INFO: Attempting NTP sync with '{server_address}' (timeout: {self.ntp_timeout}s).")
            self._log("INFO", f"Attempting NTP sync with '{server_address}' (timeout: {self.ntp_timeout}s).")
            response = client.request(server_address, version=3, timeout=self.ntp_timeout)
            ntp_datetime_utc = datetime.datetime.fromtimestamp(response.tx_time, tz=datetime.timezone.utc)
            # print(f"[TimeWidget-{self.widget_id}] INFO: NTP time received: {ntp_datetime_utc.isoformat()}")
            self._log("INFO", f"NTP time received: {ntp_datetime_utc.isoformat()}")
            
            self.last_ntp_datetime_utc = ntp_datetime_utc
            self.last_ntp_sync_monotonic_time = time.monotonic()
            
            return ntp_datetime_utc
        except ntplib.NTPException as e:
            # print(f"[TimeWidget-{self.widget_id}] ERROR: NTPException from '{server_address}': {e}")
            self._log("ERROR", f"NTPException from '{server_address}': {e}")
        except socket.gaierror as e: # Address-related error
            # print(f"[TimeWidget-{self.widget_id}] ERROR: NTP server address error for '{server_address}': {e}")
            self._log("ERROR", f"NTP server address error for '{server_address}': {e}")
        except socket.timeout as e:
            # print(f"[TimeWidget-{self.widget_id}] ERROR: NTP request timed out for '{server_address}': {e}")
            self._log("ERROR", f"NTP request timed out for '{server_address}': {e}")
        except Exception as e: # Catch any other unexpected errors
            # print(f"[TimeWidget-{self.widget_id}] ERROR: Unexpected error during NTP request to '{server_address}': {e}")
            self._log("ERROR", f"Unexpected error during NTP request to '{server_address}': {e}")
        return None

    def get_content(self) -> str:
        """Returns the current time, either formatted string for digital or pixel_map for analog."""
        current_time_for_display: datetime.datetime | None = None
        system_now = self.global_context.get('now') # System time from context

        # Update these from config each time, in case they changed in the UI
        self.enable_ntp = self.config.get('enable_ntp', False)
        self.ntp_server_address = self.config.get('ntp_server_address', 'pool.ntp.org')
        self.ntp_timeout = self.config.get('ntp_timeout', 5)
        self.time_format = self.config.get('time_format', "%H:%M") # Also update time_format
        self.display_mode = self.config.get('display_mode', self.DEFAULT_DISPLAY_MODE) # Update display_mode

        # Re-evaluate analog clock properties if config changed
        new_analog_size_str = self.config.get('analog_clock_size', self.DEFAULT_ANALOG_CLOCK_SIZE)
        if new_analog_size_str != self.analog_clock_size_str:
            self.analog_clock_size_str = new_analog_size_str
            self.analog_width, self.analog_height = self._parse_analog_size(self.analog_clock_size_str)
            self._log("INFO", f"TimeWidget analog clock size reconfigured to: {self.analog_width}x{self.analog_height}")

        new_analog_hands_color_hex = self.config.get('analog_hands_color', self.DEFAULT_ANALOG_HANDS_COLOR)
        if new_analog_hands_color_hex != self.analog_hands_color_hex:
            self.analog_hands_color_hex = new_analog_hands_color_hex
            self.analog_hands_rgb = self._hex_to_rgb(self.analog_hands_color_hex)
            self._log("INFO", f"TimeWidget analog hands color reconfigured to: {self.analog_hands_rgb}")

        if self.enable_ntp and self.ntp_server_address:
            # Dynamically calculate ntp_resync_interval_seconds from current config
            resync_hours_config = self.config.get('ntp_resync_interval_hours', self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS)
            current_ntp_resync_interval_seconds = self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS * 3600 # Default
            try:
                resync_hours_val = float(resync_hours_config)
                if resync_hours_val > 0:
                    current_ntp_resync_interval_seconds = resync_hours_val * 3600
                else:
                    # Log if it was an invalid value from config, but still use default
                    if str(resync_hours_config) != str(self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS):
                         # print(f"[TimeWidget-{self.widget_id}] WARNING: ntp_resync_interval_hours ('{resync_hours_config}') must be positive. Defaulting to {self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS}h.")
                         self._log("WARNING", f"ntp_resync_interval_hours ('{resync_hours_config}') must be positive. Defaulting to {self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS}h.")
            except ValueError:
                if str(resync_hours_config) != str(self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS):
                    # print(f"[TimeWidget-{self.widget_id}] WARNING: Invalid ntp_resync_interval_hours ('{resync_hours_config}'). Defaulting to {self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS}h.")
                    self._log("WARNING", f"Invalid ntp_resync_interval_hours ('{resync_hours_config}'). Defaulting to {self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS}h.")

            needs_resync = False
            if self.last_ntp_sync_monotonic_time is None:
                needs_resync = True
                # print(f"[TimeWidget-{self.widget_id}] INFO: First NTP sync attempt for this instance (or after config change).")
                self._log("INFO", "First NTP sync attempt for this instance (or after config change).")
            elif (time.monotonic() - self.last_ntp_sync_monotonic_time) > current_ntp_resync_interval_seconds:
                needs_resync = True
                # print(f"[TimeWidget-{self.widget_id}] INFO: NTP resync interval ({current_ntp_resync_interval_seconds / 3600}h) reached. Attempting sync.")
                self._log("INFO", f"NTP resync interval ({current_ntp_resync_interval_seconds / 3600}h) reached. Attempting sync.")

            if needs_resync:
                fetched_ntp_utc = self._fetch_ntp_time(self.ntp_server_address)
                if fetched_ntp_utc:
                    current_time_for_display = fetched_ntp_utc.astimezone()
                elif self.last_ntp_datetime_utc is not None and self.last_ntp_sync_monotonic_time is not None:
                    # print(f"[TimeWidget-{self.widget_id}] WARNING: NTP sync failed. Using last known NTP time and incrementing locally.")
                    self._log("WARNING", "NTP sync failed. Using last known NTP time and incrementing locally.")
                    elapsed_seconds = time.monotonic() - self.last_ntp_sync_monotonic_time
                    calculated_utc = self.last_ntp_datetime_utc + datetime.timedelta(seconds=elapsed_seconds)
                    current_time_for_display = calculated_utc.astimezone()
                else:
                    # print(f"[TimeWidget-{self.widget_id}] WARNING: NTP sync failed and no previous sync data. Falling back to system time.")
                    self._log("WARNING", "NTP sync failed and no previous sync data. Falling back to system time.")
                    current_time_for_display = system_now
            elif self.last_ntp_datetime_utc is not None and self.last_ntp_sync_monotonic_time is not None:
                elapsed_seconds = time.monotonic() - self.last_ntp_sync_monotonic_time
                calculated_utc = self.last_ntp_datetime_utc + datetime.timedelta(seconds=elapsed_seconds)
                current_time_for_display = calculated_utc.astimezone()
                # self._log("DEBUG", f"Using locally incremented NTP time: {current_time_for_display.isoformat()}") # Optional: for debugging
            else:
                # print(f"[TimeWidget-{self.widget_id}] WARNING: NTP enabled but in an unexpected state. Falling back to system time.")
                self._log("WARNING", "NTP enabled but in an unexpected state. Falling back to system time.")
                current_time_for_display = system_now
        else:
            current_time_for_display = system_now

        if not current_time_for_display or not isinstance(current_time_for_display, datetime.datetime):
            if self.display_mode == "analog":
                # Return an empty pixel map of the configured size on error
                return {
                    'type': 'pixel_map',
                    'width': self.analog_width,
                    'height': self.analog_height,
                    'data': [[(0,0,0)] * self.analog_width for _ in range(self.analog_height)] # All black
                }
            return "--:--" 
        
        if self.display_mode == "analog":
            self._log("DEBUG", f"Analog mode: rendering {self.analog_width}x{self.analog_height} clock for {current_time_for_display.strftime('%H:%M:%S')}")
            
            pixel_map = [[(0,0,0)] * self.analog_width for _ in range(self.analog_height)] # Black background
            
            center_x = self.analog_width / 2.0 # Use float for center for more accurate calcs
            center_y = self.analog_height / 2.0
            radius = min(center_x, center_y) * 0.85 # Radius for hands, with some padding
            
            hours = current_time_for_display.hour
            minutes = current_time_for_display.minute
            seconds = current_time_for_display.second

            # Calculate hand angles (0 degrees is 12 o'clock/up)
            # Hour hand: 360 degrees in 12 hours = 30 degrees per hour. Plus minute influence.
            hour_angle_rad = math.radians((hours % 12 + minutes / 60) * 30 - 90)
            # Minute hand: 360 degrees in 60 minutes = 6 degrees per minute.
            minute_angle_rad = math.radians(minutes * 6 - 90)
            # Second hand: 360 degrees in 60 seconds = 6 degrees per second.
            second_angle_rad = math.radians(seconds * 6 - 90)

            hands_rgb = self.analog_hands_rgb
            second_hand_color = (hands_rgb[0]//2, hands_rgb[1]//2, hands_rgb[2]//2) # Dimmer seconds
            hour_marker_color = (hands_rgb[0]//3, hands_rgb[1]//3, hands_rgb[2]//3) # Even dimmer for markers

            # Draw Hour Markers
            for i in range(12):
                angle_rad = math.radians(i * 30 - 90) # 30 degrees per hour, offset by -90 to start at 12
                outer_x = center_x + radius * math.cos(angle_rad)
                outer_y = center_y + radius * math.sin(angle_rad)
                inner_x = center_x + (radius * 0.85) * math.cos(angle_rad) # Markers are 15% of radius length
                inner_y = center_y + (radius * 0.85) * math.sin(angle_rad)
                self._draw_line_bresenham(pixel_map, inner_x, inner_y, outer_x, outer_y, hour_marker_color)

            # Hour Hand (shorter)
            hour_len = radius * 0.5
            h_x1 = center_x + hour_len * math.cos(hour_angle_rad)
            h_y1 = center_y + hour_len * math.sin(hour_angle_rad)
            self._draw_line_bresenham(pixel_map, center_x, center_y, h_x1, h_y1, hands_rgb)
            
            # Minute Hand (longer)
            minute_len = radius * 0.75
            m_x1 = center_x + minute_len * math.cos(minute_angle_rad)
            m_y1 = center_y + minute_len * math.sin(minute_angle_rad)
            self._draw_line_bresenham(pixel_map, center_x, center_y, m_x1, m_y1, hands_rgb)

            # Second Hand (longest, thinnest - or different color)
            second_len = radius * 0.8
            s_x1 = center_x + second_len * math.cos(second_angle_rad)
            s_y1 = center_y + second_len * math.sin(second_angle_rad)
            self._draw_line_bresenham(pixel_map, center_x, center_y, s_x1, s_y1, second_hand_color)
            
            # Optional: Draw a small circle at the center
            if 0 <= int(center_y) < self.analog_height and 0 <= int(center_x) < self.analog_width:
                pixel_map[int(center_y)][int(center_x)] = (50,50,50) # Grey center dot
            if 0 <= int(center_y) < self.analog_height and 0 <= int(center_x)+1 < self.analog_width:
                 pixel_map[int(center_y)][int(center_x)+1] = (50,50,50)
            if 0 <= int(center_y)+1 < self.analog_height and 0 <= int(center_x) < self.analog_width:
                 pixel_map[int(center_y)+1][int(center_x)] = (50,50,50)
            if 0 <= int(center_y)+1 < self.analog_height and 0 <= int(center_x)+1 < self.analog_width:
                 pixel_map[int(center_y)+1][int(center_x)+1] = (50,50,50)

            return {
                'type': 'pixel_map',
                'width': self.analog_width,
                'height': self.analog_height,
                'data': pixel_map
            }
            
        return current_time_for_display.strftime(self.time_format)

    @staticmethod
    def get_config_options() -> list:
        """Returns specific configuration options for the Time widget."""
        options = BaseWidget.get_config_options() # Get base options including 'enable_logging'
        options.extend([
            {
                'name': 'display_mode',
                'label': 'Display Mode',
                'type': 'select',
                'default': TimeWidget.DEFAULT_DISPLAY_MODE,
                'options': [
                    {'value': 'digital', 'label': 'Digital'},
                    {'value': 'analog', 'label': 'Analog'}
                ],
                'description': 'Choose between digital text display or an analog clock face.'
            },
            {
                'name': 'time_format',
                'label': 'Time Format (Digital)',
                'type': 'text',
                'default': '%H:%M',
                'placeholder': 'E.g., %H:%M:%S or %I:%M %p',
                'condition': {'field': 'display_mode', 'value': 'digital', 'action': 'show'}
            },
            {
                'name': 'font_size',
                'label': 'Font Size (Digital)',
                'type': 'select',
                'default': 'medium',
                'options': [
                    {'value': 'small', 'label': 'Small (3x5)'},
                    {'value': 'medium', 'label': 'Medium (5x7)'},
                    {'value': 'large', 'label': 'Large (7x9)'},
                    {'value': 'xl', 'label': 'XL (9x13)'}
                ],
                'condition': {'field': 'display_mode', 'value': 'digital', 'action': 'show'}
            },
            {
                'name': 'analog_clock_size',
                'label': 'Analog Clock Size (WxH)',
                'type': 'select',
                'default': TimeWidget.DEFAULT_ANALOG_CLOCK_SIZE,
                'options': [
                    {'value': '16x16', 'label': '16x16 pixels'},
                    {'value': '24x24', 'label': '24x24 pixels'},
                    {'value': '32x32', 'label': '32x32 pixels'},
                    {'value': '48x48', 'label': '48x48 pixels'},
                    # {'value': '64x64', 'label': '64x64 pixels'} # Max size is full matrix, might be too big for a widget
                ],
                'description': 'Size of the dedicated drawing area for the analog clock.',
                'condition': {'field': 'display_mode', 'value': 'analog', 'action': 'show'}
            },
            {
                'name': 'analog_hands_color',
                'label': 'Analog Hands Color',
                'type': 'color',
                'default': TimeWidget.DEFAULT_ANALOG_HANDS_COLOR,
                'placeholder': '#RRGGBB',
                'condition': {'field': 'display_mode', 'value': 'analog', 'action': 'show'}
            },
            {
                'name': 'enable_ntp',
                'label': 'Enable NTP Sync',
                'type': 'checkbox',
                'default': False
            },
            {
                'name': 'ntp_server_address',
                'label': 'NTP Server Address',
                'type': 'text',
                'default': 'pool.ntp.org',
                'placeholder': 'E.g., pool.ntp.org'
            },
            {
                'name': 'ntp_timeout',
                'label': 'NTP Timeout (sec)',
                'type': 'number',
                'default': 5,
                'placeholder': 'E.g., 5'
            },
            {
                'name': 'ntp_resync_interval_hours',
                'label': 'NTP Resync Interval (hours)',
                'type': 'number',
                'default': TimeWidget.DEFAULT_NTP_RESYNC_INTERVAL_HOURS, # Use class const for default
                'placeholder': 'E.g., 4'
            }
        ])
        return options 