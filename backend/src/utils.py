import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.vgg16 import preprocess_input

def preprocess_frame(frame, target_size=(224, 224)):
    frame = cv2.resize(frame, target_size)
    frame = img_to_array(frame)
    frame = np.expand_dims(frame, axis=0)
    frame = preprocess_input(frame)
    return frame

def generate_video_embedding(video_path, model):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(preprocess_frame(frame))
        if len(frames) >= 16:  # Process 16 frames at a time
            break
    cap.release()
    
    if not frames:
        return None
    
    # Generate embeddings
    embeddings = model.predict(np.vstack(frames))
    
    # Average the embeddings
    avg_embedding = np.mean(embeddings, axis=0)
    
    return avg_embedding