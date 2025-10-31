"""
Bicep Curl Exercise Detection Module.
Uses MediaPipe pose estimation to detect and count bicep curl repetitions.
"""
import cv2
import mediapipe as mp
import pygame
import threading
import time
import logging
import config
import utils

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Initialize pygame mixer
pygame.mixer.init()

# Load audio files using cross-platform paths
try:
    alert_sound = pygame.mixer.Sound(str(utils.get_audio_path("alert.mp3")))
    notinframe_sound = pygame.mixer.Sound(str(utils.get_audio_path("notinframe.mp3")))
except Exception as e:
    logger.warning(f"Could not load audio files: {e}. Audio feedback will be disabled.")
    alert_sound = None
    notinframe_sound = None


def play_audio(sound):
    """Play audio alert in a separate thread."""
    if sound:
        try:
            sound.play()
        except Exception as e:
            logger.warning(f"Error playing audio: {e}")

def bicep_curl_detection():
    """
    Bicep Curl Detection function.
    Detects and counts bicep curl repetitions using pose estimation.
    """
    try:
        # Initialize webcam using config
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not cap.isOpened():
            logger.error(f"Could not open camera {config.CAMERA_INDEX}")
            return

        # Bicep CURL counter variables
        counter = 0
        stage = None

        # Timing for audio triggers and error display
        last_alert_time = 0
        last_notinframe_time = 0
        alert_cooldown = config.AUDIO_COOLDOWN
        error_display_time = config.ERROR_DISPLAY_TIME

        # To keep track of when to stop displaying the error
        show_hands_too_high = False
        show_notinframe = False
        error_end_time_hands_too_high = 0
        error_end_time_notinframe = 0

        # Create a named window
        cv2.namedWindow('Bicep Curl Detection', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('Bicep Curl Detection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Setup MediaPipe instance using config
        with mp_pose.Pose(
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        ) as pose:
            while cap.isOpened():
                ret, frame = cap.read()
                frame = cv2.flip(frame, 1)
                if not ret:
                    break

                # Recolor image to RGB
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False

                # Make detection
                results = pose.process(image)

                # Recolor back to BGR
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                current_time = time.time()

                # Check if landmarks are detected
                if results.pose_landmarks:
                    # Extract landmarks
                    try:
                    landmarks = results.pose_landmarks.landmark
                    
                    shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    shoulder_r = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    elbow_l = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    elbow_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                    wrist_l = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    wrist_r = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]

                    # Calculate angles for both arms using shared utility
                    angle_l = utils.calculate_angle(shoulder_l, elbow_l, wrist_l)
                    angle_r = utils.calculate_angle(shoulder_r, elbow_r, wrist_r)
                    angle_l_e = utils.calculate_angle(shoulder_l, elbow_l, wrist_l)
                    angle_r_e = utils.calculate_angle(shoulder_r, elbow_r, wrist_r)
                    angle_l_h = utils.calculate_angle(hip_l, shoulder_l, elbow_l)
                    angle_r_h = utils.calculate_angle(hip_r, shoulder_r, elbow_r)

                    # Detect the curl position using config thresholds
                    thresholds = config.BICEP_CURL
                    if (angle_l_e > thresholds['down_angle_min'] and 
                        angle_r_e > thresholds['down_angle_min'] and 
                        angle_l_h < thresholds['torso_angle_max'] and 
                        angle_r_h < thresholds['torso_angle_max']):
                        stage = "down"
                    if (angle_l_e < thresholds['up_angle_max'] and 
                        angle_r_e < thresholds['up_angle_max'] and 
                        stage == 'down' and 
                        angle_l_h < thresholds['torso_angle_max'] and 
                        angle_r_h < thresholds['torso_angle_max']):
                        stage = "up"
                        counter += 1
                        logger.info(f"Bicep curl count: {counter}")

                    # Detect incorrect form
                    hands_too_high = wrist_l[1] < shoulder_l[1] and wrist_r[1] < shoulder_r[1]

                    except Exception as e:
                        logger.debug(f"Error processing landmarks: {e}")
                        hands_too_high = False

                    # Render bicep curl counter
                    # Setup status box
                    cv2.rectangle(image, (0, 0), (320, 83), (245, 117, 16), -1)

                    # Reps data
                    cv2.putText(image, 'REPS', (15, 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    cv2.putText(image, str(counter),
                                (18, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)

                    # Stage data
                    cv2.putText(image, 'STAGE', (165, 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    if stage:
                        cv2.putText(image, stage,
                                    (120, 70),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
                    
                    # Incorrect form
                    if 'hands_too_high' in locals() and hands_too_high and (current_time - last_alert_time > alert_cooldown):
                        show_hands_too_high = True
                        error_end_time_hands_too_high = current_time + error_display_time
                        cv2.rectangle(image, (0, 420), (640, 480), (0, 0, 255), -1)
                        cv2.putText(image, 'HANDS TOO HIGH', (240, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
                        # Play audio alert
                        threading.Thread(target=play_audio, args=(alert_sound,)).start()
                        last_alert_time = current_time
                else:
                    # No landmarks detected
                    if current_time - last_notinframe_time > alert_cooldown:
                        show_notinframe = True
                        error_end_time_notinframe = current_time + error_display_time
                        cv2.rectangle(image, (0, 420), (640, 480), (0, 0, 255), -1)
                        cv2.putText(image, 'NOT IN FRAME', (240, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
                        # Play "not in frame" audio alert
                        threading.Thread(target=play_audio, args=(notinframe_sound,)).start()
                        last_notinframe_time = current_time

                # Display error messages
                if show_hands_too_high:
                    cv2.rectangle(image, (0, 420), (640, 480), (0, 0, 255), -1)
                    cv2.putText(image, 'HANDS TOO HIGH', (240, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
                    if current_time > error_end_time_hands_too_high:
                        show_hands_too_high = False

                if show_notinframe:
                    cv2.rectangle(image, (0, 420), (640, 480), (0, 0, 255), -1)
                    cv2.putText(image, 'NOT IN FRAME', (240, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
                    if current_time > error_end_time_notinframe:
                        show_notinframe = False

                # Render detections
                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                               mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                               mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

                cv2.imshow('Bicep Curl Detection', image)

                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break

    except Exception as e:
        logger.error(f"Error in bicep curl detection: {e}", exc_info=True)
    finally:
        # Release resources
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        logger.info("Bicep curl detection stopped")
