import React, { useEffect, useState, useRef } from 'react';
import Hls from 'hls.js';
import io from 'socket.io-client';

const RTSPVideoAnalysis = () => {
  const [rtspUrl, setRtspUrl] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [events, setEvents] = useState([]);
  const [description, setDescription] = useState('');
  const [socket, setSocket] = useState(null);
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  useEffect(() => {
    const newSocket = io('http://localhost:5333');
    setSocket(newSocket);

    newSocket.on('analysis_result', (data) => {
      setEvents(data.events);
      if (data.description) {
        setDescription(data.description);
      }
    });

    return () => newSocket.close();
  }, []);

  const handleStartStream = () => {
    if (socket && rtspUrl) {
      socket.emit('start_rtsp_stream', { rtsp_url: rtspUrl }, (response) => {
        if (response && response.hls_url) {
          if (Hls.isSupported()) {
            const hls = new Hls({
              manifestLoadingTimeOut: 5000,
              manifestLoadingMaxRetry: Infinity,
              manifestLoadingRetryDelay: 500,
              levelLoadingTimeOut: 5000,
              levelLoadingMaxRetry: Infinity,
              levelLoadingRetryDelay: 500
            });
            hlsRef.current = hls;
            hls.loadSource(`http://localhost:5333${response.hls_url}`);
            hls.attachMedia(videoRef.current);
            hls.on(Hls.Events.MANIFEST_PARSED, () => {
              videoRef.current.play().catch(e => console.error("Error attempting to play:", e));
            });
          } else if (videoRef.current.canPlayType('application/vnd.apple.mpegurl')) {
            videoRef.current.src = `http://localhost:5333${response.hls_url}`;
            videoRef.current.play().catch(e => console.error("Error attempting to play:", e));
          }
          setIsStreaming(true);
        }
      });
    }
  };

  const handleStopStream = () => {
    if (socket) {
      socket.emit('stop_rtsp_stream');
      setIsStreaming(false);
      if (hlsRef.current) {
        hlsRef.current.destroy();
      }
      if (videoRef.current) {
        videoRef.current.src = '';
      }
    }
  };

  return (
    <div>
      <h2>RTSP Video Analysis</h2>
      <input
        type="text"
        value={rtspUrl}
        onChange={(e) => setRtspUrl(e.target.value)}
        placeholder="Enter RTSP URL"
      />
      <button onClick={handleStartStream} disabled={isStreaming}>
        Start Stream
      </button>
      <button onClick={handleStopStream} disabled={!isStreaming}>
        Stop Stream
      </button>
      <video 
        ref={videoRef} 
        controls 
        width="640" 
        height="360" 
        style={{ display: isStreaming ? 'block' : 'none' }}
      />
      <div>
        <h3>Detected Events:</h3>
        <ul>
          {events.map((event, index) => (
            <li key={index}>{event.type}: {event.description}</li>
          ))}
        </ul>
      </div>
      <div>
        <h3>Latest Description:</h3>
        <p>{description}</p>
      </div>
    </div>
  );
};

export default RTSPVideoAnalysis;