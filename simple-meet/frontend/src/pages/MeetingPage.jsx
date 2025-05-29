import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  IconButton,
  Grid,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Mic,
  MicOff,
  Videocam,
  VideocamOff,
  CallEnd,
  PresentToAll,
  Chat,
  People,
} from '@mui/icons-material';
import io from 'socket.io-client';

const SOCKET_SERVER = import.meta.env.VITE_SOCKET_SERVER || 
  (import.meta.env.PROD ? window.location.origin : 'http://localhost:5001');

function MeetingPage() {
  const { roomId } = useParams();
  const navigate = useNavigate();
  
  // State
  const [userName, setUserName] = useState('');
  const [hasJoined, setHasJoined] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isAudioOn, setIsAudioOn] = useState(true);
  const [participants, setParticipants] = useState([]);
  const [showNameDialog, setShowNameDialog] = useState(true);
  
  // Refs
  const socketRef = useRef();
  const localVideoRef = useRef();
  const localStreamRef = useRef();
  const peersRef = useRef({});
  const remoteStreamsRef = useRef({});
  
  // WebRTC configuration
  const iceServers = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
    ],
  };

  // Initialize media stream
  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      
      localStreamRef.current = stream;
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
      
      // Set initial mute states
      stream.getAudioTracks()[0].enabled = isAudioOn;
      stream.getVideoTracks()[0].enabled = isVideoOn;
    } catch (error) {
      console.error('Fehler beim Zugriff auf Mediengeräte:', error);
      alert('Bitte erlauben Sie den Zugriff auf Kamera und Mikrofon.');
    }
  };

  // Join meeting
  const joinMeeting = () => {
    if (!userName.trim()) {
      alert('Bitte geben Sie Ihren Namen ein.');
      return;
    }
    
    setShowNameDialog(false);
    setHasJoined(true);
    
    // Initialize socket connection
    socketRef.current = io(SOCKET_SERVER);
    
    // Join room
    socketRef.current.emit('join-room', { roomId, userName });
    
    // Socket event handlers
    socketRef.current.on('existing-participants', (existingParticipants) => {
      setParticipants(existingParticipants);
      
      // Create peer connections for existing participants
      existingParticipants.forEach(participant => {
        createPeerConnection(participant.userId, true);
      });
    });
    
    socketRef.current.on('user-joined', ({ userId, userName }) => {
      setParticipants(prev => [...prev, { userId, userName }]);
      createPeerConnection(userId, false);
    });
    
    socketRef.current.on('user-left', ({ userId }) => {
      setParticipants(prev => prev.filter(p => p.userId !== userId));
      if (peersRef.current[userId]) {
        peersRef.current[userId].close();
        delete peersRef.current[userId];
        delete remoteStreamsRef.current[userId];
      }
    });
    
    socketRef.current.on('offer', async ({ offer, from, userName }) => {
      const pc = peersRef.current[from];
      if (pc) {
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        socketRef.current.emit('answer', { answer, to: from });
      }
    });
    
    socketRef.current.on('answer', async ({ answer, from }) => {
      const pc = peersRef.current[from];
      if (pc) {
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
      }
    });
    
    socketRef.current.on('ice-candidate', ({ candidate, from }) => {
      const pc = peersRef.current[from];
      if (pc) {
        pc.addIceCandidate(new RTCIceCandidate(candidate));
      }
    });
  };

  // Create peer connection
  const createPeerConnection = async (userId, createOffer) => {
    const pc = new RTCPeerConnection(iceServers);
    peersRef.current[userId] = pc;
    
    // Add local stream
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => {
        pc.addTrack(track, localStreamRef.current);
      });
    }
    
    // Handle remote stream
    pc.ontrack = (event) => {
      remoteStreamsRef.current[userId] = event.streams[0];
      // Force re-render to show new video
      setParticipants(prev => [...prev]);
    };
    
    // Handle ICE candidates
    pc.onicecandidate = (event) => {
      if (event.candidate) {
        socketRef.current.emit('ice-candidate', {
          candidate: event.candidate,
          to: userId,
        });
      }
    };
    
    // Create offer if needed
    if (createOffer) {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      socketRef.current.emit('offer', { offer, to: userId });
    }
  };

  // Toggle video
  const toggleVideo = () => {
    if (localStreamRef.current) {
      const videoTrack = localStreamRef.current.getVideoTracks()[0];
      videoTrack.enabled = !videoTrack.enabled;
      setIsVideoOn(videoTrack.enabled);
    }
  };

  // Toggle audio
  const toggleAudio = () => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0];
      audioTrack.enabled = !audioTrack.enabled;
      setIsAudioOn(audioTrack.enabled);
    }
  };

  // Leave meeting
  const leaveMeeting = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
    navigate('/');
  };

  // Initialize media on component mount
  useEffect(() => {
    initializeMedia();
    
    return () => {
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
      }
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  // Video component with Google Meet style layout
  const VideoTile = ({ stream, userName, isLocal = false, isMainView = false }) => {
    const videoRef = useRef();
    
    useEffect(() => {
      if (videoRef.current && stream) {
        videoRef.current.srcObject = stream;
      }
    }, [stream]);
    
    return (
      <Paper
        elevation={3}
        sx={{
          position: 'relative',
          paddingTop: isMainView ? '56.25%' : '75%', // Different aspect ratios
          backgroundColor: '#202124',
          overflow: 'hidden',
          borderRadius: isMainView ? 2 : 1,
        }}
      >
        <video
          ref={isLocal ? localVideoRef : videoRef}
          autoPlay
          playsInline
          muted={isLocal}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            bottom: 8,
            left: 8,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            color: 'white',
            px: 1,
            py: 0.5,
            borderRadius: 1,
            fontSize: isMainView ? '1rem' : '0.875rem',
          }}
        >
          {userName} {isLocal && '(Sie)'}
        </Box>
      </Paper>
    );
  };

  // Google Meet style layout
  const renderVideoLayout = () => {
    const allParticipants = [
      { userId: 'local', userName, isLocal: true, stream: localStreamRef.current },
      ...participants.map(p => ({ 
        ...p, 
        isLocal: false, 
        stream: remoteStreamsRef.current[p.userId] 
      }))
    ];

    if (allParticipants.length === 1) {
      // Only local user - show large
      return (
        <Box sx={{ height: '100%', p: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Box sx={{ width: '100%', maxWidth: 800 }}>
            <VideoTile
              stream={localStreamRef.current}
              userName={userName}
              isLocal={true}
              isMainView={true}
            />
          </Box>
        </Box>
      );
    }

    if (allParticipants.length === 2) {
      // Two participants - show side by side
      return (
        <Box sx={{ height: '100%', p: 2 }}>
          <Grid container spacing={2} sx={{ height: '100%' }}>
            <Grid item xs={6} sx={{ height: '100%' }}>
              <VideoTile
                stream={allParticipants[0].stream}
                userName={allParticipants[0].userName}
                isLocal={allParticipants[0].isLocal}
                isMainView={true}
              />
            </Grid>
            <Grid item xs={6} sx={{ height: '100%' }}>
              <VideoTile
                stream={allParticipants[1].stream}
                userName={allParticipants[1].userName}
                isLocal={allParticipants[1].isLocal}
                isMainView={true}
              />
            </Grid>
          </Grid>
        </Box>
      );
    }

    // More than 2 participants - Google Meet style with main view and sidebar
    const mainParticipant = allParticipants.find(p => !p.isLocal) || allParticipants[0];
    const sidebarParticipants = allParticipants.filter(p => p.userId !== mainParticipant.userId);

    return (
      <Box sx={{ height: '100%', display: 'flex', p: 2, gap: 2 }}>
        {/* Main video area */}
        <Box sx={{ flex: 1 }}>
          <VideoTile
            stream={mainParticipant.stream}
            userName={mainParticipant.userName}
            isLocal={mainParticipant.isLocal}
            isMainView={true}
          />
        </Box>
        
        {/* Sidebar with other participants */}
        <Box sx={{ width: 300, display: 'flex', flexDirection: 'column', gap: 1 }}>
          {sidebarParticipants.map((participant) => (
            <Box key={participant.userId} sx={{ height: 200 }}>
              <VideoTile
                stream={participant.stream}
                userName={participant.userName}
                isLocal={participant.isLocal}
              />
            </Box>
          ))}
        </Box>
      </Box>
    );
  };

  return (
    <Box sx={{ height: '100vh', backgroundColor: '#202124' }}>
      {/* Name input dialog */}
      <Dialog open={showNameDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Meeting beitreten</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Meeting-ID: {roomId}
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label="Ihr Name"
            fullWidth
            variant="outlined"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && joinMeeting()}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => navigate('/')}>Abbrechen</Button>
          <Button onClick={joinMeeting} variant="contained">
            Beitreten
          </Button>
        </DialogActions>
      </Dialog>

      {/* Main meeting interface */}
      {hasJoined && (
        <>
          {/* Video layout */}
          <Box sx={{ height: 'calc(100% - 80px)', overflow: 'hidden' }}>
            {renderVideoLayout()}
          </Box>

          {/* Control bar */}
          <Box
            sx={{
              position: 'fixed',
              bottom: 0,
              left: 0,
              right: 0,
              height: 80,
              backgroundColor: '#202124',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
              borderTop: '1px solid #3c4043',
            }}
          >
            <IconButton
              onClick={toggleAudio}
              sx={{
                backgroundColor: isAudioOn ? '#3c4043' : '#ea4335',
                color: 'white',
                '&:hover': {
                  backgroundColor: isAudioOn ? '#5f6368' : '#d33b2c',
                },
              }}
            >
              {isAudioOn ? <Mic /> : <MicOff />}
            </IconButton>

            <IconButton
              onClick={toggleVideo}
              sx={{
                backgroundColor: isVideoOn ? '#3c4043' : '#ea4335',
                color: 'white',
                '&:hover': {
                  backgroundColor: isVideoOn ? '#5f6368' : '#d33b2c',
                },
              }}
            >
              {isVideoOn ? <Videocam /> : <VideocamOff />}
            </IconButton>

            <IconButton
              onClick={leaveMeeting}
              sx={{
                backgroundColor: '#ea4335',
                color: 'white',
                px: 3,
                '&:hover': {
                  backgroundColor: '#d33b2c',
                },
              }}
            >
              <CallEnd />
            </IconButton>

            <IconButton
              sx={{
                backgroundColor: '#3c4043',
                color: 'white',
                '&:hover': {
                  backgroundColor: '#5f6368',
                },
              }}
              disabled
            >
              <PresentToAll />
            </IconButton>

            <IconButton
              sx={{
                backgroundColor: '#3c4043',
                color: 'white',
                '&:hover': {
                  backgroundColor: '#5f6368',
                },
              }}
              disabled
            >
              <Chat />
            </IconButton>

            <IconButton
              sx={{
                backgroundColor: '#3c4043',
                color: 'white',
                '&:hover': {
                  backgroundColor: '#5f6368',
                },
              }}
            >
              <People />
              <Typography
                sx={{
                  ml: 0.5,
                  fontSize: '0.875rem',
                  color: 'white',
                }}
              >
                {participants.length + 1}
              </Typography>
            </IconButton>
          </Box>
        </>
      )}
    </Box>
  );
}

export default MeetingPage; 