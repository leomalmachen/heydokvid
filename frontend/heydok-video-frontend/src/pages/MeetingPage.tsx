import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Camera, CameraOff, Mic, MicOff, Phone, PhoneOff, Users } from 'lucide-react';
import toast from 'react-hot-toast';
import VideoRoom from '../components/VideoRoom';
import '../styles/MeetingPage.css';

interface MeetingInfo {
  meeting_id: string;
  meeting_url: string;
  created_at: string;
  expires_at: string;
  status: string;
}

const MeetingPage: React.FC = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  
  const [displayName, setDisplayName] = useState('');
  const [isJoining, setIsJoining] = useState(false);
  const [inMeeting, setInMeeting] = useState(false);
  const [meetingInfo, setMeetingInfo] = useState<MeetingInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Media controls
  const [isCameraOn, setIsCameraOn] = useState(true);
  const [isMicOn, setIsMicOn] = useState(true);
  
  // Connection info
  const [token, setToken] = useState('');
  const [livekitUrl, setLivekitUrl] = useState('');

  useEffect(() => {
    fetchMeetingInfo();
  }, [meetingId]);

  const fetchMeetingInfo = async () => {
    try {
      const response = await fetch(`/api/v1/meetings/${meetingId}/info`);
      if (!response.ok) {
        if (response.status === 404) {
          toast.error('Meeting not found');
          navigate('/');
          return;
        }
        throw new Error('Failed to fetch meeting info');
      }
      const data = await response.json();
      setMeetingInfo(data);
      
      if (data.status === 'expired') {
        toast.error('This meeting has expired');
        navigate('/');
      }
    } catch (error) {
      console.error('Error fetching meeting info:', error);
      toast.error('Failed to load meeting information');
    } finally {
      setIsLoading(false);
    }
  };

  const handleJoinMeeting = async () => {
    if (!displayName.trim()) {
      toast.error('Please enter your name');
      return;
    }

    setIsJoining(true);
    try {
      const response = await fetch(`/api/v1/meetings/${meetingId}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          display_name: displayName.trim()
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to join meeting');
      }

      const data = await response.json();
      setToken(data.token);
      setLivekitUrl(data.livekit_url);
      setInMeeting(true);
      toast.success('Joined meeting successfully!');
    } catch (error) {
      console.error('Error joining meeting:', error);
      toast.error('Failed to join meeting');
    } finally {
      setIsJoining(false);
    }
  };

  const handleLeaveMeeting = () => {
    setInMeeting(false);
    setToken('');
    toast.success('You have left the meeting');
    navigate('/');
  };

  if (isLoading) {
    return (
      <div className="meeting-page loading">
        <div className="spinner"></div>
        <p>Loading meeting...</p>
      </div>
    );
  }

  if (inMeeting && token) {
    return (
      <VideoRoom
        token={token}
        serverUrl={livekitUrl}
        roomName={meetingId!}
        displayName={displayName}
        onLeave={handleLeaveMeeting}
      />
    );
  }

  return (
    <div className="meeting-page">
      <div className="meeting-lobby">
        <div className="lobby-container">
          <div className="video-preview">
            <div className="preview-placeholder">
              <Camera size={48} />
              <p>Camera preview will be here</p>
            </div>
            
            <div className="media-controls">
              <button
                className={`control-btn ${!isCameraOn ? 'off' : ''}`}
                onClick={() => setIsCameraOn(!isCameraOn)}
              >
                {isCameraOn ? <Camera size={20} /> : <CameraOff size={20} />}
              </button>
              <button
                className={`control-btn ${!isMicOn ? 'off' : ''}`}
                onClick={() => setIsMicOn(!isMicOn)}
              >
                {isMicOn ? <Mic size={20} /> : <MicOff size={20} />}
              </button>
            </div>
          </div>

          <div className="join-form">
            <h1>Ready to join?</h1>
            <p className="meeting-id">Meeting ID: {meetingId}</p>
            
            <input
              type="text"
              placeholder="Enter your name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleJoinMeeting()}
              className="name-input"
              maxLength={50}
              autoFocus
            />

            <div className="action-buttons">
              <button
                onClick={handleJoinMeeting}
                disabled={isJoining || !displayName.trim()}
                className="join-btn primary"
              >
                {isJoining ? 'Joining...' : 'Join now'}
              </button>
              
              <button
                onClick={() => navigate('/')}
                className="join-btn secondary"
              >
                Back to home
              </button>
            </div>

            <div className="meeting-info-footer">
              <p>No account required • Just enter your name and join</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MeetingPage; 