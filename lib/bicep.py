import cv2
import mediapipe as mp
import numpy as np
import pygame
import threading
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Load audio files
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("src\\Python\\static\\audio\\alert.mp3")
notinframe_sound = pygame.mixer.Sound("src\\Python\\static\\audio\\notinframe.mp3")

# Function to calculate the angle between three points
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
    
    return angle

# Function to play the audio alert in a separate thread
def play_audio(sound):
    sound.play()

# Bicep Curl Detection function
def bicep_curl_detection():
    # Initialize webcam
    cap = cv2.VideoCapture(0)

    # Bicep CURL counter variables
    counter = 0
    stage = None

    # Timing for audio triggers and error display
    last_alert_time = 0
    last_notinframe_time = 0
    alert_cooldown = 5  # seconds
    error_display_time = 3  # seconds

    # To keep track of when to stop displaying the error
    show_hands_too_high = False
    show_notinframe = False
    error_end_time_hands_too_high = 0
    error_end_time_notinframe = 0

    # Create a named window
    cv2.namedWindow('Bicep Curl Detection', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Bicep Curl Detection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Setup MediaPipe instance
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
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

                    # Calculate angles for both arms
                    angle_l = calculate_angle(shoulder_l, elbow_l, wrist_l)
                    angle_r = calculate_angle(shoulder_r, elbow_r, wrist_r)
                    angle_l_e = calculate_angle(shoulder_l, elbow_l, wrist_l)
                    angle_r_e = calculate_angle(shoulder_r, elbow_r, wrist_r)
                    angle_l_h = calculate_angle(hip_l, shoulder_l, elbow_l)
                    angle_r_h = calculate_angle(hip_r, shoulder_r, elbow_r)

                    # Detect the curl position
                    if angle_l_e > 140 and angle_r_e > 140 and angle_l_h < 45 and angle_r_h < 45:
                        stage = "down"
                    if angle_l_e < 35 and angle_r_e < 35 and stage == 'down' and angle_l_h < 45 and angle_r_h < 45:
                        stage = "up"
                        counter += 1
                        print(counter)

                    # Detect incorrect form
                    hands_too_high = wrist_l[1] < shoulder_l[1] and wrist_r[1] < shoulder_r[1]

                except:
                    pass

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
                cv2.putText(image, stage,
                            (120, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Incorrect form
                if hands_too_high and (current_time - last_alert_time > alert_cooldown):
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
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                       mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                       mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

            cv2.imshow('Bicep Curl Detection', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

# Flask route for Bicep Curl Detection
@app.route('/bicep_curls', methods=['POST'])
def bicep_curls():
    threading.Thread(target=bicep_curl_detection).start()
    return jsonify({"status": "Bicep Curl Detection started"}), 200

# Flask Application Runner
if __name__ == "__main__":
    app.run(debug=True)
