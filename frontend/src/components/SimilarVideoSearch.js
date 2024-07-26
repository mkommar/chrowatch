import React, { useState } from 'react';
import axios from 'axios';

const SimilarVideoSearch = () => {
  const [file, setFile] = useState(null);
  const [similarVideos, setSimilarVideos] = useState([]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5333/api/similar_videos', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSimilarVideos(response.data);
    } catch (error) {
      console.error('Error finding similar videos:', error);
    }
  };

  return (
    <div>
      <h2>Find Similar Videos</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleFileChange} accept="image/*,video/*" />
        <button type="submit">Find Similar Videos</button>
      </form>
      {similarVideos.length > 0 && (
        <div>
          <h3>Similar Videos:</h3>
          <ul>
            {similarVideos.map((video) => (
              <li key={video.id}>
                {video.filename} (Similarity: {video.similarity.toFixed(2)})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SimilarVideoSearch;