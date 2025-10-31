import cv2
import time
import pygame
import mediapipe as mp
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Initialize pygame
pygame.init()
pygame.mixer.init()

last_play_time_crunch_incorrect = 0
last_play_time_joints_visible = 0

crunch_incorrect = "src\\Python\\static\\audio\\crunch_incorrect.mp3"
joints_visible = "src\\Python\\static\\audio\\joints_not_visible.mp3"

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
def crunches():
    global last_play_time_crunch_incorrect
    global last_play_time_joints_visible

    # Initialize webcam
    cap = cv2.VideoCapture(0)

    # Crunches counter variables
    counter = 0
    stage = None
    prev_stage = None

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

            required_joints_visible = False  # Initialize required_joints_visible variable
            # Extract landmarks
            try:
                landmarks = results.pose_landmarks.landmark

                # Get coordinates for left shoulder, hip, and knee
                shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee_l = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]

                # Get coordinates for right shoulder, hip, and knee
                shoulder_r = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                knee_r = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]

                # Calculate angles for both sides
                angle_l = calculate_angle(shoulder_l, hip_l, knee_l)
                angle_r = calculate_angle(shoulder_r, hip_r, knee_r)

                required_joints_visible = all(coord is not None for coord in shoulder_l + hip_l + knee_l + shoulder_r + hip_r + knee_r)

                # Crunches counter logic
                if (angle_l < 90 and angle_r < 90):
                    stage = "up"
                elif (angle_l > 100 and angle_r > 100):  
                    stage = "down"
                
                if stage == "up" and prev_stage == "down":
                    counter += 1
                    print("Crunches Count:", counter)
                
                prev_stage = stage

                crunch_incorrect_form = True if angle_l > 120 and angle_r > 120 else False

            except:
                pass

            # Render crunches counter
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
            if required_joints_visible:
                if crunch_incorrect_form:
                    error = "Incorrect form"
                    cv2.rectangle(image, (0, 420), (640, 480), (0, 0, 255), -1)
                    cv2.putText(image, error, (240, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
                        
                    # Play audio once and then repeat after 5 seconds
                    current_time = time.time()
                    if current_time - last_play_time_crunch_incorrect > 5:  # Play audio once and then repeat after 5 seconds
                        pygame.mixer.music.load(crunch_incorrect)
                        pygame.mixer.music.play()
                        last_play_time_crunch_incorrect = current_time
            else:
                cv2.rectangle(image, (0, image.shape[0] - 40), (image.shape[1], image.shape[0]), (0, 0, 255), -1)
                cv2.putText(image, 'Joints not visible', (10, image.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                
                # Play audio once and then repeat after 5 seconds
                current_time = time.time()
                if current_time - last_play_time_joints_visible > 5:  # Play audio once and then repeat after 5 seconds
                    pygame.mixer.music.load(joints_visible)
                    pygame.mixer.music.play()
                    last_play_time_joints_visible = current_time

            # Render detections
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                    mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
                # Resizeable window
            cv2.namedWindow('Crunch Detection', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Crunch Detection', 1800, 1200)  # Set the initial size of the window

            # Get the current window size
            _, _, window_width, window_height = cv2.getWindowImageRect('Crunch Detection')

            # Calculate the aspect ratio of the frame
            frame_height, frame_width = image.shape[:2]
            aspect_ratio = frame_width / frame_height

            # Calculate new dimensions to maintain aspect ratio
            new_width = window_width
            new_height = int(new_width / aspect_ratio)
            if new_height > window_height:
                new_height = window_height
                new_width = int(new_height * aspect_ratio)

            # Resize the image to fit the window while maintaining aspect ratio
            resized_image = cv2.resize(image, (new_width, new_height))

            # Create a black canvas of the window size
            canvas = np.zeros((window_height, window_width, 3), dtype=np.uint8)

            # Calculate padding to center the resized image on the canvas
            x_offset = (window_width - new_width) // 2
            y_offset = (window_height - new_height) // 2

            # Place the resized image on the canvas
            canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image

            cv2.imshow('Crunch Detection', canvas)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        # Release resources
        cap.release()
        cv2.destroyAllWindows()

@app.route('/crunches', methods=['POST'])
def run_crunches():
    try:
        crunches()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
