// src/App.js
import React, { useState } from 'react';
import VideoUpload from './components/VideoUpload';
import VideoPlayer from './components/VideoPlayer';
import EventList from './components/EventList';
import RTSPVideoAnalysis from './components/RTSPVideoAnalysis';
import SimilarVideoSearch from './components/SimilarVideoSearch';
import VectorizedVideos from './components/VectorizedVideos';

function App() {
  const [videoFile, setVideoFile] = useState(null);
  const [events, setEvents] = useState([]);
  const [temporalDescriptions, setTemporalDescriptions] = useState([]);
  const [showRTSPAnalysis, setShowRTSPAnalysis] = useState(false);
  const [uploadedVideos, setUploadedVideos] = useState([]);

  const handleUploadSuccess = (data) => {
    setUploadedVideos(prevVideos => [...prevVideos, data.message]);
    // You might want to refresh the list of vectorized videos here
  };

  const handleAnalysisComplete = (data) => {
    setVideoFile(data.video_url); // Assuming the backend returns a URL to the processed video
    setEvents(data.events);
    setTemporalDescriptions(data.temporal_descriptions);
  };

  return (
    <div className="App">
      <h1>Video Analysis</h1>
      <button onClick={() => setShowRTSPAnalysis(!showRTSPAnalysis)}>
        {showRTSPAnalysis ? 'Show Video Upload' : 'Show RTSP Analysis'}
      </button>
      {showRTSPAnalysis ? (
        <RTSPVideoAnalysis />
      ) : (
        <>
          <VideoUpload 
            onUploadSuccess={handleUploadSuccess} 
            onAnalysisComplete={handleAnalysisComplete} 
          />
          {videoFile && <VideoPlayer videoFile={videoFile} />}
          <EventList events={events} temporalDescriptions={temporalDescriptions} />
          <SimilarVideoSearch />
          <VectorizedVideos videos={uploadedVideos} />
        </>
      )}
    </div>
  );
}

export default App;