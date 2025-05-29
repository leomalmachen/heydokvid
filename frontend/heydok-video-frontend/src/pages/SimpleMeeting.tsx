import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LiveKitRoom, VideoConference } from '@livekit/components-react';
import '@livekit/components-styles';
import { joinMeeting, getMeetingInfo } from '../services/meetingService';
import { Loader2 } from 'lucide-react';

export default function SimpleMeeting() {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  const [token, setToken] = useState<string>('');
  const [livekitUrl, setLivekitUrl] = useState<string>('');
  const [displayName, setDisplayName] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [showJoinForm, setShowJoinForm] = useState(true);

  useEffect(() => {
    // Check if meeting exists
    checkMeeting();
  }, [meetingId]);

  const checkMeeting = async () => {
    if (!meetingId) return;
    
    try {
      await getMeetingInfo(meetingId);
    } catch (error) {
      setError('Meeting not found or has expired');
    }
  };

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName.trim() || !meetingId) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await joinMeeting(meetingId, displayName);
      setToken(response.token);
      setLivekitUrl(response.livekit_url);
      setShowJoinForm(false);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to join meeting');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = () => {
    navigate('/');
  };

  if (error && !showJoinForm) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-700 mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  if (showJoinForm) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full">
          <h2 className="text-3xl font-bold text-gray-900 mb-2 text-center">
            Join Meeting
          </h2>
          <p className="text-gray-600 text-center mb-8">
            Meeting ID: <span className="font-mono font-semibold">{meetingId}</span>
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleJoin}>
            <div className="mb-6">
              <label htmlFor="displayName" className="block text-sm font-medium text-gray-700 mb-2">
                Your name
              </label>
              <input
                type="text"
                id="displayName"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your name"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !displayName.trim()}
              className="w-full py-3 px-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <Loader2 className="animate-spin h-5 w-5 mr-2" />
                  Joining...
                </span>
              ) : (
                'Join Meeting'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-gray-800 text-sm"
            >
              ← Back to home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen">
      {token && livekitUrl && (
        <LiveKitRoom
          video={true}
          audio={true}
          token={token}
          serverUrl={livekitUrl}
          onDisconnected={handleDisconnect}
          data-e2ee="false"
        >
          <VideoConference />
        </LiveKitRoom>
      )}
    </div>
  );
} 