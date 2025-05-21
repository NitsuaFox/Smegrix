import datetime
import time
import feedparser # For RSS parsing
from .base_widget import BaseWidget
import requests # feedparser might use it or have its own http client
import threading # Added for background fetching

class NewsWidget(BaseWidget):
    """Displays scrolling news headlines fetched from an RSS feed."""

    DEFAULT_RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"  # BBC News top stories
    DEFAULT_UPDATE_INTERVAL_MINS = 5
    DEFAULT_NUM_HEADLINES = 5
    DEFAULT_SCROLL_INTERVAL_MS = 50 # Time in ms between 1-pixel shifts
    HEADLINE_SEPARATOR = "  •••  " 
    SCROLL_PADDING = "     " 
    INITIAL_LOADING_MESSAGE = "Loading news..."

    def __init__(self, config: dict, global_context: dict = None):
        super().__init__(config, global_context)
        
        self.rss_url = self.config.get('rss_url', self.DEFAULT_RSS_URL)
        self.update_interval_minutes = self.config.get('update_interval_minutes', self.DEFAULT_UPDATE_INTERVAL_MINS)
        self.num_headlines = self.config.get('num_headlines', self.DEFAULT_NUM_HEADLINES)
        self.font_size = self.config.get('font_size', "medium")
        self.scroll_interval_ms = self.config.get('scroll_interval_ms', self.DEFAULT_SCROLL_INTERVAL_MS)
        self.scroll_interval_seconds = self.scroll_interval_ms / 1000.0

        self.headlines_cache = []
        self.last_fetch_time = 0
        self.current_scroll_text = self.INITIAL_LOADING_MESSAGE # Initial state
        self.current_pixel_offset = 0
        self.text_is_scrollable = False
        self.looping_point_pixels = 0 
        self.time_of_last_pixel_shift = time.monotonic()
        self.char_widths_cache = {} # For caching individual character widths

        # Threading attributes
        self.data_lock = threading.Lock()
        self.is_fetching = False
        self.fetch_thread = None
        
        self._prev_rss_url = self.rss_url
        self._prev_num_headlines = self.num_headlines

        # Initial fetch and build
        self._trigger_fetch_if_needed(force_fetch=True) # Start initial fetch
        self._build_and_measure_scroll_text() # Build with loading/empty message initially

    def reconfigure(self):
        super().reconfigure()
        
        with self.data_lock: # Protect config reads and state changes
            old_rss_url = self.rss_url 
            old_num_headlines = self.num_headlines
            old_font_size = self.font_size
            old_scroll_interval_ms = self.scroll_interval_ms

            self.rss_url = self.config.get('rss_url', self.DEFAULT_RSS_URL)
            self.update_interval_minutes = self.config.get('update_interval_minutes', self.DEFAULT_UPDATE_INTERVAL_MINS)
            self.num_headlines = self.config.get('num_headlines', self.DEFAULT_NUM_HEADLINES)
            self.font_size = self.config.get('font_size', "medium")
            self.scroll_interval_ms = self.config.get('scroll_interval_ms', self.DEFAULT_SCROLL_INTERVAL_MS)
            self.scroll_interval_seconds = self.scroll_interval_ms / 1000.0

            config_affecting_fetch_changed = (old_rss_url != self.rss_url or old_num_headlines != self.num_headlines)
            font_size_changed = old_font_size != self.font_size
            scroll_speed_changed = old_scroll_interval_ms != self.scroll_interval_ms

            rebuild_text_and_reset_scroll = False

            if config_affecting_fetch_changed:
                self._log("INFO", "News widget fetch-related configuration changed.")
                self._trigger_fetch_if_needed(force_fetch=True)
                rebuild_text_and_reset_scroll = True 
            
            if font_size_changed: # If only font size changed, or also if fetch config changed
                self._log("INFO", "Font size changed for news widget.")
                rebuild_text_and_reset_scroll = True

            if rebuild_text_and_reset_scroll:
                # Always rebuild. If fetching, it will use current cache (or loading message).
                # When fetch completes, update_scroll_state will rebuild again if data changed.
                self._build_and_measure_scroll_text() 
                self.current_pixel_offset = 0
                self.time_of_last_pixel_shift = time.monotonic()
            elif scroll_speed_changed:
                self.time_of_last_pixel_shift = time.monotonic()
            
            self._prev_rss_url = self.rss_url
            self._prev_num_headlines = self.num_headlines


    def _fetch_news_background(self):
        """Fetches news data in a background thread and updates cache."""
        local_rss_url = self.rss_url # Use consistent value for this fetch run
        local_num_headlines = self.num_headlines

        self._log("DEBUG", f"Background news fetch started for {local_rss_url}")
        
        new_headlines = []
        fetch_error = None
        try:
            # It's important that feedparser's underlying socket operations have timeouts.
            # feedparser.parse itself doesn't take a direct timeout argument.
            # Default timeouts in urllib (often used by feedparser) can be long.
            # Consider adding a requests wrapper with explicit timeout if feedparser is too slow.
            feed = feedparser.parse(local_rss_url) 
            if feed.bozo:
                fetch_error = f"Error parsing RSS: {str(feed.bozo_exception)}"
            else:
                new_headlines = [e.title.strip() for e in feed.entries[:local_num_headlines] if hasattr(e, 'title')]
        except Exception as e:
            fetch_error = f"RSS fetch exception: {e}"
        
        with self.data_lock:
            if fetch_error:
                self._log("ERROR", fetch_error)
                # Potentially set a status like "Fetch Error" if headlines_cache is empty
                if not self.headlines_cache:
                    self.headlines_cache = ["Error fetching news."] 
            elif self.headlines_cache != new_headlines:
                self.headlines_cache = new_headlines
                if not self.headlines_cache: # If fetch was successful but returned no headlines
                    self.headlines_cache = ["No news headlines found."]
                self._log("INFO", f"News cache updated with {len(self.headlines_cache)} headlines.")
                # Data changed, so next get_content will trigger a rebuild of scroll text
            else:
                self._log("DEBUG", "Background news fetch complete, no changes to headlines.")

            self.last_fetch_time = time.monotonic()
            self.is_fetching = False
            # After fetch, text might need rebuilding, this will be handled by update_scroll_state
            # calling _build_and_measure_scroll_text if news_updated_flag is set by _trigger_fetch_if_needed


    def _trigger_fetch_if_needed(self, force_fetch=False) -> bool:
        """
        Checks if a news fetch is required based on time or force_fetch.
        If so, and not already fetching, starts a background fetch.
        Returns True if new data was fetched or fetch was initiated, False otherwise.
        This version doesn't directly return if data *changed*, but if a fetch *process* occurred.
        The actual data change is handled by _fetch_news_background updating headlines_cache.
        """
        current_time = time.monotonic()
        news_fetch_initiated_or_needed = False

        with self.data_lock:
            time_to_fetch = (self.last_fetch_time == 0) or \
                            ((current_time - self.last_fetch_time) / 60 >= self.update_interval_minutes)

            if (force_fetch or time_to_fetch) and not self.is_fetching:
                self.is_fetching = True
                news_fetch_initiated_or_needed = True
                self._log("INFO", f"Starting background news fetch for {self.widget_id} (URL: {self.rss_url}). Force: {force_fetch}")
                
                # Ensure previous thread is not left hanging if any, though unlikely
                if self.fetch_thread and self.fetch_thread.is_alive():
                    self._log("WARNING", "Previous fetch thread still alive. This shouldn't normally happen.")
                
                self.fetch_thread = threading.Thread(target=self._fetch_news_background)
                self.fetch_thread.daemon = True
                self.fetch_thread.start()
            elif self.is_fetching:
                self._log("DEBUG", "News fetch already in progress.")
            
        return news_fetch_initiated_or_needed


    def _get_font_name(self):
        if self.font_size == 'small': return '3x5'
        if self.font_size == 'medium': return '5x7'
        if self.font_size == 'large': return '7x9'
        if self.font_size == 'xl': return 'xl'
        return None

    def _build_and_measure_scroll_text(self):
        with self.data_lock: # Protect access to headlines_cache
            if not self.headlines_cache:
                self.current_scroll_text = self.INITIAL_LOADING_MESSAGE if self.is_fetching or self.last_fetch_time == 0 else "No news available."
            else:
                self.current_scroll_text = self.HEADLINE_SEPARATOR.join(self.headlines_cache)
        
        get_dims = self.global_context.get('get_text_dimensions')
        matrix_w = self.global_context.get('matrix_width', 64)
        font = self._get_font_name()
        self.char_widths_cache = {} # Clear old cache

        if not get_dims or not font: 
            self.text_is_scrollable = False; self.looping_point_pixels = 0; return

        # Populate char_widths_cache for all unique chars in the current scroll text + padding
        unique_chars = set(self.current_scroll_text + self.SCROLL_PADDING)
        for char_code in unique_chars:
            char = str(char_code) # Ensure it is a string
            if char not in self.char_widths_cache:
                char_w, _ = get_dims(char, font)
                self.char_widths_cache[char] = char_w

        base_w = sum(self.char_widths_cache.get(c, 0) for c in self.current_scroll_text)
        
        if base_w > matrix_w: 
            self.text_is_scrollable = True
            text_with_padding_width = sum(self.char_widths_cache.get(c, 0) for c in (self.current_scroll_text + self.SCROLL_PADDING))
            self.looping_point_pixels = text_with_padding_width
        else: 
            self.text_is_scrollable = False
            self.looping_point_pixels = base_w # Not scrolling, its own width is its boundary

    def update_scroll_state(self):
        # Check if a fetch is needed (e.g. interval passed)
        # This also handles the case where a fetch completed and headlines_cache might have changed.
        # We need a way to know if _fetch_news_background resulted in *new* data
        # to trigger _build_and_measure_scroll_text.
        # Let's simplify: _trigger_fetch_if_needed starts the fetch.
        # _build_and_measure_scroll_text will use the latest headlines_cache.
        # The key is to call _build_and_measure_scroll_text if headlines_cache could have changed.
        # The background thread updates headlines_cache.
        # So, if a fetch was running, assume it might have changed, or check a flag.
        
        # Store current text to see if it changes after potential fetch and rebuild
        prev_scroll_text = self.current_scroll_text
        
        # Try to fetch new data if interval has passed
        self._trigger_fetch_if_needed() 

        # Always rebuild text, as headlines_cache might have been updated by the background thread.
        # Or, only rebuild if a fetch was recently completed.
        # For now, let's always rebuild to ensure consistency after potential background update.
        # This could be optimized by a flag set by the background thread.
        self._build_and_measure_scroll_text()

        if prev_scroll_text != self.current_scroll_text:
            self._log("DEBUG", "News scroll text changed, resetting scroll offset.")
            self.current_pixel_offset = 0
            self.time_of_last_pixel_shift = time.monotonic()


        if self.text_is_scrollable:
            current_time = time.monotonic()
            if current_time - self.time_of_last_pixel_shift >= self.scroll_interval_seconds:
                self.current_pixel_offset += 1 
                self.time_of_last_pixel_shift += self.scroll_interval_seconds 
                if self.time_of_last_pixel_shift < current_time - self.scroll_interval_seconds:
                    self.time_of_last_pixel_shift = current_time
                if self.current_pixel_offset >= self.looping_point_pixels:
                    self.current_pixel_offset = 0 
        else:
            self.current_pixel_offset = 0

    def get_visible_text_segment(self) -> str:
        if not self.current_scroll_text or self.current_scroll_text == self.INITIAL_LOADING_MESSAGE or not self.text_is_scrollable:
            return self.current_scroll_text 

        matrix_w = self.global_context.get('matrix_width', 64)
        if not self.char_widths_cache: 
            self._log("ERROR", "Character width cache is empty. Cannot determine visible segment.")
            return "CacheErr"

        tape = self.current_scroll_text + self.SCROLL_PADDING + self.current_scroll_text
        visible_segment = ""
        current_segment_width = 0
        start_char_index_on_tape = 0
        pixel_offset_tracker = 0

        for i, char_code in enumerate(tape):
            char = str(char_code)
            char_w = self.char_widths_cache.get(char, 0)
            if pixel_offset_tracker + char_w > self.current_pixel_offset:
                start_char_index_on_tape = i
                break
            pixel_offset_tracker += char_w
        else: 
            start_char_index_on_tape = 0 

        for i in range(start_char_index_on_tape, len(tape)):
            char_to_add = tape[i]
            char_w = self.char_widths_cache.get(char_to_add, 0)
            if current_segment_width + char_w <= matrix_w:
                visible_segment += char_to_add
                current_segment_width += char_w
            else:
                break 
        
        if not visible_segment and len(tape) > start_char_index_on_tape:
             first_visible_char = tape[start_char_index_on_tape]
             if self.char_widths_cache.get(first_visible_char, 0) > 0 : 
                  return first_visible_char 

        return visible_segment

    # BaseWidget compliance
    def get_content(self) -> str:
        self.update_scroll_state() # Ensure state is updated
        return self.get_visible_text_segment()

    @staticmethod
    def get_config_options() -> list:
        options = BaseWidget.get_config_options()
        options.extend([
            { 'name': 'rss_url', 'label': 'RSS Feed URL', 'type': 'text', 'default': NewsWidget.DEFAULT_RSS_URL },
            { 'name': 'update_interval_minutes', 'label': 'Update Interval (minutes)', 'type': 'number', 'default': NewsWidget.DEFAULT_UPDATE_INTERVAL_MINS, 'min': 1 },
            { 'name': 'num_headlines', 'label': 'Number of Headlines', 'type': 'number', 'default': NewsWidget.DEFAULT_NUM_HEADLINES, 'min': 1, 'max': 20 },
            { 'name': 'scroll_interval_ms', 'label': 'Scroll Interval (ms per 1px shift)', 'type': 'number', 'default': NewsWidget.DEFAULT_SCROLL_INTERVAL_MS, 'min': 10, 'max': 500,
              'description': 'Time between 1-pixel shifts. Lower is faster. E.g., 50ms = 20px/sec.' },
            { 'name': 'font_size', 'label': 'Font Size', 'type': 'select', 'default': 'medium', 'options': [
                {'value': 'small', 'label': 'Small (3x5)'}, {'value': 'medium', 'label': 'Medium (5x7)'},
                {'value': 'large', 'label': 'Large (7x9)'}, {'value': 'xl', 'label': 'Extra Large (9x13)'}
            ] }
        ])
        return options 