// ULTRA-SIMPLE AND BULLETPROOF Meeting App
console.log('🚀 Starting ULTRA-SIMPLE meeting app...');

// GLOBAL STATE - Keep it simple but persistent
let room = null;
let localParticipant = null;
let audioEnabled = true;
let videoEnabled = true;
let screenShareEnabled = false;
let screenShareTrack = null;
const participants = new Map();

// BULLETPROOF: Prevent multiple initializations
let isInitializing = false;
let isInitialized = false;

// PERSISTENT STATE: Prevent disconnections on tab switch
let reconnectionAttempts = 0;
const MAX_RECONNECTION_ATTEMPTS = 3;
const RECONNECTION_DELAY = 2000;
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
    sessionStorage.setItem('screenShareEnabled', JSON.stringify(screenShareEnabled));
}

function loadMediaState() {
    const savedAudio = sessionStorage.getItem('audioEnabled');
    const savedVideo = sessionStorage.getItem('videoEnabled');
    const savedScreenShare = sessionStorage.getItem('screenShareEnabled');
    
    if (savedAudio !== null) {
        audioEnabled = JSON.parse(savedAudio);
    }
    if (savedVideo !== null) {
        videoEnabled = JSON.parse(savedVideo);
    }
    if (savedScreenShare !== null) {
        screenShareEnabled = JSON.parse(savedScreenShare);
    }
    
    console.log('📱 Loaded media state:', { audioEnabled, videoEnabled, screenShareEnabled });
}

// PERSISTENT: Get participant name with nice modal
function getParticipantName() {
    return new Promise((resolve, reject) => {
        // Check if patient setup was completed (patient came from setup page)
        const patientSetupCompleted = sessionStorage.getItem('patientSetupCompleted');
        const storedName = sessionStorage.getItem('participantName');
        
        if (patientSetupCompleted === 'true' && storedName) {
            console.log('✅ Patient setup completed, using stored name:', storedName);
            resolve(storedName);
            return;
        }
        
        // Check if we already have a stored name for other participants
        if (storedName && !patientSetupCompleted) {
            resolve(storedName);
            return;
        }

        // Show name input modal for guests or doctors without stored names
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
    console.log('🚀 INITIALIZING MEETING - AGGRESSIVE MODE');
    
    // Step 1: FORCE local media BEFORE connecting
    console.log('🎥 STEP 1: Getting local media FIRST...');
    try {
        // CRITICAL: Get media access immediately
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });
        console.log('✅ Local media stream obtained:', stream);
        
        // Create local video element immediately
        const localVideoContainer = document.querySelector('.participant-container:first-child video');
        if (localVideoContainer) {
            localVideoContainer.srcObject = stream;
            localVideoContainer.muted = true; // Prevent echo
            localVideoContainer.play();
            console.log('✅ Local video displayed immediately');
        }
        
    } catch (mediaError) {
        console.error('❌ Failed to get local media:', mediaError);
        alert('Kamera/Mikrofon Zugriff verweigert! Bitte erlauben Sie den Zugriff und laden Sie die Seite neu.');
        return;
    }
    
    // Step 2: Connect to room
    console.log('🎥 STEP 2: Connecting to LiveKit room...');
    await connectToRoom();
    
    // Step 3: FORCE enable local media in room
    console.log('🎥 STEP 3: Enabling local media in room...');
    await enableLocalMedia();
    
    // Step 4: AGGRESSIVE track subscription
    console.log('🎥 STEP 4: Setting up aggressive track subscription...');
    setupAggressiveTrackSubscription();
    
    console.log('✅ Meeting initialization completed');
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
    
    // CRITICAL: Add click handler to start video if autoplay fails
    video.addEventListener('click', () => {
        console.log('🎥 User clicked video, attempting to play:', participant.identity);
        video.play().then(() => {
            console.log('✅ Video started playing after user interaction:', participant.identity);
        }).catch(e => {
            console.warn('⚠️ Video still failed to play after click:', participant.identity, e);
        });
    });
    
    // Add visual indicator when video is paused
    video.addEventListener('pause', () => {
        if (!isLocal) { // Don't show for local video since it might be muted
            console.log('🎥 Video paused for:', participant.identity);
            container.style.cursor = 'pointer';
            // Add a subtle overlay to indicate clicking will start video
            if (!container.querySelector('.play-indicator')) {
                const playIndicator = document.createElement('div');
                playIndicator.className = 'play-indicator';
                playIndicator.innerHTML = '▶️ Klicken zum Starten';
                playIndicator.style.position = 'absolute';
                playIndicator.style.top = '50%';
                playIndicator.style.left = '50%';
                playIndicator.style.transform = 'translate(-50%, -50%)';
                playIndicator.style.background = 'rgba(0, 0, 0, 0.7)';
                playIndicator.style.color = 'white';
                playIndicator.style.padding = '10px 15px';
                playIndicator.style.borderRadius = '5px';
                playIndicator.style.fontSize = '14px';
                playIndicator.style.zIndex = '10';
                playIndicator.style.pointerEvents = 'none';
                container.appendChild(playIndicator);
            }
        }
    });
    
    video.addEventListener('play', () => {
        console.log('🎥 Video playing for:', participant.identity);
        container.style.cursor = 'default';
        // Remove play indicator
        const playIndicator = container.querySelector('.play-indicator');
        if (playIndicator) {
            playIndicator.remove();
        }
    });
    
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
    
    if (!videoGrid) {
        console.error('❌ videoGrid element not found!');
        return;
    }
    
    const count = containers.length;
    console.log('📐 FIXING GRID for', count, 'participants');
    console.log('📋 Container IDs:', Array.from(containers).map(c => c.id));
    
    // CRITICAL: Clear all existing styles and classes
    videoGrid.className = 'video-grid';
    videoGrid.style.cssText = '';
    
    // BULLETPROOF: Apply base grid styles
    videoGrid.style.display = 'grid';
    videoGrid.style.gap = '1rem';
    videoGrid.style.padding = '1rem';
    videoGrid.style.height = '100vh';
    videoGrid.style.width = '100vw';
    videoGrid.style.boxSizing = 'border-box';
    videoGrid.style.alignItems = 'center';
    videoGrid.style.justifyItems = 'center';
    videoGrid.style.background = '#202124';
    
    // GOOGLE MEET STYLE: Perfect layout for ALL scenarios
    if (count === 0) {
        console.log('📋 No participants - showing loading');
        return;
    } else if (count === 1) {
        // Single participant - MUCH LARGER centered layout (with safe margins)
        console.log('📋 1 participant - MUCH LARGER centered layout (no cutoff)');
        videoGrid.style.gridTemplateColumns = '1fr';
        videoGrid.style.gridTemplateRows = '1fr';
        videoGrid.style.placeItems = 'center';
        
        // HUGE but safe container for single participant - no bottom cutoff
        containers[0].style.width = 'min(90vw, 1000px)';
        containers[0].style.height = 'min(78vh, 700px)';
        containers[0].style.maxWidth = '1000px';
        containers[0].style.maxHeight = '700px';
        
        console.log('📋 Single container sized HUGE but safe (no cutoff)');
        
    } else if (count === 2) {
        // CRITICAL: Two participants - MUCH LARGER Google Meet style side-by-side
        console.log('📋 2 participants - MUCH LARGER Google Meet side-by-side layout');
        videoGrid.style.gridTemplateColumns = '1fr 1fr';
        videoGrid.style.gridTemplateRows = '1fr';
        videoGrid.style.placeItems = 'center';
        videoGrid.style.gap = '1.5rem';
        
        // MUCH LARGER sizing for 2 participants - better visibility
        containers.forEach((container, index) => {
            container.style.width = 'min(70vw, 800px)';
            container.style.height = 'min(80vh, 600px)';
            container.style.maxWidth = '800px';
            container.style.maxHeight = '600px';
            console.log(`📋 Container ${index + 1} sized MUCH LARGER for 2-person layout`);
        });
        
    } else if (count <= 4) {
        // 3-4 participants - 2x2 grid (also slightly larger)
        console.log('📋 3-4 participants - 2x2 grid');
        videoGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
        videoGrid.style.gridTemplateRows = 'repeat(2, 1fr)';
        videoGrid.style.gap = '1rem';
        
        containers.forEach(container => {
            container.style.width = 'min(45vw, 450px)';
            container.style.height = 'min(35vh, 340px)';
        });
        
    } else {
        // Many participants - responsive grid
        console.log('📋 5+ participants - responsive grid');
        const cols = Math.ceil(Math.sqrt(count));
        videoGrid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
        videoGrid.style.gap = '0.5rem';
        
        containers.forEach(container => {
            container.style.width = 'min(30vw, 250px)';
            container.style.height = 'min(25vh, 200px)';
        });
    }
    
    console.log('✅ PERFECT GRID applied:', {
        participants: count,
        columns: videoGrid.style.gridTemplateColumns,
        layout: count === 2 ? 'Google Meet Side-by-Side' : 'Grid'
    });
    
    // ENHANCED DEBUGGING: Log all current containers with video status
    console.log('🔍 DETAILED participant status:');
    containers.forEach((container, index) => {
        const nameLabel = container.querySelector('.participant-name');
        const video = container.querySelector('video');
        const hasVideoSrc = video && (video.srcObject || video.src);
        const videoDisplay = video ? video.style.display : 'none';
        
        console.log(`  ${index + 1}. ID: ${container.id}`);
        console.log(`     Name: ${nameLabel?.textContent || 'No name'}`);
        console.log(`     Video element: ${video ? 'Yes' : 'No'}`);
        console.log(`     Video source: ${hasVideoSrc ? 'Yes' : 'No'}`);
        console.log(`     Video display: ${videoDisplay}`);
        console.log(`     Container size: ${container.style.width} x ${container.style.height}`);
    });
}

// PERSISTENT: Update media button states
function updateMediaButtons() {
    // Update microphone button
    const micBtn = document.getElementById('toggleMic');
    if (micBtn) {
        micBtn.classList.toggle('active', audioEnabled);
        const micOn = micBtn.querySelector('.mic-on');
        const micOff = micBtn.querySelector('.mic-off');
        if (micOn && micOff) {
            micOn.classList.toggle('hidden', !audioEnabled);
            micOff.classList.toggle('hidden', audioEnabled);
        }
    }

    // Update video button
    const toggleVideoBtn = document.getElementById('toggleVideo');
    if (toggleVideoBtn) {
        toggleVideoBtn.classList.toggle('active', videoEnabled);
        const videoOn = toggleVideoBtn.querySelector('.video-on');
        const videoOff = toggleVideoBtn.querySelector('.video-off');
        if (videoOn && videoOff) {
            videoOn.classList.toggle('hidden', !videoEnabled);
            videoOff.classList.toggle('hidden', videoEnabled);
        }
    }

    // Update screen share button
    const toggleScreenShareBtn = document.getElementById('toggleScreenShare');
    if (toggleScreenShareBtn) {
        toggleScreenShareBtn.classList.toggle('active', screenShareEnabled);
        const screenShareOn = toggleScreenShareBtn.querySelector('.screen-share-on');
        const screenShareOff = toggleScreenShareBtn.querySelector('.screen-share-off');
        if (screenShareOn && screenShareOff) {
            screenShareOn.classList.toggle('hidden', !screenShareEnabled);
            screenShareOff.classList.toggle('hidden', screenShareEnabled);
        }
    }
}

// Screen sharing functions
async function startScreenShare() {
    if (!room || !room.localParticipant) {
        throw new Error('Kein aktiver Meeting-Raum gefunden');
    }

    try {
        console.log('🖥️ Starting screen share...');
        showStatus('Bildschirmfreigabe wird gestartet...', 'info');

        // Request screen capture
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                displaySurface: 'monitor', // Prefer monitor/screen over window
                logicalSurface: true,
                cursor: 'always'
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        console.log('🖥️ Screen capture stream obtained');

        // Get video track from stream
        const videoTrack = stream.getVideoTracks()[0];
        if (!videoTrack) {
            throw new Error('Kein Video-Track vom Bildschirm erhalten');
        }

        // Publish screen share track to LiveKit
        screenShareTrack = await room.localParticipant.publishTrack(videoTrack, {
            source: LiveKit.TrackSource.ScreenShare,
            name: 'screen_share'
        });

        console.log('🖥️ Screen share track published to LiveKit');

        // Handle track ended event (user stops sharing via browser UI)
        videoTrack.addEventListener('ended', () => {
            console.log('🖥️ Screen share ended by user');
            stopScreenShare().catch(error => {
                console.error('Error stopping screen share after user ended:', error);
            });
        });

        screenShareEnabled = true;
        showStatus('Bildschirmfreigabe aktiv', 'success');
        
        console.log('✅ Screen sharing started successfully');

    } catch (error) {
        console.error('❌ Screen share start failed:', error);
        screenShareEnabled = false;
        
        if (error.name === 'NotAllowedError') {
            throw new Error('Bildschirmfreigabe wurde vom Benutzer abgelehnt');
        } else if (error.name === 'NotSupportedError') {
            throw new Error('Bildschirmfreigabe wird von diesem Browser nicht unterstützt');
        } else if (error.name === 'AbortError') {
            throw new Error('Bildschirmfreigabe wurde abgebrochen');
        } else {
            throw new Error('Fehler beim Starten der Bildschirmfreigabe: ' + error.message);
        }
    }
}

async function stopScreenShare() {
    try {
        console.log('🖥️ Stopping screen share...');
        showStatus('Bildschirmfreigabe wird beendet...', 'info');

        if (screenShareTrack) {
            // Unpublish the screen share track
            await room.localParticipant.unpublishTrack(screenShareTrack);
            screenShareTrack = null;
            console.log('🖥️ Screen share track unpublished from LiveKit');
        }

        screenShareEnabled = false;
        showStatus('Bildschirmfreigabe beendet', 'info');
        
        console.log('✅ Screen sharing stopped successfully');

    } catch (error) {
        console.error('❌ Screen share stop failed:', error);
        screenShareEnabled = false;
        screenShareTrack = null;
        throw new Error('Fehler beim Beenden der Bildschirmfreigabe: ' + error.message);
    }
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

// Show status messages to user
function showStatus(message, type = 'info') {
    console.log(`📢 Status (${type}):`, message);
    
    // Create or update status element
    let statusElement = document.getElementById('status-message');
    if (!statusElement) {
        statusElement = document.createElement('div');
        statusElement.id = 'status-message';
        statusElement.style.cssText = `
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 6px;
            color: white;
            font-size: 0.875rem;
            z-index: 1001;
            transition: all 0.3s ease;
            max-width: 300px;
        `;
        document.body.appendChild(statusElement);
    }
    
    // Set color based on type
    switch (type) {
        case 'success':
            statusElement.style.backgroundColor = '#34a853';
            break;
        case 'warning':
            statusElement.style.backgroundColor = '#fbbc04';
            statusElement.style.color = '#000';
            break;
        case 'error':
            statusElement.style.backgroundColor = '#ea4335';
            break;
        default:
            statusElement.style.backgroundColor = '#1a73e8';
    }
    
    statusElement.textContent = message;
    statusElement.style.display = 'block';
    
    // Auto-hide after 3 seconds for success/info messages
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            if (statusElement) {
                statusElement.style.opacity = '0';
                setTimeout(() => {
                    if (statusElement && statusElement.parentNode) {
                        statusElement.parentNode.removeChild(statusElement);
                    }
                }, 300);
            }
        }, 3000);
    }
}

// EMERGENCY DEBUG: Show debug overlay
function showDebugOverlay(debugInfo) {
    const overlay = document.createElement('div');
    overlay.id = 'debug-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        font-family: monospace;
        font-size: 12px;
        padding: 20px;
        overflow-y: auto;
        z-index: 9999;
        white-space: pre-wrap;
    `;
    
    overlay.innerHTML = `
        <h2 style="color: #ff6b6b; margin-bottom: 20px;">🚨 DEBUG INFORMATION</h2>
        <button onclick="document.getElementById('debug-overlay').remove()" style="position: absolute; top: 10px; right: 10px; background: #ff6b6b; color: white; border: none; padding: 5px 10px; border-radius: 3px;">Close</button>
        
        <h3 style="color: #4ecdc4;">📊 Current State:</h3>
        ${JSON.stringify(debugInfo, null, 2)}
        
        <h3 style="color: #ffe66d;">🔍 Troubleshooting:</h3>
        1. Check if you're accessing with role=doctor parameter
        2. Verify meeting data is stored correctly
        3. Check LiveKit token and URL
        4. Verify camera permissions
        
        <h3 style="color: #ff9f43;">🛠️ Next Steps:</h3>
        - Open browser console (F12) for detailed logs
        - Check if meeting was created correctly
        - Verify network connectivity
        
        <button onclick="location.reload()" style="margin-top: 20px; background: #4ecdc4; color: white; border: none; padding: 10px 20px; border-radius: 5px;">🔄 Reload Page</button>
    `;
    
    document.body.appendChild(overlay);
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

    // Screen share toggle with persistence
    const toggleScreenShareBtn = document.getElementById('toggleScreenShare');
    if (toggleScreenShareBtn) {
        toggleScreenShareBtn.addEventListener('click', async () => {
            if (!room) return;
            try {
                if (screenShareEnabled) {
                    // Stop screen sharing
                    await stopScreenShare();
                } else {
                    // Start screen sharing
                    await startScreenShare();
                }
                updateMediaButtons();
                saveMediaState(); // Save state
                console.log('🖥️ Screen share:', screenShareEnabled ? 'enabled' : 'disabled');
            } catch (error) {
                console.error('Screen share toggle failed:', error);
                showError('Bildschirmfreigabe fehlgeschlagen: ' + error.message);
                // Ensure state is consistent
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
                    // Stop screen sharing if active
                    if (screenShareEnabled) {
                        await stopScreenShare().catch(e => console.log('Screen share cleanup failed:', e));
                    }
                    
                    // Clean disconnect
                    if (room) {
                        await room.disconnect();
                    }
                    
                    // Clear all stored data
                    sessionStorage.removeItem('meetingData');
                    sessionStorage.removeItem('participantName');
                    sessionStorage.removeItem('audioEnabled');
                    sessionStorage.removeItem('videoEnabled');
                    sessionStorage.removeItem('screenShareEnabled');
                    
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

// ULTRA-ADVANCED: Connect to LiveKit room
async function connectToRoom(data) {
    console.log('🔗 DETAILED CONNECTION ATTEMPT:', {
        livekit_url: data.livekit_url,
        token_length: data.token ? data.token.length : 0,
        token_preview: data.token ? data.token.substring(0, 50) + '...' : 'none',
        meeting_id: data.meeting_id
    });
    
    // VALIDATE URL FORMAT
    if (!data.livekit_url) {
        throw new Error('LiveKit URL is missing from meeting data');
    }
    
    if (!data.livekit_url.startsWith('wss://') && !data.livekit_url.startsWith('ws://')) {
        throw new Error(`Invalid LiveKit URL format: ${data.livekit_url} (must start with wss:// or ws://)`);
    }
    
    // VALIDATE TOKEN
    if (!data.token) {
        throw new Error('LiveKit token is missing from meeting data');
    }
    
    try {
        console.log('🏗️ Creating LiveKit Room instance...');
        
        // Initialize room with OPTIMIZED AUDIO SETTINGS
        room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true,
            // OPTIMIZED: Less aggressive audio settings for better compatibility
            audioCaptureDefaults: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: false,  // FIXED: Less aggressive - prevents audio suppression
                sampleRate: 48000,
                channelCount: 2,        // FIXED: Stereo for better quality and compatibility
            },
            videoCaptureDefaults: {
                resolution: LiveKit.VideoPresets.h720.resolution,
            },
            // OPTIMIZED: Improved publish settings
            publishDefaults: {
                stopMicTrackOnMute: false, // Keep track alive when muted
                audioPreset: LiveKit.AudioPresets.speech, // Optimized for speech
                videoSimulcastLayers: [
                    LiveKit.VideoPresets.h540,
                    LiveKit.VideoPresets.h216,
                ], // ADDED: Simulcast for better adaptation
            },
        });
        
        console.log('✅ LiveKit Room instance created successfully');
        
        // ENHANCED ERROR HANDLING for connection
        room.on(LiveKit.RoomEvent.ConnectionError, (error) => {
            console.error('🚨 CONNECTION ERROR:', error);
            showDebugOverlay({
                error: 'LiveKit Connection Error',
                details: error.message,
                livekit_url: data.livekit_url,
                timestamp: new Date().toISOString()
            });
        });
        
        room.on(LiveKit.RoomEvent.Disconnected, (reason) => {
            console.log('❌ Room disconnected:', reason);
            if (reason !== LiveKit.DisconnectReason.CLIENT_INITIATED) {
                console.log('🔄 Attempting reconnection due to unexpected disconnect...');
                attemptReconnection();
            }
        });
        
        // FIXED: Setup all event handlers BEFORE connecting
        room.on(LiveKit.RoomEvent.ParticipantConnected, (participant) => {
            console.log('🚨 ROOM EVENT: ParticipantConnected ->', participant.identity);
            console.log('  Participant details:', {
                identity: participant.identity,
                sid: participant.sid,
                trackPublications: participant.trackPublications.size,
                connectionState: participant.connectionState
            });
            handleParticipantConnected(participant);
        });
        
        room.on(LiveKit.RoomEvent.ParticipantDisconnected, (participant) => {
            console.log('🚨 ROOM EVENT: ParticipantDisconnected ->', participant.identity);
            handleParticipantDisconnected(participant);
        });
        
        room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log('🚨 ROOM EVENT: TrackSubscribed ->', {
                participantIdentity: participant.identity,
                trackKind: track.kind,
                trackSid: track.sid,
                source: publication.source,
                enabled: track.enabled,
                muted: track.muted
            });
            handleTrackSubscribed(track, publication, participant);
        });
        
        room.on(LiveKit.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
            console.log('🚨 ROOM EVENT: TrackUnsubscribed ->', {
                participantIdentity: participant.identity,
                trackKind: track.kind,
                source: publication.source
            });
            handleTrackUnsubscribed(track, publication, participant);
        });
        
        room.on(LiveKit.RoomEvent.TrackMuted, (publication, participant) => {
            console.log('🚨 ROOM EVENT: TrackMuted ->', {
                participantIdentity: participant.identity,
                trackKind: publication.kind,
                source: publication.source
            });
            handleTrackMuted(publication, participant);
        });
        
        room.on(LiveKit.RoomEvent.TrackUnmuted, (publication, participant) => {
            console.log('🚨 ROOM EVENT: TrackUnmuted ->', {
                participantIdentity: participant.identity,
                trackKind: publication.kind,
                source: publication.source
            });
            handleTrackUnmuted(publication, participant);
        });
        
        room.on(LiveKit.RoomEvent.TrackPublished, (publication, participant) => {
            console.log('🚨 ROOM EVENT: TrackPublished ->', {
                participantIdentity: participant.identity,
                trackKind: publication.kind,
                source: publication.source,
                isSubscribed: publication.isSubscribed
            });
            // Immediately try to subscribe to new tracks
            if (!publication.isSubscribed) {
                console.log('🎯 Auto-subscribing to newly published track...');
                publication.setSubscribed(true);
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
        
        // BULLETPROOF: Room connected handler
        room.on(LiveKit.RoomEvent.Connected, async () => {
            console.log('🎉 Room connected successfully!');
            console.log('🎉 Local participant identity:', room.localParticipant.identity);
            console.log('🎉 Local participant SID:', room.localParticipant.sid);
            console.log('🎉 Remote participants count:', room.remoteParticipants.size);
            
            // SUPER DEBUG: Log everything about current state
            console.log('🔍 SUPER DEBUG - ROOM STATE AFTER CONNECTION:');
            console.log('  Room state:', room.state);
            console.log('  Room name:', room.name);
            console.log('  Room SID:', room.sid);
            console.log('  Local participant:', {
                identity: room.localParticipant.identity,
                sid: room.localParticipant.sid,
                trackPublications: room.localParticipant.trackPublications.size,
                videoTracks: room.localParticipant.videoTrackPublications.size,
                audioTracks: room.localParticipant.audioTrackPublications.size
            });
            
            // CRITICAL: Process local participant first - use CONSISTENT function
            console.log('👤 Processing LOCAL participant:', room.localParticipant.identity);
            const localContainer = createConsistentContainer(room.localParticipant, true);
            console.log('👤 Local container created:', localContainer ? 'SUCCESS' : 'FAILED');
            
            // SUPER DEBUG: Log existing remote participants in detail
            console.log(`👥 SUPER DEBUG - Processing ${room.remoteParticipants.size} existing REMOTE participants`);
            room.remoteParticipants.forEach((participant, index) => {
                console.log(`🔍 REMOTE PARTICIPANT ${index + 1}:`, {
                    identity: participant.identity,
                    sid: participant.sid,
                    trackPublications: participant.trackPublications.size,
                    videoTracks: participant.videoTrackPublications.size,
                    audioTracks: participant.audioTrackPublications.size,
                    connectionState: participant.connectionState
                });
                
                // Log each track publication in detail
                participant.trackPublications.forEach((publication, trackIndex) => {
                    console.log(`  📹 Track ${trackIndex + 1}:`, {
                        kind: publication.kind,
                        source: publication.source,
                        isSubscribed: publication.isSubscribed,
                        hasTrack: !!publication.track,
                        enabled: publication.track ? publication.track.enabled : 'N/A',
                        muted: publication.track ? publication.track.muted : 'N/A',
                        sid: publication.track ? publication.track.sid : 'N/A'
                    });
                });
                
                console.log('👤 Processing existing REMOTE participant:', participant.identity);
                
                // FIXED: Use handleParticipantConnected to avoid duplicate event handlers
                // This handles container creation, track subscription AND event handlers properly
                handleParticipantConnected(participant);
            });
            
            // Enable local camera and microphone with stored state
            console.log('🎥 About to enable local media...');
            await enableLocalMedia();
            
            // IMPORTANT: Update UI after everything is set up
            updateParticipantCount();
            updateConsistentGrid();
            
            // SUPER DEBUG: Log final state before force subscription
            console.log('🔍 SUPER DEBUG - STATE BEFORE FORCE SUBSCRIPTION:');
            console.log('  Video grid containers:', document.querySelectorAll('.participant-container').length);
            document.querySelectorAll('.participant-container').forEach((container, index) => {
                const video = container.querySelector('video');
                const nameLabel = container.querySelector('.participant-name');
                console.log(`  Container ${index + 1}:`, {
                    id: container.id,
                    name: nameLabel?.textContent || 'No name',
                    hasVideo: !!video,
                    videoSource: video ? (video.srcObject ? 'Has srcObject' : 'No srcObject') : 'No video element',
                    display: container.style.display
                });
            });
            
            // CRITICAL: Force track subscription after a delay to ensure everything is ready
            setTimeout(() => {
                console.log('🔥 Running SUPER AGGRESSIVE track subscription force...');
                forceSubscribeToAllRemoteTracks();
                
                // Double-check after another delay
                setTimeout(() => {
                    console.log('🔍 FINAL SUPER DEBUG track subscription check...');
                    forceProcessAllTracks();
                    updateConsistentGrid();
                    
                    // Log final final state
                    console.log('🔍 FINAL FINAL STATE:');
                    room.remoteParticipants.forEach((participant) => {
                        const container = document.getElementById(`participant-${participant.sid}`);
                        const video = container?.querySelector('video');
                        const hasVideoSource = video && (video.srcObject || video.src);
                        console.log(`🔍 ${participant.identity}: Container=${!!container}, Video=${!!video}, Source=${hasVideoSource}`);
                        
                        if (video) {
                            console.log(`    Video details:`, {
                                src: video.src,
                                srcObject: !!video.srcObject,
                                autoplay: video.autoplay,
                                muted: video.muted,
                                paused: video.paused,
                                readyState: video.readyState,
                                networkState: video.networkState
                            });
                        }
                    });
                }, 3000);
            }, 1000);
            
            console.log('✅ Room setup completely finished!');
        });
        
        // CRITICAL: Attempt connection with detailed logging
        console.log('🚀 Attempting to connect to LiveKit...');
        console.log('📍 URL:', data.livekit_url);
        console.log('🎫 Token preview:', data.token.substring(0, 100) + '...');
        
        await room.connect(data.livekit_url, data.token);
        console.log('✅ Connected to room successfully!');
        
    } catch (error) {
        console.error('❌ DETAILED CONNECTION FAILURE:', {
            error: error.message,
            stack: error.stack,
            name: error.name,
            url: data.livekit_url,
            token_valid: !!data.token,
            token_length: data.token ? data.token.length : 0
        });
        
        // Show detailed error in debug overlay
        showDebugOverlay({
            error: 'LiveKit Connection Failed',
            error_message: error.message,
            error_stack: error.stack,
            error_name: error.name,
            livekit_url: data.livekit_url,
            token_present: !!data.token,
            token_length: data.token ? data.token.length : 0,
            timestamp: new Date().toISOString(),
            possible_causes: [
                'Invalid LiveKit URL format',
                'Network connectivity issues', 
                'Invalid or expired token',
                'CORS/firewall blocking WebSocket connection',
                'LiveKit server unreachable'
            ]
        });
        
        throw error;
    }
}

// BULLETPROOF: Handle new participant joining - AGGRESSIVE MODE
function handleParticipantConnected(participant) {
    console.log('👤 HANDLING PARTICIPANT CONNECTION:', participant.identity);
    console.log('👤 Participant SID:', participant.sid);
    console.log('👤 Is local:', participant === room.localParticipant);
    
    // Skip if this is the local participant (handled separately)
    if (participant === room.localParticipant) {
        console.log('👤 Skipping local participant container creation');
        return;
    }
    
    // Check if container already exists
    let container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        console.log('✅ Container already exists for:', participant.identity);
    } else {
        // Create new container for remote participant
        container = createConsistentContainer(participant, false);
        console.log('✅ Created new container for:', participant.identity);
    }
    
    // AGGRESSIVE: Subscribe to ALL existing tracks immediately
    console.log('🔄 Subscribing to existing tracks for:', participant.identity);
    participant.trackPublications.forEach((publication, key) => {
        console.log(`📋 Found track publication: ${publication.kind} (subscribed: ${publication.isSubscribed})`);
        
        if (publication.track) {
            console.log(`✅ Track already available: ${publication.kind}`);
            handleTrackSubscribed(publication.track, publication, participant);
        } else if (!publication.isSubscribed) {
            console.log(`🔄 Subscribing to track: ${publication.kind}`);
            publication.setSubscribed(true);
        }
    });
    
    // Update grid layout
    updateParticipantGrid();
    
    console.log(`✅ Participant ${participant.identity} fully processed`);
}

// BULLETPROOF: Handle participant leaving
function handleParticipantDisconnected(participant) {
    console.log('👋 PARTICIPANT DISCONNECTED:', participant.identity);
    
    // Remove their main container - use CONSISTENT ID scheme
    const container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        container.remove();
        console.log('🗑️ Removed container for:', participant.identity);
    }
    
    // Remove their screen share container if it exists
    const screenShareContainer = document.getElementById(`screenshare-${participant.sid}`);
    if (screenShareContainer) {
        screenShareContainer.remove();
        console.log('🗑️ Removed screen share container for:', participant.identity);
    }
    
    // Update UI
    updateParticipantCount();
    updateConsistentGrid();
}

// MEGA-IMPROVED: Handle track subscription with BULLETPROOF logic
function handleTrackSubscribed(track, publication, participant) {
    console.log(`🎵 TRACK SUBSCRIBED: ${track.kind} from ${participant.identity}`);
    console.log(`🎵 Track details:`, {
        kind: track.kind,
        sid: track.sid,
        participant: participant.identity,
        participantSid: participant.sid,
        source: publication.source,
        enabled: track.enabled,
        muted: track.muted,
        isRemote: participant !== room.localParticipant
    });
    
    // CRITICAL: Handle screen share tracks separately
    if (publication.source === LiveKit.TrackSource.ScreenShare) {
        console.log('🖥️ Handling screen share track from:', participant.identity);
        handleScreenShareTrack(track, publication, participant);
        return;
    }
    
    // FIXED: Use atomic container retrieval/creation with retry
    let container = getOrCreateParticipantContainer(participant);
    if (!container) {
        console.error('❌ Failed to get/create container for participant:', participant.identity);
        
        // EMERGENCY: Try one more time with delay
        setTimeout(() => {
            console.log('🚨 Emergency retry for container creation:', participant.identity);
            const emergencyContainer = createConsistentContainer(participant, participant === room.localParticipant);
            if (emergencyContainer) {
                console.log('✅ Emergency container created, retrying track attachment');
                if (track.kind === 'video') {
                    attachVideoTrack(track, emergencyContainer, participant);
                } else if (track.kind === 'audio') {
                    attachAudioTrack(track, emergencyContainer, participant);
                }
            }
        }, 1000);
        return;
    }
    
    // CRITICAL: Extra logging for remote participants
    if (participant !== room.localParticipant) {
        console.log(`🌐 REMOTE TRACK PROCESSING: ${track.kind} from ${participant.identity}`);
        console.log(`🌐 Container ID: ${container.id}`);
        console.log(`🌐 Track enabled: ${track.enabled}`);
        console.log(`🌐 Track muted: ${track.muted}`);
    }
    
    // SIMPLIFIED: Direct track attachment with error handling
    try {
        if (track.kind === 'video') {
            console.log(`📹 Processing VIDEO track from ${participant.identity}`);
            attachVideoTrack(track, container, participant);
        } else if (track.kind === 'audio') {
            console.log(`🔊 Processing AUDIO track from ${participant.identity}`);
            attachAudioTrack(track, container, participant);
        }
        
        // CRITICAL: Update grid after track attachment
        updateConsistentGrid();
        
        console.log(`✅ Track subscription completed for: ${participant.identity} (${track.kind})`);
        
    } catch (error) {
        console.error(`❌ Error in track subscription for ${participant.identity}:`, error);
        
        // RECOVERY: Try again after delay
        setTimeout(() => {
            console.log(`🔄 Retrying track attachment for ${participant.identity} (${track.kind})`);
            try {
                if (track.kind === 'video') {
                    attachVideoTrack(track, container, participant);
                } else if (track.kind === 'audio') {
                    attachAudioTrack(track, container, participant);
                }
            } catch (retryError) {
                console.error(`❌ Retry also failed for ${participant.identity}:`, retryError);
            }
        }, 2000);
    }
}

// NEW: Atomic container getter/creator - prevents race conditions
function getOrCreateParticipantContainer(participant) {
    const containerId = `participant-${participant.sid}`;
    let container = document.getElementById(containerId);
    
    if (container) {
        console.log('✅ Container exists for:', participant.identity);
        return container;
    }
    
    // Create container if it doesn't exist
    console.log('📦 Creating container for:', participant.identity);
    container = createConsistentContainer(participant, false);
    
    if (!container) {
        console.error('❌ Failed to create container for:', participant.identity);
        return null;
    }
    
    console.log('✅ Container created for:', participant.identity);
    return container;
}

// SIMPLIFIED: Video track attachment without aggressive retries
function attachVideoTrack(track, container, participant) {
    console.log('📹 ATTACHING VIDEO TRACK for:', participant.identity);
    console.log('📹 Is remote participant:', participant !== room.localParticipant);
    
    const video = container.querySelector('video');
    if (!video) {
        console.error('❌ No video element found in container for:', participant.identity);
        console.error('❌ Container ID:', container.id);
        console.error('❌ Container HTML:', container.innerHTML);
        return;
    }
    
    console.log('✅ Video element found for:', participant.identity);
    
    try {
        // CRITICAL: Check if track is already attached
        if (track.attachedElements && track.attachedElements.length > 0) {
            console.log('⚠️ Video track already attached for:', participant.identity);
            // But still ensure video is configured properly
            configureVideoElement(video, participant);
            return;
        }
        
        // Clear any existing video source SAFELY
        if (video.srcObject) {
            console.log('📹 Clearing previous video source for:', participant.identity);
            try {
                const existingTracks = video.srcObject.getTracks();
                existingTracks.forEach(t => {
                    try {
                        t.stop();
                    } catch (e) {
                        console.warn('⚠️ Failed to stop existing track:', e);
                    }
                });
                video.srcObject = null;
            } catch (e) {
                console.warn('⚠️ Failed to clear existing source:', e);
            }
        }
        
        // CRITICAL: Use LiveKit's attach method properly
        console.log('📹 Attaching track using LiveKit attach method...');
        track.attach(video);
        console.log('✅ Track.attach() completed for:', participant.identity);
        
        // ENHANCED: Configure video element properly
        configureVideoElement(video, participant);
        
        // AGGRESSIVE: Force video to play
        playVideoWithFallback(video, container, participant);
        
        // CRITICAL: Handle video track events
        const handleMuted = () => {
            console.log('📹❌ Video muted for:', participant.identity);
            video.style.opacity = '0.3';
            container.style.background = '#444';
        };
        
        const handleUnmuted = () => {
            console.log('📹✅ Video unmuted for:', participant.identity);
            video.style.opacity = '1';
            container.style.background = 'transparent';
        };
        
        // Remove existing event listeners to prevent duplicates
        track.off(LiveKit.TrackEvent.Muted, handleMuted);
        track.off(LiveKit.TrackEvent.Unmuted, handleUnmuted);
        
        // Add new event listeners
        track.on(LiveKit.TrackEvent.Muted, handleMuted);
        track.on(LiveKit.TrackEvent.Unmuted, handleUnmuted);
        
        console.log('✅ Video track setup completed for:', participant.identity);
        
        // CRITICAL: Special handling for remote participants
        if (participant !== room.localParticipant) {
            console.log('🌐 REMOTE VIDEO ATTACHED successfully for:', participant.identity);
            // Make sure container is visible
            container.style.display = 'block';
            container.style.visibility = 'visible';
            
            // Force a grid update to show the new video
            setTimeout(() => {
                updateConsistentGrid();
            }, 500);
        }
        
    } catch (error) {
        console.error('❌ Failed to attach video track for:', participant.identity, error);
        console.error('❌ Error details:', {
            message: error.message,
            stack: error.stack,
            trackKind: track.kind,
            trackSid: track.sid,
            containerID: container.id
        });
        
        // Visual indication of error
        container.style.background = '#800';
        const errorLabel = container.querySelector('.error-indicator');
        if (!errorLabel) {
            const indicator = document.createElement('div');
            indicator.className = 'error-indicator';
            indicator.textContent = '❌ Video Error';
            indicator.style.position = 'absolute';
            indicator.style.top = '50%';
            indicator.style.left = '50%';
            indicator.style.transform = 'translate(-50%, -50%)';
            indicator.style.color = 'white';
            indicator.style.background = 'rgba(255, 0, 0, 0.8)';
            indicator.style.padding = '5px';
            indicator.style.borderRadius = '3px';
            indicator.style.fontSize = '12px';
            container.appendChild(indicator);
        }
    }
}

// NEW: Helper function to configure video element properly
function configureVideoElement(video, participant) {
    const isLocal = participant === room.localParticipant;
    
    console.log(`🔧 Configuring video element for ${participant.identity} (local: ${isLocal})`);
    
    // Basic video configuration
    video.playsInline = true;
    video.autoplay = true;
    video.style.display = 'block';
    video.style.visibility = 'visible';
    video.style.opacity = '1';
    video.style.objectFit = 'cover';
    video.style.width = '100%';
    video.style.height = '100%';
    video.style.borderRadius = '8px';
    
    // CRITICAL: Muting configuration to prevent echo
    if (isLocal) {
        // Local video must be muted to prevent echo
        video.muted = true;
        video.volume = 0;
        console.log('🔇 Local video muted to prevent echo');
    } else {
        // Remote video should NOT be muted
        video.muted = false;
        video.volume = 1.0;
        console.log('🔊 Remote video unmuted for audio');
    }
    
    // Add data attributes for debugging
    video.setAttribute('data-participant', participant.identity);
    video.setAttribute('data-participant-sid', participant.sid);
    video.setAttribute('data-is-local', isLocal.toString());
    
    console.log(`✅ Video element configured for ${participant.identity}`);
}

// SIMPLIFIED: Audio track attachment without complex logic
function attachAudioTrack(track, container, participant) {
    console.log('🔊 ATTACHING AUDIO TRACK for:', participant.identity);
    
    try {
        // CRITICAL: Check if track is already attached
        if (track.attachedElements && track.attachedElements.length > 0) {
            console.log('⚠️ Audio track already attached for:', participant.identity);
            return;
        }
        
        // Remove any existing audio elements for this participant
        const existingAudios = container.querySelectorAll('audio');
        existingAudios.forEach(audio => {
            if (audio.srcObject) {
                const tracks = audio.srcObject.getTracks();
                tracks.forEach(t => t.stop());
            }
            audio.remove();
        });
        
        // FIXED: Create and configure audio element properly
        const audio = document.createElement('audio');
        audio.autoplay = true;
        audio.muted = false; // Remote audio should NOT be muted
        audio.volume = 1.0;
        audio.style.display = 'none';
        audio.setAttribute('data-participant', participant.identity);
        
        // CRITICAL: Attach track using LiveKit's method
        track.attach(audio);
        container.appendChild(audio);
        
        // SIMPLIFIED: Direct play attempt
        audio.play().then(() => {
            console.log('✅ Audio playing successfully for:', participant.identity);
        }).catch(e => {
            console.warn('⚠️ Audio autoplay prevented for:', participant.identity, e);
            // Add user interaction fallback
            addAudioClickFallback(container, audio, participant);
        });
        
        console.log('✅ Audio track attached successfully for:', participant.identity);
        
    } catch (error) {
        console.error('❌ Failed to attach audio track for:', participant.identity, error);
    }
}

// NEW: Simplified video play with user interaction fallback
function playVideoWithFallback(video, container, participant) {
    video.play().then(() => {
        console.log('✅ Video playing automatically for:', participant.identity);
        container.style.background = 'transparent';
        container.style.cursor = 'default';
    }).catch(e => {
        console.warn('⚠️ Video autoplay prevented for:', participant.identity, 'Adding click handler');
        
        // Visual indicator for user interaction needed
        container.style.background = '#333';
        container.style.cursor = 'pointer';
        
        // Add click handler for manual play
        const clickHandler = async () => {
            try {
                await video.play();
                console.log('✅ Video started after user click for:', participant.identity);
                container.style.background = 'transparent';
                container.style.cursor = 'default';
                container.removeEventListener('click', clickHandler);
            } catch (e2) {
                console.error('❌ Video failed to play even after click:', e2);
            }
        };
        
        container.addEventListener('click', clickHandler);
    });
}

// NEW: Audio click fallback for mobile browsers
function addAudioClickFallback(container, audio, participant) {
    const clickHandler = async () => {
        try {
            await audio.play();
            console.log('✅ Audio started after user interaction for:', participant.identity);
            container.removeEventListener('click', clickHandler);
        } catch (e) {
            console.warn('⚠️ Audio still failed after user interaction:', e);
        }
    };
    
    container.addEventListener('click', clickHandler);
}

// Handle track unsubscription
function handleTrackUnsubscribed(track, publication, participant) {
    console.log(`🔇 TRACK UNSUBSCRIBED: ${track.kind} from ${participant.identity}`);
    
    // Handle screen share track removal
    if (publication.source === LiveKit.TrackSource.ScreenShare) {
        console.log('🖥️ Screen share track unsubscribed from:', participant.identity);
        
        // Remove the screen share container
        const screenShareContainer = document.getElementById(`screenshare-${participant.sid}`);
        if (screenShareContainer && screenShareContainer.parentNode) {
            screenShareContainer.remove();
            console.log('✅ Screen share container removed for:', participant.identity);
        }
        
        // Update grid layout
        updateConsistentGrid();
        return;
    }
    
    // Handle regular video/audio track removal
    console.log('🔇 Regular track unsubscribed, updating layout');
    updateConsistentGrid();
}

// Handle track muted
function handleTrackMuted(publication, participant) {
    console.log(`🔇 Track muted: ${publication.kind} from ${participant.identity}`);
}

// Handle track unmuted
function handleTrackUnmuted(publication, participant) {
    console.log(`🔊 Track unmuted: ${publication.kind} from ${participant.identity}`);
}

// CRITICAL FIX: Enable local media - SUPER AGGRESSIVE VERSION  
async function enableLocalMedia() {
    console.log('🎥 ENABLING LOCAL MEDIA - SUPER AGGRESSIVE MODE');
    
    if (!room || !room.localParticipant) {
        console.error('❌ No room or local participant available');
        throw new Error('Room not connected');
    }
    
    try {
        console.log('🎥 Local participant identity:', room.localParticipant.identity);
        console.log('🎥 Local participant SID:', room.localParticipant.sid);
        
        // STEP 1: Enable camera with aggressive retry
        let cameraEnabled = false;
        let attempts = 0;
        const maxAttempts = 5;
        
        while (!cameraEnabled && attempts < maxAttempts) {
            try {
                console.log(`🎥 Camera enable attempt ${attempts + 1}/${maxAttempts}`);
                await room.localParticipant.setCameraEnabled(true);
                cameraEnabled = true;
                console.log('✅ Camera enabled successfully!');
            } catch (error) {
                console.warn(`⚠️ Camera enable attempt ${attempts + 1} failed:`, error);
                attempts++;
                if (attempts < maxAttempts) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
        }
        
        if (!cameraEnabled) {
            throw new Error('Failed to enable camera after multiple attempts');
        }
        
        // STEP 2: Enable microphone
        try {
            await room.localParticipant.setMicrophoneEnabled(true);
            console.log('✅ Microphone enabled successfully!');
        } catch (error) {
            console.warn('⚠️ Microphone enable failed:', error);
            // Continue anyway, video is more important
        }
        
        // STEP 3: FORCE local video display
        await forceLocalVideoDisplay();
        
        // STEP 4: Update media button states
        updateMediaButtonStates();
        
        console.log('✅ Local media setup completed successfully!');
        
    } catch (error) {
        console.error('❌ Failed to enable local media:', error);
        showError('Kamera konnte nicht aktiviert werden: ' + error.message);
        throw error;
    }
}

// FORCE local video display for ALL participants (especially patients)
async function forceLocalVideoDisplay() {
    console.log('🎥 FORCING LOCAL VIDEO DISPLAY...');
    
    // Wait a bit for tracks to be published
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Find or create local participant container
    let localContainer = document.getElementById(`participant-${room.localParticipant.sid}`);
    
    if (!localContainer) {
        console.log('🎥 Creating local participant container...');
        localContainer = createConsistentContainer(room.localParticipant, true);
    }
    
    const localVideo = localContainer.querySelector('video');
    if (!localVideo) {
        console.error('❌ No video element found in local container');
        return;
    }
    
    // AGGRESSIVE: Try multiple methods to attach local video
    console.log('🎥 Attempting to attach local video track...');
    
    // Method 1: Find camera track from publications
    room.localParticipant.videoTrackPublications.forEach((publication) => {
        if (publication.source === LiveKit.TrackSource.Camera && publication.track) {
            console.log('✅ Found local camera track, attaching...');
            publication.track.attach(localVideo);
            localVideo.muted = true; // Prevent echo
            localVideo.play().catch(e => console.log('Video play error:', e));
            
            // Add participant name
            const nameElement = localContainer.querySelector('.participant-name');
            if (nameElement) {
                nameElement.textContent = room.localParticipant.identity + ' (Sie)';
            }
            
            console.log('✅ Local video displayed successfully!');
        }
    });
    
    // Method 2: If no published track found, get media stream directly
    if (!localVideo.srcObject && !localVideo.currentSrc) {
        console.log('🎥 No published track found, getting media stream directly...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true
            });
            localVideo.srcObject = stream;
            localVideo.muted = true;
            localVideo.play();
            console.log('✅ Local video attached via direct media stream');
        } catch (error) {
            console.error('❌ Failed to get direct media stream:', error);
        }
    }
    
    // Update grid
    updateParticipantGrid();
}

// Handle screen share track from other participants
function handleScreenShareTrack(track, publication, participant) {
    console.log('🖥️ Handling screen share track from:', participant.identity);
    
    // Create or get a dedicated screen share container
    let screenShareContainer = document.getElementById(`screenshare-${participant.sid}`);
    
    if (!screenShareContainer) {
        // Create a new container for screen share
        screenShareContainer = document.createElement('div');
        screenShareContainer.id = `screenshare-${participant.sid}`;
        screenShareContainer.className = 'participant-container screen-share-container';
        
        // Create video element for screen share
        const video = document.createElement('video');
        video.autoplay = true;
        video.playsInline = true;
        video.muted = false; // Screen shares can have audio
        video.className = 'screen-share-video';
        
        // Create label for screen share
        const label = document.createElement('div');
        label.className = 'participant-name';
        label.textContent = `🖥️ ${participant.identity} (Bildschirm)`;
        
        screenShareContainer.appendChild(video);
        screenShareContainer.appendChild(label);
        
        // Add to video grid
        const videoGrid = document.getElementById('videoGrid');
        if (videoGrid) {
            videoGrid.appendChild(screenShareContainer);
            console.log('✅ Screen share container created and added to grid');
        }
    }
    
    // Get the video element from the screen share container
    const video = screenShareContainer.querySelector('video');
    if (!video) {
        console.error('❌ No video element found in screen share container');
        return;
    }
    
    try {
        // Attach the screen share track
        track.attach(video);
        
        // Ensure video is visible and playing
        video.style.display = 'block';
        video.style.visibility = 'visible';
        video.style.opacity = '1';
        
        // Try to play the video
        video.play().then(() => {
            console.log('✅ Screen share playing successfully from:', participant.identity);
        }).catch(e => {
            console.warn('⚠️ Screen share autoplay prevented:', e);
        });
        
        console.log('✅ Screen share track attached for:', participant.identity);
        
        // Handle track events
        track.on(LiveKit.TrackEvent.Ended, () => {
            console.log('🖥️ Screen share ended for:', participant.identity);
            // Remove the screen share container
            if (screenShareContainer && screenShareContainer.parentNode) {
                screenShareContainer.remove();
            }
            updateConsistentGrid();
        });
        
        // Update grid layout
        updateConsistentGrid();
        
    } catch (error) {
        console.error('❌ Failed to attach screen share track:', error);
    }
}

// DEBUGGING: Force process all available tracks
function forceProcessAllTracks() {
    console.log('🔍 FORCE PROCESSING ALL AVAILABLE TRACKS...');
    
    if (!room) {
        console.error('❌ No room available for track processing');
        return;
    }
    
    console.log('🔍 Room state:', room.state);
    console.log('🔍 Local participant:', room.localParticipant?.identity);
    console.log('🔍 Remote participants count:', room.remoteParticipants.size);
    
    // Process local participant
    if (room.localParticipant) {
        console.log('🔍 Local participant tracks:');
        room.localParticipant.trackPublications.forEach((publication, key) => {
            console.log(`  - ${publication.kind} (${publication.source}): subscribed=${publication.isSubscribed}, track=${!!publication.track}`);
            if (publication.track && publication.isSubscribed) {
                console.log('    → Processing local track');
                handleTrackSubscribed(publication.track, publication, room.localParticipant);
            }
        });
    }
    
    // Process remote participants
    console.log('🔍 Remote participants and their tracks:');
    room.remoteParticipants.forEach((participant) => {
        console.log(`👤 Participant: ${participant.identity} (SID: ${participant.sid})`);
        console.log(`   Track publications: ${participant.trackPublications.size}`);
        
        participant.trackPublications.forEach((publication, key) => {
            console.log(`  - ${publication.kind} (${publication.source}): subscribed=${publication.isSubscribed}, track=${!!publication.track}`);
            if (publication.track && publication.isSubscribed) {
                console.log('    → Processing remote track');
                handleTrackSubscribed(publication.track, publication, participant);
            } else if (!publication.isSubscribed) {
                console.log('    → Track not subscribed, attempting to subscribe...');
                publication.setSubscribed(true);
            }
        });
    });
    
    // Update grid
    updateConsistentGrid();
    console.log('🔍 Force processing completed');
}

// Add this function to global scope for debugging
window.forceProcessAllTracks = forceProcessAllTracks;

// DEBUGGING: Add a button to manually trigger track processing
function addDebugButton() {
    const debugBtn = document.createElement('button');
    debugBtn.textContent = '🔍 Debug Tracks';
    debugBtn.style.position = 'fixed';
    debugBtn.style.top = '10px';
    debugBtn.style.right = '10px';
    debugBtn.style.zIndex = '9999';
    debugBtn.style.background = '#ff4444';
    debugBtn.style.color = 'white';
    debugBtn.style.border = 'none';
    debugBtn.style.padding = '10px';
    debugBtn.style.borderRadius = '5px';
    debugBtn.style.cursor = 'pointer';
    
    debugBtn.onclick = () => {
        console.log('🔍 Manual debug triggered');
        forceProcessAllTracks();
    };
    
    document.body.appendChild(debugBtn);
    
    // Add second button for force subscription
    const forceBtn = document.createElement('button');
    forceBtn.textContent = '🔥 Force Video';
    forceBtn.style.position = 'fixed';
    forceBtn.style.top = '50px';
    forceBtn.style.right = '10px';
    forceBtn.style.zIndex = '9999';
    forceBtn.style.background = '#ff8800';
    forceBtn.style.color = 'white';
    forceBtn.style.border = 'none';
    forceBtn.style.padding = '10px';
    forceBtn.style.borderRadius = '5px';
    forceBtn.style.cursor = 'pointer';
    
    forceBtn.onclick = () => {
        console.log('🔥 Force video subscription triggered');
        forceSubscribeToAllRemoteTracks();
    };
    
    document.body.appendChild(forceBtn);
}

// Add debug button when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addDebugButton);
} else {
    addDebugButton();
}

// CRITICAL FIX: Force subscribe to all remote tracks
function forceSubscribeToAllRemoteTracks() {
    console.log('🔥 FORCE SUBSCRIBING TO ALL REMOTE TRACKS...');
    
    if (!room) {
        console.error('❌ No room available');
        return false;
    }
    
    if (room.state !== 'connected') {
        console.error('❌ Room not connected, state:', room.state);
        return false;
    }
    
    let subscriptionAttempts = 0;
    let trackProcessAttempts = 0;
    
    room.remoteParticipants.forEach((participant) => {
        console.log(`🎯 Processing remote participant: ${participant.identity} (SID: ${participant.sid})`);
        
        // Ensure container exists
        const container = getOrCreateParticipantContainer(participant);
        if (!container) {
            console.error(`❌ Failed to get/create container for ${participant.identity}`);
            return;
        }
        
        participant.trackPublications.forEach((publication) => {
            console.log(`🎯 Found track: ${publication.kind} (${publication.source})`);
            console.log(`   - Subscribed: ${publication.isSubscribed}`);
            console.log(`   - Has track: ${!!publication.track}`);
            console.log(`   - Track enabled: ${publication.track ? publication.track.enabled : 'N/A'}`);
            console.log(`   - Track muted: ${publication.track ? publication.track.muted : 'N/A'}`);
            
            // FORCE SUBSCRIPTION if not subscribed
            if (!publication.isSubscribed) {
                console.log(`🔥 FORCE SUBSCRIBING to ${publication.kind} from ${participant.identity}`);
                publication.setSubscribed(true).then(() => {
                    console.log(`✅ Successfully subscribed to ${publication.kind} from ${participant.identity}`);
                }).catch(e => {
                    console.error(`❌ Failed to subscribe to ${publication.kind} from ${participant.identity}:`, e);
                });
                subscriptionAttempts++;
            } else if (publication.track) {
                // Track is subscribed and available - ensure it's properly attached
                console.log(`🎥 Re-processing subscribed ${publication.kind} track from ${participant.identity}`);
                handleTrackSubscribed(publication.track, publication, participant);
                trackProcessAttempts++;
            }
        });
        
        console.log(`📊 Participant ${participant.identity}: ${subscriptionAttempts} subscription attempts, ${trackProcessAttempts} track processes`);
    });
    
    console.log(`🔥 Force subscription completed:`);
    console.log(`   - Remote participants: ${room.remoteParticipants.size}`);
    console.log(`   - Subscription attempts: ${subscriptionAttempts}`);
    console.log(`   - Track processes: ${trackProcessAttempts}`);
    
    // Update grid immediately
    updateConsistentGrid();
    
    // Give time for subscriptions to process, then update again
    setTimeout(() => {
        console.log('🔄 Post-subscription grid update...');
        updateConsistentGrid();
        
        // Final verification
        setTimeout(() => {
            console.log('🔍 Final verification of track attachments...');
            room.remoteParticipants.forEach((participant) => {
                const container = document.getElementById(`participant-${participant.sid}`);
                const video = container?.querySelector('video');
                const hasVideoSource = video && (video.srcObject || video.src);
                console.log(`🔍 ${participant.identity}: Container=${!!container}, Video=${!!video}, Source=${hasVideoSource}`);
            });
        }, 2000);
    }, 1000);
    
    return true;
}

// Add forceSubscribeToAllRemoteTracks to global scope
window.forceSubscribeToAllRemoteTracks = forceSubscribeToAllRemoteTracks; 

// MISSING FUNCTION: connectToRoom - SUPER AGGRESSIVE VERSION
async function connectToRoom() {
    console.log('🔗 CONNECTING TO ROOM - AGGRESSIVE MODE');
    
    // Get meeting data
    let meetingData = sessionStorage.getItem('meetingData');
    if (!meetingData) {
        console.error('❌ No meeting data found');
        throw new Error('Meeting data not found');
    }
    
    meetingData = JSON.parse(meetingData);
    console.log('📋 Meeting data:', meetingData);
    
    // Create room with aggressive settings
    room = new LiveKit.Room({
        adaptiveStream: true,
        dynacast: true,
        audioCaptureDefaults: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
        },
        videoCaptureDefaults: {
            resolution: {
                width: 1280,
                height: 720
            },
            frameRate: 30
        }
    });
    
    // CRITICAL: Set up ALL event handlers BEFORE connecting
    setupRoomEvents();
    
    // Connect to room
    console.log('🔗 Connecting to LiveKit...');
    await room.connect(meetingData.livekit_url, meetingData.token);
    
    console.log('✅ Connected to room:', room.name);
    console.log('🎯 Local participant:', room.localParticipant.identity);
    console.log('👥 Remote participants:', room.remoteParticipants.size);
    
    // FORCE track subscription for ALL existing participants
    room.remoteParticipants.forEach(participant => {
        console.log('🔄 Processing existing participant:', participant.identity);
        handleParticipantConnected(participant);
    });
}

// AGGRESSIVE track subscription setup
function setupAggressiveTrackSubscription() {
    console.log('🎯 Setting up AGGRESSIVE track subscription...');
    
    if (!room) {
        console.error('❌ No room available for track subscription');
        return;
    }
    
    // Force subscribe to ALL tracks immediately
    const forceSubscribeInterval = setInterval(() => {
        room.remoteParticipants.forEach(participant => {
            participant.trackPublications.forEach(publication => {
                if (!publication.isSubscribed && publication.isEnabled) {
                    console.log('🔄 FORCING subscription to:', publication.kind, 'from', participant.identity);
                    publication.setSubscribed(true);
                }
            });
        });
    }, 1000);
    
    // Stop after 30 seconds
    setTimeout(() => {
        clearInterval(forceSubscribeInterval);
        console.log('⏹️ Stopped aggressive track subscription');
    }, 30000);
}

// FIXED: Room Events Setup - AGGRESSIVE MODE
function setupRoomEvents() {
    console.log('🎬 Setting up room events - AGGRESSIVE MODE');
    
    // BULLETPROOF: Room connected handler
    room.on(LiveKit.RoomEvent.Connected, async () => {
        console.log('🎉 Room connected successfully!');
        console.log('🎉 Local participant identity:', room.localParticipant.identity);
        console.log('🎉 Local participant SID:', room.localParticipant.sid);
        console.log('🎉 Remote participants count:', room.remoteParticipants.size);
        
        // IMMEDIATE: Enable local media
        console.log('🎥 Enabling local camera and microphone...');
        await enableLocalMedia();
        
        // IMMEDIATE: Process all existing participants
        console.log('👥 Processing existing participants...');
        room.remoteParticipants.forEach(participant => {
            console.log('👤 Processing existing remote participant:', participant.identity);
            handleParticipantConnected(participant);
        });
        
        // Update UI
        showStatus('Verbunden! Video wird geladen...', 'success');
        hideLoadingOverlay();
    });
    
    // Participant connected
    room.on(LiveKit.RoomEvent.ParticipantConnected, (participant) => {
        console.log('👤 NEW PARTICIPANT CONNECTED:', participant.identity);
        handleParticipantConnected(participant);
    });
    
    // Participant disconnected  
    room.on(LiveKit.RoomEvent.ParticipantDisconnected, (participant) => {
        console.log('👤 PARTICIPANT DISCONNECTED:', participant.identity);
        const container = document.getElementById(`participant-${participant.sid}`);
        if (container) {
            container.remove();
            updateParticipantGrid();
        }
    });
    
    // CRITICAL: Track subscribed
    room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {
        console.log(`🎵 TRACK SUBSCRIBED: ${track.kind} from ${participant.identity}`);
        handleTrackSubscribed(track, publication, participant);
    });
    
    // Track unsubscribed
    room.on(LiveKit.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
        console.log(`🔇 TRACK UNSUBSCRIBED: ${track.kind} from ${participant.identity}`);
        track.detach();
    });
    
    // Track published
    room.on(LiveKit.RoomEvent.TrackPublished, (publication, participant) => {
        console.log(`📢 TRACK PUBLISHED: ${publication.kind} from ${participant.identity}`);
        // Force immediate subscription
        setTimeout(() => {
            if (!publication.isSubscribed) {
                console.log('🔄 Force subscribing to newly published track');
                publication.setSubscribed(true);
            }
        }, 100);
    });
    
    // Connection quality changed
    room.on(LiveKit.RoomEvent.ConnectionQualityChanged, (quality, participant) => {
        console.log(`📶 Connection quality for ${participant.identity}:`, quality);
    });
    
    // Disconnected
    room.on(LiveKit.RoomEvent.Disconnected, () => {
        console.log('❌ Room disconnected');
        showError('Verbindung unterbrochen. Seite wird neu geladen...');
        setTimeout(() => location.reload(), 3000);
    });
}