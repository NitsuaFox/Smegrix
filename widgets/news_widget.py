import datetime
import time
import feedparser # For RSS parsing
from .base_widget import BaseWidget
import requests # feedparser might use it or have its own http client

class NewsWidget(BaseWidget):
    """Displays scrolling news headlines fetched from an RSS feed."""

    DEFAULT_RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"  # BBC News top stories
    DEFAULT_UPDATE_INTERVAL_MINS = 5
    DEFAULT_NUM_HEADLINES = 5
    DEFAULT_SCROLL_INTERVAL_MS = 50 # Time in ms between 1-pixel shifts
    HEADLINE_SEPARATOR = "  •••  " 
    SCROLL_PADDING = "     " 

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
        self.current_scroll_text = ""
        self.current_pixel_offset = 0
        self.text_is_scrollable = False
        self.looping_point_pixels = 0 
        self.time_of_last_pixel_shift = time.monotonic()
        self.char_widths_cache = {} # For caching individual character widths

        self._prev_rss_url = self.rss_url
        self._prev_num_headlines = self.num_headlines

        self._fetch_news()
        self._build_and_measure_scroll_text()

    def reconfigure(self):
        super().reconfigure()
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

        if config_affecting_fetch_changed:
            self._log("INFO", "News widget fetch-related configuration changed, forcing news fetch.")
            if self._fetch_news(force_fetch=True):
                self._build_and_measure_scroll_text()
            else:
                self._build_and_measure_scroll_text()
            self.current_pixel_offset = 0
            self.time_of_last_pixel_shift = time.monotonic() # Reset timer if text content changes
        elif font_size_changed:
            self._log("INFO", "Font size changed, remeasuring scroll text & char widths.")
            self._build_and_measure_scroll_text()
            self.current_pixel_offset = 0
            self.time_of_last_pixel_shift = time.monotonic() # Reset timer if text metrics change
        elif scroll_speed_changed:
            # Only scroll speed changed, no need to remeasure, just reset timer baseline
            self.time_of_last_pixel_shift = time.monotonic()
        
        self._prev_rss_url = self.rss_url
        self._prev_num_headlines = self.num_headlines

    def _fetch_news(self, force_fetch=False):
        current_time = time.monotonic(); updated_content = False 
        if not force_fetch and self.last_fetch_time != 0 and (current_time - self.last_fetch_time) / 60 < self.update_interval_minutes: return False 
        self._log("DEBUG", f"Attempting news fetch from {self.rss_url}{' (forced)' if force_fetch else ''}") # Changed to DEBUG for less noise
        try:
            feed = feedparser.parse(self.rss_url)
            if feed.bozo: ex = feed.bozo_exception; self._log("ERROR", f"Error parsing RSS: {str(ex)}"); self.last_fetch_time = current_time; return False 
            new_h = [e.title.strip() for e in feed.entries[:self.num_headlines] if hasattr(e, 'title')]
            if self.headlines_cache != new_h: self.headlines_cache = new_h; updated_content = True
            if updated_content: self._log("INFO", f"News updated: {len(self.headlines_cache)} hdl.")
            elif force_fetch: self._log("DEBUG", "Forced fetch, no changes.") # Changed to DEBUG
            self.last_fetch_time = current_time; return updated_content
        except Exception as e: self._log("ERROR", f"RSS fetch error: {e}"); self.last_fetch_time = current_time; return False

    def _get_font_name(self):
        if self.font_size == 'small': return '3x5'
        if self.font_size == 'medium': return '5x7'
        if self.font_size == 'large': return '7x9'
        if self.font_size == 'xl': return 'xl'
        return None

    def _build_and_measure_scroll_text(self):
        if not self.headlines_cache: self.current_scroll_text = "No news available."
        else: self.current_scroll_text = self.HEADLINE_SEPARATOR.join(self.headlines_cache)
        
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
        self.current_pixel_offset = 0
        self.time_of_last_pixel_shift = time.monotonic() # Reset timer whenever text/metrics change

    def update_scroll_state(self):
        news_updated = self._fetch_news()
        if news_updated:
            self._build_and_measure_scroll_text()

        if not self.current_scroll_text: # Should have been set by init or reconfigure
             self._build_and_measure_scroll_text()

        if self.text_is_scrollable:
            current_time = time.monotonic()
            # Check if enough time has passed for at least one 1-pixel shift
            if current_time - self.time_of_last_pixel_shift >= self.scroll_interval_seconds:
                self.current_pixel_offset += 1 # Shift by exactly 1 pixel
                self.time_of_last_pixel_shift += self.scroll_interval_seconds # Advance the last shift time by one interval
                
                # If, due to a long frame, we fell behind, ensure time_of_last_pixel_shift catches up to current_time
                # to prevent a burst of shifts on the next frame.
                if self.time_of_last_pixel_shift < current_time - self.scroll_interval_seconds:
                    self.time_of_last_pixel_shift = current_time

                # Looping logic for current_pixel_offset
                if self.current_pixel_offset >= self.looping_point_pixels:
                    self.current_pixel_offset = 0 # Simple reset for 1-pixel step
        else:
            self.current_pixel_offset = 0

    def get_visible_text_segment(self) -> str:
        if not self.current_scroll_text or self.current_scroll_text == "No news available." or not self.text_is_scrollable:
            return self.current_scroll_text # Static display

        matrix_w = self.global_context.get('matrix_width', 64)
        if not self.char_widths_cache: # Should be populated by _build_and_measure_scroll_text
            self._log("ERROR", "Character width cache is empty. Cannot determine visible segment.")
            return "CacheErr"

        tape = self.current_scroll_text + self.SCROLL_PADDING + self.current_scroll_text
        visible_segment = ""
        current_segment_width = 0
        start_char_index_on_tape = 0
        pixel_offset_tracker = 0

        # 1. Find the first character on the tape that should start the visible segment
        for i, char_code in enumerate(tape):
            char = str(char_code)
            char_w = self.char_widths_cache.get(char, 0)
            if pixel_offset_tracker + char_w > self.current_pixel_offset:
                start_char_index_on_tape = i
                # The part of this char that is visible is (pixel_offset_tracker + char_w) - self.current_pixel_offset
                # However, draw_text handles clipping from left, so we just need to provide the string starting here.
                break
            pixel_offset_tracker += char_w
        else: # Should not happen if looping_point_pixels is correct and offset is managed
            start_char_index_on_tape = 0 

        # 2. Build the visible segment from this starting character
        for i in range(start_char_index_on_tape, len(tape)):
            char_to_add = tape[i]
            char_w = self.char_widths_cache.get(char_to_add, 0)
            if current_segment_width + char_w <= matrix_w:
                visible_segment += char_to_add
                current_segment_width += char_w
            else:
                break # Segment is full
        
        # If, due to large char width vs offset, first char itself is clipped, ensure something is returned if possible
        if not visible_segment and len(tape) > start_char_index_on_tape:
             first_visible_char = tape[start_char_index_on_tape]
             if self.char_widths_cache.get(first_visible_char, 0) > 0 : # Check if it has a measurable width
                  return first_visible_char # Return just the first char that should be partially visible

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