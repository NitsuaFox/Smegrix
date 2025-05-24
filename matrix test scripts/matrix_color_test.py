#!/usr/bin/env python3
"""
Matrix Color and Gradient Test Script
Tests full-screen solid colors and gradients on the RGB LED matrix.
"""

import time
import sys
import os

# Add the matrix library path
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/rpi-rgb-led-matrix/bindings/python')

from rgbmatrix import RGBMatrix, RGBMatrixOptions

def setup_matrix():
    """Initialize the RGB matrix with proper settings for 64x64 Adafruit Bonnet"""
    print("🔧 Setting up 64x64 RGB Matrix...")
    
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    options.gpio_slowdown = 2
    options.disable_hardware_pulsing = False
    
    matrix = RGBMatrix(options=options)
    print(f"✅ Matrix initialized: {matrix.width}x{matrix.height}")
    return matrix

def fill_solid_color(matrix, r, g, b, color_name):
    """Fill entire matrix with a solid color"""
    print(f"🎨 Testing solid color: {color_name} (R:{r}, G:{g}, B:{b})")
    
    canvas = matrix.CreateFrameCanvas()
    
    # Fill every pixel with the specified color
    for x in range(matrix.width):
        for y in range(matrix.height):
            canvas.SetPixel(x, y, r, g, b)
    
    matrix.SwapOnVSync(canvas)
    time.sleep(2.0)  # Display for 2 seconds

def horizontal_gradient(matrix, r1, g1, b1, r2, g2, b2, gradient_name):
    """Create horizontal gradient from left to right"""
    print(f"🌈 Testing horizontal gradient: {gradient_name}")
    
    canvas = matrix.CreateFrameCanvas()
    width = matrix.width
    
    for x in range(width):
        # Calculate interpolation factor (0.0 to 1.0)
        factor = x / (width - 1)
        
        # Interpolate RGB values
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        
        # Fill column with interpolated color
        for y in range(matrix.height):
            canvas.SetPixel(x, y, r, g, b)
    
    matrix.SwapOnVSync(canvas)
    time.sleep(3.0)  # Display for 3 seconds

def vertical_gradient(matrix, r1, g1, b1, r2, g2, b2, gradient_name):
    """Create vertical gradient from top to bottom"""
    print(f"🌈 Testing vertical gradient: {gradient_name}")
    
    canvas = matrix.CreateFrameCanvas()
    height = matrix.height
    
    for y in range(height):
        # Calculate interpolation factor (0.0 to 1.0)
        factor = y / (height - 1)
        
        # Interpolate RGB values
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        
        # Fill row with interpolated color
        for x in range(matrix.width):
            canvas.SetPixel(x, y, r, g, b)
    
    matrix.SwapOnVSync(canvas)
    time.sleep(3.0)  # Display for 3 seconds

def radial_gradient(matrix, center_r, center_g, center_b, edge_r, edge_g, edge_b, gradient_name):
    """Create radial gradient from center to edges"""
    print(f"🌈 Testing radial gradient: {gradient_name}")
    
    canvas = matrix.CreateFrameCanvas()
    center_x = matrix.width // 2
    center_y = matrix.height // 2
    max_distance = ((center_x ** 2) + (center_y ** 2)) ** 0.5
    
    for x in range(matrix.width):
        for y in range(matrix.height):
            # Calculate distance from center
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            factor = min(distance / max_distance, 1.0)
            
            # Interpolate RGB values
            r = int(center_r + (edge_r - center_r) * factor)
            g = int(center_g + (edge_g - center_g) * factor)
            b = int(center_b + (edge_b - center_b) * factor)
            
            canvas.SetPixel(x, y, r, g, b)
    
    matrix.SwapOnVSync(canvas)
    time.sleep(3.0)  # Display for 3 seconds

def run_color_tests(matrix):
    """Run comprehensive color and gradient tests"""
    print("\n🚀 Starting comprehensive matrix color tests...\n")
    
    # Test solid colors
    print("=" * 50)
    print("SOLID COLOR TESTS")
    print("=" * 50)
    
    solid_colors = [
        (255, 0, 0, "Pure Red"),
        (0, 255, 0, "Pure Green"),
        (0, 0, 255, "Pure Blue"),
        (255, 255, 255, "White"),
        (255, 255, 0, "Yellow"),
        (255, 0, 255, "Magenta"),
        (0, 255, 255, "Cyan"),
        (255, 128, 0, "Orange"),
        (128, 0, 128, "Purple"),
        (0, 0, 0, "Black (off)")
    ]
    
    for r, g, b, name in solid_colors:
        fill_solid_color(matrix, r, g, b, name)
    
    # Test horizontal gradients
    print("\n" + "=" * 50)
    print("HORIZONTAL GRADIENT TESTS")
    print("=" * 50)
    
    horizontal_gradients = [
        (255, 0, 0, 0, 0, 255, "Red to Blue"),
        (0, 255, 0, 255, 255, 0, "Green to Yellow"),
        (0, 0, 0, 255, 255, 255, "Black to White"),
        (255, 0, 255, 0, 255, 255, "Magenta to Cyan")
    ]
    
    for r1, g1, b1, r2, g2, b2, name in horizontal_gradients:
        horizontal_gradient(matrix, r1, g1, b1, r2, g2, b2, name)
    
    # Test vertical gradients
    print("\n" + "=" * 50)
    print("VERTICAL GRADIENT TESTS")
    print("=" * 50)
    
    vertical_gradients = [
        (255, 0, 0, 0, 255, 0, "Red to Green (top to bottom)"),
        (0, 0, 255, 255, 255, 0, "Blue to Yellow (top to bottom)"),
        (255, 255, 255, 0, 0, 0, "White to Black (top to bottom)")
    ]
    
    for r1, g1, b1, r2, g2, b2, name in vertical_gradients:
        vertical_gradient(matrix, r1, g1, b1, r2, g2, b2, name)
    
    # Test radial gradients
    print("\n" + "=" * 50)
    print("RADIAL GRADIENT TESTS")
    print("=" * 50)
    
    radial_gradients = [
        (255, 255, 255, 255, 0, 0, "White center to Red edge"),
        (0, 0, 255, 0, 255, 0, "Blue center to Green edge"),
        (255, 255, 0, 128, 0, 128, "Yellow center to Purple edge")
    ]
    
    for center_r, center_g, center_b, edge_r, edge_g, edge_b, name in radial_gradients:
        radial_gradient(matrix, center_r, center_g, center_b, edge_r, edge_g, edge_b, name)
    
    print("\n✅ All color tests completed!")
    print("Press Ctrl+C to exit...")

def main():
    print("🎮 Matrix Color & Gradient Test Script")
    print("🔗 For 64x64 RGB LED Matrix with Adafruit Bonnet")
    print("-" * 50)
    
    try:
        matrix = setup_matrix()
        run_color_tests(matrix)
        
        # Keep running until user stops
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 