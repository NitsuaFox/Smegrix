#!/usr/bin/env python3
"""
Low Power Test Script
Designed for testing with insufficient power supplies (1A-2A).
Uses very dim colors and partial patterns to stay within power limits.
"""

import time
import sys
import os

# Add the matrix library path
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/rpi-rgb-led-matrix/bindings/python')

from rgbmatrix import RGBMatrix, RGBMatrixOptions

def setup_matrix():
    """Initialize the RGB matrix with power-saving settings"""
    print("🔧 Setting up 64x64 RGB Matrix for LOW POWER operation...")
    print("⚠️  Using 1A power supply - VERY LIMITED brightness!")
    
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    options.gpio_slowdown = 4  # Higher to reduce flicker
    options.disable_hardware_pulsing = False
    
    matrix = RGBMatrix(options=options)
    print(f"✅ Matrix initialized: {matrix.width}x{matrix.height}")
    return matrix

def safe_fill_test(matrix, r, g, b, description):
    """Fill matrix with VERY dim colors safe for 1A supply"""
    print(f"🔋 Testing: {description} - RGB({r}, {g}, {b}) - SAFE for 1A")
    
    canvas = matrix.CreateFrameCanvas()
    for x in range(matrix.width):
        for y in range(matrix.height):
            canvas.SetPixel(x, y, r, g, b)
    matrix.SwapOnVSync(canvas)
    time.sleep(3.0)

def partial_pattern_test(matrix):
    """Test patterns that only light a small percentage of pixels"""
    print("\n📍 PARTIAL PATTERN TESTS (Low Power)")
    print("=" * 50)
    
    patterns = [
        ("border_only", "Border Only"),
        ("cross", "Cross Pattern"),
        ("corners", "Corner Dots"),
        ("checkerboard_sparse", "Sparse Checkerboard")
    ]
    
    for pattern_type, description in patterns:
        print(f"🎨 Testing: {description}")
        canvas = matrix.CreateFrameCanvas()
        
        if pattern_type == "border_only":
            # Only light the border
            for x in range(matrix.width):
                canvas.SetPixel(x, 0, 32, 0, 0)  # Top edge
                canvas.SetPixel(x, matrix.height-1, 32, 0, 0)  # Bottom edge
            for y in range(matrix.height):
                canvas.SetPixel(0, y, 32, 0, 0)  # Left edge
                canvas.SetPixel(matrix.width-1, y, 32, 0, 0)  # Right edge
                
        elif pattern_type == "cross":
            # Cross pattern
            mid_x = matrix.width // 2
            mid_y = matrix.height // 2
            for x in range(matrix.width):
                canvas.SetPixel(x, mid_y, 0, 32, 0)
            for y in range(matrix.height):
                canvas.SetPixel(mid_x, y, 0, 32, 0)
                
        elif pattern_type == "corners":
            # Corner dots
            canvas.SetPixel(0, 0, 64, 0, 0)
            canvas.SetPixel(matrix.width-1, 0, 0, 64, 0)
            canvas.SetPixel(0, matrix.height-1, 0, 0, 64)
            canvas.SetPixel(matrix.width-1, matrix.height-1, 64, 64, 0)
            
        elif pattern_type == "checkerboard_sparse":
            # Very sparse checkerboard (every 8th pixel)
            for y in range(0, matrix.height, 8):
                for x in range(0, matrix.width, 8):
                    if (x + y) % 16 == 0:
                        canvas.SetPixel(x, y, 16, 16, 16)
        
        matrix.SwapOnVSync(canvas)
        time.sleep(4.0)

def gradient_test_safe(matrix):
    """Test very dim gradients safe for 1A"""
    print("\n🌈 SAFE GRADIENT TESTS")
    print("=" * 50)
    
    # Very dim horizontal gradient
    print("🌈 Dim horizontal gradient (Red to Blue)")
    canvas = matrix.CreateFrameCanvas()
    for x in range(matrix.width):
        factor = x / (matrix.width - 1)
        r = int(16 * (1 - factor))  # Max 16 instead of 255
        b = int(16 * factor)
        for y in range(matrix.height):
            canvas.SetPixel(x, y, r, 0, b)
    matrix.SwapOnVSync(canvas)
    time.sleep(5.0)
    
    # Very dim vertical gradient
    print("🌈 Dim vertical gradient (Green to Yellow)")
    canvas = matrix.CreateFrameCanvas()
    for y in range(matrix.height):
        factor = y / (matrix.height - 1)
        g = int(16 * (1 - factor))
        r = int(16 * factor)
        for x in range(matrix.width):
            canvas.SetPixel(x, y, r, g, 0)
    matrix.SwapOnVSync(canvas)
    time.sleep(5.0)

def scrolling_text_safe(matrix):
    """Display scrolling text with very low power"""
    print("\n📝 SAFE SCROLLING TEXT")
    print("=" * 50)
    print("🔤 Scrolling: 'NEED 4A PSU' in dim red")
    
    # Simple pixel font for "NEED 4A PSU"
    message = "NEED 4A PSU"
    
    for offset in range(len(message) * 8 + matrix.width):
        canvas = matrix.CreateFrameCanvas()
        
        # Very simple 5x7 pixel font simulation
        char_x = matrix.width - offset
        for char in message:
            if char_x > -8 and char_x < matrix.width:
                # Draw a simple rectangle for each character
                for py in range(20, 27):  # 7 pixels high
                    for px in range(max(0, char_x), min(matrix.width, char_x + 5)):
                        if py < matrix.height:
                            canvas.SetPixel(px, py, 8, 0, 0)  # Very dim red
            char_x += 6
        
        matrix.SwapOnVSync(canvas)
        time.sleep(0.1)

def main():
    print("🔋 LOW POWER TEST SCRIPT")
    print("🔗 For 64x64 RGB LED Matrix with 1A Power Supply")
    print("=" * 60)
    print("⚠️  WARNING: Your 1A power supply is INSUFFICIENT!")
    print("⚠️  64x64 matrix needs 4A+ for full brightness")
    print("⚠️  This script uses VERY dim colors to avoid damage")
    print("=" * 60)
    print("🛒 BUY: 5V 4A or 5V 10A power supply ASAP!")
    print("🔗 Example: Adafruit 5V 4A or 5V 10A switching supply")
    print("=" * 60)
    
    try:
        matrix = setup_matrix()
        
        # Test very dim solid colors first
        print("\n🎨 VERY DIM COLOR TESTS (Safe for 1A)")
        print("=" * 50)
        
        safe_colors = [
            (16, 0, 0, "Very Dim Red"),
            (0, 16, 0, "Very Dim Green"),
            (0, 0, 16, "Very Dim Blue"),
            (8, 8, 8, "Very Dim White"),
            (8, 8, 0, "Very Dim Yellow"),
            (8, 0, 8, "Very Dim Magenta"),
            (0, 8, 8, "Very Dim Cyan")
        ]
        
        for r, g, b, name in safe_colors:
            safe_fill_test(matrix, r, g, b, name)
        
        # Test partial patterns
        partial_pattern_test(matrix)
        
        # Test safe gradients
        gradient_test_safe(matrix)
        
        # Test scrolling text
        scrolling_text_safe(matrix)
        
        print("\n✅ Low power tests completed!")
        print("\n🔌 NEXT STEPS:")
        print("1. 🛒 ORDER: 5V 4A power supply immediately")
        print("2. 🔌 BRANDS: Adafruit, Mean Well, or similar quality")
        print("3. ⚠️  AVOID: Cheap USB chargers or phone adapters")
        print("4. 🔧 CONNECTOR: Make sure it fits your bonnet's power jack")
        print("5. 🧪 RETEST: Once you have proper power, run full brightness tests")
        print("\nPress Ctrl+C to exit...")
        
        # Keep running with safe dim display
        canvas = matrix.CreateFrameCanvas()
        for x in range(matrix.width):
            for y in range(matrix.height):
                canvas.SetPixel(x, y, 4, 0, 0)  # Very dim red
        matrix.SwapOnVSync(canvas)
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        print("💡 Remember: Get a 5V 4A+ power supply!")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 