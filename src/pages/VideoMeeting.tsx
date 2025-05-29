import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

export const VideoMeeting = () => {
  const { meetingCode } = useParams();
  const navigate = useNavigate();
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(true);
  
  useEffect(() => {
    // Get token from SessionStorage
    const savedToken = sessionStorage.getItem('meetingToken');
    
    if (!savedToken) {
      // No token = back to join page
      navigate(`/meet/${meetingCode}`);
      return;
    }
  }, [meetingCode, navigate]);
  
  const handleLeave = () => {
    sessionStorage.clear();
    toast.success('Left meeting');
    navigate('/');
  };
  
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center text-white">
      <div className="relative w-full max-w-4xl aspect-video bg-gray-800 rounded-lg overflow-hidden">
        <video
          className="w-full h-full object-cover"
          autoPlay
          playsInline
          muted={!audioEnabled}
        />
      </div>
      
      <div className="mt-4 flex gap-4">
        <button
          onClick={() => setVideoEnabled(!videoEnabled)}
          className={`px-4 py-2 rounded-full ${
            videoEnabled ? 'bg-green-500' : 'bg-red-500'
          }`}
        >
          {videoEnabled ? 'Video On' : 'Video Off'}
        </button>
        
        <button
          onClick={() => setAudioEnabled(!audioEnabled)}
          className={`px-4 py-2 rounded-full ${
            audioEnabled ? 'bg-green-500' : 'bg-red-500'
          }`}
        >
          {audioEnabled ? 'Audio On' : 'Audio Off'}
        </button>
        
        <button
          onClick={handleLeave}
          className="px-4 py-2 rounded-full bg-red-500"
        >
          Leave Meeting
        </button>
      </div>
    </div>
  );
}; 