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
    
    // DOCTOR FIX: Enhanced logging for doctors
    if (userRole === 'doctor') {
        console.log('🩺 DOCTOR CONNECTION DEBUG:');
        console.log('  Meeting ID:', meetingData.meeting_id);
        console.log('  User Role:', meetingData.user_role);
        console.log('  Token Preview:', meetingData.token ? meetingData.token.substring(0, 50) + '...' : 'NO TOKEN');
        console.log('  LiveKit URL:', meetingData.livekit_url);
        console.log('  Browser:', navigator.userAgent);
        console.log('  Timestamp:', new Date().toISOString());
    }
    
    try {
        room = createStableRoom();
        console.log('✅ Room created successfully');
        
        // Setup basic event handlers
        room.on(LiveKit.RoomEvent.Connected, async () => {
            console.log('✅ Connected to meeting!');
            
            // DOCTOR FIX: Additional debug info on connection
            if (userRole === 'doctor') {
                console.log('🩺 DOCTOR CONNECTED - Room Details:');
                console.log('  Local Participant:', room.localParticipant?.identity);
                console.log('  Room Name:', room.name);
                console.log('  Connection State:', room.state);
                console.log('  Can Publish Video:', room.localParticipant?.permissions?.canPublish);
            }
            
            // IMMEDIATE UI FIX: Create local participant container right away
            console.log('🎯 Creating local participant container...');
            const localContainer = createParticipantContainer(room.localParticipant);
            console.log('✅ Local participant container created');
            
            // TIMING FIX: Wait a moment for room to be fully ready before enabling media
            console.log('⏳ Waiting for room to be fully ready...');
            setTimeout(async () => {
                console.log('🎬 Room should be ready now, enabling media...');
                await enableLocalMedia();
                updateUI();
            }, 1500);
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
            
            // DOCTOR FIX: Special handling for doctor disconnections
            if (userRole === 'doctor') {
                console.log('🩺 DOCTOR DISCONNECTED:', reason);
                
                if (reason !== LiveKit.DisconnectReason.CLIENT_INITIATED) {
                    // Show doctor-specific reconnection message
                    showEarlyWarning('Verbindung verloren', 'Als Arzt versuche ich automatisch eine Wiederverbindung...');
                }
            }
            
            if (reason !== LiveKit.DisconnectReason.CLIENT_INITIATED) {
                setTimeout(reconnectToMeeting, 3000);
            }
        });
        
        // Add more specific error handlers
        room.on(LiveKit.RoomEvent.ConnectionQualityChanged, (quality, participant) => {
            console.log('📶 Connection quality changed:', quality, participant?.identity);
            
            // DOCTOR FIX: Warn doctor about poor connection quality
            if (userRole === 'doctor' && quality === 'poor') {
                showEarlyWarning('Schlechte Verbindungsqualität', 'Ihre Internetverbindung ist möglicherweise zu schwach für eine stabile Video-Übertragung.');
            }
        });
        
        room.on(LiveKit.RoomEvent.MediaDevicesError, (error) => {
            console.error('🎥 Media devices error:', error);
            
            // DOCTOR FIX: Show specific help for doctors with media errors
            if (userRole === 'doctor') {
                console.error('🩺 DOCTOR MEDIA ERROR:', error);
                showEarlyWarning('Kamera/Mikrofon Problem', 'Klicken Sie auf das Hilfe-Symbol (?) für Lösungsschritte.');
                
                // Show the help button
                const helpButton = document.getElementById('cameraHelp');
                if (helpButton) {
                    helpButton.style.display = 'block';
                    helpButton.style.background = '#ea4335';
                    helpButton.style.animation = 'pulse 2s infinite';
                }
            }
        });
        
        room.on(LiveKit.RoomEvent.ConnectionStateChanged, (state) => {
            console.log('🔌 Connection state changed:', state);
            
            // DOCTOR FIX: Log state changes for doctors
            if (userRole === 'doctor') {
                console.log('🩺 DOCTOR CONNECTION STATE:', state);
            }
        });
        
        // Connect to room with detailed logging
        console.log('🌐 Attempting LiveKit connection...');
        console.log('📡 URL:', meetingData.livekit_url);
        console.log('🎫 Token preview:', meetingData.token.substring(0, 50) + '...');
        
        await room.connect(meetingData.livekit_url, meetingData.token);
        
        console.log('🎉 LiveKit connection successful!');
        
        // DOCTOR FIX: Store successful connection info for doctors
        if (userRole === 'doctor') {
            const connectionInfo = {
                connected_at: new Date().toISOString(),
                meeting_id: meetingData.meeting_id,
                room_name: room.name,
                participant_id: room.localParticipant?.sid,
                success: true
            };
            sessionStorage.setItem('doctorConnectionInfo', JSON.stringify(connectionInfo));
        }
        
    } catch (error) {
        console.error('❌ Connection failed:', error);
        console.error('❌ Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        
        // DOCTOR FIX: Enhanced error logging for doctors
        if (userRole === 'doctor') {
            console.error('🩺 DOCTOR CONNECTION FAILED:');
            console.error('  Error Type:', error.name);
            console.error('  Error Message:', error.message);
            console.error('  Meeting ID:', meetingData.meeting_id);
            console.error('  LiveKit URL:', meetingData.livekit_url);
            console.error('  Token Length:', meetingData.token ? meetingData.token.length : 0);
            
            // Store error info for support
            const errorInfo = {
                error_at: new Date().toISOString(),
                error_name: error.name,
                error_message: error.message,
                meeting_id: meetingData.meeting_id,
                user_role: userRole,
                browser: navigator.userAgent
            };
            sessionStorage.setItem('doctorConnectionError', JSON.stringify(errorInfo));
        }
        
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
    console.log('🎥 ENABLING LOCAL MEDIA - LiveKit Corrected Method');
    
    if (!room || !room.localParticipant) {
        console.error('❌ No room or local participant available');
        return;
    }
    
    console.log('🎯 Room state:', room.state);
    console.log('🎯 Local participant identity:', room.localParticipant.identity);
    
    try {
        // STEP 1: Enable camera using correct LiveKit API
        if (videoEnabled) {
            console.log('🎬 Enabling camera via LiveKit setCameraEnabled...');
            try {
                await room.localParticipant.setCameraEnabled(true);
                console.log('✅ LiveKit setCameraEnabled(true) successful!');
                
                // CORRECT: Wait for track to be published and use proper API
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // CORRECT: Use videoTrackPublications instead of getTrackPublication
                console.log('🔍 Looking for published video tracks...');
                console.log('📊 Video track publications:', room.localParticipant.videoTrackPublications.size);
                
                let videoTrack = null;
                room.localParticipant.videoTrackPublications.forEach((publication) => {
                    console.log('📹 Found video publication:', {
                        source: publication.source,
                        kind: publication.kind,
                        trackSid: publication.trackSid,
                        hasTrack: !!publication.track
                    });
                    
                    // CORRECT: Check for camera source specifically
                    if (publication.source === LiveKit.TrackSource.Camera && publication.track) {
                        videoTrack = publication.track;
                        console.log('✅ Found camera track!');
                    }
                });
                
                if (videoTrack) {
                    console.log('🎯 Attaching video track to local element...');
                    
                    // Find local video element
                    const localVideo = document.querySelector('.participant-container.local video');
                    if (localVideo) {
                        // CORRECT: Use LiveKit's attach method
                        videoTrack.attach(localVideo);
                        localVideo.muted = true;
                        
                        // Force play with error handling
                        try {
                            await localVideo.play();
                            console.log('✅ Video playing successfully!');
                        } catch (playError) {
                            console.log('⚠️ Video autoplay blocked, user interaction needed:', playError);
                            // Add click handler to start video
                            localVideo.addEventListener('click', () => {
                                localVideo.play().catch(e => console.log('Manual play failed:', e));
                            });
                        }
                        
                        // Remove placeholder
                        const placeholder = localVideo.closest('.participant-container').querySelector('.video-placeholder');
                        if (placeholder) {
                            placeholder.remove();
                            console.log('✅ Video placeholder removed');
                        }
                        
                        console.log('✅ Video track attached and playing!');
                    } else {
                        console.error('❌ No local video element found');
                    }
                } else {
                    console.warn('⚠️ No camera track found after setCameraEnabled');
                    console.log('🔍 Available video publications:');
                    room.localParticipant.videoTrackPublications.forEach((pub) => {
                        console.log('  -', pub.source, pub.kind, !!pub.track);
                    });
                }
                
            } catch (cameraError) {
                console.error('❌ LiveKit camera enable failed:', cameraError);
                throw cameraError;
            }
        }
        
        // STEP 2: Enable microphone
        if (audioEnabled) {
            console.log('🎤 Enabling microphone via LiveKit...');
            try {
                await room.localParticipant.setMicrophoneEnabled(true);
                console.log('✅ LiveKit microphone enabled successfully!');
            } catch (micError) {
                console.error('❌ LiveKit microphone enable failed:', micError);
                // Don't throw here, camera is more important
            }
        }
        
        // STEP 3: Update UI state
        console.log('🎯 Updating UI state...');
        
        // Remove loading state
        const loadingState = document.getElementById('loadingState');
        if (loadingState) {
            loadingState.remove();
            console.log('✅ Loading state removed');
        }
        
        // Update button states
        const toggleVideo = document.getElementById('toggleVideo');
        const toggleMic = document.getElementById('toggleMic');
        if (toggleVideo) {
            toggleVideo.classList.toggle('active', videoEnabled);
        }
        if (toggleMic) {
            toggleMic.classList.toggle('active', audioEnabled);
        }
        
        console.log('🎉 LOCAL MEDIA SETUP COMPLETED SUCCESSFULLY!');
        
    } catch (error) {
        console.error('❌ LOCAL MEDIA SETUP FAILED:', error);
        
        // Show user-friendly error
        const localContainer = document.querySelector('.participant-container.local');
        if (localContainer) {
            const placeholder = localContainer.querySelector('.video-placeholder') || 
                               localContainer.querySelector('div[style*="text-align: center"]');
            
            if (placeholder) {
                placeholder.innerHTML = `
                    <div style="color: white; text-align: center; padding: 20px;">
                        <div style="font-size: 32px; margin-bottom: 10px;">📷❌</div>
                        <div style="font-weight: bold; margin-bottom: 10px;">Kamera Problem</div>
                        <div style="font-size: 14px; margin-bottom: 15px;">${error.message}</div>
                        <div style="font-size: 12px; color: #ccc; margin-bottom: 15px;">
                            Klicken Sie auf das 🔒 in der Adressleiste<br>
                            und erlauben Sie Kamera-Zugriff
                        </div>
                        <button onclick="location.reload()" style="
                            padding: 8px 16px;
                            background: #4285f4;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 12px;
                        ">Seite neu laden</button>
                    </div>
                `;
            }
        }
        
        // Remove loading state even on error
        const loadingState = document.getElementById('loadingState');
        if (loadingState) {
            loadingState.remove();
        }
        
        // DOCTOR FIX: Show help for doctors
        if (userRole === 'doctor') {
            const helpButton = document.getElementById('cameraHelp');
            if (helpButton) {
                helpButton.style.display = 'block';
                helpButton.style.background = '#ea4335';
                helpButton.style.animation = 'pulse 2s infinite';
            }
        }
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
    container.style.cssText = `
        position: relative;
        background: #2d2d2d;
        border-radius: 8px;
        overflow: hidden;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    `;
    
    const nameLabel = document.createElement('div');
    nameLabel.className = 'participant-name';
    nameLabel.textContent = isLocal ? 'Sie' : participant.identity;
    nameLabel.style.cssText = `
        position: absolute;
        bottom: 10px;
        left: 10px;
        background: rgba(0,0,0,0.7);
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 14px;
        z-index: 10;
    `;
    
    // Add placeholder when no video
    const placeholder = document.createElement('div');
    placeholder.className = 'video-placeholder';
    placeholder.innerHTML = `
        <div style="text-align: center; color: #888;">
            <div style="font-size: 48px; margin-bottom: 10px;">👤</div>
            <div>${isLocal ? 'Ihre Kamera wird geladen...' : 'Wartet auf Video...'}</div>
        </div>
    `;
    placeholder.style.cssText = `
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #1a1a1a;
    `;
    
    container.appendChild(placeholder);
    container.appendChild(nameLabel);
    
    const videoGrid = document.getElementById('videoGrid');
    const loadingState = document.getElementById('loadingState');
    
    // IMPORTANT: Remove loading state when first participant appears
    if (loadingState) {
        console.log('🎯 Removing loading state - participant container created');
        loadingState.remove();
    }
    
    videoGrid.appendChild(container);
    participants.set(participant.sid, container);
    
    console.log(`✅ Participant container created for: ${isLocal ? 'local' : participant.identity}`);
    
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
    console.log('📹 Attaching video track for:', participant.identity);
    
    // Remove placeholder if it exists
    const placeholder = container.querySelector('.video-placeholder');
    if (placeholder) {
        console.log('🎯 Removing video placeholder');
        placeholder.remove();
    }
    
    // Remove existing video
    const existingVideo = container.querySelector('video');
    if (existingVideo) {
        existingVideo.remove();
    }
    
    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    video.muted = participant === room.localParticipant;
    video.style.cssText = `
        width: 100%;
        height: 100%;
        object-fit: cover;
        background: #000;
    `;
    
    track.attach(video);
    container.appendChild(video);
    
    console.log('✅ Video track attached and placeholder removed for:', participant.identity);
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
    
    // DOCTOR FIX: Add system diagnostics for doctors
    if (userRole === 'doctor') {
        await runDoctorDiagnostics();
    }
    
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

// DOCTOR FIX: Run diagnostics specifically for doctors
async function runDoctorDiagnostics() {
    console.log('🩺 Running doctor diagnostics...');
    
    // Check browser support
    const diagnostics = {
        browser: navigator.userAgent,
        webrtc_support: !!(window.RTCPeerConnection || window.webkitRTCPeerConnection),
        getUserMedia_support: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
        livekit_loaded: typeof window.LiveKit !== 'undefined',
        url: window.location.href,
        timestamp: new Date().toISOString()
    };
    
    console.log('🔧 DOCTOR DIAGNOSTICS:', diagnostics);
    
    // Check media devices
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const cameras = devices.filter(device => device.kind === 'videoinput');
            const microphones = devices.filter(device => device.kind === 'audioinput');
            
            console.log('📹 Available cameras:', cameras.length);
            console.log('🎤 Available microphones:', microphones.length);
            
            diagnostics.available_cameras = cameras.length;
            diagnostics.available_microphones = microphones.length;
            
            // If no cameras found, show early warning
            if (cameras.length === 0) {
                console.warn('⚠️ No cameras detected! This may cause issues.');
                showEarlyWarning('Keine Kamera erkannt', 'Es wurde keine Kamera gefunden. Bitte prüfen Sie Ihre Hardware-Verbindung.');
            }
            
        } catch (deviceError) {
            console.error('❌ Device enumeration failed:', deviceError);
            diagnostics.device_error = deviceError.message;
        }
    }
    
    // Store diagnostics for support
    sessionStorage.setItem('doctorDiagnostics', JSON.stringify(diagnostics));
    
    return diagnostics;
}

// DOCTOR FIX: Show early warning messages
function showEarlyWarning(title, message) {
    const warningDiv = document.createElement('div');
    warningDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 15px;
        border-radius: 8px;
        max-width: 300px;
        z-index: 1000;
        font-size: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    
    warningDiv.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 5px;">${title}</div>
        <div>${message}</div>
        <button onclick="this.parentElement.remove()" style="
            margin-top: 10px;
            background: #856404;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        ">Verstanden</button>
    `;
    
    document.body.appendChild(warningDiv);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (warningDiv.parentElement) {
            warningDiv.remove();
        }
    }, 10000);
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
    
    // DOCTOR FIX: Camera help button
    const cameraHelp = document.getElementById('cameraHelp');
    if (cameraHelp) {
        cameraHelp.addEventListener('click', () => {
            showCameraHelpModal();
        });
        
        // Show help button for doctors
        if (userRole === 'doctor') {
            cameraHelp.style.display = 'block';
        }
    }
    
    // DOCTOR FIX: Help modal buttons
    const copyDiagnostics = document.getElementById('copyDiagnostics');
    if (copyDiagnostics) {
        copyDiagnostics.addEventListener('click', copyDiagnosticsToClipboard);
    }
    
    const refreshPage = document.getElementById('refreshPage');
    if (refreshPage) {
        refreshPage.addEventListener('click', () => {
            location.reload();
        });
    }
}

// DOCTOR FIX: Show camera help modal
function showCameraHelpModal() {
    const modal = document.getElementById('cameraHelpModal');
    const diagnosticsInfo = document.getElementById('diagnosticsInfo');
    
    if (modal) {
        modal.classList.add('show');
        
        // Load and display diagnostics
        const storedDiagnostics = sessionStorage.getItem('doctorDiagnostics');
        if (storedDiagnostics && diagnosticsInfo) {
            const diagnostics = JSON.parse(storedDiagnostics);
            diagnosticsInfo.innerHTML = `
Browser: ${diagnostics.browser}<br>
WebRTC Support: ${diagnostics.webrtc_support ? '✅' : '❌'}<br>
getUserMedia Support: ${diagnostics.getUserMedia_support ? '✅' : '❌'}<br>
LiveKit Loaded: ${diagnostics.livekit_loaded ? '✅' : '❌'}<br>
Available Cameras: ${diagnostics.available_cameras || 'Unknown'}<br>
Available Microphones: ${diagnostics.available_microphones || 'Unknown'}<br>
URL: ${diagnostics.url}<br>
Timestamp: ${new Date(diagnostics.timestamp).toLocaleString()}<br>
${diagnostics.device_error ? `Device Error: ${diagnostics.device_error}<br>` : ''}
            `.trim();
        }
    }
}

// DOCTOR FIX: Copy diagnostics to clipboard
async function copyDiagnosticsToClipboard() {
    const storedDiagnostics = sessionStorage.getItem('doctorDiagnostics');
    if (storedDiagnostics) {
        try {
            const diagnostics = JSON.parse(storedDiagnostics);
            const diagnosticsText = `
HeyDok Video - Diagnose Report
=================================
Browser: ${diagnostics.browser}
WebRTC Support: ${diagnostics.webrtc_support ? 'Yes' : 'No'}
getUserMedia Support: ${diagnostics.getUserMedia_support ? 'Yes' : 'No'}
LiveKit Loaded: ${diagnostics.livekit_loaded ? 'Yes' : 'No'}
Available Cameras: ${diagnostics.available_cameras || 'Unknown'}
Available Microphones: ${diagnostics.available_microphones || 'Unknown'}
URL: ${diagnostics.url}
Timestamp: ${new Date(diagnostics.timestamp).toLocaleString()}
${diagnostics.device_error ? `Device Error: ${diagnostics.device_error}` : ''}
Meeting ID: ${meetingId}
User Role: ${userRole}
            `.trim();
            
            await navigator.clipboard.writeText(diagnosticsText);
            
            // Show confirmation
            const button = document.getElementById('copyDiagnostics');
            const originalText = button.textContent;
            button.textContent = '✅ Kopiert!';
            button.style.background = '#34a853';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
            }, 2000);
            
        } catch (error) {
            console.error('Failed to copy diagnostics:', error);
            alert('Konnte Diagnose nicht kopieren. Bitte verwenden Sie Strg+A und Strg+C im Diagnose-Bereich.');
        }
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