import React, { useEffect, useState } from 'react';
import { 
  LiveKitRoom, 
  VideoConference, 
  RoomAudioRenderer,
  DisconnectButton,
  TrackToggle,
  useLocalParticipant,
  useParticipants,
  StartAudio
} from '@livekit/components-react';
import { 
  Track, 
  ConnectionState
} from 'livekit-client';
import { Camera, CameraOff, Mic, MicOff, PhoneOff, ScreenShare, Users } from 'lucide-react';
import toast from 'react-hot-toast';
import '@livekit/components-styles';
import '../styles/VideoRoom.css';

interface VideoRoomProps {
  token: string;
  serverUrl: string;
  roomName: string;
  displayName: string;
  onLeave: () => void;
}

// Enhanced Control Bar with Medical-specific Features
const MedicalControlBar: React.FC<{ onLeave: () => void }> = ({ onLeave }) => {
  const { localParticipant } = useLocalParticipant();
  const participants = useParticipants();
  const [isRecording, setIsRecording] = useState(false);

  const startRecording = async () => {
    try {
      const response = await fetch(`/api/v1/meetings/${localParticipant.identity}/start-recording`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        setIsRecording(true);
        toast.success('Recording started');
      }
    } catch (error) {
      toast.error('Failed to start recording');
    }
  };

  const stopRecording = async () => {
    try {
      const response = await fetch(`/api/v1/meetings/${localParticipant.identity}/stop-recording`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setIsRecording(false);
        toast.success('Recording stopped');
      }
    } catch (error) {
      toast.error('Failed to stop recording');
    }
  };

  // Check if user is physician based on metadata
  const isPhysician = localParticipant.metadata ? 
    JSON.parse(localParticipant.metadata).role === 'physician' : false;

  return (
    <div className="medical-control-bar">
      <div className="meeting-info">
        <span className="participant-count">
          <Users size={16} /> {participants.length}
        </span>
        {isRecording && <span className="recording-indicator">🔴 Recording</span>}
      </div>

      <div className="control-buttons">
        <TrackToggle source={Track.Source.Microphone} showIcon={true}>
          <Mic size={20} />
          <MicOff size={20} />
        </TrackToggle>

        <TrackToggle source={Track.Source.Camera} showIcon={true}>
          <Camera size={20} />
          <CameraOff size={20} />
        </TrackToggle>

        <TrackToggle source={Track.Source.ScreenShare} captureOptions={{ audio: true }}>
          <ScreenShare size={20} />
        </TrackToggle>

        {/* Recording Control - Only for physicians */}
        {isPhysician && (
          <button
            className={`control-btn ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            title={isRecording ? 'Stop Recording' : 'Start Recording'}
          >
            <div className="record-icon" />
          </button>
        )}

        <DisconnectButton>
          <PhoneOff size={20} />
        </DisconnectButton>
      </div>
    </div>
  );
};

// Main VideoRoom Component
const VideoRoom: React.FC<VideoRoomProps> = ({ 
  token, 
  serverUrl, 
  roomName, 
  displayName, 
  onLeave 
}) => {
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.Disconnected);

  const handleDisconnected = () => {
    toast.success('You have left the meeting');
    onLeave();
  };

  const handleError = (error: Error) => {
    console.error('Room error:', error);
    toast.error(`Connection error: ${error.message}`);
  };

  const handleConnectionStateChanged = (state: ConnectionState) => {
    setConnectionState(state);
    
    switch (state) {
      case ConnectionState.Connected:
        toast.success('Connected to meeting');
        break;
      case ConnectionState.Connecting:
        toast.loading('Connecting to meeting...');
        break;
      case ConnectionState.Disconnected:
        toast.dismiss();
        break;
      case ConnectionState.Reconnecting:
        toast.loading('Reconnecting...');
        break;
    }
  };

  return (
    <div className="video-room-container">
      <LiveKitRoom
        video={true}
        audio={true}
        token={token}
        serverUrl={serverUrl}
        data-lk-theme="default"
        style={{ height: '100vh' }}
        onDisconnected={handleDisconnected}
        onError={handleError}
        options={{
          adaptiveStream: true,
          dynacast: true,
          videoCaptureDefaults: {
            resolution: { width: 1280, height: 720 },
            facingMode: 'user',
          },
          audioCaptureDefaults: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        }}
      >
        {/* Audio renderer for remote participants */}
        <RoomAudioRenderer />
        
        {/* Start Audio component for iOS Safari */}
        <StartAudio label="Click to enable audio" />
        
        {/* Main video conference layout */}
        <VideoConference />
        
        {/* Custom control bar */}
        <MedicalControlBar onLeave={onLeave} />
      </LiveKitRoom>
    </div>
  );
};

export default VideoRoom; 