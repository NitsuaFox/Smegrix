import datetime
import requests
from .base_widget import BaseWidget

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

    def get_content(self) -> str:
        """Fetches weather data and formats it using the user-defined display_format string."""

        temp_unit_param = 'celsius' if self.units == 'metric' else 'fahrenheit'
        wind_speed_unit_param = 'ms' # Open-Meteo default for current is km/h, let's request m/s for metric for consistency
        # Or make windspeed_unit fully configurable
        if self.units == 'imperial':
            wind_speed_unit_param = 'mph' 
        elif self.units == 'metric': # Default metric to km/h for OpenMeteo default unless specified
            wind_speed_unit_param = 'kmh' # Open-Meteo Current Weather default, daily default is also km/h
            # If we want m/s for metric in current weather, it needs specific handling or config.
            # For now, we'll stick to km/h for metric current weather as it's simpler from Open-Meteo.

        params = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'current_weather': 'true',
            'daily': 'sunrise,sunset,temperature_2m_max,temperature_2m_min,weathercode', # Added weathercode for daily too
            'temperature_unit': temp_unit_param,
            'windspeed_unit': wind_speed_unit_param, 
            'timezone': 'auto'
        }

        try:
            print(f"[WeatherWidget-{self.widget_id}] INFO: Fetching weather for lat={self.latitude}, lon={self.longitude} (Location: '{self.location_name}') with params: {params}")
            response = requests.get(self.API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            weather_data = response.json()
            # print(f"[WeatherWidget-{self.widget_id}] DEBUG: API Response: {weather_data}") # For debugging

            available_data = {
                'temp': 'N/A',
                'unit_symbol': 'C' if self.units == 'metric' else 'F',
                'sunrise_time': 'N/A',
                'sunset_time': 'N/A',
                'wind_speed': 'N/A',
                'wind_unit': 'km/h' if self.units == 'metric' else 'mph', # Defaulting wind_unit text based on query
                'weather_desc': 'N/A',
                'temp_max': 'N/A',
                'temp_min': 'N/A',
                'daily_weather_desc': 'N/A' # For daily summary
            }
            if wind_speed_unit_param == 'ms': available_data['wind_unit'] = 'm/s' # Correct unit display

            current_weather = weather_data.get('current_weather')
            if current_weather:
                if 'temperature' in current_weather:
                    available_data['temp'] = f"{current_weather['temperature']:.0f}"
                if 'windspeed' in current_weather:
                    available_data['wind_speed'] = f"{current_weather['windspeed']:.0f}"
                if 'weathercode' in current_weather:
                    code = current_weather['weathercode']
                    available_data['weather_desc'] = WMO_WEATHER_CODES.get(code, "Unknown Code")
            
            daily_data = weather_data.get('daily')
            if daily_data:
                if daily_data.get('sunrise') and len(daily_data['sunrise']) > 0:
                    try: dt_obj = datetime.datetime.fromisoformat(daily_data['sunrise'][0]); available_data['sunrise_time'] = dt_obj.strftime(self.time_display_format)
                    except ValueError: print(f"[WeatherWidget-{self.widget_id}] WARNING: Could not parse sunrise time.")
                
                if daily_data.get('sunset') and len(daily_data['sunset']) > 0:
                    try: dt_obj = datetime.datetime.fromisoformat(daily_data['sunset'][0]); available_data['sunset_time'] = dt_obj.strftime(self.time_display_format)
                    except ValueError: print(f"[WeatherWidget-{self.widget_id}] WARNING: Could not parse sunset time.")

                if daily_data.get('temperature_2m_max') and len(daily_data['temperature_2m_max']) > 0:
                    available_data['temp_max'] = f"{daily_data['temperature_2m_max'][0]:.0f}"
                if daily_data.get('temperature_2m_min') and len(daily_data['temperature_2m_min']) > 0:
                    available_data['temp_min'] = f"{daily_data['temperature_2m_min'][0]:.0f}"
                if daily_data.get('weathercode') and len(daily_data['weathercode']) > 0:
                    code = daily_data['weathercode'][0]
                    available_data['daily_weather_desc'] = WMO_WEATHER_CODES.get(code, "Unknown Code")

            try: return self.display_format.format_map(available_data)
            except KeyError as e: print(f"[WeatherWidget-{self.widget_id}] WARNING: Invalid key '{e}' in display_format. Available: {list(available_data.keys())}"); return "Format Err"

        except requests.exceptions.HTTPError as e: print(f"[WeatherWidget-{self.widget_id}] ERROR: HTTP Error: {e} - Resp: {e.response.text}"); return "Weather: HTTP Err"
        except requests.exceptions.RequestException as e: print(f"[WeatherWidget-{self.widget_id}] ERROR: RequestException: {e}"); return "Weather: Net Err"
        except Exception as e: print(f"[WeatherWidget-{self.widget_id}] ERROR: Unexpected error: {e}"); return "Weather: Data Err"

    @staticmethod
    def get_config_options() -> list:
        return [
            # API Key field removed
            {
                'name': 'location_name',
                'label': 'Location Name (Display Only)',
                'type': 'text',
                'default': 'Billingham,UK',
                'placeholder': 'E.g., London,UK (Uses hardcoded Lat/Lon for Billingham unless overridden)'
            },
            # Future: Add latitude and longitude fields for user input
            # {
            #     'name': 'latitude',
            #     'label': 'Latitude',
            #     'type': 'number',
            #     'default': WeatherWidget.DEFAULT_LATITUDE,
            #     'placeholder': 'E.g., 51.5074'
            # },
            # {
            #     'name': 'longitude',
            #     'label': 'Longitude',
            #     'type': 'number',
            #     'default': WeatherWidget.DEFAULT_LONGITUDE,
            #     'placeholder': 'E.g., -0.1278'
            # },
            {
                'name': 'units',
                'label': 'Units (Temp & Wind Speed Display)',
                'type': 'select',
                'default': 'metric',
                'options': [
                    {'value': 'metric', 'label': 'Celsius, km/h (or m/s if API allows)'},
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
                'placeholder': 'E.g., {temp}{unit_symbol} {weather_desc}',
                'description': 'Placeholders: {temp}, {unit_symbol}, {sunrise_time}, {sunset_time}, {wind_speed}, {wind_unit}, {weather_desc}, {temp_max}, {temp_min}, {daily_weather_desc}.'
            },
            {
                'name': 'font_size',
                'label': 'Font Size',
                'type': 'select',
                'default': 'medium',
                'options': [
                    {'value': 'small', 'label': 'Small (3x5)'},
                    {'value': 'medium', 'label': 'Medium (5x7)'}
                    # Add other sizes if desired for WeatherWidget in the future
                ]
            }
        ] 