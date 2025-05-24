#!/usr/bin/env python3
"""
Flicker Diagnostic Script
Tests different brightness levels and GPIO settings to diagnose flickering issues.
"""

import time
import sys
import os

# Add the matrix library path
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/rpi-rgb-led-matrix/bindings/python')

from rgbmatrix import RGBMatrix, RGBMatrixOptions

def create_matrix_with_slowdown(slowdown_value):
    """Create matrix with specific GPIO slowdown value"""
    print(f"🔧 Testing with GPIO slowdown: {slowdown_value}")
    
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    options.gpio_slowdown = slowdown_value
    options.disable_hardware_pulsing = False
    
    matrix = RGBMatrix(options=options)
    return matrix

def test_brightness_levels(matrix, color_name, r, g, b):
    """Test different brightness levels for a specific color"""
    print(f"\n🎨 Testing {color_name} at different brightness levels:")
    print("💡 Watch for flickering - it should be worst at highest brightness")
    
    # Test various brightness levels
    brightness_levels = [25, 50, 75, 100, 150, 200, 255]
    
    for brightness in brightness_levels:
        # Scale RGB values by brightness percentage
        scaled_r = int((r * brightness) / 255)
        scaled_g = int((g * brightness) / 255)
        scaled_b = int((b * brightness) / 255)
        
        print(f"  🔆 Brightness {brightness}/255 - RGB({scaled_r}, {scaled_g}, {scaled_b})")
        
        canvas = matrix.CreateFrameCanvas()
        for x in range(matrix.width):
            for y in range(matrix.height):
                canvas.SetPixel(x, y, scaled_r, scaled_g, scaled_b)
        matrix.SwapOnVSync(canvas)
        time.sleep(4.0)

def test_partial_fill_patterns(matrix):
    """Test different fill percentages to correlate with power draw"""
    print("\n⚡ POWER DRAW CORRELATION TEST")
    print("=" * 50)
    print("Testing different amounts of lit pixels (correlates with power draw)")
    
    patterns = [
        (25, "25% of pixels lit"),
        (50, "50% of pixels lit"), 
        (75, "75% of pixels lit"),
        (100, "100% of pixels lit (maximum power draw)")
    ]
    
    for percentage, description in patterns:
        print(f"🔋 {description}")
        canvas = matrix.CreateFrameCanvas()
        
        total_pixels = matrix.width * matrix.height
        pixels_to_light = int((total_pixels * percentage) / 100)
        
        count = 0
        for y in range(matrix.height):
            for x in range(matrix.width):
                if count < pixels_to_light:
                    # Light pixel in red (high power draw)
                    canvas.SetPixel(x, y, 255, 0, 0)
                    count += 1
                else:
                    # Leave pixel off
                    canvas.SetPixel(x, y, 0, 0, 0)
        
        matrix.SwapOnVSync(canvas)
        time.sleep(5.0)

def test_different_slowdown_values(base_slowdown=2):
    """Test different GPIO slowdown values"""
    print("\n🐌 GPIO SLOWDOWN TESTS")
    print("=" * 50)
    print("Testing different GPIO slowdown values - higher = less flicker but slower refresh")
    
    slowdown_values = [1, 2, 3, 4, 5]
    
    for slowdown in slowdown_values:
        try:
            print(f"\n--- Testing GPIO slowdown: {slowdown} ---")
            matrix = create_matrix_with_slowdown(slowdown)
            
            # Test red at full brightness (worst case for flickering)
            print("🔴 Testing pure RED at maximum brightness")
            canvas = matrix.CreateFrameCanvas()
            for x in range(matrix.width):
                for y in range(matrix.height):
                    canvas.SetPixel(x, y, 255, 0, 0)
            matrix.SwapOnVSync(canvas)
            time.sleep(5.0)
            
            # Clean up
            del matrix
            
        except Exception as e:
            print(f"❌ Error with slowdown {slowdown}: {e}")

def test_low_power_colors(matrix):
    """Test colors that draw less power"""
    print("\n🔋 LOW POWER COLOR TESTS")
    print("=" * 50)
    print("Testing dimmer colors that should flicker less")
    
    low_power_colors = [
        (64, 0, 0, "Dim Red"),
        (0, 64, 0, "Dim Green"),
        (0, 0, 64, "Dim Blue"),
        (32, 32, 32, "Dim White"),
        (128, 64, 0, "Dim Orange"),
        (64, 0, 64, "Dim Purple")
    ]
    
    for r, g, b, name in low_power_colors:
        print(f"🎨 Testing: {name} - RGB({r}, {g}, {b})")
        canvas = matrix.CreateFrameCanvas()
        for x in range(matrix.width):
            for y in range(matrix.height):
                canvas.SetPixel(x, y, r, g, b)
        matrix.SwapOnVSync(canvas)
        time.sleep(4.0)

def main():
    print("⚡ FLICKER DIAGNOSTIC SCRIPT")
    print("🔗 For 64x64 RGB LED Matrix with Adafruit Bonnet")
    print("=" * 60)
    print("This script tests flickering issues related to:")
    print("1. Power supply capacity")
    print("2. GPIO timing settings") 
    print("3. Brightness correlation")
    print("=" * 60)
    
    # Get current power supply info
    print("\n❓ POWER SUPPLY CHECK:")
    print("What power supply are you using?")
    print("• 64x64 matrix needs 4A+ at full brightness")
    print("• Flickering at high brightness = insufficient power")
    print("• Red LEDs typically draw slightly more current")
    
    try:
        # Test with default settings first
        print(f"\n🔧 Creating matrix with default settings...")
        matrix = create_matrix_with_slowdown(2)
        
        # Run diagnostics
        test_brightness_levels(matrix, "RED", 255, 0, 0)
        test_brightness_levels(matrix, "GREEN", 0, 255, 0) 
        test_brightness_levels(matrix, "BLUE", 0, 0, 255)
        test_partial_fill_patterns(matrix)
        test_low_power_colors(matrix)
        
        # Clean up current matrix
        del matrix
        
        # Test different GPIO slowdown values
        test_different_slowdown_values()
        
        print("\n✅ Flicker diagnostic completed!")
        print("\n🔧 SOLUTIONS FOR FLICKERING:")
        print("1. 🔌 POWER SUPPLY: Use 5V 4A+ power supply")
        print("2. 🐌 GPIO SLOWDOWN: Try --led-slowdown-gpio=4 or higher")
        print("3. ⚡ REDUCE BRIGHTNESS: Use dimmer colors for less power draw")
        print("4. 🎛️ QUALITY MODE: Re-run installer with 'quality' option")
        print("5. 🔧 HARDWARE: Add capacitors near power input (advanced)")
        print("\nPress Ctrl+C to exit...")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Diagnostic stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 