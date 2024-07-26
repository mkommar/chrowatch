import React from 'react';

function VideoPlayer({ videoFile }) {
  const videoUrl = URL.createObjectURL(videoFile);

  return (
    <div>
      <video width="640" height="480" controls>
        <source src={videoUrl} type={videoFile.type} />
        Your browser does not support the video tag.
      </video>
    </div>
  );
}

export default VideoPlayer;