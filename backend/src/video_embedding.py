import cv2
import numpy as np
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array

# Load VGG16 model
vgg_model = VGG16(weights='imagenet', include_top=False, pooling='avg')

def generate_video_embedding(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while len(frames) < 16:  # Process up to 16 frames
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (224, 224))
        frame = img_to_array(frame)
        frame = np.expand_dims(frame, axis=0)
        frame = preprocess_input(frame)
        frames.append(frame)
    cap.release()
    
    if not frames:
        return None
    
    # Generate embeddings
    embeddings = vgg_model.predict(np.vstack(frames))
    
    # Average the embeddings
    avg_embedding = np.mean(embeddings, axis=0)
    
    return avg_embedding