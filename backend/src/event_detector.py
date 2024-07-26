import cv2
import torch
import numpy as np
from PIL import Image

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def detect_event(frame, timestamp, prev_frame=None, prev_objects=None):
    events = []
    objects = []
    
    # Convert frame to RGB (YOLOv5 expects RGB images)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Perform object detection
    results = model(rgb_frame)
    
    # Process results
    for *box, conf, cls in results.xyxy[0]:  # xyxy, confidence, class
        class_name = model.names[int(cls)]
        if conf > 0.5:  # Confidence threshold
            x1, y1, x2, y2 = map(int, box)
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            obj = {
                'type': class_name,
                'confidence': conf.item(),
                'box': (x1, y1, x2, y2),
                'center': (center_x, center_y)
            }
            objects.append(obj)
            events.append({
                'type': 'object_detected',
                'description': f'{class_name} detected with confidence {conf:.2f} at position ({center_x}, {center_y})',
                'timestamp': timestamp,
                'object': obj
            })
    
    # Motion detection for objects
    if prev_objects is not None:
        for curr_obj in objects:
            for prev_obj in prev_objects:
                if curr_obj['type'] == prev_obj['type']:
                    dx = curr_obj['center'][0] - prev_obj['center'][0]
                    dy = curr_obj['center'][1] - prev_obj['center'][1]
                    distance = np.sqrt(dx**2 + dy**2)
                    if distance > 10:  # Threshold for significant motion
                        events.append({
                            'type': 'object_motion',
                            'description': f'{curr_obj["type"]} moved {distance:.2f} pixels',
                            'timestamp': timestamp,
                            'object': curr_obj,
                            'motion': (dx, dy)
                        })
    
    # Color dominance
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    dominant_color = np.argmax(np.mean(frame, axis=(0,1)))
    color_names = ['blue', 'green', 'red']
    events.append({
        'type': 'color_dominance',
        'description': f'Dominant color is {color_names[dominant_color]}',
        'timestamp': timestamp
    })
    
    # Brightness detection
    brightness = np.mean(gray)
    if brightness > 200:
        events.append({
            'type': 'bright_scene',
            'description': 'The scene is very bright',
            'timestamp': timestamp
        })
    elif brightness < 50:
        events.append({
            'type': 'dark_scene',
            'description': 'The scene is very dark',
            'timestamp': timestamp
        })
    
    # Overall motion detection
    if prev_frame is not None:
        frame_diff = cv2.absdiff(prev_frame, gray)
        if np.mean(frame_diff) > 30:
            events.append({
                'type': 'motion_detected',
                'description': 'Significant overall motion detected',
                'timestamp': timestamp
            })
    
    return events, objects

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    events = []
    prev_frame = None
    prev_objects = None
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        current_time = frame_count / fps
        
        frame_events, objects = detect_event(frame, current_time, prev_frame, prev_objects)
        events.extend(frame_events)
        
        prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prev_objects = objects
    
    cap.release()
    return events