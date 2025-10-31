"""
Configuration settings for the exercise detection application.
"""
import os
from pathlib import Path

# Flask Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# MediaPipe Configuration
MIN_DETECTION_CONFIDENCE = float(os.getenv('MIN_DETECTION_CONFIDENCE', 0.5))
MIN_TRACKING_CONFIDENCE = float(os.getenv('MIN_TRACKING_CONFIDENCE', 0.5))

# Camera Configuration
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))

# Audio Configuration
AUDIO_COOLDOWN = int(os.getenv('AUDIO_COOLDOWN', 5))  # seconds between audio alerts
ERROR_DISPLAY_TIME = int(os.getenv('ERROR_DISPLAY_TIME', 3))  # seconds to display errors

# Exercise Angle Thresholds
BICEP_CURL = {
    'down_angle_min': 140,
    'up_angle_max': 35,
    'torso_angle_max': 45,
}

LATERAL_RAISES = {
    'raised_angle_min': 100,
    'lowered_angle_min': 50,
    'lowered_angle_max': 75,
}

SHOULDER_PRESS = {
    'pressing_angle_min': 150,
    'lowered_angle_min': 95,
    'lowered_angle_max': 150,
    'hands_too_low_angle_max': 80,
}

CRUNCHES = {
    'up_angle_max': 90,
    'down_angle_min': 100,
    'incorrect_form_angle_min': 120,
}

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
AUDIO_DIR = PROJECT_ROOT / "static" / "audio"

# Create audio directory if it doesn't exist
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

