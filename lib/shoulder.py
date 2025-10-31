import cv2
import time
import pygame
import mediapipe as mp
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pygame.init()
pygame.mixer.init()

last_play_time_hands_low = 0
last_play_time_joints_visible = 0

hands_low = "src\\Python\\static\\audio\\low_hands.mp3"
joints_visible = "src\\Python\\static\\audio\\joints_not_visible.mp3"

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
    
    return angle

def shoulder_press():
    global last_play_time_hands_low
    global last_play_time_joints_visible

    cap = cv2.VideoCapture(0)

    counter = 0
    stage = None
    prev_stage = None

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            if not ret:
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            required_joints_visible = False
            try:
                landmarks = results.pose_landmarks.landmark

                shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow_l = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist_l = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                shoulder_r = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                elbow_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                wrist_r = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]

                angle_l = calculate_angle(shoulder_l, elbow_l, wrist_l)
                angle_r = calculate_angle(shoulder_r, elbow_r, wrist_r)
                angle_torso_arm_l = calculate_angle(hip_l, shoulder_l, elbow_l)
                angle_torso_arm_r = calculate_angle(hip_r, shoulder_r, elbow_r)

                required_joints_visible = all(coord is not None for coord in hip_l + shoulder_l + wrist_l + elbow_l + hip_r + shoulder_r + wrist_r + elbow_r)

                if (angle_l > 150 and angle_r > 150) and (angle_torso_arm_l > 150 and angle_torso_arm_r > 150):
                    stage = "pressing"
                elif (95 < angle_l < 150 and 95 < angle_r < 150) and (95 < angle_torso_arm_l < 150 and 95 < angle_torso_arm_r < 150):
                    stage = "lowered"
                
                if stage == "pressing" and prev_stage == "lowered":
                    counter += 1
                    print("Shoulder Press Count:", counter)
                
                prev_stage = stage

                hands_too_low = True if angle_torso_arm_l < 80 and angle_torso_arm_r < 80 else False

            except Exception as e:
                print(f"Error processing pose: {e}")

            cv2.rectangle(image, (0, 0), (320, 83), (245, 117, 16), -1)

            cv2.putText(image, 'REPS', (15, 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter),
                    (18, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.putText(image, 'STAGE', (165, 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, stage,
                    (120, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
          

            if required_joints_visible:
                if hands_too_low:
                    error = "Hands too low"
                    cv2.rectangle(image, (0, 420), (640, 480), (0, 0, 255), -1)
                    cv2.putText(image, error, (240, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
                 
                    current_time = time.time()
                    if (current_time - last_play_time_hands_low) > 5:
                        pygame.mixer.music.load(hands_low)
                        pygame.mixer.music.play()
                        last_play_time_hands_low = current_time
                    
            else:
                cv2.rectangle(image, (0, image.shape[0] - 40), (image.shape[1], image.shape[0]), (0, 0, 255), -1)
                cv2.putText(image, 'Joints not visible', (10, image.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
                current_time = time.time()
                if (current_time - last_play_time_joints_visible) > 5:
                    pygame.mixer.music.load(joints_visible)
                    pygame.mixer.music.play()
                    last_play_time_joints_visible = current_time
            
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                    mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
            
                    # Resizeable window
            cv2.namedWindow('Shoulder Press Detection', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Shoulder Press Detection', 1800, 1200)  # Set the initial size of the window

            # Get the current window size
            _, _, window_width, window_height = cv2.getWindowImageRect('Shoulder Press Detection')

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

            cv2.imshow('Shoulder Press Detection', canvas)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

@app.route('/shoulder_press', methods=['POST'])
def run_shoulder_press():
    try:
        shoulder_press()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
