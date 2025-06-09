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

// DOCTOR FIX: Get role from URL parameters
const urlParams = new URLSearchParams(window.location.search);
const userRole = urlParams.get('role') || 'patient';
const isDirect = urlParams.get('direct') === 'true';

console.log(`👤 User role detected: ${userRole}, direct access: ${isDirect}`);

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
    console.log('📊 Meeting data:', {
        meeting_id: meetingData.meeting_id,
        livekit_url: meetingData.livekit_url,
        token_length: meetingData.token ? meetingData.token.length : 0,
        user_role: meetingData.user_role
    });
    
    try {
        room = createStableRoom();
        console.log('✅ Room created successfully');
        
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
        
        // Add more specific error handlers
        room.on(LiveKit.RoomEvent.ConnectionQualityChanged, (quality, participant) => {
            console.log('📶 Connection quality changed:', quality, participant?.identity);
        });
        
        room.on(LiveKit.RoomEvent.MediaDevicesError, (error) => {
            console.error('🎥 Media devices error:', error);
        });
        
        room.on(LiveKit.RoomEvent.ConnectionStateChanged, (state) => {
            console.log('🔌 Connection state changed:', state);
        });
        
        // Connect to room with detailed logging
        console.log('🌐 Attempting LiveKit connection...');
        console.log('📡 URL:', meetingData.livekit_url);
        console.log('🎫 Token preview:', meetingData.token.substring(0, 50) + '...');
        
        await room.connect(meetingData.livekit_url, meetingData.token);
        
        console.log('🎉 LiveKit connection successful!');
        
    } catch (error) {
        console.error('❌ Connection failed:', error);
        console.error('❌ Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        
        // More user-friendly error message
        let errorMessage = 'Verbindung fehlgeschlagen';
        if (error.message.includes('401')) {
            errorMessage = 'Token ungültig - bitte Meeting neu starten';
        } else if (error.message.includes('timeout')) {
            errorMessage = 'Verbindung zu langsam - bitte erneut versuchen';
        } else if (error.message.includes('websocket')) {
            errorMessage = 'WebSocket-Verbindung fehlgeschlagen - Firewall prüfen';
        }
        
        showError(errorMessage + ': ' + error.message);
        
        // Try automatic retry after 3 seconds
        setTimeout(() => {
            console.log('🔄 Automatic retry in 3 seconds...');
            connectToMeeting(meetingData);
        }, 3000);
    }
}

// STABLE: Enable local media with error handling
async function enableLocalMedia() {
    try {
        console.log('🎥 Enabling local media...');
        console.log('📹 Video enabled:', videoEnabled);
        console.log('🎤 Audio enabled:', audioEnabled);
        
        if (!room || !room.localParticipant) {
            console.error('❌ No room or local participant available');
            return;
        }
        
        // Try to enable media step by step
        if (audioEnabled && videoEnabled) {
            console.log('🎬 Enabling camera and microphone...');
            await room.localParticipant.enableCameraAndMicrophone();
            console.log('✅ Camera and microphone enabled successfully');
        } else if (audioEnabled) {
            console.log('🎤 Enabling microphone only...');
            await room.localParticipant.setMicrophoneEnabled(true);
            console.log('✅ Microphone enabled successfully');
        } else if (videoEnabled) {
            console.log('📹 Enabling camera only...');
            await room.localParticipant.setCameraEnabled(true);
            console.log('✅ Camera enabled successfully');
        }
        
        console.log('✅ Local media setup completed');
        
        // Remove loading state
        const loadingState = document.getElementById('loadingState');
        if (loadingState) {
            console.log('🎯 Removing loading state');
            loadingState.remove();
        }
        
    } catch (error) {
        console.error('❌ Failed to enable media:', error);
        console.error('❌ Media error details:', {
            name: error.name,
            message: error.message,
            code: error.code
        });
        
        // Continue without local media but inform user
        const loadingState = document.getElementById('loadingState');
        if (loadingState) {
            loadingState.innerHTML = `
                <div class="spinner"></div>
                <p>⚠️ Kamera/Mikrofon nicht verfügbar</p>
                <p>Sie können trotzdem teilnehmen</p>
            `;
        }
        
        // Try to continue without media after 2 seconds
        setTimeout(() => {
            if (loadingState) {
                loadingState.remove();
            }
        }, 2000);
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
        let participantName;
        let apiEndpoint;
        let requestBody;
        
        // DOCTOR FIX: Handle doctor vs patient differently
        if (userRole === 'doctor') {
            console.log('🩺 Doctor joining - using stored meeting data');
            
            // Get doctor name from session storage (set during meeting creation)
            const storedMeetingData = sessionStorage.getItem('doctorMeetingData');
            if (storedMeetingData) {
                const meetingInfo = JSON.parse(storedMeetingData);
                // Extract doctor name from the meeting status
                participantName = meetingInfo.meeting_status?.doctor_name || 'Doctor';
                console.log(`🩺 Using doctor name: ${participantName}`);
            } else {
                // Fallback: fetch meeting info to get doctor name
                console.log('🩺 Fetching meeting info for doctor name...');
                const infoResponse = await fetch(`/api/meetings/${meetingId}/info`);
                if (infoResponse.ok) {
                    const meetingInfo = await infoResponse.json();
                    participantName = meetingInfo.host_name || 'Doctor';
                } else {
                    participantName = 'Doctor';
                }
            }
            
            // Use doctor join endpoint
            apiEndpoint = `/api/meetings/${meetingId}/join-doctor`;
            requestBody = {
                participant_name: participantName,
                participant_role: 'doctor'
            };
            
        } else {
            // Patient flow (existing logic)
            console.log('👤 Patient joining - requesting name');
            participantName = sessionStorage.getItem('participantName') || 
                              prompt('Ihr Name:') || 'Patient';
            
            sessionStorage.setItem('participantName', participantName);
            
            apiEndpoint = `/api/meetings/${meetingId}/join`;
            requestBody = {
                participant_name: participantName,
                participant_role: 'patient'
            };
        }
        
        console.log(`🔗 Joining via ${apiEndpoint} as ${participantName}`);
        
        // Join meeting
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to join meeting');
        }
        
        const meetingData = await response.json();
        sessionStorage.setItem('meetingData', JSON.stringify(meetingData));
        
        console.log('✅ Meeting join successful, connecting to LiveKit...');
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