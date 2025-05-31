#!/usr/bin/env python3
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time
import os

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'

# Per Adafruit docs, Raspberry Pi 4 needs a slowdown of 4
options.gpio_slowdown = 4  # For Pi 4. Use 1 for Pi 3, 0 for older Pis
options.brightness = 100  # 0-100

# Debug print
print("Initializing matrix...")
print(f"Using GPIO slowdown: {options.gpio_slowdown}")
print(f"Brightness: {options.brightness}")

try:
    # Initialize matrix
    matrix = RGBMatrix(options=options)
    print("Matrix initialized successfully.")
    
    # Create a canvas to draw on
    offscreen_canvas = matrix.CreateFrameCanvas()
    
    # Create a font - find font file using current script location as reference
    font = graphics.Font()
    font_path = "/home/pip/Smegrix/rpi-rgb-led-matrix/fonts/7x13.bdf"
    
    # If the font file doesn't exist at the specified path, try some alternatives
    if not os.path.exists(font_path):
        potential_paths = [
            "/home/pip/Smegrix/rpi-rgb-led-matrix/fonts/7x13.bdf",
            "../rpi-rgb-led-matrix/fonts/7x13.bdf",
            "rpi-rgb-led-matrix/fonts/7x13.bdf",
            "/home/pip/rpi-rgb-led-matrix/fonts/7x13.bdf"
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                font_path = path
                break
    
    print(f"Loading font from: {font_path}")
    font.LoadFont(font_path)
    
    # Create some colors
    textColor = graphics.Color(255, 255, 0)  # Yellow
    
    # Message to scroll
    text = "Smooth scrolling with 1 pixel movement - Smegrix display test"
    
    # Initial position
    pos = offscreen_canvas.width  # Start off right edge
    
    # Configure scrolling speed (smaller is faster)
    # 0.01 would be very fast, 0.1 would be slow
    scroll_speed = 0.02  # seconds per pixel movement
    
    # Debug print
    print(f"Starting smooth scroll with speed {scroll_speed}s per pixel")
    
    # Main loop
    while True:
        # Clear the canvas
        offscreen_canvas.Clear()
        
        # Draw the text at the current position
        graphics.DrawText(offscreen_canvas, font, pos, 20, textColor, text)
        
        # Display the canvas
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        
        # Move text position 1 pixel to the left
        pos -= 1
        
        # If the text has scrolled completely off to the left,
        # start over from the right
        if pos < -len(text) * 7:  # Estimate text width (7 pixels per char)
            pos = offscreen_canvas.width
            print("Restarting scroll from right edge")
        
        # Sleep for a short time to control scroll speed
        time.sleep(scroll_speed)
        
except KeyboardInterrupt:
    print("Keyboard interrupt received. Exiting...")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    print("Cleaning up...")
    if 'matrix' in locals():
        matrix.Clear()
    print("Done.") 