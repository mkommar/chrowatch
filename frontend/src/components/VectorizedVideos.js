// src/components/VectorizedVideos.js
import React from 'react';

const VectorizedVideos = ({ videos }) => {
  return (
    <div>
      <h2>Vectorized Videos</h2>
      {videos.length === 0 ? (
        <p>No videos have been vectorized yet.</p>
      ) : (
        <ul>
          {videos.map((video, index) => (
            <li key={index}>{video}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default VectorizedVideos;