// src/components/VideoUpload.js
import React, { useState } from 'react';
import axios from 'axios';

const VideoUpload = ({ onUploadSuccess, onAnalysisComplete }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async (action) => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('video', file);

    try {
      // First, upload the video
      const uploadResponse = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (action === 'vectorize') {
        // If vectorizing, call the vectorize endpoint
        await axios.post(`/api/vectorize/${uploadResponse.data.video_id}`);
        onUploadSuccess(uploadResponse.data);
      } else if (action === 'analyze') {
        // If analyzing, call the analyze endpoint
        const analyzeResponse = await axios.post('/api/analyze', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        onAnalysisComplete(analyzeResponse.data);
      }

      setUploading(false);
    } catch (error) {
      setUploading(false);
      setError('Error processing video: ' + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div>
      <h2>Upload Video</h2>
      <input 
        type="file" 
        onChange={handleFileChange} 
        accept="video/*"
        disabled={uploading}
      />
      <button onClick={() => handleUpload('vectorize')} disabled={uploading || !file}>
        {uploading ? 'Processing...' : 'Upload and Vectorize'}
      </button>
      <button onClick={() => handleUpload('analyze')} disabled={uploading || !file}>
        {uploading ? 'Processing...' : 'Upload and Analyze'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default VideoUpload;