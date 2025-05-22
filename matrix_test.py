#!/usr/bin/env python3
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import time

print("Matrix test script started.")

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1  # This is 1 for a single bonnet

# IMPORTANT: For Adafruit Bonnet/HAT:
options.hardware_mapping = 'adafruit-hat'
# If you experience flicker, and have done the hardware mod (connecting GPIO4 to GPIO18 on the bonnet),
# you can try 'adafruit-hat-pwm'. Start with 'adafruit-hat' first.

# Per Adafruit docs, Raspberry Pi 4 needs a slowdown of 4
options.gpio_slowdown = 4  # For Pi 4. Use 1 for Pi 3, 0 for older Pis
print(f"Using GPIO slowdown: {options.gpio_slowdown}")

# Other options you might need to experiment with if you have issues:
# options.pwm_lsb_nanoseconds = 130  # Default is 130. Higher values for less ghosting, lower for higher refresh rate.
options.brightness = 100  # 0-100
# options.scan_mode = 0  # 0 for progressive, 1 for interlaced
# options.drop_privileges = True  # Recommended to keep True

print(f"Initializing matrix with options: rows={options.rows}, cols={options.cols}, mapping={options.hardware_mapping}")

try:
    matrix = RGBMatrix(options=options)
    print("Matrix initialized successfully.")
except Exception as e:
    print(f"Error initializing matrix: {e}")
    print("Please ensure the script is run with sudo (sudo python3 matrix_test.py) if not already.")
    print("Also check your wiring and power supply.")
    exit(1)

try:
    print("Starting display test. Press CTRL-C to stop.")

    # Create an offscreen canvas. This is good practice for smoother animations.
    offscreen_canvas = matrix.CreateFrameCanvas()

    # Example 1: Draw a single white pixel at (0,0)
    print("Drawing a single white pixel at (0,0) for 5 seconds...")
    offscreen_canvas.Clear()  # Clear previous content
    offscreen_canvas.SetPixel(0, 0, 255, 255, 255)  # x, y, R, G, B
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)  # Display the canvas
    time.sleep(5)

    # Example 2: Fill the screen with red
    print("Filling screen with RED for 5 seconds...")
    offscreen_canvas.Clear()
    for y in range(options.rows):
        for x in range(options.cols):
            offscreen_canvas.SetPixel(x, y, 255, 0, 0)  # R, G, B
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    print("Screen should be RED.")
    time.sleep(5)

    # Example 3: Fill the screen with green
    print("Filling screen with GREEN for 5 seconds...")
    offscreen_canvas.Clear()
    for y in range(options.rows):
        for x in range(options.cols):
            offscreen_canvas.SetPixel(x, y, 0, 255, 0)  # R, G, B
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    print("Screen should be GREEN.")
    time.sleep(5)

    # Example 4: Fill the screen with blue
    print("Filling screen with BLUE for 5 seconds...")
    offscreen_canvas.Clear()
    for y in range(options.rows):
        for x in range(options.cols):
            offscreen_canvas.SetPixel(x, y, 0, 0, 255)  # R, G, B
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    print("Screen should be BLUE.")
    time.sleep(5)

    # Example 5: Horizontal scrolling bar
    print("Showing scrolling horizontal bar...")
    for i in range(10):  # Repeat 10 times
        offscreen_canvas.Clear()
        # Draw a horizontal bar that moves down
        bar_pos = i % options.rows
        for x in range(options.cols):
            offscreen_canvas.SetPixel(x, bar_pos, 255, 255, 0)  # Yellow bar
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        time.sleep(0.1)

    print("Test sequence finished.")

except KeyboardInterrupt:
    print("Exiting due to CTRL-C.")
except Exception as e:
    print(f"An error occurred during the display test: {e}")
finally:
    print("Clearing matrix and exiting.")
    if 'matrix' in locals():  # Ensure matrix was initialized
        matrix.Clear()  # Clear the display before exiting 