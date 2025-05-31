#!/usr/bin/env python3
"""
Red Channel Diagnostic Script
Specifically tests RGB channels to identify hardware/wiring issues.
"""

import time
import sys
import os

# Add the matrix library path
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/rpi-rgb-led-matrix/bindings/python')

from rgbmatrix import RGBMatrix, RGBMatrixOptions

def setup_matrix():
    """Initialize the RGB matrix with proper settings for 64x64 Adafruit Bonnet"""
    print("🔧 Setting up 64x64 RGB Matrix for channel diagnostics...")
    
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

def test_individual_channels(matrix):
    """Test each RGB channel individually at different intensities"""
    print("\n🔍 INDIVIDUAL CHANNEL DIAGNOSTICS")
    print("=" * 50)
    
    # Test different intensities for each channel
    intensities = [32, 64, 128, 255]  # Low to high brightness
    
    for intensity in intensities:
        print(f"\n--- Testing at intensity: {intensity} ---")
        
        # Test RED channel only
        print(f"🔴 Testing RED channel only at intensity {intensity}")
        canvas = matrix.CreateFrameCanvas()
        for x in range(matrix.width):
            for y in range(matrix.height):
                canvas.SetPixel(x, y, intensity, 0, 0)  # Only red
        matrix.SwapOnVSync(canvas)
        time.sleep(3.0)
        
        # Test GREEN channel only
        print(f"🟢 Testing GREEN channel only at intensity {intensity}")
        canvas = matrix.CreateFrameCanvas()
        for x in range(matrix.width):
            for y in range(matrix.height):
                canvas.SetPixel(x, y, 0, intensity, 0)  # Only green
        matrix.SwapOnVSync(canvas)
        time.sleep(3.0)
        
        # Test BLUE channel only
        print(f"🔵 Testing BLUE channel only at intensity {intensity}")
        canvas = matrix.CreateFrameCanvas()
        for x in range(matrix.width):
            for y in range(matrix.height):
                canvas.SetPixel(x, y, 0, 0, intensity)  # Only blue
        matrix.SwapOnVSync(canvas)
        time.sleep(3.0)

def test_rgb_combinations(matrix):
    """Test RGB channel combinations to see which work"""
    print("\n🌈 RGB COMBINATION DIAGNOSTICS")
    print("=" * 50)
    
    combinations = [
        (255, 0, 0, "Pure RED"),
        (0, 255, 0, "Pure GREEN"), 
        (0, 0, 255, "Pure BLUE"),
        (255, 255, 0, "RED + GREEN (should be YELLOW)"),
        (255, 0, 255, "RED + BLUE (should be MAGENTA)"),
        (0, 255, 255, "GREEN + BLUE (should be CYAN)"),
        (128, 128, 128, "Equal RGB (should be GRAY)"),
        (255, 255, 255, "All channels MAX (should be WHITE)")
    ]
    
    for r, g, b, description in combinations:
        print(f"🎨 Testing: {description} - RGB({r}, {g}, {b})")
        canvas = matrix.CreateFrameCanvas()
        for x in range(matrix.width):
            for y in range(matrix.height):
                canvas.SetPixel(x, y, r, g, b)
        matrix.SwapOnVSync(canvas)
        time.sleep(4.0)

def test_quadrant_pattern(matrix):
    """Test different channels in different quadrants"""
    print("\n📍 QUADRANT PATTERN TEST")
    print("=" * 50)
    print("🔴 Top-left: RED only")
    print("🟢 Top-right: GREEN only") 
    print("🔵 Bottom-left: BLUE only")
    print("⚪ Bottom-right: WHITE (all channels)")
    
    canvas = matrix.CreateFrameCanvas()
    
    mid_x = matrix.width // 2
    mid_y = matrix.height // 2
    
    for x in range(matrix.width):
        for y in range(matrix.height):
            if x < mid_x and y < mid_y:
                # Top-left: RED only
                canvas.SetPixel(x, y, 255, 0, 0)
            elif x >= mid_x and y < mid_y:
                # Top-right: GREEN only
                canvas.SetPixel(x, y, 0, 255, 0)
            elif x < mid_x and y >= mid_y:
                # Bottom-left: BLUE only
                canvas.SetPixel(x, y, 0, 0, 255)
            else:
                # Bottom-right: WHITE (all channels)
                canvas.SetPixel(x, y, 255, 255, 255)
    
    matrix.SwapOnVSync(canvas)
    print("⏰ Displaying quadrant pattern for 10 seconds...")
    time.sleep(10.0)

def test_rgb_sequence_variations(matrix):
    """Test different RGB sequence mappings in case that's the issue"""
    print("\n🔄 RGB SEQUENCE DIAGNOSTIC")
    print("=" * 50)
    print("Testing if RGB sequence mapping is incorrect...")
    
    # Try different RGB orders to see if channels are swapped
    sequences = [
        (255, 0, 0, "Standard RGB: RED"),
        (0, 255, 0, "Standard RGB: GREEN"),
        (0, 0, 255, "Standard RGB: BLUE"),
    ]
    
    print("If colors appear wrong, you may need --led-rgb-sequence parameter")
    print("Common alternatives: RBG, GRB, GBR, BRG, BGR")
    
    for r, g, b, description in sequences:
        print(f"Testing: {description}")
        canvas = matrix.CreateFrameCanvas()
        for x in range(matrix.width):
            for y in range(matrix.height):
                canvas.SetPixel(x, y, r, g, b)
        matrix.SwapOnVSync(canvas)
        time.sleep(4.0)

def main():
    print("🔍 RED CHANNEL DIAGNOSTIC SCRIPT")
    print("🔗 For 64x64 RGB LED Matrix with Adafruit Bonnet")
    print("=" * 60)
    print("This script will help identify RGB channel issues.")
    print("Watch the matrix and note any missing/wrong colors.")
    print("=" * 60)
    
    try:
        matrix = setup_matrix()
        
        # Run diagnostic tests
        test_individual_channels(matrix)
        test_rgb_combinations(matrix)
        test_quadrant_pattern(matrix)
        test_rgb_sequence_variations(matrix)
        
        print("\n✅ Diagnostic tests completed!")
        print("\n📋 TROUBLESHOOTING TIPS:")
        print("1. If RED appears as a different color, try --led-rgb-sequence=RBG or GRB")
        print("2. If RED is completely missing, check data cable connections")
        print("3. If RED is dim/flickering, check power supply capacity")
        print("4. If only part of matrix has RED issues, matrix may be defective")
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