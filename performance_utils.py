import os
import platform
import subprocess
import psutil
import time
import json

# Class to detect and manage Raspberry Pi specific optimizations
class RaspberryPiOptimizer:
    def __init__(self):
        self.is_raspberry_pi = self._detect_raspberry_pi()
        self.settings_file = "pi_optimizations.json"
        self.applied_optimizations = self._load_settings()
        
        # Debug print to help diagnose Pi detection
        print(f"[PI_OPT] Raspberry Pi detection: {self.is_raspberry_pi}")
        if self.is_raspberry_pi:
            print(f"[PI_OPT] Loaded optimization settings: {self.applied_optimizations}")
        
    def _detect_raspberry_pi(self):
        """Detect if running on a Raspberry Pi"""
        try:
            # Method 1: Check model file
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read()
                    if 'raspberry pi' in model.lower():
                        print(f"[PI_OPT] Detected Raspberry Pi model: {model}")
                        return True
            
            # Method 2: Check platform info
            system_info = platform.uname()
            if 'arm' in system_info.machine.lower() and 'linux' in system_info.system.lower():
                # Further check with CPU info
                if os.path.exists('/proc/cpuinfo'):
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read().lower()
                        if 'raspberry pi' in cpuinfo or 'bcm' in cpuinfo:
                            print(f"[PI_OPT] Detected Raspberry Pi from CPU info")
                            return True
            
            return False
        except Exception as e:
            print(f"[PI_OPT] Error in Raspberry Pi detection: {e}")
            return False
    
    def _load_settings(self):
        """Load previously applied optimizations"""
        if not os.path.exists(self.settings_file):
            return {
                "gpu_mem": 0,
                "disable_overscan": False,
                "disable_hdmi_blanking": False,
                "disable_audio": False,
                "cpu_governor": "",
                "applied_date": ""
            }
            
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[PI_OPT] Error loading optimization settings: {e}")
            return {
                "gpu_mem": 0,
                "disable_overscan": False,
                "disable_hdmi_blanking": False,
                "disable_audio": False, 
                "cpu_governor": "",
                "applied_date": ""
            }
    
    def _save_settings(self):
        """Save applied optimizations"""
        try:
            with open(self.settings_file, 'w') as f:
                self.applied_optimizations["applied_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
                json.dump(self.applied_optimizations, f, indent=2)
        except Exception as e:
            print(f"[PI_OPT] Error saving optimization settings: {e}")
    
    def apply_performance_optimizations(self, gpu_mem=128, disable_overscan=True, 
                                        disable_hdmi_blanking=True, disable_audio=False):
        """Apply Raspberry Pi specific optimizations"""
        if not self.is_raspberry_pi:
            print("[PI_OPT] Not running on a Raspberry Pi, skipping optimizations")
            return False
            
        print("[PI_OPT] Applying Raspberry Pi optimizations...")
        success = True
        
        # Update config.txt - requires sudo which may prompt for password
        if self._update_config_txt(gpu_mem, disable_overscan, disable_hdmi_blanking, disable_audio):
            self.applied_optimizations["gpu_mem"] = gpu_mem
            self.applied_optimizations["disable_overscan"] = disable_overscan
            self.applied_optimizations["disable_hdmi_blanking"] = disable_hdmi_blanking
            self.applied_optimizations["disable_audio"] = disable_audio
        else:
            success = False
            
        # Set CPU governor to performance
        if self._set_cpu_governor("performance"):
            self.applied_optimizations["cpu_governor"] = "performance"
        else:
            success = False
            
        # Save settings
        self._save_settings()
        
        return success
    
    def _update_config_txt(self, gpu_mem, disable_overscan, disable_hdmi_blanking, disable_audio):
        """Update /boot/config.txt with performance optimizations"""
        # This is a simulation as we can't write to /boot/config.txt without sudo
        # In practice, this would need to be run with sudo
        try:
            config_path = "/boot/config.txt"
            
            if not os.path.exists(config_path):
                print(f"[PI_OPT] Config file {config_path} not found")
                return False
                
            print(f"[PI_OPT] These changes would be applied to {config_path}:")
            print(f"[PI_OPT] - gpu_mem={gpu_mem}")
            print(f"[PI_OPT] - disable_overscan={'1' if disable_overscan else '0'}")
            print(f"[PI_OPT] - hdmi_blanking={'0' if disable_hdmi_blanking else '1'}")
            print(f"[PI_OPT] - dtparam=audio={'off' if disable_audio else 'on'}")
            
            # In production, we would create a script to modify config.txt with sudo
            # and have the user run it
            self._create_optimization_script(gpu_mem, disable_overscan, disable_hdmi_blanking, disable_audio)
            
            return True
        except Exception as e:
            print(f"[PI_OPT] Error updating config.txt: {e}")
            return False
    
    def _create_optimization_script(self, gpu_mem, disable_overscan, disable_hdmi_blanking, disable_audio):
        """Create a script that can be run with sudo to apply optimizations"""
        core_count = psutil.cpu_count()
        governor_commands = ""
        for i in range(core_count):
            governor_commands += f"echo \"performance\" > /sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor\n"

        script_content = f"""#!/bin/bash
# Raspberry Pi Performance Optimization Script
# Run with sudo: sudo bash {os.path.abspath('optimize_raspberry_pi.sh')}

CONFIG="/boot/config.txt"

# Backup original config
cp $CONFIG $CONFIG.backup

# Apply optimizations
echo "[PI_OPT] Applying performance optimizations to $CONFIG"

# GPU Memory
grep -q "^gpu_mem=" $CONFIG && sed -i "s/^gpu_mem=.*/gpu_mem={gpu_mem}/" $CONFIG || echo "gpu_mem={gpu_mem}" >> $CONFIG

# Overscan
grep -q "^disable_overscan=" $CONFIG && sed -i "s/^disable_overscan=.*/disable_overscan={'1' if disable_overscan else '0'}/" $CONFIG || echo "disable_overscan={'1' if disable_overscan else '0'}" >> $CONFIG

# HDMI Blanking
grep -q "^hdmi_blanking=" $CONFIG && sed -i "s/^hdmi_blanking=.*/hdmi_blanking={'0' if disable_hdmi_blanking else '1'}/" $CONFIG || echo "hdmi_blanking={'0' if disable_hdmi_blanking else '1'}" >> $CONFIG

# Audio
grep -q "^dtparam=audio=" $CONFIG && sed -i "s/^dtparam=audio=.*/dtparam=audio={'off' if disable_audio else 'on'}/" $CONFIG || echo "dtparam=audio={'off' if disable_audio else 'on'}" >> $CONFIG

echo "[PI_OPT] Setting CPU governor to performance..."
{governor_commands}
echo "[PI_OPT] CPU governor commands added to script."

echo "[PI_OPT] Optimizations applied. Original config backed up to $CONFIG.backup"
echo "[PI_OPT] Reboot recommended: sudo reboot"
"""
        with open("optimize_raspberry_pi.sh", "w") as f:
            f.write(script_content)
            
        os.chmod("optimize_raspberry_pi.sh", 0o755)  # Make executable
        print("[PI_OPT] Created optimization script: optimize_raspberry_pi.sh")
        print("[PI_OPT] Run with: sudo bash optimize_raspberry_pi.sh")
    
    def _set_cpu_governor(self, governor="performance"):
        """Set CPU governor for better performance"""
        if not self.is_raspberry_pi:
            return False
            
        try:
            # Check if cpufreq directory exists
            cpufreq_path = "/sys/devices/system/cpu/cpu0/cpufreq"
            if not os.path.exists(cpufreq_path):
                print(f"[PI_OPT] CPU frequency scaling not available at {cpufreq_path}")
                return False
                
            # Check current governor
            current_governor = "unknown"
            try:
                with open(f"{cpufreq_path}/scaling_governor", "r") as f:
                    current_governor = f.read().strip()
            except:
                pass
                
            print(f"[PI_OPT] Current CPU governor: {current_governor}")
            
            if current_governor == governor:
                print(f"[PI_OPT] CPU governor already set to {governor}")
                return True
                
            # This would typically require sudo, so we'll just print the command
            # The actual commands are now added to the script in _create_optimization_script
            print(f"[PI_OPT] To set CPU governor to {governor}, ensure optimize_raspberry_pi.sh is run with sudo.")
            # core_count = psutil.cpu_count() # No longer needed to print here
            # for i in range(core_count):
            #     print(f"[PI_OPT] sudo sh -c 'echo {governor} > /sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor'")
                
            # print(f"[PI_OPT] Added command to optimization script") # This message is now misleading here
            return True # Assume the script will handle it
        except Exception as e:
            print(f"[PI_OPT] Error setting CPU governor: {e}")
            return False
    
    def get_system_stats(self):
        """Get current system statistics"""
        stats = {
            "cpu_percent": psutil.cpu_percent(interval=0.02),
            "memory_percent": psutil.virtual_memory().percent,
            "temperature": self._get_cpu_temperature() if self.is_raspberry_pi else "N/A",
            "cpu_frequency": self._get_cpu_frequency() if self.is_raspberry_pi else "N/A"
        }
        return stats
    
    def _get_cpu_temperature(self):
        """Get CPU temperature on Raspberry Pi"""
        try:
            temp_file = '/sys/class/thermal/thermal_zone0/temp'
            if os.path.exists(temp_file):
                with open(temp_file, 'r') as f:
                    temp = float(f.read().strip()) / 1000.0
                    return f"{temp:.1f}°C"
            return "N/A"
        except Exception as e:
            print(f"[PI_OPT] Error getting CPU temperature: {e}")
            return "Error"
    
    def _get_cpu_frequency(self):
        """Get current CPU frequency on Raspberry Pi"""
        try:
            freq_file = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'
            if os.path.exists(freq_file):
                with open(freq_file, 'r') as f:
                    freq = float(f.read().strip()) / 1000.0
                    return f"{freq:.0f} MHz"
            return "N/A"
        except Exception as e:
            print(f"[PI_OPT] Error getting CPU frequency: {e}")
            return "Error"

# Flask performance optimizations
def optimize_flask_app():
    """Return a dict of recommended Flask optimizations"""
    return {
        "threaded": True,
        "debug": False,
        "host": "0.0.0.0",
        "port": 5001
    }

# Application specific optimizations
def get_app_optimizations():
    """Get recommendations for application optimizations"""
    return {
        "reduce_update_frequency": False,
        "recommended_update_interval": 0.1,  # seconds
        "skip_frame_threshold": 100,  # ms
        "disable_widget_animations": True,
        "reduce_font_complexity": False,
        "buffer_size_reduction": 25,  # %
    } 