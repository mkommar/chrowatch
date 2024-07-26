import React from 'react';

const UploadedVideosList = ({ videos }) => {
  return (
    <div>
      <h3>Uploaded Videos</h3>
      {videos.length === 0 ? (
        <p>No videos uploaded yet.</p>
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

export default UploadedVideosList;