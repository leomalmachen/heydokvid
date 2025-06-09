// STABLE MEETING - Optimized for connection stability
console.log('🔧 Loading STABLE meeting configuration...');

// Global variables
let room = null;
let localParticipant = null;
let audioEnabled = true;
let videoEnabled = true;
const participants = new Map();

// Get meeting ID from URL
const pathParts = window.location.pathname.split('/');
const meetingId = pathParts[pathParts.length - 1];

// STABLE: Conservative LiveKit Room Configuration
function createStableRoom() {
    console.log('🏗️ Creating STABLE LiveKit Room...');
    
    const room = new LiveKit.Room({
        // STABILITY: Disable aggressive features
        adaptiveStream: false,
        dynacast: false,
        
        // CONSERVATIVE: Audio settings for maximum compatibility
        audioCaptureDefaults: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: false,  // Prevent audio suppression
            sampleRate: 44100,       // Standard sample rate
            channelCount: 1,         // Mono for stability
        },
        
        // CONSERVATIVE: Video settings
        videoCaptureDefaults: {
            resolution: { width: 640, height: 480 },  // Lower resolution
            frameRate: 15,  // Lower frame rate
        },
        
        // STABLE: Publish settings
        publishDefaults: {
            stopMicTrackOnMute: false,
            audioPreset: LiveKit.AudioPresets.speech,
            videoEncoding: {
                maxBitrate: 300000,      // Lower bitrate for stability
                maxFramerate: 15,
            }
        }
    });
    
    return room;
}

// STABLE: Connect with retry mechanism
async function connectToMeeting(meetingData) {
    console.log('🔗 Connecting to meeting with stable settings...');
    
    try {
        room = createStableRoom();
        
        // Setup basic event handlers
        room.on(LiveKit.RoomEvent.Connected, async () => {
            console.log('✅ Connected to meeting!');
            await enableLocalMedia();
            updateUI();
        });
        
        room.on(LiveKit.RoomEvent.ParticipantConnected, (participant) => {
            console.log('👤 Participant joined:', participant.identity);
            handleParticipantJoined(participant);
        });
        
        room.on(LiveKit.RoomEvent.ParticipantDisconnected, (participant) => {
            console.log('👋 Participant left:', participant.identity);
            handleParticipantLeft(participant);
        });
        
        room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log('📹 Track subscribed:', track.kind, 'from', participant.identity);
            handleTrackSubscribed(track, publication, participant);
        });
        
        room.on(LiveKit.RoomEvent.Disconnected, (reason) => {
            console.log('❌ Disconnected:', reason);
            if (reason !== LiveKit.DisconnectReason.CLIENT_INITIATED) {
                setTimeout(reconnectToMeeting, 3000);
            }
        });
        
        // Connect to room
        await room.connect(meetingData.livekit_url, meetingData.token);
        
    } catch (error) {
        console.error('❌ Connection failed:', error);
        showError('Verbindung fehlgeschlagen: ' + error.message);
    }
}

// STABLE: Enable local media with error handling
async function enableLocalMedia() {
    try {
        console.log('🎥 Enabling local media...');
        
        // Enable camera if available
        if (videoEnabled) {
            await room.localParticipant.enableCameraAndMicrophone();
        } else {
            await room.localParticipant.setMicrophoneEnabled(audioEnabled);
        }
        
        console.log('✅ Local media enabled');
        
    } catch (error) {
        console.error('❌ Failed to enable media:', error);
        // Continue without local media
    }
}

// STABLE: Handle participant joining
function handleParticipantJoined(participant) {
    const container = createParticipantContainer(participant);
    
    // Subscribe to existing tracks
    participant.trackPublications.forEach((publication) => {
        if (publication.isSubscribed && publication.track) {
            handleTrackSubscribed(publication.track, publication, participant);
        }
    });
}

// STABLE: Handle participant leaving
function handleParticipantLeft(participant) {
    const container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        container.remove();
    }
    participants.delete(participant.sid);
    updateUI();
}

// STABLE: Handle track subscription
function handleTrackSubscribed(track, publication, participant) {
    const container = getOrCreateParticipantContainer(participant);
    
    if (track.kind === 'video') {
        attachVideoTrack(track, container, participant);
    } else if (track.kind === 'audio') {
        attachAudioTrack(track, container, participant);
    }
}

// STABLE: Create participant container
function createParticipantContainer(participant) {
    const isLocal = participant === room.localParticipant;
    const containerId = `participant-${participant.sid}`;
    
    let container = document.getElementById(containerId);
    if (container) {
        return container;
    }
    
    container = document.createElement('div');
    container.id = containerId;
    container.className = `participant-container ${isLocal ? 'local' : 'remote'}`;
    
    const nameLabel = document.createElement('div');
    nameLabel.className = 'participant-name';
    nameLabel.textContent = isLocal ? 'Sie' : participant.identity;
    
    container.appendChild(nameLabel);
    
    const videoGrid = document.getElementById('videoGrid');
    const loadingState = document.getElementById('loadingState');
    
    if (loadingState) {
        loadingState.remove();
    }
    
    videoGrid.appendChild(container);
    participants.set(participant.sid, container);
    
    return container;
}

// STABLE: Get or create participant container
function getOrCreateParticipantContainer(participant) {
    let container = participants.get(participant.sid);
    if (!container) {
        container = createParticipantContainer(participant);
    }
    return container;
}

// STABLE: Attach video track
function attachVideoTrack(track, container, participant) {
    const existingVideo = container.querySelector('video');
    if (existingVideo) {
        existingVideo.remove();
    }
    
    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    video.muted = participant === room.localParticipant;
    
    track.attach(video);
    container.appendChild(video);
    
    console.log('📹 Video track attached for:', participant.identity);
}

// STABLE: Attach audio track
function attachAudioTrack(track, container, participant) {
    if (participant === room.localParticipant) {
        return; // Don't play local audio
    }
    
    const existingAudio = container.querySelector('audio');
    if (existingAudio) {
        existingAudio.remove();
    }
    
    const audio = document.createElement('audio');
    audio.autoplay = true;
    
    track.attach(audio);
    container.appendChild(audio);
    
    console.log('🔊 Audio track attached for:', participant.identity);
}

// STABLE: Reconnect function
async function reconnectToMeeting() {
    console.log('🔄 Attempting to reconnect...');
    
    const meetingData = sessionStorage.getItem('meetingData');
    if (meetingData) {
        await connectToMeeting(JSON.parse(meetingData));
    }
}

// STABLE: Update UI
function updateUI() {
    const participantCount = room ? room.remoteParticipants.size + 1 : 1;
    const countElement = document.getElementById('participantCount');
    if (countElement) {
        countElement.textContent = participantCount;
    }
}

// STABLE: Show error
function showError(message) {
    console.error('❌', message);
    alert(message);
}

// STABLE: Initialize meeting
async function initializeStableMeeting() {
    console.log('🚀 Initializing stable meeting...');
    
    try {
        // Get participant name
        const participantName = sessionStorage.getItem('participantName') || 
                              prompt('Ihr Name:') || 'Teilnehmer';
        
        sessionStorage.setItem('participantName', participantName);
        
        // Join meeting
        const response = await fetch(`/api/meetings/${meetingId}/join`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ participant_name: participantName })
        });
        
        if (!response.ok) {
            throw new Error('Failed to join meeting');
        }
        
        const meetingData = await response.json();
        sessionStorage.setItem('meetingData', JSON.stringify(meetingData));
        
        await connectToMeeting(meetingData);
        
    } catch (error) {
        console.error('❌ Failed to initialize meeting:', error);
        showError('Meeting konnte nicht initialisiert werden: ' + error.message);
    }
}

// STABLE: Setup event listeners
function setupStableEventListeners() {
    // Toggle microphone
    const toggleMic = document.getElementById('toggleMic');
    if (toggleMic) {
        toggleMic.addEventListener('click', async () => {
            if (room && room.localParticipant) {
                audioEnabled = !audioEnabled;
                await room.localParticipant.setMicrophoneEnabled(audioEnabled);
                toggleMic.classList.toggle('active', audioEnabled);
            }
        });
    }
    
    // Toggle video
    const toggleVideo = document.getElementById('toggleVideo');
    if (toggleVideo) {
        toggleVideo.addEventListener('click', async () => {
            if (room && room.localParticipant) {
                videoEnabled = !videoEnabled;
                await room.localParticipant.setCameraEnabled(videoEnabled);
                toggleVideo.classList.toggle('active', videoEnabled);
            }
        });
    }
    
    // Leave meeting
    const leaveMeeting = document.getElementById('leaveMeeting');
    if (leaveMeeting) {
        leaveMeeting.addEventListener('click', () => {
            if (room) {
                room.disconnect();
            }
            window.location.href = '/';
        });
    }
}

// STABLE: Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setupStableEventListeners();
        initializeStableMeeting();
    });
} else {
    setupStableEventListeners();
    initializeStableMeeting();
} 