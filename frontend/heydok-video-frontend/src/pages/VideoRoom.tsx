import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { roomService } from '../services/rooms';
import {
  LiveKitRoom,
  VideoConference,
  formatChatMessageLinks,
  useToken
} from '@livekit/components-react';
import '@livekit/components-styles';
import { 
  ArrowLeftIcon,
  MicrophoneIcon,
  VideoCameraIcon,
  ComputerDesktopIcon,
  ChatBubbleLeftRightIcon,
  UsersIcon,
  PhoneXMarkIcon
} from '@heroicons/react/24/outline';

const VideoRoom: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [token, setToken] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [roomInfo, setRoomInfo] = useState<any>(null);

  const serverUrl = process.env.REACT_APP_LIVEKIT_URL || 'wss://google-meet-replacer-fcw5apmd.livekit.cloud';

  useEffect(() => {
    if (roomId) {
      loadRoomAndToken();
    }
  }, [roomId]);

  const loadRoomAndToken = async () => {
    try {
      // Get room info
      const room = await roomService.getRoom(roomId!);
      setRoomInfo(room);

      // Get token
      const tokenData = await roomService.getRoomToken(roomId!, user?.email);
      setToken(tokenData.token);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Laden des Raums');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = () => {
    navigate('/dashboard');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-heydok-primary mx-auto mb-4"></div>
          <p className="text-white">Raum wird geladen...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-secondary"
          >
            Zurück zum Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-900">
      {/* Custom Header */}
      <div className="absolute top-0 left-0 right-0 z-50 bg-gray-900/90 backdrop-blur-sm border-b border-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors mr-4"
            >
              <ArrowLeftIcon className="w-5 h-5 text-white" />
            </button>
            <div>
              <h1 className="text-white font-semibold">{roomInfo?.name || 'Video Konferenz'}</h1>
              <p className="text-gray-400 text-sm">Raum ID: {roomId}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-heydok-primary font-bold">heydok</span>
          </div>
        </div>
      </div>

      {/* LiveKit Room */}
      <div className="h-full pt-16">
        <LiveKitRoom
          video={true}
          audio={true}
          token={token}
          serverUrl={serverUrl}
          data-lk-theme="default"
          onDisconnected={handleDisconnect}
          style={{ height: '100%' }}
        >
          <VideoConference 
            chatMessageFormatter={formatChatMessageLinks}
          />
        </LiveKitRoom>
      </div>
    </div>
  );
};

export default VideoRoom; 