import cv2
import time
from event_detector import detect_event
from description_generator import generate_description
from datetime import datetime

def process_video_realtime(video_path, model_type='gpt', model_name='gpt-4o'):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    start_time = time.time()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        current_time = start_time + (frame_count / fps)
        
        # Detect events
        events = detect_event(frame, current_time)
        
        # Generate description every 5 seconds
        if frame_count % int(fps * 5) == 0:
            description = generate_description(events, model_type, model_name)
            if description:
                print(f"At {datetime.fromtimestamp(current_time).strftime('%H:%M:%S')}:")
                print(description)
                print()
        
        # Real-time display (optional)
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()