import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Video, Mic, MicOff, VideoOff, ArrowLeft } from 'lucide-react';
import { meetingApi } from '../services/api';
import toast from 'react-hot-toast';

const MeetingLobby: React.FC = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState('');
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isAudioOn, setIsAudioOn] = useState(true);
  const [isJoining, setIsJoining] = useState(false);
  const [meetingInfo, setMeetingInfo] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Meeting-Info abrufen
    const fetchMeetingInfo = async () => {
      if (!meetingId) return;
      
      try {
        const info = await meetingApi.getMeetingInfo(meetingId);
        setMeetingInfo(info);
      } catch (error) {
        toast.error('Meeting nicht gefunden oder abgelaufen');
        navigate('/');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMeetingInfo();
  }, [meetingId, navigate]);

  const handleJoinMeeting = async () => {
    if (!displayName.trim()) {
      toast.error('Bitte geben Sie Ihren Namen ein');
      return;
    }

    if (!meetingId) return;

    try {
      setIsJoining(true);
      const response = await meetingApi.joinMeeting(meetingId, displayName);
      
      // Speichere die Meeting-Daten im SessionStorage
      sessionStorage.setItem('meetingToken', response.token);
      sessionStorage.setItem('livekitUrl', response.livekit_url);
      sessionStorage.setItem('participantId', response.participant_id);
      sessionStorage.setItem('displayName', displayName);
      sessionStorage.setItem('isVideoOn', isVideoOn.toString());
      sessionStorage.setItem('isAudioOn', isAudioOn.toString());
      
      // Navigiere zur Video-Seite
      navigate(`/meeting/${meetingId}/room`);
    } catch (error) {
      toast.error('Fehler beim Beitreten des Meetings');
      console.error('Error joining meeting:', error);
    } finally {
      setIsJoining(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Lade Meeting-Informationen...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              <span>Zurück</span>
            </button>
            <div className="text-gray-300">
              Meeting-Code: <span className="font-mono font-medium text-white">{meetingId}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <div className="bg-gray-800 rounded-2xl p-8 shadow-xl">
            <h2 className="text-2xl font-bold text-white mb-6 text-center">
              Bereit zum Beitreten?
            </h2>

            {/* Video Preview */}
            <div className="bg-gray-900 rounded-lg h-48 mb-6 flex items-center justify-center relative">
              {isVideoOn ? (
                <div className="text-gray-500">
                  <Video className="h-12 w-12" />
                  <p className="text-sm mt-2">Kamera-Vorschau</p>
                </div>
              ) : (
                <div className="text-gray-500">
                  <VideoOff className="h-12 w-12" />
                  <p className="text-sm mt-2">Kamera ist aus</p>
                </div>
              )}
            </div>

            {/* Controls */}
            <div className="flex justify-center space-x-4 mb-6">
              <button
                onClick={() => setIsAudioOn(!isAudioOn)}
                className={`p-3 rounded-full transition-colors ${
                  isAudioOn
                    ? 'bg-gray-700 hover:bg-gray-600 text-white'
                    : 'bg-red-600 hover:bg-red-700 text-white'
                }`}
              >
                {isAudioOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
              </button>
              <button
                onClick={() => setIsVideoOn(!isVideoOn)}
                className={`p-3 rounded-full transition-colors ${
                  isVideoOn
                    ? 'bg-gray-700 hover:bg-gray-600 text-white'
                    : 'bg-red-600 hover:bg-red-700 text-white'
                }`}
              >
                {isVideoOn ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
              </button>
            </div>

            {/* Name Input */}
            <div className="mb-6">
              <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">
                Ihr Name
              </label>
              <input
                id="name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleJoinMeeting()}
                placeholder="Geben Sie Ihren Namen ein"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                autoFocus
              />
            </div>

            {/* Join Button */}
            <button
              onClick={handleJoinMeeting}
              disabled={isJoining || !displayName.trim()}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isJoining ? 'Trete bei...' : 'Jetzt teilnehmen'}
            </button>

            {/* Meeting Info */}
            {meetingInfo && (
              <div className="mt-4 text-center text-sm text-gray-400">
                {meetingInfo.name && <p>{meetingInfo.name}</p>}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default MeetingLobby; 