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

// PERSISTENT: Reconnection system
async function attemptReconnection() {
    if (isReconnecting || reconnectionAttempts >= MAX_RECONNECTION_ATTEMPTS) {
        console.log('🚫 Reconnection skipped - already reconnecting or max attempts reached');
        return;
    }
    
    isReconnecting = true;
    reconnectionAttempts++;
    
    console.log(`🔄 Attempting reconnection ${reconnectionAttempts}/${MAX_RECONNECTION_ATTEMPTS}...`);
    showStatus(`Verbindung wird wiederhergestellt... (${reconnectionAttempts}/${MAX_RECONNECTION_ATTEMPTS})`, 'warning');
    
    try {
        // Clear the current room
        if (room) {
            room.disconnect();
            room = null;
        }
        
        // Clear video grid
        const videoGrid = document.getElementById('videoGrid');
        if (videoGrid) {
            videoGrid.innerHTML = '';
        }
        
        // Recreate meeting data if needed
        let currentMeetingData = sessionStorage.getItem('meetingData');
        if (!currentMeetingData) {
            const participantName = sessionStorage.getItem('participantName') || 'Teilnehmer';
            
            const response = await fetch(`/api/meetings/${meetingId}/join`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ participant_name: participantName })
            });
            
            if (!response.ok) {
                throw new Error('Fehler beim Wiederherstellen der Meeting-Daten');
            }
            
            currentMeetingData = await response.json();
            sessionStorage.setItem('meetingData', JSON.stringify(currentMeetingData));
        } else {
            currentMeetingData = JSON.parse(currentMeetingData);
        }
        
        // Reconnect to room
        await connectToRoom(currentMeetingData);
        
        console.log('✅ Reconnection successful!');
        showStatus('Verbindung wiederhergestellt!', 'success');
        reconnectionAttempts = 0;
        
    } catch (error) {
        console.error(`❌ Reconnection attempt ${reconnectionAttempts} failed:`, error);
        
        if (reconnectionAttempts >= MAX_RECONNECTION_ATTEMPTS) {
            showError('Verbindung konnte nicht wiederhergestellt werden. Bitte laden Sie die Seite neu.');
        } else {
            // Try again after delay
            setTimeout(attemptReconnection, RECONNECTION_DELAY);
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

// PERSISTENT: Get participant name with nice modal
function getParticipantName() {
    return new Promise((resolve, reject) => {
        // Check if we already have a stored name
        const storedName = sessionStorage.getItem('participantName');
        if (storedName) {
            resolve(storedName);
            return;
        }

        // Show name input modal
        const nameModal = document.getElementById('nameModal');
        const nameInput = document.getElementById('participantNameInput');
        const confirmBtn = document.getElementById('confirmJoin');
        const cancelBtn = document.getElementById('cancelJoin');
        const nameError = document.getElementById('nameError');

        if (!nameModal || !nameInput || !confirmBtn || !cancelBtn) {
            // Fallback to prompt if modal elements not found
            const name = prompt('Dein Name:') || 'Teilnehmer';
            sessionStorage.setItem('participantName', name);
            resolve(name);
            return;
        }

        // Show modal
        nameModal.classList.add('show');
        nameInput.focus();

        // Handle confirm
        const handleConfirm = () => {
            const name = nameInput.value.trim();
            
            if (!name) {
                nameError.textContent = 'Bitte geben Sie einen Namen ein';
                nameError.style.display = 'block';
                nameInput.focus();
                return;
            }

            if (name.length < 2) {
                nameError.textContent = 'Name muss mindestens 2 Zeichen lang sein';
                nameError.style.display = 'block';
                nameInput.focus();
                return;
            }

            // Success
            sessionStorage.setItem('participantName', name);
            nameModal.classList.remove('show');
            cleanup();
            resolve(name);
        };

        // Handle cancel
        const handleCancel = () => {
            nameModal.classList.remove('show');
            cleanup();
            reject(new Error('User cancelled joining'));
        };

        // Handle Enter key
        const handleKeyPress = (e) => {
            if (e.key === 'Enter') {
                handleConfirm();
            }
        };

        // Cleanup function
        const cleanup = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            nameInput.removeEventListener('keypress', handleKeyPress);
            nameError.style.display = 'none';
            nameInput.value = '';
        };

        // Add event listeners
        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        nameInput.addEventListener('keypress', handleKeyPress);
    });
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
            // IMPROVED: Use nice modal for name input
            try {
                const participantName = await getParticipantName();
                
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
                
            } catch (nameError) {
                if (nameError.message === 'User cancelled joining') {
                    // Redirect back to homepage
                    window.location.href = '/';
                    return;
                }
                throw nameError;
            }
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

// GOOGLE MEET STYLE: Create participant video container
function createParticipantContainer(participant, isLocal = false) {
    console.log(`📹 Creating ${isLocal ? 'LOCAL' : 'REMOTE'} container for:`, participant.name || participant.identity);
    
    // BULLETPROOF: Prevent duplicates
    const existingContainer = document.getElementById(`participant-${participant.identity}`);
    if (existingContainer) {
        console.log('⚠️ Container already exists for:', participant.identity);
        return existingContainer;
    }
    
    const container = document.createElement('div');
    container.className = 'participant-container';
    container.id = `participant-${participant.identity}`;
    container.setAttribute('data-participant', participant.identity);
    
    // Create video element
    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    video.muted = isLocal; // IMPORTANT: Mute local to prevent feedback
    video.id = `video-${participant.identity}`;
    
    // Create overlay for participant name and controls
    const overlay = document.createElement('div');
    overlay.className = 'participant-overlay';
    
    const nameLabel = document.createElement('div');
    nameLabel.className = 'participant-name';
    nameLabel.textContent = participant.name || participant.identity;
    if (isLocal) nameLabel.textContent += ' (Du)';
    
    // Audio indicator
    const audioIndicator = document.createElement('div');
    audioIndicator.className = 'audio-indicator';
    audioIndicator.innerHTML = '🎤';
    audioIndicator.style.display = 'none';
    
    overlay.appendChild(nameLabel);
    overlay.appendChild(audioIndicator);
    
    container.appendChild(video);
    container.appendChild(overlay);
    
    // Add to grid
    const videoGrid = document.getElementById('videoGrid');
    if (videoGrid) {
        videoGrid.appendChild(container);
        console.log(`✅ ${isLocal ? 'LOCAL' : 'REMOTE'} container added to grid:`, participant.identity);
        
        // MEGA-IMPORTANT: Trigger layout recalculation
        updateVideoGridLayout();
    } else {
        console.error('❌ Video grid not found!');
    }
    
    return container;
}

// ULTRA-ADVANCED: Connect to LiveKit room
async function connectToRoom(data) {
    console.log('🔗 Connecting to LiveKit room...', data.livekit_url);
    
    try {
        // Initialize room
        room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true,
            videoCaptureDefaults: {
                resolution: LiveKit.VideoPresets.h720.resolution,
            },
        });
        
        // BULLETPROOF: Event handlers setup
        room.on(LiveKit.RoomEvent.Connected, () => {
            console.log('🎉 Room connected successfully!');
            
            // CRITICAL: Process local participant first
            console.log('👤 Processing LOCAL participant:', room.localParticipant.identity);
            const localContainer = createParticipantContainer(room.localParticipant, true);
            
            // MEGA-IMPORTANT: Process ALL existing remote participants
            console.log(`👥 Processing ${room.remoteParticipants.size} existing REMOTE participants`);
            room.remoteParticipants.forEach((participant) => {
                console.log('👤 Processing existing REMOTE participant:', participant.identity);
                handleParticipantConnected(participant);
                
                // CRITICAL: Subscribe to their existing tracks
                participant.trackPublications.forEach((publication) => {
                    if (publication.isSubscribed && publication.track) {
                        console.log('🎵 Attaching existing track:', publication.kind, 'from', participant.identity);
                        handleTrackSubscribed(publication.track, publication, participant);
                    }
                });
            });
            
            // Enable local camera and microphone with stored state
            enableLocalMedia();
        });
        
        room.on(LiveKit.RoomEvent.ParticipantConnected, handleParticipantConnected);
        room.on(LiveKit.RoomEvent.ParticipantDisconnected, handleParticipantDisconnected);
        room.on(LiveKit.RoomEvent.TrackSubscribed, handleTrackSubscribed);
        room.on(LiveKit.RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed);
        room.on(LiveKit.RoomEvent.TrackMuted, handleTrackMuted);
        room.on(LiveKit.RoomEvent.TrackUnmuted, handleTrackUnmuted);
        
        // Enhanced error handling
        room.on(LiveKit.RoomEvent.Disconnected, (reason) => {
            console.log('❌ Room disconnected:', reason);
            if (reason !== LiveKit.DisconnectReason.CLIENT_INITIATED) {
                attemptReconnection();
            }
        });
        
        room.on(LiveKit.RoomEvent.Reconnecting, () => {
            console.log('🔄 Room reconnecting...');
            showStatus('Verbindung wird wiederhergestellt...', 'warning');
        });
        
        room.on(LiveKit.RoomEvent.Reconnected, () => {
            console.log('✅ Room reconnected!');
            showStatus('Verbindung wiederhergestellt!', 'success');
        });
        
        // Connect to room
        await room.connect(data.livekit_url, data.token);
        console.log('✅ Connected to room successfully!');
        
    } catch (error) {
        console.error('❌ Failed to connect to room:', error);
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

// MEGA-IMPROVED: Handle new participant joining
function handleParticipantConnected(participant) {
    console.log('👤 NEW PARTICIPANT CONNECTED:', participant.identity);
    
    // BULLETPROOF: Create container for new participant
    const container = createParticipantContainer(participant, false);
    
    // IMPORTANT: Subscribe to their tracks immediately
    participant.trackPublications.forEach((publication) => {
        if (publication.isSubscribed && publication.track) {
            console.log('🎵 Subscribing to existing track:', publication.kind, 'from', participant.identity);
            handleTrackSubscribed(publication.track, publication, participant);
        }
    });
    
    // CRITICAL: Listen for future track events
    participant.on(LiveKit.ParticipantEvent.TrackSubscribed, (track, publication) => {
        console.log('🎵 Track subscribed event for:', participant.identity, track.kind);
        handleTrackSubscribed(track, publication, participant);
    });
    
    participant.on(LiveKit.ParticipantEvent.TrackUnsubscribed, (track, publication) => {
        console.log('🔇 Track unsubscribed for:', participant.identity, track.kind);
        handleTrackUnsubscribed(track, publication, participant);
    });
    
    // Update UI
    updateParticipantCount();
    updateVideoGridLayout();
    
    console.log('✅ Participant setup completed for:', participant.identity);
}

// BULLETPROOF: Handle participant leaving
function handleParticipantDisconnected(participant) {
    console.log('👋 PARTICIPANT DISCONNECTED:', participant.identity);
    
    // Remove their container
    const container = document.getElementById(`participant-${participant.identity}`);
    if (container) {
        container.remove();
        console.log('🗑️ Removed container for:', participant.identity);
    }
    
    // Update UI
    updateParticipantCount();
    updateVideoGridLayout();
}

// ULTRA-ROBUST: Handle track subscription (when video/audio arrives)
function handleTrackSubscribed(track, publication, participant) {
    console.log(`🎵 TRACK SUBSCRIBED: ${track.kind} from ${participant.identity}`);
    
    // Get participant container
    const container = document.getElementById(`participant-${participant.identity}`);
    if (!container) {
        console.warn('⚠️ No container found for participant:', participant.identity);
        // Try to create it
        createParticipantContainer(participant, false);
        return;
    }
    
    // Get video element
    const video = container.querySelector('video');
    if (!video) {
        console.error('❌ No video element found in container for:', participant.identity);
        return;
    }
    
    if (track.kind === 'video') {
        console.log('📹 Attaching VIDEO track for:', participant.identity);
        track.attach(video);
        
        // Show video, hide avatar
        video.style.display = 'block';
        
        // Handle video track events
        track.on(LiveKit.TrackEvent.Muted, () => {
            console.log('📹❌ Video muted for:', participant.identity);
            video.style.display = 'none';
        });
        
        track.on(LiveKit.TrackEvent.Unmuted, () => {
            console.log('📹✅ Video unmuted for:', participant.identity);
            video.style.display = 'block';
        });
        
    } else if (track.kind === 'audio') {
        console.log('🔊 Attaching AUDIO track for:', participant.identity);
        track.attach(video); // Audio can also be attached to video element
        
        // Handle audio indicators
        const audioIndicator = container.querySelector('.audio-indicator');
        if (audioIndicator) {
            track.on(LiveKit.TrackEvent.Muted, () => {
                audioIndicator.style.display = 'none';
            });
            
            track.on(LiveKit.TrackEvent.Unmuted, () => {
                audioIndicator.style.display = 'block';
            });
            
            // Set initial state
            audioIndicator.style.display = track.isMuted ? 'none' : 'block';
        }
    }
    
    console.log(`✅ Track attached successfully: ${track.kind} for ${participant.identity}`);
}

// Handle track unsubscription
function handleTrackUnsubscribed(track, publication, participant) {
    console.log(`🔇 TRACK UNSUBSCRIBED: ${track.kind} from ${participant.identity}`);
    
    if (track) {
        track.detach();
    }
}

// Handle track muted
function handleTrackMuted(publication, participant) {
    console.log(`🔇 Track muted: ${publication.kind} from ${participant.identity}`);
}

// Handle track unmuted
function handleTrackUnmuted(publication, participant) {
    console.log(`🔊 Track unmuted: ${publication.kind} from ${participant.identity}`);
}

// PERSISTENT: Enable local media with saved state
async function enableLocalMedia() {
    if (!room || !room.localParticipant) {
        console.error('❌ No room or local participant available');
        return;
    }
    
    try {
        console.log('🎥 Enabling local media with saved state...');
        
        // Enable camera and microphone based on saved state
        await room.localParticipant.setCameraEnabled(videoEnabled);
        await room.localParticipant.setMicrophoneEnabled(audioEnabled);
        
        // Update UI buttons
        updateMediaButtons();
        
        // Get local tracks and attach them
        room.localParticipant.audioTrackPublications.forEach((publication) => {
            if (publication.track) {
                const container = document.getElementById(`participant-${room.localParticipant.identity}`);
                if (container) {
                    const video = container.querySelector('video');
                    if (video) {
                        publication.track.attach(video);
                    }
                }
            }
        });
        
        room.localParticipant.videoTrackPublications.forEach((publication) => {
            if (publication.track) {
                const container = document.getElementById(`participant-${room.localParticipant.identity}`);
                if (container) {
                    const video = container.querySelector('video');
                    if (video) {
                        publication.track.attach(video);
                        video.style.display = videoEnabled ? 'block' : 'none';
                    }
                }
            }
        });
        
        console.log('✅ Local media enabled successfully');
        
        // Hide loading and show controls
        const loadingElement = document.getElementById('loadingState');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
        // Update participant count and layout
        updateParticipantCount();
        updateVideoGridLayout();
        
        // Set share link
        const shareUrl = window.location.href;
        const shareLinkInput = document.getElementById('shareLinkInput');
        if (shareLinkInput) {
            shareLinkInput.value = shareUrl;
        }
        
    } catch (error) {
        console.error('❌ Failed to enable local media:', error);
        showError('Fehler beim Aktivieren von Kamera/Mikrofon: ' + error.message);
    }
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

// Update participant count in UI
function updateParticipantCount() {
    if (!room) return;
    
    const totalParticipants = 1 + room.remoteParticipants.size; // Local + remote
    console.log(`👥 Total participants: ${totalParticipants}`);
    
    // Update UI element if it exists
    const countElement = document.querySelector('.participant-count');
    if (countElement) {
        countElement.textContent = `${totalParticipants} Teilnehmer`;
    }
    
    // Update page title
    document.title = `HeyDok Video (${totalParticipants} Teilnehmer)`;
}

// GOOGLE MEET STYLE: Update video grid layout
function updateVideoGridLayout() {
    const videoGrid = document.getElementById('videoGrid');
    if (!videoGrid) return;
    
    const containers = videoGrid.querySelectorAll('.participant-container');
    const participantCount = containers.length;
    
    console.log(`🎨 Updating grid layout for ${participantCount} participants`);
    
    // Remove existing grid classes
    videoGrid.className = 'video-grid';
    
    // Apply grid layout based on participant count
    if (participantCount === 1) {
        videoGrid.classList.add('grid-1');
    } else if (participantCount === 2) {
        videoGrid.classList.add('grid-2');
    } else if (participantCount <= 4) {
        videoGrid.classList.add('grid-4');
    } else if (participantCount <= 6) {
        videoGrid.classList.add('grid-6');
    } else {
        videoGrid.classList.add('grid-many');
    }
    
    console.log(`✅ Grid updated with class: grid-${participantCount <= 4 ? participantCount : participantCount <= 6 ? '6' : 'many'}`);
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