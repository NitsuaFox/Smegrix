# display.py

# Basic 5x7 pixel font (5 wide, 7 high)
FONT_5X7 = {
    ' ': [0, 0, 0, 0, 0, 0, 0],
    'A': [14, 17, 17, 31, 17, 17, 17],
    'B': [30, 17, 17, 30, 17, 17, 30],
    'C': [14, 17, 16, 16, 16, 17, 14],
    'D': [30, 17, 17, 17, 17, 17, 30],
    'E': [31, 16, 16, 30, 16, 16, 31],
    'F': [31, 16, 16, 30, 16, 16, 16],
    'G': [14, 17, 16, 23, 17, 17, 14],
    'H': [17, 17, 17, 31, 17, 17, 17],
    'I': [14, 4, 4, 4, 4, 4, 14],
    'J': [1, 1, 1, 1, 1, 17, 14],
    'K': [17, 18, 20, 24, 20, 18, 17],
    'L': [16, 16, 16, 16, 16, 16, 31],
    'M': [17, 27, 21, 17, 17, 17, 17],
    'N': [17, 25, 21, 19, 17, 17, 17],
    'O': [14, 17, 17, 17, 17, 17, 14],
    'P': [30, 17, 17, 30, 16, 16, 16],
    'Q': [14, 17, 17, 17, 21, 18, 15],
    'R': [30, 17, 17, 30, 20, 18, 17],
    'S': [14, 17, 16, 14, 1, 17, 14],
    'T': [31, 4, 4, 4, 4, 4, 4],
    'U': [17, 17, 17, 17, 17, 17, 14],
    'V': [17, 17, 17, 17, 17, 10, 4],
    'W': [17, 17, 17, 21, 21, 27, 17],
    'X': [17, 10, 4, 10, 17, 17, 17],
    'Y': [17, 17, 10, 4, 4, 4, 4],
    'Z': [31, 1, 2, 4, 8, 16, 31],
    ':': [0, 0, 4, 0, 4, 0, 0], # Centered single-dot colon for 5x7
    '/': [1, 2, 4, 8, 16, 0, 0],  # Forward slash
    '0': [14, 17, 19, 21, 25, 17, 14],
    '1': [4, 12, 4, 4, 4, 4, 14],
    '2': [14, 17, 1, 2, 4, 8, 31],
    '3': [31, 1, 2, 14, 1, 17, 14],
    '4': [24, 20, 18, 17, 31, 1, 1],
    '5': [31, 16, 16, 30, 1, 1, 30],
    '6': [14, 16, 16, 30, 17, 17, 14],
    '7': [31, 1, 2, 4, 8, 8, 8],
    '8': [14, 17, 17, 14, 17, 17, 14],
    '9': [14, 17, 17, 15, 1, 1, 14],
    '-': [0, 0, 0, 31, 0, 0, 0], # Dash/Minus
}

# Compact 3x5 pixel font (3 wide, 5 high) - Primarily for digits
FONT_3X5 = {
    ' ': [0, 0, 0, 0, 0],
    '0': [7, 5, 5, 5, 7], # Binary: 111, 101, 101, 101, 111
    '1': [2, 2, 2, 2, 2], # Binary: 010, 010, 010, 010, 010
    '2': [7, 1, 7, 4, 7], # Binary: 111, 001, 111, 100, 111
    '3': [7, 1, 7, 1, 7], # Binary: 111, 001, 111, 001, 111
    '4': [5, 5, 7, 1, 1], # Binary: 101, 101, 111, 001, 001
    '5': [7, 4, 7, 1, 7], # Binary: 111, 100, 111, 001, 111
    '6': [7, 4, 7, 5, 7], # Binary: 111, 100, 111, 101, 111
    '7': [7, 1, 1, 1, 1], # Binary: 111, 001, 001, 001, 001
    '8': [7, 5, 7, 5, 7], # Binary: 111, 101, 111, 101, 111
    '9': [7, 5, 7, 1, 7], # Binary: 111, 101, 111, 001, 111
    ':': [0, 2, 0, 2, 0], # Binary: 000, 010, 000, 010, 000 (Centered for 3-wide)
    # Add other characters if needed, but digits and colon are primary for time
}

# Larger font: 7x9 (Width x Height) - for "Large" size
FONT_7X9 = {
    ' ': [0, 0, 0, 0, 0, 0, 0, 0, 0], # 7 bits wide, 9 rows high
    '0': [62, 65, 97, 97, 97, 97, 65, 65, 62],  # 0111110, 1000001, 1100001, ...
    '1': [16, 48, 16, 16, 16, 16, 16, 16, 62],  # 0010000, 0110000, ...
    '2': [62, 65, 1, 1, 30, 48, 64, 64, 127],
    '3': [127, 1, 1, 62, 1, 1, 1, 65, 62],
    '4': [6, 14, 22, 38, 64, 127, 2, 2, 2],
    '5': [127, 64, 64, 126, 1, 1, 1, 65, 62],
    '6': [30, 32, 64, 64, 126, 65, 65, 65, 62],
    '7': [127, 1, 1, 2, 4, 8, 16, 16, 16],
    '8': [62, 65, 65, 62, 65, 65, 65, 65, 62],
    '9': [62, 65, 65, 65, 126, 1, 1, 1, 62],
    ':': [0, 0, 8, 0, 8, 0, 0, 0, 0] # Centered single-dot colon for 7x9 (col 3: 0001000)
}
# For "XL", we'll reuse FONT_7X9 for now. A true XL font would be even bigger.
FONT_XL = FONT_7X9 
DEFAULT_CHAR_BITMAP_7X9 = [127, 65, 93, 93, 93, 65, 127,0,0] # Question mark for 7x9
DEFAULT_CHAR_BITMAP_XL = DEFAULT_CHAR_BITMAP_7X9

# Re-add missing default character bitmaps
DEFAULT_CHAR_BITMAP_5X7 = [31, 17, 21, 21, 21, 17, 31] # '?' for 5x7
DEFAULT_CHAR_BITMAP_3X5 = [7, 5, 7, 5, 7] # '8' as a fallback for 3x5, or a simple '?' like: [7,1,2,1,7]

# Extra Large Font: 9x13 (Width x Height)
FONT_9X13 = {
    ' ': [0,0,0,0,0,0,0,0,0,0,0,0,0], # 9 bits wide, 13 rows high
    '0': [124, 258, 258, 386, 386, 386, 386, 386, 386, 386, 258, 258, 124], # 01111100, 100000010, ...
    '1': [48, 112, 112, 48, 48, 48, 48, 48, 48, 48, 48, 48, 126], # 000110000, 001110000, ...
    '2': [124, 258, 2, 2, 2, 4, 8, 16, 32, 64, 128, 258, 510],
    '3': [510, 2, 2, 2, 60, 2, 2, 2, 2, 2, 2, 258, 124],
    '4': [12, 28, 60, 108, 108, 204, 204, 510, 12, 12, 12, 12, 12],
    '5': [510, 256, 256, 256, 252, 2, 2, 2, 2, 2, 2, 258, 124],
    '6': [124, 258, 256, 256, 256, 380, 386, 386, 386, 386, 258, 258, 124],
    '7': [510, 2, 2, 4, 4, 8, 8, 16, 16, 32, 32, 32, 32],
    '8': [124, 258, 258, 258, 124, 258, 258, 258, 258, 258, 258, 258, 124],
    '9': [124, 258, 258, 386, 386, 386, 386, 254, 2, 2, 2, 258, 124],
    ':': [0,0,0,0,16,0,16,0,0,0,0,0,0] # Centered single-dot colon for 9x13 (col 4: 000010000), adjusted vertically
}
DEFAULT_CHAR_BITMAP_9X13 = [511, 257, 377, 377, 345, 313, 257, 511,0,0,0,0,0] # Placeholder '?' for 9x13

DEFAULT_BG_COLOR = (0, 0, 0) # Black
DEFAULT_FG_COLOR = (255, 255, 255) # White

class Display:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pixel_buffer = [[DEFAULT_BG_COLOR for _ in range(width)] for _ in range(height)]
        
        self.fonts = {
            "5x7": {"data": FONT_5X7, "char_width": 5, "char_height": 7, "default_bitmap": DEFAULT_CHAR_BITMAP_5X7},
            "3x5": {"data": FONT_3X5, "char_width": 3, "char_height": 5, "default_bitmap": DEFAULT_CHAR_BITMAP_3X5},
            "7x9": {"data": FONT_7X9, "char_width": 7, "char_height": 9, "default_bitmap": DEFAULT_CHAR_BITMAP_7X9},
            "xl":  {"data": FONT_XL,  "char_width": 9, "char_height": 13, "default_bitmap": DEFAULT_CHAR_BITMAP_XL} # XL uses 9x13 now
        }
        self.default_font_name = "5x7" # Keep 5x7 as the default if no font is specified

    def clear(self, bg_color=DEFAULT_BG_COLOR):
        """Clears the pixel buffer (sets all pixels to bg_color)."""
        self.pixel_buffer = [[bg_color for _ in range(self.width)] for _ in range(self.height)]

    def set_pixel(self, x, y, color_tuple):
        """
        Sets a single pixel in the buffer.
        (x, y) are coordinates, color_tuple is an (R, G, B) tuple.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            if not (isinstance(color_tuple, tuple) and len(color_tuple) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in color_tuple)):
                color_tuple = DEFAULT_FG_COLOR 
            self.pixel_buffer[y][x] = color_tuple

    def draw_text(self, text_string, x_start, y_start, color_tuple=DEFAULT_FG_COLOR, font_name=None):
        """
        Draws text onto the pixel_buffer.
        text_string: The string to draw.
        x_start, y_start: Top-left coordinates to start drawing the text.
        color_tuple: The (R, G, B) tuple for the text color.
        font_name: The name of the font to use (e.g., "5x7", "3x5"). Defaults to self.default_font_name.
        """
        current_x = x_start
        current_y = y_start

        selected_font_name = font_name if font_name in self.fonts else self.default_font_name
        font_info = self.fonts[selected_font_name]
        font_data = font_info["data"]
        font_width = font_info["char_width"]
        font_height = font_info["char_height"]
        default_char_bitmap = font_info["default_bitmap"]
        char_spacing = 1 # Space between characters

        if not (isinstance(color_tuple, tuple) and len(color_tuple) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in color_tuple)):
            color_tuple = DEFAULT_FG_COLOR

        for char_code in text_string.upper(): # Fonts defined with uppercase keys
            char_bitmap = font_data.get(char_code, default_char_bitmap)

            if current_x + font_width > self.width: # Basic word wrap (char level)
                current_x = x_start
                current_y += font_height + char_spacing # Move to next line

            if current_y + font_height > self.height: # Stop if text goes off screen
                return 

            for y_offset, row_pixels in enumerate(char_bitmap):
                # Ensure row_pixels is an integer for bitwise operations
                if not isinstance(row_pixels, int):
                    # print(f"Warning: row_pixels for char '{char_code}' in font '{selected_font_name}' is not an int: {row_pixels}")
                    continue # Skip this row or character if data is malformed

                for x_offset in range(font_width):
                    # Shift bits from left to right. FONT_5x7 uses 0-4 for 5 bits, FONT_3X5 uses 0-2 for 3 bits.
                    if (row_pixels >> (font_width - 1 - x_offset)) & 1: 
                        self.set_pixel(current_x + x_offset, current_y + y_offset, color_tuple)
            
            current_x += font_width + char_spacing

    def get_buffer(self):
        """
        Returns the current pixel buffer.
        Each pixel is an (R, G, B) tuple.
        """
        return self.pixel_buffer

if __name__ == '__main__':
    test_display = Display(width=64, height=32)
    test_display.clear()
    
    red = (255, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    yellow = (255, 255, 0)

    test_display.draw_text("HELLO", 1, 1, red)
    test_display.draw_text("WORLD!", 1, 10, green) 
    test_display.draw_text("RGB", 1, 19, blue)
    test_display.draw_text("DATE:24/07", 1, 28, yellow)

    buffer = test_display.get_buffer()
    print(f"Testing Display class ({test_display.width}x{test_display.height}) with colors:")
    for r_idx, r_val in enumerate(buffer):
        if r_idx >= test_display.height : break
        row_str_simple = ""
        for c_idx, c_val_tuple in enumerate(r_val):
            if c_idx >= test_display.width : break
            # Simple representation: # if not background, . if background
            row_str_simple += "#" if c_val_tuple != DEFAULT_BG_COLOR else "."
        print(f"{r_idx:02d}: {row_str_simple}")
    
    # print("\nPixel (1,1) color:", buffer[1][1]) # Should be red for 'H'
    # print("Pixel (0,0) color:", buffer[0][0]) # Should be background