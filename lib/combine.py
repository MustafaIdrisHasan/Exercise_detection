from flask import Flask, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import pygame

app = Flask(__name__)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

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

# Function to run bicep curl detection
def bicep_curl():
    # Initialize webcam
    cap = cv2.VideoCapture(0)

    # Bicep curl counter variables
    counter = 0
    stage = None

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

            # Extract landmarks
            try:
                landmarks = results.pose_landmarks.landmark
                
                # Calculate angles for both arms and the angle between the torso and the left and right upper arms
                angle_l = calculate_angle([landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y], 
                                          [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y], 
                                          [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y])
                angle_r = calculate_angle([landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y], 
                                          [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y], 
                                          [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y])
                angle_l_h = calculate_angle([landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y], 
                                            [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y], 
                                            [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y])
                angle_r_h = calculate_angle([landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y], 
                                            [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y], 
                                            [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y])

                # Determine the stage of the movement
                if angle_l > 140 and angle_r > 140 and angle_l_h < 45 and angle_r_h < 45:
                    stage = "down"
                if angle_l < 35 and angle_r < 35 and stage == 'down' and angle_l_h < 45 and angle_r_h < 45:
                    stage = "up"
                    counter += 1
                    print(counter)

                hands_too_low = True if angle_l > 160 and angle_r > 160 else False

            except:
                pass

                        # Render detections
            cv2.putText(image, 'REPS: {}'.format(counter), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(image, 'STAGE: {}'.format(stage), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            if hands_too_low:
                cv2.putText(image, 'HANDS TOO LOW', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Display the frame
            cv2.imshow('Bicep Curl Detection', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

@app.route('/bicep_curl', methods=['POST'])
def run_detection_bicep_curl():
    try:
        bicep_curl()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Function to run shoulder press detection
def shoulder_press():

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pygame.init()
    pygame.mixer.init()

    last_play_time_hands_low = 0
    last_play_time_joints_visible = 0

    hands_low = "hands_too_low.mp3"
    joints_visible = "joints_not_visible.mp3"

    # Initialize webcam
    cap = cv2.VideoCapture(0)

    # Shoulder press counter variables
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

            # Extract landmarks
            try:
                landmarks = results.pose_landmarks.landmark

                # Get coordinates for left shoulder, elbow, wrist, and hip
                shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow_l = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist_l = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                # Get coordinates for right shoulder, elbow, wrist, and hip
                shoulder_r = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                elbow_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                wrist_r = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]

                # Calculate angles for both arms and the angle between the torso and the left and right upper arms
                angle_l = calculate_angle(shoulder_l, elbow_l, wrist_l)
                angle_r = calculate_angle(shoulder_r, elbow_r, wrist_r)
                angle_torso_arm_l = calculate_angle(hip_l, shoulder_l, elbow_l)
                angle_torso_arm_r = calculate_angle(hip_r, shoulder_r, elbow_r)
                angle_arm_forearm_l = calculate_angle(shoulder_l, elbow_l, wrist_l)
                angle_arm_forearm_r = calculate_angle(shoulder_r, elbow_r, wrist_r)

                # Shoulder press counter logic
                if (angle_l > 150 and angle_r > 150) and (angle_torso_arm_l > 150 and angle_torso_arm_r > 150) and (angle_arm_forearm_l > 150 and angle_arm_forearm_r > 150):
                    stage = "pressing"
                else:  # If not pressing (lowered arms or incorrect angles)
                    stage = "lowered"
                
                if stage == "pressing" and prev_stage == "lowered":
                    counter += 1
                    print("Shoulder Press Count:", counter)
                
                prev_stage = stage

                if angle_torso_arm_l < 65 and angle_torso_arm_r < 65:
                    hands_too_low = True 
                elif angle_torso_arm_l < 65 and angle_torso_arm_r > 65:
                    hands_too_low= True
                elif angle_torso_arm_l > 65 and angle_torso_arm_r < 65:
                    hands_too_low= True
                else:
                    hands_too_low =False

            except:
                pass

            # Render shoulder press counter
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
            
            #incorrect form
            if hands_too_low:
                # Stage data
                cv2.rectangle(image, (0,420), (640,480), (0,0,255), -1)
                cv2.putText(image, 'HANDS TOO LOW', (240,450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2, cv2.LINE_AA)

            # Render detections
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                      mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                      mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                                    )
            cv2.imshow('Shoulder Press Detection', image)
        
        #resizeable window
        ##cv2.namedWindow('Shoulder Press Detection', cv2.WINDOW_NORMAL)
        #cv2.resizeWindow('Shoulder Press Detection', 5000000, 620000)  # Set the initial size of the window

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

@app.route('/shoulder_press', methods=['POST'])
def run_detection_shoulder_press():
    try:
        shoulder_press()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
##code for Squat
def squats():
    cap = cv2.VideoCapture(0)

    # Squat counter variables
    counter = 0
    stage = None

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

            # Extract landmarks
            try:
                landmarks = results.pose_landmarks.landmark
                
                # Get coordinates for hips, knees, and ankles
                hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee_l = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle_l = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                
                hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                knee_r = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                ankle_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]

                # Calculate angles for squat
                angle_l = calculate_angle(hip_l, knee_l, ankle_l)
                angle_r = calculate_angle(hip_r, knee_r, ankle_r)

                # Squat counter logic
                if angle_l < 90 and angle_r < 90:  # If both legs are bent (squatting)
                    if stage != "squatting":  # If not already in squatting stage
                        stage = "squatting"
                        counter += 1
                        print("Squat Count:", counter)
                else:  # If not squatting (standing)
                    if stage != "standing":  # If not already in standing stage
                        stage = "standing"
            except:
                pass
                    
            

            # Render squat counter
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

            # Render detections
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                       mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                       mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                                       )

            cv2.imshow('Squat Detection', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

@app.route('/squats', methods=['POST'])
def run_detection_squats():
    try:
        squats()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
##Code for tricep
def tricep_pushdowns():
    cap = cv2.VideoCapture(0)

    # Triceps counter variables
    counter = 0
    stage = None

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

            # Extract landmarks
            try:
                landmarks = results.pose_landmarks.landmark
                
                # Get coordinates for shoulders, elbows, and wrists
                shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow_l = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist_l = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                
                shoulder_r = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                elbow_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                wrist_r = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

                # Calculate angles for triceps extension
                angle_l = calculate_angle(shoulder_l, elbow_l, wrist_l)
                angle_r = calculate_angle(shoulder_r, elbow_r, wrist_r)

                # Triceps counter logic
                prev_stage = None  # Variable to keep track of the previous stage

# Triceps counter logic
                if angle_l > 160 and angle_r > 160:
                    stage = "extending"
                else:  # If not extending
                    stage = "contracting"

                if prev_stage == "contracting" and stage == "extending":
                    counter += 1
                    print("Triceps Count:", counter)

                prev_stage = stage  # Update previous stage             
                    
                # Check if arms are folded
                if angle_l < 30 and angle_r < 30:
                    cv2.putText(image, 'Do not fold your arms!', (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    
            except:
                pass

            # Render triceps counter
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

            # Render detections
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                       mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                       mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                                       )

            cv2.imshow('Triceps Detection', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

@app.route('/tricep_pushdowns', methods=['POST'])
def run_detection_tricep_pushdowns():
    try:
        tricep_pushdowns()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
if __name__ == '__main__':
    app.run(debug=True)

