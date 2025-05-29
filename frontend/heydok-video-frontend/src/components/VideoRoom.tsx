import React, { useEffect, useRef, useState } from 'react';
import { Camera, CameraOff, Mic, MicOff, PhoneOff, ScreenShare, Users, MessageSquare } from 'lucide-react';
import '../styles/VideoRoom.css';

interface VideoRoomProps {
  token: string;
  serverUrl: string;
  roomName: string;
  displayName: string;
  onLeave: () => void;
}

const VideoRoom: React.FC<VideoRoomProps> = ({ token, serverUrl, roomName, displayName, onLeave }) => {
  const [isCameraOn, setIsCameraOn] = useState(true);
  const [isMicOn, setIsMicOn] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [participants, setParticipants] = useState<string[]>([displayName]);
  
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideosRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize video/audio streams
    initializeMedia();
    
    return () => {
      // Cleanup media streams
      stopAllStreams();
    };
  }, []);

  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: isCameraOn,
        audio: isMicOn
      });
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Error accessing media devices:', error);
    }
  };

  const stopAllStreams = () => {
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
    }
  };

  const toggleCamera = async () => {
    setIsCameraOn(!isCameraOn);
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !isCameraOn;
      }
    }
  };

  const toggleMic = async () => {
    setIsMicOn(!isMicOn);
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream;
      const audioTrack = stream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !isMicOn;
      }
    }
  };

  const toggleScreenShare = async () => {
    if (!isScreenSharing) {
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: false
        });
        setIsScreenSharing(true);
        
        screenStream.getVideoTracks()[0].onended = () => {
          setIsScreenSharing(false);
        };
      } catch (error) {
        console.error('Error sharing screen:', error);
      }
    } else {
      setIsScreenSharing(false);
    }
  };

  const handleLeave = () => {
    stopAllStreams();
    onLeave();
  };

  return (
    <div className="video-room">
      <div className="video-grid">
        <div className="video-container local">
          <video
            ref={localVideoRef}
            autoPlay
            muted
            playsInline
            className="video-element"
          />
          <div className="video-label">You ({displayName})</div>
          {!isCameraOn && (
            <div className="video-off-placeholder">
              <CameraOff size={48} />
              <p>Camera is off</p>
            </div>
          )}
        </div>
        
        <div ref={remoteVideosRef} className="remote-videos">
          {/* Remote participant videos will be added here dynamically */}
          <div className="no-participants">
            <Users size={48} />
            <p>Waiting for others to join...</p>
          </div>
        </div>
      </div>

      <div className="controls-bar">
        <div className="meeting-info">
          <span className="room-name">{roomName}</span>
          <span className="participant-count">
            <Users size={16} /> {participants.length}
          </span>
        </div>

        <div className="control-buttons">
          <button
            className={`control-btn ${!isMicOn ? 'off' : ''}`}
            onClick={toggleMic}
            title={isMicOn ? 'Turn off microphone' : 'Turn on microphone'}
          >
            {isMicOn ? <Mic size={20} /> : <MicOff size={20} />}
          </button>

          <button
            className={`control-btn ${!isCameraOn ? 'off' : ''}`}
            onClick={toggleCamera}
            title={isCameraOn ? 'Turn off camera' : 'Turn on camera'}
          >
            {isCameraOn ? <Camera size={20} /> : <CameraOff size={20} />}
          </button>

          <button
            className={`control-btn ${isScreenSharing ? 'active' : ''}`}
            onClick={toggleScreenShare}
            title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
          >
            <ScreenShare size={20} />
          </button>

          <button
            className="control-btn leave"
            onClick={handleLeave}
            title="Leave meeting"
          >
            <PhoneOff size={20} />
          </button>
        </div>

        <div className="extra-controls">
          <button className="control-btn" title="Chat">
            <MessageSquare size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default VideoRoom; 