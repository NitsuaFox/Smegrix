import time
import threading
import json
import os
from collections import deque

class PerformanceOptimizer:
    def __init__(self, log_file="performance_log.json", log_size=1000, performance_threshold_ms=50):
        self.log_file = log_file
        self.log_size = log_size  # Maximum number of entries to keep in memory
        self.performance_threshold_ms = performance_threshold_ms  # Warning threshold in ms
        self.performance_log = deque(maxlen=log_size)
        self.lock = threading.Lock()
        self.timing_data = {}
        self.enabled = True
        
        # Load existing log if available
        self._load_log()
        
        # Debug settings that can be adjusted
        self.settings = {
            "skip_frame_rendering": False,
            "reduce_update_frequency": False,
            "update_interval_multiplier": 20.0,  # MODIFIED - Increased interval
            "disable_animations": False,
            "minimize_logging": True,
            "log_settings_updates": False,  # Disable settings update logs
        }
        
        print(f"[PERF] Performance optimizer initialized with threshold: {performance_threshold_ms}ms")
    
    def _load_log(self):
        """Load existing performance log if available"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.performance_log = deque(data[-self.log_size:], maxlen=self.log_size)
                        print(f"[PERF] Loaded {len(self.performance_log)} performance log entries")
            except Exception as e:
                print(f"[PERF] Error loading performance log: {e}")
    
    def save_log(self):
        """Save performance log to file"""
        with self.lock:
            try:
                with open(self.log_file, 'w') as f:
                    json.dump(list(self.performance_log), f)
            except Exception as e:
                print(f"[PERF] Error saving performance log: {e}")
    
    def start_timer(self, section_name):
        """Start timing a section of code"""
        if not self.enabled:
            return
            
        self.timing_data[section_name] = time.monotonic()
    
    def end_timer(self, section_name, log=True):
        """End timing a section of code and optionally log results"""
        if not self.enabled or section_name not in self.timing_data:
            return 0
        
        duration_ms = (time.monotonic() - self.timing_data[section_name]) * 1000
        
        if log:
            exceeded = duration_ms > self.performance_threshold_ms
            
            # Only log if it exceeded threshold and minimize_logging is False
            if exceeded and not self.settings["minimize_logging"]:
                print(f"[PERF] {section_name}: {duration_ms:.2f}ms (SLOW)")
            
            with self.lock:
                self.performance_log.append({
                    "timestamp": time.time(),
                    "section": section_name,
                    "duration_ms": duration_ms,
                    "exceeded_threshold": exceeded
                })
        
        del self.timing_data[section_name]
        return duration_ms
    
    def should_skip_frame(self):
        """Determine if we should skip rendering this frame to catch up"""
        if not self.enabled:
            return False
            
        return self.settings["skip_frame_rendering"]
    
    def get_update_interval(self, original_interval):
        """Get potentially adjusted update interval based on performance settings"""
        if not self.enabled or not self.settings["reduce_update_frequency"]:
            return original_interval
            
        return original_interval * self.settings["update_interval_multiplier"]
    
    def should_disable_animations(self):
        """Check if animations should be disabled for better performance"""
        if not self.enabled:
            return False
            
        return self.settings["disable_animations"]
    
    def get_performance_summary(self):
        """Get a summary of performance data"""
        with self.lock:
            if not self.performance_log:
                return {"message": "No performance data collected yet"}
                
            total_entries = len(self.performance_log)
            exceeded_count = sum(1 for entry in self.performance_log if entry.get("exceeded_threshold", False))
            
            by_section = {}
            for entry in self.performance_log:
                section = entry.get("section", "unknown")
                if section not in by_section:
                    by_section[section] = {
                        "count": 0,
                        "total_ms": 0,
                        "max_ms": 0,
                        "exceeded_count": 0
                    }
                
                by_section[section]["count"] += 1
                by_section[section]["total_ms"] += entry.get("duration_ms", 0)
                by_section[section]["max_ms"] = max(by_section[section]["max_ms"], entry.get("duration_ms", 0))
                if entry.get("exceeded_threshold", False):
                    by_section[section]["exceeded_count"] += 1
            
            # Calculate averages
            for section, data in by_section.items():
                data["avg_ms"] = data["total_ms"] / data["count"] if data["count"] > 0 else 0
                data["exceed_percent"] = (data["exceeded_count"] / data["count"] * 100) if data["count"] > 0 else 0
            
            # Sort sections by average time (descending)
            sorted_sections = sorted(by_section.items(), key=lambda x: x[1]["avg_ms"], reverse=True)
            
            return {
                "total_entries": total_entries,
                "exceeded_threshold_count": exceeded_count,
                "exceeded_percent": (exceeded_count / total_entries * 100) if total_entries > 0 else 0,
                "sections": dict(sorted_sections)
            }

    def update_settings(self, new_settings):
        """Update optimization settings"""
        if not isinstance(new_settings, dict):
            return False
            
        for key, value in new_settings.items():
            if key in self.settings:
                self.settings[key] = value
                
        # Only print settings update if log_settings_updates is enabled
        if self.settings.get("log_settings_updates", False):
            print(f"[PERF] Settings updated: {self.settings}")
        return True
        
    def get_settings(self):
        """Get current optimization settings"""
        return self.settings

# Global instance
optimizer = PerformanceOptimizer() 