import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  LiveKitRoom,
  VideoConference,
  GridLayout,
  ParticipantTile,
  ControlBar,
  RoomAudioRenderer,
  useTracks,
} from '@livekit/components-react';
import '@livekit/components-styles';
import { Track } from 'livekit-client';
import { meetingApi } from '../services/api';
import toast from 'react-hot-toast';

const MeetingRoom: React.FC = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(null);
  const [serverUrl, setServerUrl] = useState<string | null>(null);
  const [participantId, setParticipantId] = useState<string | null>(null);

  useEffect(() => {
    // Hole die Meeting-Daten aus dem SessionStorage
    const storedToken = sessionStorage.getItem('meetingToken');
    const storedUrl = sessionStorage.getItem('livekitUrl');
    const storedParticipantId = sessionStorage.getItem('participantId');

    if (!storedToken || !storedUrl) {
      // Wenn keine Daten vorhanden sind, zurück zur Lobby
      navigate(`/meeting/${meetingId}`);
      return;
    }

    setToken(storedToken);
    setServerUrl(storedUrl);
    setParticipantId(storedParticipantId);
  }, [meetingId, navigate]);

  const handleDisconnect = async () => {
    // Meeting verlassen
    if (meetingId && participantId) {
      try {
        await meetingApi.leaveMeeting(meetingId, participantId);
      } catch (error) {
        console.error('Error leaving meeting:', error);
      }
    }

    // SessionStorage leeren
    sessionStorage.clear();
    
    // Zur Homepage navigieren
    navigate('/');
    toast.success('Meeting verlassen');
  };

  if (!token || !serverUrl) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Lade Meeting...</div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-900">
      <LiveKitRoom
        video={true}
        audio={true}
        token={token}
        serverUrl={serverUrl}
        onDisconnected={handleDisconnect}
        data-lk-theme="default"
        style={{ height: '100vh' }}
      >
        <MyVideoConference />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
};

// Custom Video Conference Component für Google Meet Style
function MyVideoConference() {
  const tracks = useTracks(
    [
      { source: Track.Source.Camera, withPlaceholder: true },
      { source: Track.Source.ScreenShare, withPlaceholder: false },
    ],
    { onlySubscribed: false }
  );

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Main video grid */}
      <div className="flex-1 p-4">
        <GridLayout tracks={tracks}>
          <ParticipantTile />
        </GridLayout>
      </div>

      {/* Control bar at bottom */}
      <div className="bg-gray-800 border-t border-gray-700">
        <ControlBar 
          variation="verbose"
          controls={{
            camera: true,
            microphone: true,
            screenShare: true,
            chat: false,
            leave: true,
          }}
        />
      </div>
    </div>
  );
}

export default MeetingRoom; 