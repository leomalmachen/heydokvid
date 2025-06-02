// ULTRA-SIMPLE AND BULLETPROOF Meeting App
console.log('🚀 Starting ULTRA-SIMPLE meeting app...');

// GLOBAL STATE - Keep it simple but persistent
let room = null;
let localParticipant = null;
let audioEnabled = true;
let videoEnabled = true;
const participants = new Map();

// BULLETPROOF: Prevent multiple initializations
let isInitializing = false;
let isInitialized = false;

// PERSISTENT STATE: Prevent disconnections on tab switch
let reconnectionAttempts = 0;
const MAX_RECONNECTION_ATTEMPTS = 3;
let isReconnecting = false;
let meetingData = null;

// Get meeting ID from URL
const pathParts = window.location.pathname.split('/');
const meetingId = pathParts[pathParts.length - 1];

// BULLETPROOF: Handle page visibility to prevent disconnects
function handleVisibilityChange() {
    if (document.hidden && room && room.state === 'connected') {
        console.log('🔄 Page hidden, maintaining connection...');
        // Keep connection alive - don't disconnect on tab switch
        return;
    } else if (!document.hidden && room && room.state === 'disconnected') {
        console.log('🔄 Page visible again, attempting reconnection...');
        attemptReconnection();
    }
}

// PERSISTENT: Automatic reconnection logic
async function attemptReconnection() {
    if (isReconnecting || reconnectionAttempts >= MAX_RECONNECTION_ATTEMPTS) {
        return;
    }
    
    isReconnecting = true;
    reconnectionAttempts++;
    
    console.log(`🔄 Attempting reconnection ${reconnectionAttempts}/${MAX_RECONNECTION_ATTEMPTS}...`);
    
    try {
        if (meetingData) {
            await connectToRoom(meetingData);
            reconnectionAttempts = 0; // Reset on successful reconnection
            console.log('✅ Reconnection successful!');
        }
    } catch (error) {
        console.error('❌ Reconnection failed:', error);
        if (reconnectionAttempts >= MAX_RECONNECTION_ATTEMPTS) {
            showError('Verbindung verloren. Bitte Seite neu laden.');
        } else {
            // Try again after delay
            setTimeout(attemptReconnection, 2000);
        }
    } finally {
        isReconnecting = false;
    }
}

// BULLETPROOF: Media state persistence
function saveMediaState() {
    sessionStorage.setItem('audioEnabled', JSON.stringify(audioEnabled));
    sessionStorage.setItem('videoEnabled', JSON.stringify(videoEnabled));
}

function loadMediaState() {
    const savedAudio = sessionStorage.getItem('audioEnabled');
    const savedVideo = sessionStorage.getItem('videoEnabled');
    
    if (savedAudio !== null) {
        audioEnabled = JSON.parse(savedAudio);
    }
    if (savedVideo !== null) {
        videoEnabled = JSON.parse(savedVideo);
    }
    
    console.log('📱 Loaded media state:', { audioEnabled, videoEnabled });
}

// ULTRA-SIMPLE initialization
async function initializeMeeting() {
    // BULLETPROOF: Prevent multiple calls
    if (isInitializing || isInitialized) {
        console.log('⚠️ Meeting already initializing or initialized, skipping...');
        return;
    }
    
    isInitializing = true;
    console.log('🔥 ULTRA-SIMPLE initialization starting...');
    
    try {
        // SECURITY: Check if we're in a secure context
        if (!window.isSecureContext) {
            throw new Error('Diese App benötigt eine sichere HTTPS-Verbindung für Kamera und Mikrofon.');
        }
        
        // Load previous media state
        loadMediaState();
        
        // Set up page visibility handling
        document.addEventListener('visibilitychange', handleVisibilityChange);
        
        // Wait for LiveKit - SIMPLE check
        if (typeof window.LiveKit === 'undefined') {
            console.log('⏳ Waiting for LiveKit...');
            let attempts = 0;
            while (typeof window.LiveKit === 'undefined' && attempts < 50) {
                await new Promise(resolve => setTimeout(resolve, 100));
                attempts++;
            }
            
            if (typeof window.LiveKit === 'undefined') {
                throw new Error('LiveKit could not be loaded');
            }
        }
        
        console.log('✅ LiveKit available, proceeding...');
        
        // SECURITY: Pre-check media permissions
        try {
            console.log('🔒 Checking media permissions...');
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                // Test media access to avoid later issues
                const testStream = await navigator.mediaDevices.getUserMedia({ 
                    video: true, 
                    audio: true 
                });
                // Immediately stop the test stream
                testStream.getTracks().forEach(track => track.stop());
                console.log('✅ Media permissions granted');
            }
        } catch (mediaError) {
            console.warn('⚠️ Media permission check failed:', mediaError);
            // Continue anyway, but user will be prompted later
        }
        
        // Get meeting data - SIMPLE approach
        meetingData = sessionStorage.getItem('meetingData');
        
        if (!meetingData) {
            // BULLETPROOF: Prevent duplicate participants
            let participantName = sessionStorage.getItem('participantName');
            if (!participantName) {
                participantName = prompt('Dein Name:') || 'Teilnehmer';
                sessionStorage.setItem('participantName', participantName);
            }
            
            console.log('🔗 Joining meeting...');
            const response = await fetch(`/api/meetings/${meetingId}/join`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ participant_name: participantName })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Could not join meeting');
            }

            meetingData = await response.json();
            sessionStorage.setItem('meetingData', JSON.stringify(meetingData));
        } else {
            meetingData = JSON.parse(meetingData);
        }

        // Connect to room - ULTRA-SIMPLE
        await connectToRoom(meetingData);
        
        isInitialized = true;
        console.log('🎉 ULTRA-SIMPLE initialization completed!');
        
    } catch (error) {
        console.error('❌ Initialization failed:', error);
        showError('Fehler beim Verbinden: ' + error.message);
    } finally {
        isInitializing = false;
    }
}

// ULTRA-SIMPLE room connection with persistent media
async function connectToRoom(meetingData) {
    try {
        console.log('🔗 Connecting with ULTRA-SIMPLE settings...');
        
        // ULTRA-SIMPLE LiveKit room - minimal config
        room = new LiveKit.Room({
            adaptiveStream: false, // Disable adaptive streaming
            dynacast: false,       // Disable dynacast
            audioCaptureDefaults: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
            },
            videoCaptureDefaults: {
                resolution: { width: 640, height: 480 }, 
                frameRate: 15,
            },
            publishDefaults: {
                videoSimulcastLayers: [], 
                stopMicTrackOnMute: false,
                videoCodec: 'vp8',
                videoEncoding: {
                    maxBitrate: 500000,
                    maxFramerate: 15,
                },
            },
        });

        // SIMPLE event handlers
        room.on(LiveKit.RoomEvent.TrackSubscribed, handleTrackSubscribed);
        room.on(LiveKit.RoomEvent.ParticipantConnected, handleParticipantConnected);
        room.on(LiveKit.RoomEvent.ParticipantDisconnected, handleParticipantDisconnected);
        room.on(LiveKit.RoomEvent.Disconnected, handleDisconnect);
        room.on(LiveKit.RoomEvent.LocalTrackPublished, handleLocalTrackPublished);
        room.on(LiveKit.RoomEvent.Connected, handleRoomConnected);

        // Connect
        console.log('🔌 Connecting to LiveKit...');
        await room.connect(meetingData.livekit_url, meetingData.token);
        console.log('✅ Connected to room!');

        // Hide loading
        const loadingElement = document.getElementById('loadingState');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        localParticipant = room.localParticipant;
        
        // CRITICAL: Create local participant container immediately
        console.log('🏗️ Creating local participant container...');
        createConsistentContainer(localParticipant, true);
        
        // PERSISTENT media setup - restore previous state
        try {
            console.log('🎥 Setting up PERSISTENT media...');
            
            // Apply saved media state immediately
            await room.localParticipant.setMicrophoneEnabled(audioEnabled);
            await room.localParticipant.setCameraEnabled(videoEnabled);
            
            // Update UI buttons to reflect current state
            updateMediaButtons();
            
            console.log('✅ Media setup completed with persistent state');
            
        } catch (mediaError) {
            console.warn('⚠️ Media setup failed, continuing without:', mediaError);
        }

        // IMPORTANT: Process existing participants in the room
        console.log('👥 Processing existing participants...');
        room.participants.forEach((participant) => {
            console.log('🔄 Adding existing participant:', participant.identity);
            handleParticipantConnected(participant);
        });

        // Update UI
        updateParticipantCount();
        updateConsistentGrid();

        // Set share link
        const shareUrl = window.location.href;
        const shareLinkInput = document.getElementById('shareLinkInput');
        if (shareLinkInput) {
            shareLinkInput.value = shareUrl;
        }

        // Reset reconnection attempts on successful connection
        reconnectionAttempts = 0;

    } catch (error) {
        console.error('❌ Connection failed:', error);
        throw error;
    }
}

// NEW: Handle room connected event
function handleRoomConnected() {
    console.log('🎉 Room connected successfully!');
    
    // Ensure local participant container exists
    if (localParticipant) {
        let localContainer = document.getElementById(`participant-${localParticipant.sid}`);
        if (!localContainer) {
            console.log('🔧 Creating missing local container...');
            createConsistentContainer(localParticipant, true);
        }
    }
    
    // Process any existing participants
    if (room && room.participants) {
        room.participants.forEach((participant) => {
            if (!participants.has(participant.sid)) {
                console.log('🔧 Adding missing participant:', participant.identity);
                handleParticipantConnected(participant);
            }
        });
    }
    
    updateConsistentGrid();
}

// BULLETPROOF track subscription
function handleTrackSubscribed(track, publication, participant) {
    console.log('📹 Track subscribed:', track.kind, 'from', participant.identity);
    
    // BULLETPROOF: Check if container already exists
    let container = document.getElementById(`participant-${participant.sid}`);
    if (!container) {
        console.log('📦 Creating container for:', participant.identity);
        container = createConsistentContainer(participant, false);
    }
    
    // SIMPLE track attachment
    attachTrackSimple(track, container);
    
    // Update grid after track attachment
    updateConsistentGrid();
}

// BULLETPROOF participant connection with duplicate prevention
function handleParticipantConnected(participant) {
    console.log('👤 Participant connected:', participant.identity);
    
    // BULLETPROOF: Prevent duplicates
    if (participants.has(participant.sid)) {
        console.log('⚠️ Participant already exists, ignoring:', participant.identity);
        return;
    }
    
    participants.set(participant.sid, participant);
    
    // Create container
    createConsistentContainer(participant, false);
    
    // IMPORTANT: Subscribe to existing tracks
    participant.tracks.forEach((publication) => {
        if (publication.track) {
            console.log('🔗 Subscribing to existing track:', publication.kind, 'from', participant.identity);
            handleTrackSubscribed(publication.track, publication, participant);
        }
    });
    
    // Update UI with consistent layout
    updateParticipantCount();
    updateConsistentGrid();
}

// SIMPLE participant disconnect
function handleParticipantDisconnected(participant) {
    console.log('👋 Participant disconnected:', participant.identity);
    
    participants.delete(participant.sid);
    
    const container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        container.remove();
    }
    
    updateParticipantCount();
    updateConsistentGrid();
}

// PERSISTENT disconnect handling - prevent unnecessary disconnects
function handleDisconnect(reason) {
    console.log('💥 Disconnected from room:', reason);
    
    // Only show error if it's not due to page visibility
    if (!document.hidden && reason !== 'CLIENT_INITIATED') {
        console.log('🔄 Unexpected disconnect, attempting reconnection...');
        setTimeout(attemptReconnection, 1000);
    }
}

function handleLocalTrackPublished(publication, participant) {
    console.log('📤 Local track published:', publication.kind);
    
    // Create local participant container if not exists
    let container = document.getElementById(`participant-${participant.sid}`);
    if (!container) {
        container = createConsistentContainer(participant, true);
    }
    
    // Attach local track
    if (publication.track) {
        attachTrackSimple(publication.track, container);
    }
    
    // Update grid after local track
    updateConsistentGrid();
}

// CONSISTENT container creation for all users (Google Meet style)
function createConsistentContainer(participant, isLocal = false) {
    console.log('🏗️ Creating CONSISTENT container for:', participant.identity);
    
    // BULLETPROOF: Check for existing container
    const existingContainer = document.getElementById(`participant-${participant.sid}`);
    if (existingContainer) {
        console.log('⚠️ Container already exists for:', participant.identity);
        return existingContainer;
    }
    
    const container = document.createElement('div');
    container.id = `participant-${participant.sid}`;
    container.className = 'participant-container';
    
    // CONSISTENT: Always same structure for all participants
    container.style.position = 'relative';
    container.style.background = '#202124';
    container.style.borderRadius = '8px';
    container.style.overflow = 'hidden';
    container.style.aspectRatio = '16/9';
    container.style.minHeight = '200px';
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';
    
    // Video element - CONSISTENT for all
    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    video.muted = isLocal;
    video.style.width = '100%';
    video.style.height = '100%';
    video.style.objectFit = 'cover';
    video.style.background = '#202124';
    
    // Name label - CONSISTENT positioning for all
    const nameLabel = document.createElement('div');
    nameLabel.className = 'participant-name';
    nameLabel.textContent = participant.identity + (isLocal ? ' (Du)' : '');
    nameLabel.style.position = 'absolute';
    nameLabel.style.bottom = '0.5rem';
    nameLabel.style.left = '0.5rem';
    nameLabel.style.background = 'rgba(0, 0, 0, 0.7)';
    nameLabel.style.color = '#e8eaed';
    nameLabel.style.padding = '0.25rem 0.75rem';
    nameLabel.style.borderRadius = '4px';
    nameLabel.style.fontSize = '0.875rem';
    nameLabel.style.zIndex = '5';
    
    container.appendChild(video);
    container.appendChild(nameLabel);
    
    const videoGrid = document.getElementById('videoGrid');
    if (videoGrid) {
        videoGrid.appendChild(container);
        updateConsistentGrid();
    }
    
    return container;
}

// ULTRA-SIMPLE track attachment
function attachTrackSimple(track, container) {
    console.log('🔗 Attaching track:', track.kind);
    
    try {
        if (track.kind === LiveKit.Track.Kind.Video) {
            const video = container.querySelector('video');
            if (video) {
                track.attach(video);
                video.play().catch(e => console.warn('Autoplay prevented:', e));
                console.log('✅ Video track attached');
            }
        } else if (track.kind === LiveKit.Track.Kind.Audio) {
            const audio = document.createElement('audio');
            audio.autoplay = true;
            track.attach(audio);
            container.appendChild(audio);
            console.log('✅ Audio track attached');
        }
    } catch (error) {
        console.error('❌ Track attachment failed:', error);
    }
}

// CONSISTENT grid update - Google Meet style layout for ALL users
function updateConsistentGrid() {
    const videoGrid = document.getElementById('videoGrid');
    const containers = document.querySelectorAll('.participant-container');
    
    if (!videoGrid) return;
    
    const count = containers.length;
    console.log('📐 Updating CONSISTENT grid for', count, 'participants');
    console.log('📋 Container IDs:', Array.from(containers).map(c => c.id));
    
    // Remove all previous classes and styles
    videoGrid.className = '';
    videoGrid.style.display = 'grid';
    videoGrid.style.gap = '1rem';
    videoGrid.style.padding = '1rem';
    videoGrid.style.height = '100%';
    videoGrid.style.width = '100%';
    videoGrid.style.flex = '1';
    videoGrid.style.alignItems = 'stretch';
    videoGrid.style.justifyItems = 'stretch';
    
    // CONSISTENT: Google Meet style layout for ALL scenarios
    if (count === 0) {
        // No participants yet - show loading
        console.log('📋 No participants to display');
        return;
    } else if (count === 1) {
        // Single participant - centered
        videoGrid.style.gridTemplateColumns = '1fr';
        videoGrid.style.maxWidth = '600px';
        videoGrid.style.margin = '0 auto';
        videoGrid.style.gridAutoRows = 'minmax(300px, 1fr)';
    } else if (count === 2) {
        // Two participants - ALWAYS side by side (consistent for ALL users)
        videoGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
        videoGrid.style.maxWidth = 'none';
        videoGrid.style.margin = '0';
        videoGrid.style.gridAutoRows = 'minmax(250px, 1fr)';
    } else if (count <= 4) {
        // 3-4 participants - 2x2 grid
        videoGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
        videoGrid.style.maxWidth = 'none';
        videoGrid.style.margin = '0';
        videoGrid.style.gridAutoRows = 'minmax(200px, 1fr)';
    } else {
        // Many participants - responsive grid
        videoGrid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(250px, 1fr))';
        videoGrid.style.maxWidth = 'none';
        videoGrid.style.margin = '0';
        videoGrid.style.gridAutoRows = 'minmax(180px, 1fr)';
        videoGrid.style.gap = '0.5rem';
    }
    
    console.log('✅ CONSISTENT grid applied:', {
        participants: count,
        columns: videoGrid.style.gridTemplateColumns,
        layout: 'Google Meet style'
    });
    
    // DEBUGGING: Log all current containers
    console.log('🔍 Current participants in DOM:');
    containers.forEach((container, index) => {
        const nameLabel = container.querySelector('.participant-name');
        const hasVideo = container.querySelector('video');
        console.log(`  ${index + 1}. ${container.id} - ${nameLabel?.textContent} - Video: ${hasVideo ? 'Yes' : 'No'}`);
    });
}

// PERSISTENT: Update media button states
function updateMediaButtons() {
    const toggleMicBtn = document.getElementById('toggleMic');
    const toggleVideoBtn = document.getElementById('toggleVideo');
    
    if (toggleMicBtn) {
        toggleMicBtn.classList.toggle('active', audioEnabled);
        const micOnIcon = toggleMicBtn.querySelector('.mic-on');
        const micOffIcon = toggleMicBtn.querySelector('.mic-off');
        if (micOnIcon && micOffIcon) {
            micOnIcon.classList.toggle('hidden', !audioEnabled);
            micOffIcon.classList.toggle('hidden', audioEnabled);
        }
    }
    
    if (toggleVideoBtn) {
        toggleVideoBtn.classList.toggle('active', videoEnabled);
        const videoOnIcon = toggleVideoBtn.querySelector('.video-on');
        const videoOffIcon = toggleVideoBtn.querySelector('.video-off');
        if (videoOnIcon && videoOffIcon) {
            videoOnIcon.classList.toggle('hidden', !videoEnabled);
            videoOffIcon.classList.toggle('hidden', videoEnabled);
        }
    }
    
    console.log('🎛️ Media buttons updated:', { audioEnabled, videoEnabled });
}

// SIMPLE helper functions
function updateParticipantCount() {
    // Count all participants including local participant
    const remoteParticipants = room ? room.participants.size : 0;
    const localParticipant = room && room.localParticipant ? 1 : 0;
    const totalCount = remoteParticipants + localParticipant;
    
    console.log('👥 Participant count update:', { 
        remote: remoteParticipants, 
        local: localParticipant, 
        total: totalCount 
    });
    
    const participantCountElement = document.getElementById('participantCount');
    if (participantCountElement) {
        participantCountElement.textContent = totalCount;
    }
}

function showError(message) {
    const loadingState = document.getElementById('loadingState');
    if (loadingState) {
        loadingState.innerHTML = `
            <div style="text-align: center; color: #ea4335;">
                <h3>⚠️ Fehler</h3>
                <p>${message}</p>
                <button onclick="window.location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #1a73e8; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Seite neu laden
                </button>
            </div>
        `;
    }
}

// PERSISTENT control handlers with state saving
function setupEventListeners() {
    // Microphone toggle with persistence
    const toggleMicBtn = document.getElementById('toggleMic');
    if (toggleMicBtn) {
        toggleMicBtn.addEventListener('click', async () => {
            if (!room) return;
            try {
                audioEnabled = !audioEnabled;
                await room.localParticipant.setMicrophoneEnabled(audioEnabled);
                updateMediaButtons();
                saveMediaState(); // Save state
                console.log('🎤 Microphone:', audioEnabled ? 'enabled' : 'disabled');
            } catch (error) {
                console.error('Microphone toggle failed:', error);
                // Revert state on error
                audioEnabled = !audioEnabled;
                updateMediaButtons();
            }
        });
    }

    // Video toggle with persistence
    const toggleVideoBtn = document.getElementById('toggleVideo');
    if (toggleVideoBtn) {
        toggleVideoBtn.addEventListener('click', async () => {
            if (!room) return;
            try {
                videoEnabled = !videoEnabled;
                await room.localParticipant.setCameraEnabled(videoEnabled);
                updateMediaButtons();
                saveMediaState(); // Save state
                console.log('📹 Camera:', videoEnabled ? 'enabled' : 'disabled');
            } catch (error) {
                console.error('Video toggle failed:', error);
                // Revert state on error
                videoEnabled = !videoEnabled;
                updateMediaButtons();
            }
        });
    }

    // Leave meeting with cleanup
    const leaveMeetingBtn = document.getElementById('leaveMeeting');
    if (leaveMeetingBtn) {
        leaveMeetingBtn.addEventListener('click', async () => {
            if (confirm('Meeting verlassen?')) {
                try {
                    // Clean disconnect
                    if (room) {
                        await room.disconnect();
                    }
                    
                    // Clear all stored data
                    sessionStorage.removeItem('meetingData');
                    sessionStorage.removeItem('participantName');
                    sessionStorage.removeItem('audioEnabled');
                    sessionStorage.removeItem('videoEnabled');
                    
                    // Notify backend about leaving
                    const participantName = sessionStorage.getItem('participantName');
                    if (participantName) {
                        fetch(`/api/meetings/${meetingId}/leave`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ participant_name: participantName })
                        }).catch(e => console.log('Leave notification failed:', e));
                    }
                    
                    window.location.href = '/';
                } catch (error) {
                    console.error('Leave meeting error:', error);
                    window.location.href = '/';
                }
            }
        });
    }

    // Share functionality
    const shareLinkBtn = document.getElementById('shareLink');
    const copyLinkBtn = document.getElementById('copyLink');
    const shareModal = document.getElementById('shareModal');
    
    if (shareLinkBtn && shareModal) {
        shareLinkBtn.addEventListener('click', () => {
            shareModal.classList.add('show');
        });
    }
    
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', async () => {
            const input = document.getElementById('shareLinkInput');
            if (!input) return;
            
            try {
                await navigator.clipboard.writeText(input.value);
                copyLinkBtn.textContent = '✓ Kopiert!';
                setTimeout(() => {
                    copyLinkBtn.textContent = '📋 Kopieren';
                }, 2000);
            } catch (error) {
                console.error('Copy failed:', error);
                // Fallback for older browsers
                input.select();
                input.setSelectionRange(0, 99999);
                document.execCommand('copy');
                copyLinkBtn.textContent = '✓ Kopiert!';
                setTimeout(() => {
                    copyLinkBtn.textContent = '📋 Kopieren';
                }, 2000);
            }
        });
    }
    
    if (shareModal) {
        shareModal.addEventListener('click', (e) => {
            if (e.target.id === 'shareModal') {
                e.target.classList.remove('show');
            }
        });
    }

    // BULLETPROOF: Handle page unload
    window.addEventListener('beforeunload', () => {
        if (room && room.state === 'connected') {
            // Save current state before leaving
            saveMediaState();
        }
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setupEventListeners();
        initializeMeeting();
    });
} else {
    setupEventListeners();
    initializeMeeting();
} 