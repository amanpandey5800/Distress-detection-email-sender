import cv2
import mediapipe as mp
import numpy as np
import time
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import threading

# Setup
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

# Webcam input
cap = cv2.VideoCapture(0)
prev_frame_time = 0
new_frame_time = 0

# Email configuration
EMAIL_ADDRESS = 'aman.pandey_cs.aiml21@gla.ac.in'
EMAIL_PASSWORD = 'pamybdncydabieum'
RECIPIENT_ADDRESS = 'amanpandey5800@gmail.com'
SMTP_SERVER = 'smtp.gmail.com'  
SMTP_PORT = 587  # Port for TLS

def send_email_with_attachment(filename):
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_ADDRESS
    msg['Subject'] = 'Recorded Video'
    
    body = 'Please find the recorded video attached.'
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach the video file
    attachment = open(filename, 'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={filename}')
    msg.attach(part)
    
    # Send the email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        print(f"Email sent with attachment: {filename}")

def record(duration=6):
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    
    # Generate a unique filename based on the current time
    filename = f"output_{int(time.time())}.avi"
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
    
    t_end = time.time() + duration
    while time.time() < t_end:
        success, image = cap.read()
        if not success:
            break
        out.write(image)
        cv2.putText(image, "Recording...", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('Recording', image)
        cv2.waitKey(1)
    
    out.release()
    print(f"Recording saved as {filename}")
    
    # Send the recorded file via email
    send_email_with_attachment(filename)
    
    # Optionally, delete the file after sending
    os.remove(filename)

def close_program_after_delay(delay):
    time.sleep(delay)
    cap.release()
    cv2.destroyAllWindows()
    print("Program closed after delay.")

frame_counter = 0
with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring No Video in Camera frame")
            continue

        # Drawing
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            # Get the landmarks (keypoints) of the body
            landmarks = results.pose_landmarks.landmark
            
            left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y
            right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y
            mouth = landmarks[mp_pose.PoseLandmark.MOUTH_LEFT].y
            shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
            dist_mid_y = (shoulder + mouth)/2
            print(dist_mid_y)

            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            fps = str(int(fps))
            if(left_wrist < dist_mid_y and right_wrist < dist_mid_y):
                message = f"Distress Detected {fps}"
                frame_counter += 1
            else:
                message = fps
                frame_counter = 0
            if (frame_counter > 30):
                message = "Warn 1"
            if (frame_counter > 60):
                message = "Warn 2"
                record(duration=6)  # Record for 6 seconds after "Warn 2"
                # Start a separate thread to close the program after 10 seconds
                threading.Thread(target=close_program_after_delay, args=(10,)).start()
                break  # Exit the loop after recording and sending email
            if (frame_counter > 90):
                message = "Calling Emergency Services"
                frame_counter = 0
            
            cv2.putText(image, message, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
        )

        cv2.imshow('MediaPipe Pose Estimation Program Video Demo', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
