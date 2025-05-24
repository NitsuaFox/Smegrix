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
    '.': [0, 0, 0, 0, 0, 0, 4], # Dot for 5x7
}

# Compact 3x5 pixel font (3 wide, 5 high) - Primarily for digits
FONT_3X5 = {
    ' ': [0, 0, 0, 0, 0], # Binary: 000, 000, 000, 000, 000
    'A': [7, 5, 7, 5, 5], # Binary: 111, 101, 111, 101, 101
    'B': [6, 5, 6, 5, 6], # Binary: 110, 101, 110, 101, 110 
    'C': [7, 4, 4, 4, 7], # Binary: 111, 100, 100, 100, 111
    'D': [6, 5, 5, 5, 6], # Binary: 110, 101, 101, 101, 110 
    'E': [7, 4, 6, 4, 7], # Binary: 111, 100, 110, 100, 111
    'F': [7, 4, 6, 4, 4], # Binary: 111, 100, 110, 100, 100
    'G': [7, 4, 5, 5, 7], # Binary: 111, 100, 101, 101, 111 
    'H': [5, 5, 7, 5, 5], # Binary: 101, 101, 111, 101, 101
    'I': [7, 2, 2, 2, 7], # Binary: 111, 010, 010, 010, 111 
    'J': [1, 1, 1, 5, 7], # Binary: 001, 001, 001, 101, 111
    'K': [5, 6, 4, 6, 5], # Binary: 101, 110, 100, 110, 101 
    'L': [4, 4, 4, 4, 7], # Binary: 100, 100, 100, 100, 111
    'M': [5, 7, 7, 5, 5], # Binary: 101, 111, 111, 101, 101 
    'N': [5, 7, 7, 7, 5], # Binary: 101, 111, 111, 111, 101 
    'O': [7, 5, 5, 5, 7], # Binary: 111, 101, 101, 101, 111
    'P': [7, 5, 7, 4, 4], # Binary: 111, 101, 111, 100, 100
    'Q': [7, 5, 5, 6, 7], # Binary: 111, 101, 101, 110, 111 
    'R': [7, 5, 6, 5, 5], # Binary: 111, 101, 110, 101, 101 
    'S': [7, 4, 7, 1, 7], # Binary: 111, 100, 111, 001, 111 
    'T': [7, 2, 2, 2, 2], # Binary: 111, 010, 010, 010, 010
    'U': [5, 5, 5, 5, 7], # Binary: 101, 101, 101, 101, 111
    'V': [5, 5, 5, 2, 2], # Binary: 101, 101, 101, 010, 010 
    'W': [5, 5, 7, 7, 5], # Binary: 101, 101, 111, 111, 101 
    'X': [5, 2, 2, 2, 5], # Binary: 101, 010, 010, 010, 101 
    'Y': [5, 5, 2, 2, 2], # Binary: 101, 101, 010, 010, 010
    'Z': [7, 1, 2, 4, 7], # Binary: 111, 001, 010, 100, 111
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
    '.': [0, 0, 0, 0, 2], # Dot for 3x5 (010 on the last row)
    # Add other characters if needed, but digits and colon are primary for time
}

# Larger font: 7x9 (Width x Height) - for "Large" size
FONT_7X9 = {
    ' ': [0,0,0,0,0,0,0,0,0],
    'A': [28, 34, 65, 65, 127, 65, 65, 65, 65], 
    'B': [126, 65, 65, 126, 65, 65, 65, 65, 126],
    'C': [62, 65, 64, 64, 64, 64, 64, 65, 62],  
    'D': [126, 65, 65, 65, 65, 65, 65, 65, 126],
    'E': [127, 64, 64, 124, 64, 64, 64, 64, 127],
    'F': [127, 64, 64, 124, 64, 64, 64, 64, 64],
    'G': [62, 65, 64, 64, 79, 65, 65, 65, 62],
    'H': [65, 65, 65, 127, 65, 65, 65, 65, 65],
    'I': [62, 16, 16, 16, 16, 16, 16, 16, 62],
    'J': [2, 2, 2, 2, 2, 2, 66, 66, 60],
    'K': [65, 66, 68, 120, 68, 66, 65, 65, 65],
    'L': [64, 64, 64, 64, 64, 64, 64, 64, 127],
    'M': [65, 99, 85, 73, 65, 65, 65, 65, 65],
    'N': [65, 97, 81, 73, 69, 67, 65, 65, 65],
    'O': [62, 65, 65, 65, 65, 65, 65, 65, 62],
    'P': [126, 65, 65, 126, 64, 64, 64, 64, 64],
    'Q': [62, 65, 65, 65, 65, 81, 73, 18, 60],
    'R': [126, 65, 65, 126, 72, 68, 66, 65, 65],
    'S': [62, 65, 64, 60, 2, 1, 65, 65, 62],
    'T': [127, 16, 16, 16, 16, 16, 16, 16, 16],
    'U': [65, 65, 65, 65, 65, 65, 65, 65, 62],
    'V': [65, 65, 65, 65, 65, 65, 34, 28, 16],
    'W': [65, 65, 65, 65, 73, 85, 99, 65, 65],
    'X': [65, 65, 34, 28, 16, 28, 34, 65, 65],
    'Y': [65, 65, 34, 28, 16, 16, 16, 16, 16],
    'Z': [127, 1, 2, 4, 8, 16, 32, 64, 127],
    '0': [62, 65, 97, 97, 97, 97, 65, 65, 62],
    '1': [16, 48, 16, 16, 16, 16, 16, 16, 62],
    '2': [62, 65, 1, 1, 30, 48, 64, 64, 127],
    '3': [127, 1, 1, 62, 1, 1, 1, 65, 62],
    '4': [6, 14, 22, 38, 64, 127, 2, 2, 2],
    '5': [127, 64, 64, 126, 1, 1, 1, 65, 62],
    '6': [30, 32, 64, 64, 126, 65, 65, 65, 62],
    '7': [127, 1, 1, 2, 4, 8, 16, 16, 16],
    '8': [62, 65, 65, 62, 65, 65, 65, 65, 62],
    '9': [62, 65, 65, 65, 126, 1, 1, 1, 62],
    ':': [0,0,0,0,16,0,16,0,0],
    '.': [0,0,0,0,0,0,0,0,8] # Dot for 7x9 (0001000 on the last row)
}
DEFAULT_CHAR_BITMAP_7X9 = [127, 65, 93, 93, 93, 65, 127,0,0] # Question mark for 7x9

# Re-add missing default character bitmaps
DEFAULT_CHAR_BITMAP_5X7 = [31, 17, 21, 21, 21, 17, 31] # '?' for 5x7
DEFAULT_CHAR_BITMAP_3X5 = [7, 5, 7, 5, 7] # '8' as a fallback for 3x5, or a simple '?' like: [7,1,2,1,7]

# Extra Large Font: 9x13 (Width x Height)
FONT_9X13 = {
    ' ': [0,0,0,0,0,0,0,0,0,0,0,0,0], # 9 bits wide, 13 rows high
    # Uppercase Letters A-Z for 9x13
    # Each character is 9 pixels wide and 13 pixels high.
    # Values are hex representations of pixel rows.
    'A': [0x070, 0x0F8, 0x18C, 0x18C, 0x18C, 0x18C, 0x1FC, 0x1FC, 0x18C, 0x18C, 0x18C, 0x18C, 0x000], # .XXX.  .XXXXX. X..XX..X X..XX..X X..XX..X X..XX..X XXXXXXXX XXXXXXXX X..XX..X X..XX..X X..XX..X X..XX..X .........
    'B': [0x1FC, 0x1FC, 0x18C, 0x18C, 0x18C, 0x1F8, 0x1F8, 0x18C, 0x18C, 0x18C, 0x18C, 0x1FC, 0x1FC], # XXXXXXX XXXXXXX X..XX..X X..XX..X X..XX..X XXXXXX. XXXXXX. X..XX..X X..XX..X X..XX..X X..XX..X XXXXXXX XXXXXXX
    'C': [0x0FC, 0x0FC, 0x186, 0x186, 0x180, 0x180, 0x180, 0x180, 0x180, 0x186, 0x186, 0x0FC, 0x0FC], # .XXXXX. .XXXXX. X..X..XX X..X..XX X....... X....... X....... X....... X....... X..X..XX X..X..XX .XXXXX. .XXXXX.
    'D': [0x1F8, 0x1F8, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x1F8, 0x1F8], # XXXXXX. XXXXXX. X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X XXXXXX. XXXXXX.
    'E': [0x1FE, 0x1FE, 0x180, 0x180, 0x180, 0x1F0, 0x1F0, 0x180, 0x180, 0x180, 0x180, 0x1FE, 0x1FE], # XXXXXXX. XXXXXXX. X....... X....... X....... XXXX.... XXXX.... X....... X....... X....... X....... XXXXXXX. XXXXXXX.
    'F': [0x1FE, 0x1FE, 0x180, 0x180, 0x180, 0x1F0, 0x1F0, 0x180, 0x180, 0x180, 0x180, 0x180, 0x180], # XXXXXXX. XXXXXXX. X....... X....... X....... XXXX.... XXXX.... X....... X....... X....... X....... X....... X.......
    'G': [0x0FC, 0x0FC, 0x186, 0x186, 0x180, 0x180, 0x180, 0x19E, 0x19E, 0x186, 0x186, 0x0FE, 0x0FE], # .XXXXX. .XXXXX. X..X..XX X..X..XX X....... X....... X....... X..XXX.X X..XXX.X X..X..XX X..X..XX .XXXXXX. .XXXXXX.
    'H': [0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x1FC, 0x1FC, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C], # X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X XXXXXXXX XXXXXXXX X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X
    'I': [0x078, 0x078, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x078, 0x078], # .XXX... .XXX... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... .XXX... .XXX...
    'J': [0x00E, 0x00E, 0x006, 0x006, 0x006, 0x006, 0x006, 0x006, 0x186, 0x186, 0x186, 0x0FC, 0x0FC], # ....XXX ....XXX .....XX .....XX .....XX .....XX .....XX .....XX X..X..XX X..X..XX X..X..XX .XXXXX. .XXXXX.
    'K': [0x18C, 0x18C, 0x198, 0x1B0, 0x1E0, 0x1C0, 0x1C0, 0x1E0, 0x1B0, 0x198, 0x18C, 0x18C, 0x18C], # X..XX..X X..XX..X X..XX... X.XX.... XXX..... XX...... XX...... XXX..... X.XX.... X..XX... X..XX..X X..XX..X X..XX..X
    'L': [0x180, 0x180, 0x180, 0x180, 0x180, 0x180, 0x180, 0x180, 0x180, 0x180, 0x180, 0x1FE, 0x1FE], # X....... X....... X....... X....... X....... X....... X....... X....... X....... X....... X....... XXXXXXX. XXXXXXX.
    'M': [0x183, 0x1C7, 0x1EF, 0x1DB, 0x1DB, 0x1DB, 0x1DB, 0x183, 0x183, 0x183, 0x183, 0x183, 0x183], # X..X..XX XX.X.XXX XXXX.XXX XX.X.X.X XX.X.X.X XX.X.X.X XX.X.X.X X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX
    'N': [0x183, 0x183, 0x1C3, 0x1E3, 0x1F3, 0x1BB, 0x19B, 0x18B, 0x187, 0x183, 0x183, 0x183, 0x183], # X..X..XX X..X..XX XX..X.XX XXX.X.XX XXXX.X.X X.X.X.XX X.X.X..X X..XX.XX X..X.XXX X..X..XX X..X..XX X..X..XX X..X..XX
    'O': [0x0FC, 0x0FC, 0x186, 0x186, 0x186, 0x186, 0x186, 0x186, 0x186, 0x186, 0x186, 0x0FC, 0x0FC], # .XXXXX. .XXXXX. X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX .XXXXX. .XXXXX.
    'P': [0x1FC, 0x1FC, 0x186, 0x186, 0x186, 0x1FC, 0x1FC, 0x180, 0x180, 0x180, 0x180, 0x180, 0x180], # XXXXXXX XXXXXXX X..X..XX X..X..XX X..X..XX XXXXXXX XXXXXXX X....... X....... X....... X....... X....... X.......
    'Q': [0x0FC, 0x0FC, 0x186, 0x186, 0x186, 0x186, 0x186, 0x186, 0x1A6, 0x1E6, 0x18E, 0x0FE, 0x07C], # .XXXXX. .XXXXX. X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX X.X.X.XX XXX.X.XX X..XX.XX .XXXXXX. .XXX.XX.
    'R': [0x1FC, 0x1FC, 0x186, 0x186, 0x186, 0x1FC, 0x1FC, 0x1B0, 0x1D8, 0x1CC, 0x18E, 0x186, 0x186], # XXXXXXX XXXXXXX X..X..XX X..X..XX X..X..XX XXXXXXX XXXXXXX X.XX.... XX.XX... XXX.XX.. X..XX.XX X..X..XX X..X..XX
    'S': [0x0FE, 0x0FE, 0x180, 0x180, 0x180, 0x0F0, 0x0F0, 0x00E, 0x00E, 0x006, 0x186, 0x1FE, 0x1FE], # .XXXXXX. .XXXXXX. X....... X....... X....... .XXXX... .XXXX... ....XXX ....XXX .....XX X..X..XX XXXXXXX. XXXXXXX.
    'T': [0x1FE, 0x1FE, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030], # XXXXXXX. XXXXXXX. ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX....
    'U': [0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x0FC, 0x0FC], # X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X .XXXXX. .XXXXX.
    'V': [0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x18C, 0x0FC, 0x0FC, 0x078, 0x078, 0x030, 0x030], # X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X X..XX..X .XXXXX. .XXXXX. .XXX... .XXX... ..XX.... ..XX....
    'W': [0x183, 0x183, 0x183, 0x183, 0x183, 0x183, 0x1DB, 0x1DB, 0x1EF, 0x1EF, 0x1C7, 0x0C3, 0x000], # X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX X..X..XX XX.X.X.X XX.X.X.X XXXX.XXX XXXX.XXX XX..X.XX .X..X.XX .........
    'X': [0x18C, 0x18C, 0x18C, 0x0D8, 0x0F0, 0x070, 0x070, 0x0F0, 0x0D8, 0x18C, 0x18C, 0x18C, 0x18C], # X..XX..X X..XX..X X..XX..X .X.XX... .XXXX... ..XXX... ..XXX... .XXXX... .X.XX... X..XX..X X..XX..X X..XX..X X..XX..X
    'Y': [0x18C, 0x18C, 0x18C, 0x0D8, 0x0F0, 0x070, 0x070, 0x030, 0x030, 0x030, 0x030, 0x030, 0x030], # X..XX..X X..XX..X X..XX..X .X.XX... .XXXX... ..XXX... ..XXX... ..XX.... ..XX.... ..XX.... ..XX.... ..XX.... ..XX....
    'Z': [0x1FE, 0x1FE, 0x00C, 0x018, 0x030, 0x060, 0x0C0, 0x180, 0x180, 0x180, 0x180, 0x1FE, 0x1FE], # XXXXXXX. XXXXXXX. ....XX.. ...XX... ..XX.... .XX..... X....... X....... X....... X....... X....... XXXXXXX. XXXXXXX.
    # Updated 9x13 Digits - Bolder, 2-pixel stroke digital clock style
    '0': [0x0FE, 0x0FE, 0x183, 0x183, 0x183, 0x183, 0x183, 0x183, 0x183, 0x183, 0x183, 0x0FE, 0x0FE], # .#######. ##...## .#######.
    '1': [0x00C, 0x00C, 0x00C, 0x00C, 0x00C, 0x00C, 0x00C, 0x00C, 0x00C, 0x00C, 0x00C, 0x00C, 0x00C], # .....##.. (simple centered 2-px bar)
    '2': [0x0FE, 0x0FE, 0x003, 0x003, 0x003, 0x0FE, 0x0FE, 0x180, 0x180, 0x180, 0x180, 0x0FE, 0x0FE], # .#######. .....## .#######. ##...... .#######.
    '3': [0x0FE, 0x0FE, 0x003, 0x003, 0x003, 0x0FE, 0x0FE, 0x003, 0x003, 0x003, 0x003, 0x0FE, 0x0FE], # .#######. .....## .#######. .....## .#######.
    '4': [0x183, 0x183, 0x183, 0x183, 0x183, 0x0FE, 0x0FE, 0x003, 0x003, 0x003, 0x003, 0x003, 0x003], # ##...## .#######. .....##
    '5': [0x0FE, 0x0FE, 0x180, 0x180, 0x180, 0x0FE, 0x0FE, 0x003, 0x003, 0x003, 0x003, 0x0FE, 0x0FE], # .#######. ##...... .#######. .....## .#######.
    '6': [0x0FE, 0x0FE, 0x180, 0x180, 0x180, 0x0FE, 0x0FE, 0x183, 0x183, 0x183, 0x183, 0x0FE, 0x0FE], # .#######. ##...... .#######. ##...## .#######.
    '7': [0x0FE, 0x0FE, 0x003, 0x003, 0x003, 0x003, 0x003, 0x003, 0x003, 0x003, 0x003, 0x003, 0x003], # .#######. .....##
    '8': [0x0FE, 0x0FE, 0x183, 0x183, 0x183, 0x0FE, 0x0FE, 0x183, 0x183, 0x183, 0x183, 0x0FE, 0x0FE], # .#######. ##...## .#######. ##...## .#######.
    '9': [0x0FE, 0x0FE, 0x183, 0x183, 0x183, 0x0FE, 0x0FE, 0x003, 0x003, 0x003, 0x003, 0x0FE, 0x0FE], # .#######. ##...## .#######. .....## .#######.
    # Updated Colon and Period
    ':': [0x000, 0x000, 0x000, 0x030, 0x030, 0x000, 0x000, 0x000, 0x030, 0x030, 0x000, 0x000, 0x000], # Centered 2x2 pixel dots for colon
    '.': [0x000, 0x000, 0x000, 0x000, 0x000, 0x000, 0x000, 0x000, 0x000, 0x000, 0x000, 0x030, 0x030]  # 2x2 pixel dot at bottom-center
}
DEFAULT_CHAR_BITMAP_9X13 = [0x0F0, 0x186, 0x186, 0x006, 0x018, 0x030, 0x030, 0x030, 0x000, 0x030, 0x030, 0x000, 0x000] # Updated '?' for 9x13 (13 rows high)

# For "XL", we'll use FONT_9X13 as it is the largest defined.
FONT_XL = FONT_9X13
DEFAULT_CHAR_BITMAP_XL = DEFAULT_CHAR_BITMAP_9X13 # XL should use the 9x13 default character

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
            "xl":  {"data": FONT_XL,  "char_width": 9, "char_height": 13, "default_bitmap": DEFAULT_CHAR_BITMAP_XL} # XL uses 9x13 now via FONT_XL
        }
        self.default_font_name = "5x7" # Keep 5x7 as the default if no font is specified

    def clear(self, bg_color=DEFAULT_BG_COLOR):
        """Clears the pixel buffer by setting all existing pixels to bg_color."""
        # Iterate through the existing buffer and update pixels in place
        for r_idx in range(self.height): # Corrected variable name for clarity
            for c_idx in range(self.width): # Corrected variable name for clarity
                self.pixel_buffer[r_idx][c_idx] = bg_color

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

    def get_text_dimensions(self, text_string, font_name=None):
        """
        Calculates the dimensions (width, height) of a text string if rendered with a given font.
        Does not consider wrapping; calculates width as if on a single line.

        Args:
            text_string (str): The string to measure.
            font_name (str, optional): The name of the font to use. Defaults to self.default_font_name.

        Returns:
            tuple: (width_in_cells, height_in_cells)
        """
        selected_font_name = font_name if font_name in self.fonts else self.default_font_name
        font_info = self.fonts[selected_font_name]
        
        font_char_width = font_info["char_width"]
        font_char_height = font_info["char_height"]
        char_spacing = 1  # Standard spacing between characters used in draw_text

        if not text_string:
            return (0, font_char_height) # Height of one line, 0 width

        num_chars = len(text_string)
        
        # Total width = (num_chars * char_width) + (max(0, num_chars - 1) * char_spacing)
        # This assumes all characters in the specified font have the same 'char_width'.
        # For proportionally spaced fonts, this would need to iterate and sum individual char widths.
        # Given the current font structure, fixed width per font is assumed.
        calculated_width = (num_chars * font_char_width)
        if num_chars > 1:
            calculated_width += (num_chars - 1) * char_spacing
        
        # Ensure minimum width of 1 cell if there's any character
        calculated_width = max(1, calculated_width) if num_chars > 0 else 0

        return (calculated_width, font_char_height)

    def draw_pixel_map(self, x_offset, y_offset, pixel_map_data):
        """
        Draws a pre-rendered pixel_map onto the main display buffer.
        x_offset, y_offset: Top-left coordinates on the main display where the pixel_map should be placed.
        pixel_map_data: A 2D list (list of lists) where each inner list is a row of (R,G,B) color tuples.
        """
        if not pixel_map_data or not isinstance(pixel_map_data, list):
            return

        map_height = len(pixel_map_data)
        if map_height == 0:
            return
        
        map_width = len(pixel_map_data[0]) # Assume all rows have the same width
        if map_width == 0:
            return

        for r_idx in range(map_height):
            if r_idx + y_offset >= self.height: # Stop if map goes off bottom edge
                break
            for c_idx in range(map_width):
                if c_idx + x_offset >= self.width: # Stop if map goes off right edge for this row
                    break
                
                color_tuple = pixel_map_data[r_idx][c_idx]
                
                # Validate color_tuple before setting (copied from set_pixel)
                if not (isinstance(color_tuple, tuple) and len(color_tuple) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in color_tuple)):
                    # This case should ideally not happen if pixel_map_data is well-formed
                    # print(f"Warning: Invalid color in pixel_map at ({r_idx},{c_idx}): {color_tuple}. Skipping pixel.")
                    continue # Or set to a default error color, but skipping is safer for now

                # Direct buffer update without individual set_pixel call overhead
                self.pixel_buffer[y_offset + r_idx][x_offset + c_idx] = color_tuple

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