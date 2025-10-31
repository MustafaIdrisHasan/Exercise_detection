"""
Shared utility functions for exercise detection modules.
"""
import numpy as np
from pathlib import Path
import os

def calculate_angle(a, b, c):
    """
    Calculate the angle between three points.
    
    Args:
        a: First point [x, y]
        b: Middle point (vertex) [x, y]
        c: Third point [x, y]
    
    Returns:
        Angle in degrees (0-180)
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
    
    return angle

def get_audio_path(filename):
    """
    Get cross-platform path to audio files.
    
    Args:
        filename: Name of the audio file (e.g., "alert.mp3")
    
    Returns:
        Path object to the audio file
    """
    # Try multiple possible locations
    possible_paths = [
        Path("src") / "Python" / "static" / "audio" / filename,
        Path("static") / "audio" / filename,
        Path("audio") / filename,
        Path("lib") / "static" / "audio" / filename,
    ]
    
    # Also try relative to current file
    current_dir = Path(__file__).parent
    possible_paths.extend([
        current_dir / "static" / "audio" / filename,
        current_dir.parent / "src" / "Python" / "static" / "audio" / filename,
    ])
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Return the most likely path even if it doesn't exist (will raise error when used)
    return possible_paths[0]

def get_project_root():
    """
    Get the project root directory.
    
    Returns:
        Path object to project root
    """
    current_file = Path(__file__).resolve()
    # Navigate up from lib/utils.py to project root
    return current_file.parent.parent

