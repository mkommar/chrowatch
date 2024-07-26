import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import tempfile
import os
import json
import threading
import time
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from event_detector import detect_event
from description_generator import generate_temporal_description
from werkzeug.utils import secure_filename
from database import insert_video, update_video_embedding, get_all_videos, get_video_by_id, get_vectorized_videos
from vector_search import cosine_similarity_search
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from event_detector import process_video
from io import BytesIO

UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Initialize Flask app
app = Flask(__name__, static_folder='../../frontend/build', static_url_path='')
app.config['UPLOAD_FOLDER'] = 'uploads'  # Make sure this folder exists
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Load VGG16 model for video embedding
vgg_model = VGG16(weights='imagenet', include_top=False, pooling='avg')

def generate_video_embedding(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (224, 224))
        frame = img_to_array(frame)
        frame = np.expand_dims(frame, axis=0)
        frame = preprocess_input(frame)
        frames.append(frame)
        if len(frames) >= 16:  # Process 16 frames at a time
            break
    cap.release()
    
    if not frames:
        return None
    
    # Generate embeddings
    embeddings = vgg_model.predict(np.vstack(frames))
    
    # Average the embeddings
    avg_embedding = np.mean(embeddings, axis=0)
    
    return avg_embedding

socketio = SocketIO(app, cors_allowed_origins="*")

rtsp_url = None
stop_stream = False
ffmpeg_process = None

# Create a directory to store HLS segments
hls_dir = os.path.join(os.getcwd(), 'hls_temp')
os.makedirs(hls_dir, exist_ok=True)

def convert_rtsp_to_hls(rtsp_url):
    global ffmpeg_process
    
    output_path = os.path.join(hls_dir, 'stream.m3u8')
    
    ffmpeg_command = [
        'ffmpeg',
        '-i', rtsp_url,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-f', 'hls',
        '-hls_time', '1',
        '-hls_list_size', '3',
        '-hls_flags', 'delete_segments+append_list+omit_endlist',
        '-hls_segment_type', 'mpegts',
        '-hls_segment_filename', os.path.join(hls_dir, 'segment%d.ts'),
        output_path
    ]
    
    ffmpeg_process = subprocess.Popen(ffmpeg_command)

def process_rtsp_stream():
    global rtsp_url, stop_stream
    cap = cv2.VideoCapture(rtsp_url)
    
    start_time = time.time()
    frame_count = 0
    
    while not stop_stream:
        ret, frame = cap.read()
        if not ret:
            break
        
        current_time = time.time() - start_time
        events = detect_event(frame, current_time)
        
        if int(current_time) % 10 == 0:
            description = generate_temporal_description(events, 'bedrock', 'anthropic.claude-3-sonnet-20240229-v1:0')
        else:
            description = None
        
        socketio.emit('analysis_result', {
            'events': events,
            'description': description,
            'timestamp': current_time
        })
        
        frame_count += 1
        time.sleep(0.033)
    
    cap.release()

@socketio.on('start_rtsp_stream')
def start_rtsp_stream(data):
    global rtsp_url, stop_stream
    rtsp_url = data['rtsp_url']
    stop_stream = False
    threading.Thread(target=process_rtsp_stream).start()
    convert_rtsp_to_hls(rtsp_url)
    return {'hls_url': '/hls/stream.m3u8'}

@socketio.on('stop_rtsp_stream')
def stop_rtsp_stream():
    global stop_stream, ffmpeg_process
    stop_stream = True
    if ffmpeg_process:
        ffmpeg_process.terminate()
        ffmpeg_process = None

@app.route('/hls/<path:filename>')
def serve_hls(filename):
    return send_from_directory(hls_dir, filename)

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video = request.files['video']
    model_type = request.form.get('model_type', 'bedrock')
    model_name = request.form.get('model_name', 'anthropic.claude-3-sonnet-20240229-v1:0')

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
        video.save(temp_file.name)
        video_path = temp_file.name

    try:
        events = process_video(video_path)
        
        # Generate temporal descriptions for every 10 seconds
        temporal_descriptions = []
        for i in range(0, len(events), 10 * 30):  # Assuming 30 fps
            segment_events = events[i:i+10*30]
            if segment_events:
                start_time = segment_events[0]['timestamp']
                end_time = segment_events[-1]['timestamp']
                description = generate_temporal_description(segment_events, model_type, model_name)
                temporal_descriptions.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'description': description
                })

        return jsonify({
            'events': events,
            'temporal_descriptions': temporal_descriptions
        })

    finally:
        os.unlink(video_path)

@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if video:
        filename = secure_filename(video.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure the upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        video.save(filepath)
        
        try:
            video_id = insert_video(filename, filepath)
            return jsonify({'message': 'Video uploaded successfully', 'video_id': video_id}), 200
        except Exception as e:
            return jsonify({'error': f'An error occurred during processing: {str(e)}'}), 500

    return jsonify({'error': 'Invalid file'}), 400

@app.route('/api/similar_videos', methods=['POST'])
def find_similar_videos():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Generate embedding for the uploaded file
            query_embedding = generate_video_embedding(filepath)
            
            if query_embedding is None:
                return jsonify({'error': 'Failed to generate embedding for the uploaded file'}), 500

            # Get all videos from database
            all_videos = get_all_videos()
            if not all_videos:
                return jsonify({'error': 'No videos in database to compare'}), 404

            database_vectors = np.array([video['embedding'] for video in all_videos if video['embedding'] is not None])
            
            if database_vectors.size == 0:
                return jsonify({'error': 'No embeddings found in the database'}), 404

            # Perform similarity search
            top_indices, similarities = cosine_similarity_search(query_embedding, database_vectors, top_k=5)
            
            similar_videos = [
                {
                    'id': all_videos[i]['id'],
                    'filename': all_videos[i]['filename'],
                    'similarity': float(similarities[j])
                }
                for j, i in enumerate(top_indices)
            ]
            
            return jsonify(similar_videos)

        except Exception as e:
            return jsonify({'error': f'An error occurred during processing: {str(e)}'}), 500

        finally:
            # Clean up temporary file
            os.remove(filepath)

    return jsonify({'error': 'Invalid file'}), 400

@app.route('/api/vectorized_videos', methods=['GET'])
def get_vectorized_videos():
    videos = get_all_videos()  # Implement this function in your database.py
    return jsonify([{
        'id': video['id'],
        'filename': video['filename'],
        'vectorized': video['embedding'] is not None
    } for video in videos])

@app.route('/api/vectorize/<int:video_id>', methods=['POST'])
def vectorize_video(video_id):
    video = get_video_by_id(video_id)  # Implement this function in your database.py
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    embedding = generate_video_embedding(video['filepath'])
    update_video_embedding(video_id, embedding)  # Implement this function in your database.py

    return jsonify({'message': 'Video vectorized successfully'})

@app.route('/api/thumbnail/<int:video_id>')
def get_thumbnail(video_id):
    video = get_video_by_id(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    cap = cv2.VideoCapture(video['filepath'])
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({'error': 'Failed to generate thumbnail'}), 500

    _, buffer = cv2.imencode('.jpg', frame)
    io_buf = BytesIO(buffer)
    io_buf.seek(0)

    return send_file(io_buf, mimetype='image/jpeg')


# Serve React App
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    file_name = path.split('/')[-1]
    dir_name = os.path.join(app.static_folder, '/'.join(path.split('/')[:-1]))
    return send_from_directory(dir_name, file_name)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5333)
