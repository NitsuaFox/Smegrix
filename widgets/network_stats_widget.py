import subprocess
import re
import sys
from datetime import datetime, timedelta
from .base_widget import BaseWidget

class NetworkStatsWidget(BaseWidget):
    """Displays various network statistics like SSID or IP address, based on the OS."""

    def __init__(self, config: dict, global_context: dict = None):
        super().__init__(config, global_context)
        self.os_override = self.config.get('os_override', 'auto')
        self.font_size = self.config.get('font_size', 'medium')
        self.stat_to_display = self.config.get('stat_to_display', 'ssid')
        self._log("INFO", f"NetworkStatsWidget initialized with os_override: {self.os_override}, font_size: {self.font_size}, stat: {self.stat_to_display}")

        # Cache variables
        self._cached_ssid = None
        self._cached_ip = None
        self._cached_rssi = None
        self._last_ssid_check_time = None
        self._last_ip_check_time = None
        self._last_rssi_check_time = None
        self._cache_duration = timedelta(hours=48) # Cache for 48 hours

        # Cache variables for uptime
        self._cached_uptime = None
        self._last_uptime_check_time = None

    def _get_wifi_interface_macos(self) -> str | None:
        """Helper to find the active Wi-Fi interface name on macOS."""
        try:
            hw_ports_process = subprocess.run(
                ['networksetup', '-listallhardwareports'],
                capture_output=True, text=True, check=True, timeout=3
            )
            lines = hw_ports_process.stdout.splitlines()
            for i, line in enumerate(lines):
                if "Wi-Fi" in line or "AirPort" in line:
                    if i + 1 < len(lines):
                        device_line = lines[i+1]
                        match = re.search(r"Device: (en\d+)", device_line)
                        if match:
                            wifi_port = match.group(1)
                            self._log("DEBUG", f"Found Wi-Fi port for macOS: {wifi_port}")
                            return wifi_port
            self._log("WARNING", "Could not determine Wi-Fi port on macOS.")
            return None
        except Exception as e:
            self._log("ERROR", f"Error finding Wi-Fi interface on macOS: {e}")
            return None

    def _get_ssid_macos(self) -> str:
        """Fetches SSID on macOS using networksetup."""
        wifi_port = self._get_wifi_interface_macos()
        if not wifi_port:
            return "No Wi-Fi Port"
        try:
            get_network_process = subprocess.run(
                ['networksetup', '-getairportnetwork', wifi_port],
                capture_output=True, text=True, check=True, timeout=3
            )
            output = get_network_process.stdout.strip()
            if "You are not associated with an AirPort network." in output or not output:
                self._log("INFO", f"macOS not associated with a Wi-Fi network on port {wifi_port}.")
                return "Not Connected"
            ssid_match = re.search(r"Current Wi-Fi Network: (.+)", output)
            if ssid_match:
                ssid = ssid_match.group(1).strip()
                self._log("DEBUG", f"macOS SSID found: {ssid} via networksetup on port {wifi_port}")
                return ssid
            else:
                if output: return output 
                self._log("WARNING", f"macOS SSID pattern not found in networksetup output for port {wifi_port}: {output}")
                return "SSID N/A"
        except subprocess.CalledProcessError as e:
            if e.cmd and len(e.cmd) > 1 and e.cmd[1] == '-getairportnetwork':
                if "Wi-Fi is not associated with an AirPort network" in e.stderr or \
                   "Wi-Fi is not associated with an AirPort network" in e.stdout or \
                   "You are not associated with an AirPort network" in e.stdout or \
                   "Error: Wi-Fi is not turned on" in e.stdout or \
                   "Error: Wi-Fi is not turned on" in e.stderr:
                    self._log("INFO", f"macOS not associated or Wi-Fi off (CalledProcessError): {e.cmd}")
                    return "Not Connected"
            self._log("ERROR", f"Error fetching macOS SSID with networksetup: {e} - stderr: {e.stderr}")
            return "Err:NetSetup"
        except FileNotFoundError:
            self._log("ERROR", "networksetup command not found.")
            return "Err:CmdNotFound"
        except subprocess.TimeoutExpired:
            self._log("ERROR", "Timeout fetching macOS SSID with networksetup.")
            return "Err:Timeout"
        except Exception as e:
            self._log("ERROR", f"Unexpected error fetching macOS SSID with networksetup: {e}")
            return "Err:SSIDGen"

    def _get_ip_macos(self) -> str:
        """Fetches IP address on macOS for the primary network interface."""
        self._log("DEBUG", "Attempting to fetch IP for primary interface on macOS.")
        try:
            # Get the primary network interface (e.g., en0, en1)
            route_cmd = "route -n get default | grep 'interface:' | awk '{print $2}'"
            interface_process = subprocess.run(route_cmd, shell=True, capture_output=True, text=True, check=True, timeout=2)
            primary_interface = interface_process.stdout.strip()
            
            if not primary_interface:
                self._log("WARNING", "Could not determine primary network interface on macOS via route command.")
                # Fallback to trying the Wi-Fi interface if primary cannot be determined
                wifi_interface = self._get_wifi_interface_macos()
                if not wifi_interface:
                    self._log("WARNING", "No Wi-Fi interface found as fallback for macOS IP.")
                    return "No IF (macOS)"
                self._log("DEBUG", f"Falling back to Wi-Fi interface for IP: {wifi_interface}")
                interface_to_use = wifi_interface
            else:
                self._log("DEBUG", f"Primary network interface on macOS: {primary_interface}")
                interface_to_use = primary_interface

            # Get the IP address for the determined interface
            ip_process = subprocess.run(['ipconfig', 'getifaddr', interface_to_use], capture_output=True, text=True, check=True, timeout=3)
            ip_address = ip_process.stdout.strip()
            
            if ip_address:
                self._log("DEBUG", f"macOS IP address for interface {interface_to_use} found: {ip_address}")
                return ip_address
            else:
                self._log("WARNING", f"ipconfig getifaddr {interface_to_use} returned no output.")
                return "No IP (macOS)"
        except subprocess.CalledProcessError as e:
            self._log("ERROR", f"Error fetching macOS IP for primary interface: {e} - cmd: {e.cmd} - stderr: {e.stderr}")
            return "Err:IP macOS"
        except FileNotFoundError:
            self._log("ERROR", "ipconfig or route command not found for macOS IP.")
            return "Err:CmdNotFound"
        except subprocess.TimeoutExpired:
            self._log("ERROR", "Timeout fetching macOS IP for primary interface.")
            return "Err:Timeout"
        except Exception as e:
            self._log("ERROR", f"Unexpected error fetching macOS IP: {e}")
            return "Err:IPGen"

    def _get_uptime_macos(self) -> str:
        """Fetches system uptime on macOS using the uptime command."""
        try:
            process = subprocess.run(['uptime'], capture_output=True, text=True, check=True, timeout=3)
            # Example output: "10:30  up 2 days,  4:35, 2 users, load averages: 1.78 1.99 2.17"
            # We want to extract the "up ..." part.
            match = re.search(r"up ([^,]+(?:, [^,]+)*), \d+ users?", process.stdout)
            if match:
                uptime_str = match.group(1).strip()
                
                parsed_days = 0
                parsed_hours = 0
                parsed_minutes = 0

                # Try to extract days
                day_search_match = re.search(r"(\d+)\s*day(s)?", uptime_str)
                if day_search_match:
                    parsed_days = int(day_search_match.group(1))
                    comma_index = uptime_str.find(',')
                    if comma_index != -1:
                        remaining_str_after_days = uptime_str[comma_index+1:].strip()
                    else:
                        remaining_str_after_days = ""
                else:
                    remaining_str_after_days = uptime_str

                # Try to extract HH:MM from the remaining string
                time_hm_search_match = re.search(r"(\d+):(\d+)", remaining_str_after_days)
                if time_hm_search_match:
                    parsed_hours = int(time_hm_search_match.group(1))
                    parsed_minutes = int(time_hm_search_match.group(2))
                else:
                    # If not HH:MM, try to extract minutes (e.g. "55 min") from the remaining string
                    min_search_match = re.search(r"(\d+)\s*min(s)?", remaining_str_after_days)
                    if min_search_match:
                        parsed_minutes = int(min_search_match.group(1))
                
                parts = []
                if parsed_days > 0: parts.append(f"{parsed_days}d")
                if parsed_hours > 0: parts.append(f"{parsed_hours}h")
                # Append minutes if > 0, or if it's the only component (even if 0, e.g. "0m" for very short uptimes)
                if parsed_minutes > 0 or (parsed_days == 0 and parsed_hours == 0):
                    parts.append(f"{parsed_minutes}m")

                if not parts:
                    return "Up <1m" # Fallback for very short or unparseable (though initial match should ensure some content)
                
                return f"Up {':'.join(parts)}"
            self._log("WARNING", f"Could not parse uptime from macOS output: {process.stdout}")
            return "Up N/A (macOS)"
        except subprocess.CalledProcessError as e:
            self._log("ERROR", f"Error fetching macOS uptime: {e}")
            return "Err:Uptime"
        except FileNotFoundError:
            self._log("ERROR", "uptime command not found on macOS.")
            return "Err:CmdNotFound"
        except subprocess.TimeoutExpired:
            self._log("ERROR", "Timeout fetching macOS uptime.")
            return "Err:Timeout"
        except Exception as e:
            self._log("ERROR", f"Unexpected error fetching macOS uptime: {e}")
            return "Err:UptimeGen"

    def _get_wifi_interface_linux(self) -> str | None:
        """Helper to find the active Wi-Fi interface name on Linux (e.g., wlan0)."""
        try:
            # Try with `iwgetid` first as it directly gives the interface if connected
            process = subprocess.run(['iwgetid'], capture_output=True, text=True, check=False, timeout=2)
            if process.returncode == 0 and process.stdout.strip():
                interface_name = process.stdout.split(' ', 1)[0].strip()
                if interface_name:
                    self._log("DEBUG", f"Found Linux Wi-Fi interface via iwgetid: {interface_name}")
                    return interface_name
            
            # Fallback: Check `ip -o link show` output for common Wi-Fi patterns
            process = subprocess.run(['ip', '-o', 'link', 'show'], capture_output=True, text=True, check=True, timeout=2)
            for line in process.stdout.splitlines():
                if 'wlan' in line or 'wifi' in line or 'wlp' in line: # Common prefixes for Wi-Fi interfaces
                    parts = line.split(': ')
                    if len(parts) > 1:
                        interface_name = parts[1].split('@')[0] # Get name before @ if virtual
                        # Further check if it's up and has a link (more complex, skipping for now)
                        self._log("DEBUG", f"Found potential Linux Wi-Fi interface via ip link: {interface_name}")
                        # For simplicity, returning the first one found. Might need refinement.
                        return interface_name
            self._log("WARNING", "Could not determine Wi-Fi interface on Linux.")
            return None
        except Exception as e:
            self._log("ERROR", f"Error finding Wi-Fi interface on Linux: {e}")
            return None

    def _get_ssid_linux(self) -> str:
        """Fetches SSID on Linux using iwgetid or nmcli."""
        try:
            process = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, check=True, timeout=3)
            ssid = process.stdout.strip()
            if ssid: return ssid
        except Exception: pass # Handled by nmcli fallback

        try:
            cmd = "nmcli -t -f active,ssid dev wifi | grep '^yes:' | cut -d: -f2"
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True, timeout=3)
            ssid = process.stdout.strip()
            if ssid: return ssid
            return "No SSID (nmcli)"
        except Exception as e:
            self._log("ERROR", f"Linux SSID fetch failed for all methods: {e}")
            return "Err:LinuxSSID"

    def _get_ip_linux(self) -> str:
        """Fetches IP address on Linux."""
        try:
            # hostname -I gets all IPs, space separated. We take the first one.
            process = subprocess.run(['hostname', '-I'], capture_output=True, text=True, check=True, timeout=3)
            ip_address = process.stdout.strip().split(' ')[0]
            if ip_address:
                self._log("DEBUG", f"Linux IP address found: {ip_address}")
                return ip_address
            else:
                self._log("WARNING", "hostname -I returned no output.")
                return "No IP (Linux)"
        except subprocess.CalledProcessError as e:
            self._log("ERROR", f"Error fetching Linux IP with hostname -I: {e}")
            return "Err:IP Linux"
        except FileNotFoundError:
            self._log("INFO", "hostname command not found. Trying ip addr.")
            # Fallback to parsing `ip addr` if hostname -I fails or not found
            wifi_interface = self._get_wifi_interface_linux()
            if wifi_interface:
                try:
                    # Get IP from 'ip addr show dev <interface>'
                    cmd = f"ip -4 addr show dev {wifi_interface} | grep -oP 'inet \\K[\\d.]+'"
                    process = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True, timeout=3)
                    ip_address = process.stdout.strip()
                    if ip_address:
                        self._log("DEBUG", f"Linux IP for {wifi_interface} via ip addr: {ip_address}")
                        return ip_address
                    else:
                        self._log("WARNING", f"ip addr for {wifi_interface} gave no IP.")
                        return "No IP (ip addr)"
                except Exception as e_ip:
                    self._log("ERROR", f"Error fetching IP with ip addr for {wifi_interface}: {e_ip}")
                    return "Err:IP (ip addr)"
            return "No IF/IP (Linux)"
        except subprocess.TimeoutExpired:
            self._log("ERROR", "Timeout fetching Linux IP.")
            return "Err:Timeout"
        except Exception as e:
            self._log("ERROR", f"Unexpected error fetching Linux IP: {e}")
            return "Err:IPGen"

    def _get_uptime_linux(self) -> str:
        """Fetches system uptime on Linux, preferring 'uptime -p'."""
        try:
            # Try 'uptime -p' for pretty format first
            process = subprocess.run(['uptime', '-p'], capture_output=True, text=True, check=True, timeout=3)
            # Example output: "up 2 hours, 7 minutes"
            # Remove "up " prefix
            uptime_str = process.stdout.strip()
            if uptime_str.startswith("up "):
                uptime_str = uptime_str[3:]
            return f"Up {uptime_str}"
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e_p:
            self._log("WARNING", f"Fetching uptime with 'uptime -p' failed: {e_p}. Trying /proc/uptime.")
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                
                days = int(uptime_seconds // (24 * 3600))
                uptime_seconds %= (24 * 3600)
                hours = int(uptime_seconds // 3600)
                uptime_seconds %= 3600
                minutes = int(uptime_seconds // 60)
                
                parts = []
                if days > 0: parts.append(f"{days}d")
                if hours > 0: parts.append(f"{hours}h")
                if minutes > 0 or (days == 0 and hours == 0) : parts.append(f"{minutes}m") # Show minutes if uptime is < 1h
                
                return f"Up {', '.join(parts)}" if parts else "Up <1m"

            except Exception as e_proc:
                self._log("ERROR", f"Error fetching Linux uptime from /proc/uptime: {e_proc}")
                return "Err:UptimeProc"
        except Exception as e:
            self._log("ERROR", f"Unexpected error fetching Linux uptime: {e}")
            return "Err:UptimeGen"

    def _get_ssid_windows(self) -> str:
        """Placeholder for fetching SSID on Windows."""
        self._log("INFO", "Windows SSID fetching not yet implemented.")
        return "Win N/A"

    def _get_ip_windows(self) -> str:
        """Placeholder for fetching IP address on Windows."""
        self._log("INFO", "Windows IP fetching not yet implemented.")
        return "Win IP N/A"

    def _get_rssi_macos(self) -> str:
        """Fetches RSSI (signal strength) on macOS using the airport command."""
        try:
            process = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                capture_output=True, text=True, check=True, timeout=5
            )
            rssi_match = re.search(r"^\s*agrCtlRSSI: (.+)$", process.stdout, re.MULTILINE)
            if rssi_match:
                rssi = rssi_match.group(1).strip()
                self._log("DEBUG", f"macOS RSSI found: {rssi}")
                return f"{rssi} dBm"
            else:
                self._log("WARNING", "RSSI not found in airport output")
                return "No RSSI"
        except subprocess.CalledProcessError as e:
            self._log("ERROR", f"Error fetching macOS RSSI with airport: {e}")
            return "Err:Airport"
        except FileNotFoundError:
            self._log("ERROR", "airport command not found on macOS.")
            return "Err:CmdNotFound"
        except subprocess.TimeoutExpired:
            self._log("ERROR", "Timeout fetching macOS RSSI.")
            return "Err:Timeout"
        except Exception as e:
            self._log("ERROR", f"Unexpected error fetching macOS RSSI: {e}")
            return "Err:RSSIGen"

    def _get_rssi_linux(self) -> str:
        """Fetches RSSI (signal strength) on Linux using iwgetid or iwconfig."""
        wifi_interface = self._get_wifi_interface_linux()
        if not wifi_interface:
            self._log("WARNING", "No Wi-Fi interface found for RSSI on Linux.")
            return "No Wi-Fi IF"
        
        try:
            # Try iwgetid first
            process = subprocess.run(['iwgetid', wifi_interface, '--signal'], 
                                   capture_output=True, text=True, check=True, timeout=3)
            output = process.stdout.strip()
            if output:
                # Output format: "wlan0:Signal level=XX dBm"
                rssi_match = re.search(r"Signal level=(-?\d+)", output)
                if rssi_match:
                    rssi = rssi_match.group(1)
                    self._log("DEBUG", f"Linux RSSI found via iwgetid: {rssi}")
                    return f"{rssi} dBm"
        except Exception:
            self._log("DEBUG", "iwgetid failed, trying iwconfig")
        
        try:
            # Fallback to iwconfig
            process = subprocess.run(['iwconfig', wifi_interface], 
                                   capture_output=True, text=True, check=True, timeout=3)
            # Look for "Signal level=XX dBm" in iwconfig output
            rssi_match = re.search(r"Signal level=(-?\d+)", process.stdout)
            if rssi_match:
                rssi = rssi_match.group(1)
                self._log("DEBUG", f"Linux RSSI found via iwconfig: {rssi}")
                return f"{rssi} dBm"
            else:
                self._log("WARNING", f"No RSSI found in iwconfig output for {wifi_interface}")
                return "No Signal Data"
        except subprocess.CalledProcessError as e:
            self._log("ERROR", f"Error fetching Linux RSSI with iwconfig: {e}")
            return "Err:iwconfig"
        except FileNotFoundError:
            self._log("ERROR", "iwconfig command not found on Linux.")
            return "Err:CmdNotFound"
        except subprocess.TimeoutExpired:
            self._log("ERROR", "Timeout fetching Linux RSSI.")
            return "Err:Timeout"
        except Exception as e:
            self._log("ERROR", f"Unexpected error fetching Linux RSSI: {e}")
            return "Err:RSSIGen"

    def _get_rssi_windows(self) -> str:
        """Placeholder for fetching RSSI on Windows."""
        self._log("INFO", "Windows RSSI fetching not yet implemented.")
        return "Win RSSI N/A"

    def get_content(self) -> str:
        """Returns the selected network statistic based on the OS, using a cache."""
        now = datetime.now()

        if self.stat_to_display == 'ssid':
            if self._cached_ssid and self._last_ssid_check_time and (now - self._last_ssid_check_time < self._cache_duration):
                self._log("DEBUG", f"Returning cached SSID: {self._cached_ssid}")
                return self._cached_ssid
            self._log("INFO", "Cache miss or stale for SSID. Fetching fresh data.")
        elif self.stat_to_display == 'ip':
            if self._cached_ip and self._last_ip_check_time and (now - self._last_ip_check_time < self._cache_duration):
                self._log("DEBUG", f"Returning cached IP: {self._cached_ip}")
                return self._cached_ip
            self._log("INFO", "Cache miss or stale for IP. Fetching fresh data.")
        elif self.stat_to_display == 'uptime':
            if self._cached_uptime and self._last_uptime_check_time and (now - self._last_uptime_check_time < self._cache_duration):
                self._log("DEBUG", f"Returning cached uptime: {self._cached_uptime}")
                return self._cached_uptime
            self._log("INFO", "Cache miss or stale for uptime. Fetching fresh data.")
        elif self.stat_to_display == 'rssi':
            if self._cached_rssi and self._last_rssi_check_time and (now - self._last_rssi_check_time < self._cache_duration):
                self._log("DEBUG", f"Returning cached RSSI: {self._cached_rssi}")
                return self._cached_rssi
            self._log("INFO", "Cache miss or stale for RSSI. Fetching fresh data.")

        current_os = self.os_override
        if current_os == 'auto':
            if sys.platform == "darwin": current_os = 'macos'
            elif sys.platform.startswith("linux"): current_os = 'linux'
            elif sys.platform == "win32": current_os = 'windows'
            else:
                self._log("WARNING", f"Unsupported OS for 'auto' mode: {sys.platform}")
                return "OS N/A"
        
        self._log("DEBUG", f"Determined OS for {self.__class__.__name__} data fetch: {current_os}, stat: {self.stat_to_display}")

        fetched_value = "Err:Fetch"
        if self.stat_to_display == 'ssid':
            if current_os == 'macos': fetched_value = self._get_ssid_macos()
            elif current_os == 'linux': fetched_value = self._get_ssid_linux()
            elif current_os == 'windows': fetched_value = self._get_ssid_windows()
            self._cached_ssid = fetched_value
            self._last_ssid_check_time = now
            self._log("INFO", f"Fetched and cached SSID: {self._cached_ssid}")
        elif self.stat_to_display == 'ip':
            if current_os == 'macos': fetched_value = self._get_ip_macos()
            elif current_os == 'linux': fetched_value = self._get_ip_linux()
            elif current_os == 'windows': fetched_value = self._get_ip_windows()
            self._cached_ip = fetched_value
            self._last_ip_check_time = now
            self._log("INFO", f"Fetched and cached IP: {self._cached_ip}")
        elif self.stat_to_display == 'uptime':
            if current_os == 'macos': fetched_value = self._get_uptime_macos()
            elif current_os == 'linux': fetched_value = self._get_uptime_linux()
            elif current_os == 'windows': fetched_value = "Win Uptime N/A" # Placeholder for Windows
            else: fetched_value = "OS Uptime N/A"
            self._cached_uptime = fetched_value
            self._last_uptime_check_time = now
            self._log("INFO", f"Fetched and cached uptime: {self._cached_uptime}")
        elif self.stat_to_display == 'rssi':
            if current_os == 'macos': fetched_value = self._get_rssi_macos()
            elif current_os == 'linux': fetched_value = self._get_rssi_linux()
            elif current_os == 'windows': fetched_value = self._get_rssi_windows()
            self._cached_rssi = fetched_value
            self._last_rssi_check_time = now
            self._log("INFO", f"Fetched and cached RSSI: {self._cached_rssi}")
        else:
            self._log("WARNING", f"Invalid stat_to_display ('{self.stat_to_display}') or OS ('{current_os}') combination.")
            return "Cfg Err"
        
        return fetched_value

    @staticmethod
    def get_config_options() -> list:
        options = BaseWidget.get_config_options()
        options.extend([
            {
                'name': 'stat_to_display',
                'label': 'Statistic to Display',
                'type': 'select',
                'default': 'ssid',
                'options': [
                    {'value': 'ssid', 'label': 'SSID (Network Name)'},
                    {'value': 'ip', 'label': 'IP Address'},
                    {'value': 'uptime', 'label': 'System Uptime'},
                    {'value': 'rssi', 'label': 'RSSI (Signal Strength)'}
                ],
                'description': 'Choose which network statistic to display.'
            },
            {
                'name': 'os_override',
                'label': 'Operating System',
                'type': 'select',
                'default': 'auto',
                'options': [
                    {'value': 'auto', 'label': 'Auto-detect'},
                    {'value': 'macos', 'label': 'macOS'},
                    {'value': 'linux', 'label': 'Linux'},
                    {'value': 'windows', 'label': 'Windows'}
                ],
                'description': 'Select the OS for data detection. \'Auto-detect\' uses the system where the app runs.'
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
                ],
                'description': 'Select the font size for the displayed network statistic.'
            }
        ])
        return options 