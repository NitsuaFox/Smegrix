import datetime
import requests
from .base_widget import BaseWidget
import time # Added for caching
import re # For parsing display_format
import threading # Added for background fetching

# WMO Weather interpretation codes (simplified)
# Source: Open-Meteo documentation
WMO_WEATHER_CODES = {
    0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing Rime Fog",
    51: "Light Drizzle", 53: "Mod Drizzle", 55: "Dense Drizzle",
    56: "Light Freezing Drizzle", 57: "Dense Freezing Drizzle",
    61: "Slight Rain", 63: "Mod Rain", 65: "Heavy Rain",
    66: "Light Freezing Rain", 67: "Heavy Freezing Rain",
    71: "Slight Snowfall", 73: "Mod Snowfall", 75: "Heavy Snowfall",
    77: "Snow Grains",
    80: "Slight Rain Showers", 81: "Mod Rain Showers", 82: "Violent Rain Showers",
    85: "Slight Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", # Slight or moderate
    96: "Thunderstorm w/ Slight Hail", 99: "Thunderstorm w/ Heavy Hail",
}

class WeatherWidget(BaseWidget):
    """Displays weather information from Open-Meteo using a user-defined format string."""

    # Open-Meteo API endpoint
    API_BASE_URL = "https://api.open-meteo.com/v1/forecast" 

    # Hardcoded coordinates for Billingham, UK for this version
    # A future improvement would be to use geocoding for the location string
    DEFAULT_LATITUDE = 54.61 
    DEFAULT_LONGITUDE = -1.29
    DEFAULT_UPDATE_INTERVAL_MINUTES = 30

    def __init__(self, config: dict, global_context: dict = None):
        super().__init__(config, global_context)
        # self.api_key = self.config.get('api_key', '') # No longer needed for Open-Meteo basic use
        self.location_name = self.config.get('location_name', 'Billingham,UK') # Kept for display/config purposes
        self.units = self.config.get('units', 'metric') # metric for Celsius, imperial for Fahrenheit
        
        # For now, we use hardcoded lat/lon. User can override via config if we add lat/lon fields.
        self.latitude = self.config.get('latitude', self.DEFAULT_LATITUDE)
        self.longitude = self.config.get('longitude', self.DEFAULT_LONGITUDE)
        self.time_display_format = self.config.get('time_display_format', '%H:%M') # For sunrise/sunset
        # New: User-defined format string for the display
        self.display_format = self.config.get('display_format', 'Temp: {temp}{unit_symbol}')
        self.font_size = self.config.get('font_size', "medium") # Add font_size
        
        # Caching attributes
        self.update_interval_minutes = self.config.get('update_interval_minutes', self.DEFAULT_UPDATE_INTERVAL_MINUTES)
        self.last_weather_data = None
        self.last_fetch_time = 0 # Use 0 to ensure first fetch always happens
        self.is_fetching = False # Flag to indicate if a fetch is in progress
        self.fetch_thread = None # Holds the reference to the fetch thread
        self.data_lock = threading.Lock() # Lock for accessing shared data like last_weather_data
        # Ensure super().__init__ is called if not already, for enable_logging
        # It's called at the top of __init__ in this class, so self.enable_logging and self._log are available

    def reconfigure(self):
        super().reconfigure() # Call base class reconfigure
        # Re-apply WeatherWidget specific configurations
        with self.data_lock: # Ensure thread safety when reconfiguring
            self.location_name = self.config.get('location_name', 'Billingham,UK')
            self.units = self.config.get('units', 'metric')
            self.latitude = self.config.get('latitude', self.DEFAULT_LATITUDE)
            self.longitude = self.config.get('longitude', self.DEFAULT_LONGITUDE)
            self.time_display_format = self.config.get('time_display_format', '%H:%M')
            self.display_format = self.config.get('display_format', 'Temp: {temp}{unit_symbol}')
            self.font_size = self.config.get('font_size', "medium")
            self.update_interval_minutes = self.config.get('update_interval_minutes', self.DEFAULT_UPDATE_INTERVAL_MINUTES)
            # Don't reset cache on reconfigure, let get_content handle it.
            # If location or units change, next fetch will get new data.

    def _parse_weather_data(self, weather_data_json: dict) -> dict:
        """Helper to parse the JSON response from Open-Meteo into a flat dictionary."""
        available_data = {
            'temp': 'N/A',
            'unit_symbol': 'C' if self.units == 'metric' else 'F',
            'sunrise_time': 'N/A',
            'sunset_time': 'N/A',
            'wind_speed': 'N/A',
            'wind_unit': 'km/h' if self.units == 'metric' else 'mph',
            'weather_desc': 'N/A', # Current weather description
            'temp_max': 'N/A', # Today's max, will also be temp_max_0
            'temp_min': 'N/A', # Today's min, will also be temp_min_0
            'daily_weather_desc': 'N/A' # Today's weather, will also be weather_desc_0
            # Numbered forecast keys like temp_max_0, temp_min_1, dow_1 etc., will be added dynamically below
        }
        # Determine wind unit based on query parameters, not just self.units for display
        # This part relies on how wind_speed_unit_param was set during the API call.
        # For simplicity, this example assumes wind_speed_unit_param was 'kmh' for metric and 'mph' for imperial.
        # If 'ms' was requested for metric, this 'wind_unit' would need adjustment.
        # Let's ensure this reflects the typical Open-Meteo response based on 'kmh'/'mph' request.

        current_weather = weather_data_json.get('current_weather')
        if current_weather:
            if 'temperature' in current_weather:
                available_data['temp'] = f"{current_weather['temperature']:.0f}"
            if 'windspeed' in current_weather:
                available_data['wind_speed'] = f"{current_weather['windspeed']:.0f}"
            if 'weathercode' in current_weather:
                code = current_weather['weathercode']
                available_data['weather_desc'] = WMO_WEATHER_CODES.get(code, "Unknown")

        daily_data = weather_data_json.get('daily')
        if daily_data:
            # Determine how many days of data we actually have in the response for daily fields
            num_days_in_response = 0
            if daily_data.get('time') and isinstance(daily_data['time'], list):
                num_days_in_response = len(daily_data['time'])
            elif daily_data.get('temperature_2m_max') and isinstance(daily_data['temperature_2m_max'], list):
                 # Fallback if 'time' is not present but other daily arrays are
                num_days_in_response = len(daily_data['temperature_2m_max'])

            # Populate sunrise and sunset (usually only for day 0 from this API structure)
            if daily_data.get('sunrise') and len(daily_data['sunrise']) > 0:
                try: 
                    dt_obj = datetime.datetime.fromisoformat(daily_data['sunrise'][0])
                    available_data['sunrise_time'] = dt_obj.strftime(self.time_display_format)
                except ValueError: self._log("WARNING", "Could not parse sunrise time.")
            
            if daily_data.get('sunset') and len(daily_data['sunset']) > 0:
                try: 
                    dt_obj = datetime.datetime.fromisoformat(daily_data['sunset'][0])
                    available_data['sunset_time'] = dt_obj.strftime(self.time_display_format)
                except ValueError: self._log("WARNING", "Could not parse sunset time.")

            # Get today's date to calculate future dates for Day of Week
            # Use global_context if available and valid, otherwise fallback to datetime.date.today()
            today_date = None
            gc_now = self.global_context.get('now')
            if gc_now and isinstance(gc_now, datetime.datetime):
                today_date = gc_now.date()
            else:
                today_date = datetime.date.today()
                self._log("DEBUG", "Global context 'now' not available or invalid for DOW calculation, using system date.")

            # Populate data for each day (0 to N-1)
            for day_index in range(num_days_in_response):
                # Calculate date for the current forecast day_index
                current_forecast_date = today_date + datetime.timedelta(days=day_index)
                available_data[f'dow_{day_index}'] = current_forecast_date.strftime("%a").upper()

                if daily_data.get('temperature_2m_max') and len(daily_data['temperature_2m_max']) > day_index:
                    available_data[f'temp_max_{day_index}'] = f"{daily_data['temperature_2m_max'][day_index]:.0f}"
                if daily_data.get('temperature_2m_min') and len(daily_data['temperature_2m_min']) > day_index:
                    available_data[f'temp_min_{day_index}'] = f"{daily_data['temperature_2m_min'][day_index]:.0f}"
                if daily_data.get('weathercode') and len(daily_data['weathercode']) > day_index:
                    code = daily_data['weathercode'][day_index]
                    available_data[f'weather_desc_{day_index}'] = WMO_WEATHER_CODES.get(code, "Unknown")

            # For convenience and backward compatibility, map day 0 data to older keys too
            if 'temp_max_0' in available_data: available_data['temp_max'] = available_data['temp_max_0']
            if 'temp_min_0' in available_data: available_data['temp_min'] = available_data['temp_min_0']
            if 'weather_desc_0' in available_data: available_data['daily_weather_desc'] = available_data['weather_desc_0']
        
        return available_data

    def _fetch_data_background(self):
        """Fetches weather data in a background thread."""
        temp_unit_param = 'celsius' if self.units == 'metric' else 'fahrenheit'
        wind_speed_unit_param = 'kmh' if self.units == 'metric' else 'mph'
        max_days_needed = 0
        if self.display_format:
            matches = re.findall(r'\{(?:temp_max|temp_min|weather_desc|dow)_(\d+)\}', self.display_format)
            if matches:
                max_days_needed = max(int(m) for m in matches)
        api_forecast_days = max_days_needed + 1
        params = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'current_weather': 'true',
            'daily': 'sunrise,sunset,temperature_2m_max,temperature_2m_min,weathercode',
            'temperature_unit': temp_unit_param,
            'windspeed_unit': wind_speed_unit_param,
            'timezone': 'auto',
            'forecast_days': api_forecast_days
        }

        new_data = None
        fetch_error = None
        try:
            self._log("INFO", f"Background fetching weather for lat={self.latitude}, lon={self.longitude}")
            response = requests.get(self.API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            new_data = response.json()
        except requests.exceptions.HTTPError as e:
            fetch_error = f"HTTP Error: {e} - Resp: {e.response.text if e.response else 'No response'}"
        except requests.exceptions.RequestException as e:
            fetch_error = f"RequestException: {e}"
        except Exception as e:
            fetch_error = f"Unexpected error during fetch: {e}"
        finally:
            with self.data_lock:
                if new_data:
                    self.last_weather_data = new_data
                    self.last_fetch_time = time.monotonic()
                    self._log("INFO", "Background fetch successful, cache updated.")
                elif fetch_error:
                    self._log("ERROR", fetch_error)
                self.is_fetching = False # Reset fetching flag

    def get_content(self) -> str:
        """Fetches weather data (or uses cache) and formats it."""
        current_monotonic_time = time.monotonic()
        
        # Critical config items read directly, assume reconfigure handles updates if necessary
        # These are used to decide IF we need to fetch, not necessarily for the fetch itself,
        # which is now in background and will use the instance's current lat/lon/units.
        update_interval_min = self.config.get('update_interval_minutes', self.DEFAULT_UPDATE_INTERVAL_MINUTES)
        current_display_format = self.config.get('display_format', 'Temp: {temp}{unit_symbol}')

        effective_interval_seconds = update_interval_min * 60 if update_interval_min > 0 else 0
        
        needs_fetch = False
        with self.data_lock: # Protect access to last_fetch_time and is_fetching
            if self.last_fetch_time == 0: # First ever call or data explicitly cleared
                 needs_fetch = True
            elif effective_interval_seconds > 0 and \
                 (current_monotonic_time - self.last_fetch_time) >= effective_interval_seconds:
                 needs_fetch = True
            
            if needs_fetch and not self.is_fetching:
                self.is_fetching = True
                self._log("INFO", f"Cache stale or missing. Starting background fetch for {self.widget_id}.")
                # Use current instance attributes for the fetch
                self.fetch_thread = threading.Thread(target=self._fetch_data_background)
                self.fetch_thread.daemon = True 
                self.fetch_thread.start()

        # Always try to return content, even if stale or fetching
        with self.data_lock: # Protect access to self.last_weather_data
            if self.last_weather_data:
                parsed_data = self._parse_weather_data(self.last_weather_data) # Uses instance units/time_format
                try:
                    return current_display_format.format_map(parsed_data)
                except KeyError as e: 
                    self._log("WARNING", f"Invalid key '{e}' in display_format. Available: {list(parsed_data.keys())}")
                    return "Format Err"
                except Exception as e: 
                    self._log("ERROR", f"Formatting data: {e}")
                    return "Render Err"
            elif self.is_fetching:
                return "Updating..." 
            else: # No data and not fetching (e.g. first load failed and interval not passed)
                return "No Data"

    @staticmethod
    def get_config_options() -> list:
        options = BaseWidget.get_config_options() # Start with base options (includes 'enable_logging')
        options.extend([
            {
                'name': 'location_name',
                'label': 'Location Name (Display Only)',
                'type': 'text',
                'default': 'Billingham,UK',
                'placeholder': 'E.g., London,UK (Uses hardcoded Lat/Lon for Billingham unless overridden)'
            },
            {
                'name': 'latitude',
                'label': 'Latitude',
                'type': 'number',
                'default': WeatherWidget.DEFAULT_LATITUDE,
                'placeholder': 'E.g., 54.61'
            },
            {
                'name': 'longitude',
                'label': 'Longitude',
                'type': 'number',
                'default': WeatherWidget.DEFAULT_LONGITUDE,
                'placeholder': 'E.g., -1.29'
            },
            {
                'name': 'units',
                'label': 'Units',
                'type': 'select',
                'default': 'metric',
                'options': [
                    {'value': 'metric', 'label': 'Celsius, km/h'},
                    {'value': 'imperial', 'label': 'Fahrenheit, mph'}
                ]
            },
            {
                'name': 'time_display_format',
                'label': 'Sunrise/Sunset Time Format',
                'type': 'text',
                'default': '%H:%M',
                'placeholder': 'E.g. %I:%M %p for 12-hour'
            },
            {
                'name': 'display_format',
                'label': 'Display Format String',
                'type': 'text',
                'default': 'Temp: {temp}{unit_symbol}',
                'placeholder': 'E.g., {temp}{unit_symbol} {weather_desc_0}',
                'description': 'Placeholders: {temp} (current), {unit_symbol}, {sunrise_time}, {sunset_time}, {wind_speed}, {wind_unit}, {weather_desc} (current). For daily data (today=0, tomorrow=1, etc.): {temp_max_N}, {temp_min_N}, {weather_desc_N}, {dow_N} (day of week, e.g., MON). Example: {dow_1}: {temp_max_1}{unit_symbol}'
            },
            {
                'name': 'update_interval_minutes',
                'label': 'Update Interval (minutes)',
                'type': 'number',
                'default': WeatherWidget.DEFAULT_UPDATE_INTERVAL_MINUTES,
                'placeholder': 'E.g., 15, 30, 60',
                'description': 'How often to fetch new weather data. Min 1. Set 0 to update on every cycle (not recommended).'
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
        ])
        return options 