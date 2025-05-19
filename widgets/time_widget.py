import datetime
from .base_widget import BaseWidget
import ntplib # Using ntplib for NTP communication
import socket # For specific socket errors
import time # For time.monotonic()

class TimeWidget(BaseWidget):
    """Displays the current time, with optional NTP sync."""

    # Default resync interval if not specified or invalid in config
    DEFAULT_NTP_RESYNC_INTERVAL_HOURS = 4

    def __init__(self, config: dict, global_context: dict = None):
        super().__init__(config, global_context)
        # These are relatively static settings, can be set once if config object doesn't change
        # or re-evaluated if needed (as done for resync interval in get_content now)
        self.time_format = self.config.get('time_format', "%H:%M")
        self.font_size = self.config.get('font_size', "medium")
        self.enable_ntp = self.config.get('enable_ntp', False)
        self.ntp_server_address = self.config.get('ntp_server_address', 'pool.ntp.org')
        self.ntp_timeout = self.config.get('ntp_timeout', 5) 
        
        # NTP state attributes - these must persist across get_content calls for the same instance
        self.last_ntp_datetime_utc: datetime.datetime | None = None
        self.last_ntp_sync_monotonic_time: float | None = None
        
        # self.ntp_resync_interval_seconds is now calculated dynamically in get_content
        # to pick up config changes immediately.

    def _fetch_ntp_time(self, server_address: str) -> datetime.datetime | None:
        """Fetches time from an NTP server using ntplib and updates sync state."""
        client = ntplib.NTPClient()
        try:
            print(f"[TimeWidget-{self.widget_id}] INFO: Attempting NTP sync with '{server_address}' (timeout: {self.ntp_timeout}s).")
            response = client.request(server_address, version=3, timeout=self.ntp_timeout)
            # response.tx_time is the time the server transmitted the response (UTC)
            # To get local time, one would typically need timezone info. For now, we assume server's UTC is desired.
            # Or, if the system running this code has correct timezone settings, fromtimestamp will convert to local.
            # However, NTP itself is about UTC. If we want timezone-aware display, that's another layer.
            ntp_datetime_utc = datetime.datetime.fromtimestamp(response.tx_time, tz=datetime.timezone.utc)
            print(f"[TimeWidget-{self.widget_id}] INFO: NTP time received: {ntp_datetime_utc.isoformat()}")
            
            # Update last sync info
            self.last_ntp_datetime_utc = ntp_datetime_utc
            self.last_ntp_sync_monotonic_time = time.monotonic()
            
            return ntp_datetime_utc
        except ntplib.NTPException as e:
            print(f"[TimeWidget-{self.widget_id}] ERROR: NTPException from '{server_address}': {e}")
        except socket.gaierror as e: # Address-related error
            print(f"[TimeWidget-{self.widget_id}] ERROR: NTP server address error for '{server_address}': {e}")
        except socket.timeout as e:
            print(f"[TimeWidget-{self.widget_id}] ERROR: NTP request timed out for '{server_address}': {e}")
        except Exception as e: # Catch any other unexpected errors
            print(f"[TimeWidget-{self.widget_id}] ERROR: Unexpected error during NTP request to '{server_address}': {e}")
        return None # Fallback in case of any error

    def get_content(self) -> str:
        """Returns the current time formatted, potentially synced with NTP."""
        current_time_for_display: datetime.datetime | None = None
        system_now = self.global_context.get('now') # System time from context

        # Update these from config each time, in case they changed in the UI
        self.enable_ntp = self.config.get('enable_ntp', False)
        self.ntp_server_address = self.config.get('ntp_server_address', 'pool.ntp.org')
        self.ntp_timeout = self.config.get('ntp_timeout', 5)
        self.time_format = self.config.get('time_format', "%H:%M") # Also update time_format

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
                         print(f"[TimeWidget-{self.widget_id}] WARNING: ntp_resync_interval_hours ('{resync_hours_config}') must be positive. Defaulting to {self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS}h.")
            except ValueError:
                if str(resync_hours_config) != str(self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS):
                    print(f"[TimeWidget-{self.widget_id}] WARNING: Invalid ntp_resync_interval_hours ('{resync_hours_config}'). Defaulting to {self.DEFAULT_NTP_RESYNC_INTERVAL_HOURS}h.")

            needs_resync = False
            if self.last_ntp_sync_monotonic_time is None:
                needs_resync = True
                print(f"[TimeWidget-{self.widget_id}] INFO: First NTP sync attempt for this instance (or after config change).")
            elif (time.monotonic() - self.last_ntp_sync_monotonic_time) > current_ntp_resync_interval_seconds:
                needs_resync = True
                print(f"[TimeWidget-{self.widget_id}] INFO: NTP resync interval ({current_ntp_resync_interval_seconds / 3600}h) reached. Attempting sync.")

            if needs_resync:
                fetched_ntp_utc = self._fetch_ntp_time(self.ntp_server_address)
                if fetched_ntp_utc:
                    # Successfully synced, use this new time
                    current_time_for_display = fetched_ntp_utc.astimezone()
                elif self.last_ntp_datetime_utc is not None and self.last_ntp_sync_monotonic_time is not None:
                    # Sync failed, but we have a previous sync. Use that and calculate forward.
                    print(f"[TimeWidget-{self.widget_id}] WARNING: NTP sync failed. Using last known NTP time and incrementing locally.")
                    elapsed_seconds = time.monotonic() - self.last_ntp_sync_monotonic_time
                    calculated_utc = self.last_ntp_datetime_utc + datetime.timedelta(seconds=elapsed_seconds)
                    current_time_for_display = calculated_utc.astimezone()
                else:
                    # Sync failed and no previous sync data. Fallback to system time.
                    print(f"[TimeWidget-{self.widget_id}] WARNING: NTP sync failed and no previous sync data. Falling back to system time.")
                    current_time_for_display = system_now
            elif self.last_ntp_datetime_utc is not None and self.last_ntp_sync_monotonic_time is not None:
                # Not time to resync, use last NTP time and increment locally
                elapsed_seconds = time.monotonic() - self.last_ntp_sync_monotonic_time
                calculated_utc = self.last_ntp_datetime_utc + datetime.timedelta(seconds=elapsed_seconds)
                current_time_for_display = calculated_utc.astimezone()
                # print(f"[TimeWidget-{self.widget_id}] DEBUG: Using locally incremented NTP time: {current_time_for_display.isoformat()}") # Optional: for debugging
            else:
                 # Should not happen if logic is correct (enable_ntp is true but no sync info and not needing resync)
                 # This case implies last_ntp_datetime_utc or last_ntp_sync_monotonic_time is None,
                 # which should have triggered needs_resync. But as a safeguard:
                print(f"[TimeWidget-{self.widget_id}] WARNING: NTP enabled but in an unexpected state. Falling back to system time.")
                current_time_for_display = system_now
        else:
            current_time_for_display = system_now

        if not current_time_for_display or not isinstance(current_time_for_display, datetime.datetime):
            return "--:--" 
        return current_time_for_display.strftime(self.time_format)

    @staticmethod
    def get_config_options() -> list:
        """Returns specific configuration options for the Time widget."""
        options = BaseWidget.get_config_options()
        options.extend([
            {
                'name': 'time_format',
                'label': 'Time Format',
                'type': 'text',
                'default': '%H:%M',
                'placeholder': 'E.g., %H:%M:%S or %I:%M %p'
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
                    {'value': 'xl', 'label': 'XL (9x13)'}
                ]
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