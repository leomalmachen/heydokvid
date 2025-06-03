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
        
        console.log('🚀 Starting ULTRA-SIMPLE meeting initialization...');
        showStatus('Verbindung wird aufgebaut...', 'info');
        
        // Validate meeting ID from global variable
        if (!meetingId || meetingId === 'meeting') {
            throw new Error('Meeting-ID nicht gefunden in URL');
        }
        
        console.log('Meeting ID:', meetingId);
        
        // Check if we have stored meeting data from patient setup
        let meetingData = sessionStorage.getItem('meetingData');
        const patientSetupCompleted = sessionStorage.getItem('patientSetupCompleted');
        
        if (patientSetupCompleted === 'true' && meetingData) {
            console.log('✅ Using stored meeting data from patient setup');
            try {
                meetingData = JSON.parse(meetingData);
                
                // Verify the meeting data is for the correct meeting
                if (meetingData.meeting_id === meetingId) {
                    console.log('✅ Meeting data matches current meeting ID');
                    
                    // Connect directly to room
                    await connectToRoom(meetingData);
                    isInitialized = true;
                    console.log('🎉 Patient initialization completed using stored data!');
                    return;
                } else {
                    console.warn('⚠️ Stored meeting data is for different meeting, clearing...');
                    sessionStorage.removeItem('meetingData');
                    sessionStorage.removeItem('patientSetupCompleted');
                    meetingData = null;
                }
            } catch (error) {
                console.error('❌ Error parsing stored meeting data:', error);
                sessionStorage.removeItem('meetingData');
                sessionStorage.removeItem('patientSetupCompleted');
                meetingData = null;
            }
        }
        
        if (!meetingData) {
            // Check user role from URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const userRole = urlParams.get('role');
            
            // IMPROVED: Use nice modal for name input
            try {
                const participantName = await getParticipantName();
                
                // Use role-specific endpoints
                let joinEndpoint, joinData;
                
                if (userRole === 'doctor') {
                    console.log('🩺 Doctor joining meeting...');
                    joinEndpoint = `/api/meetings/${meetingId}/join-doctor`;
                    joinData = {
                        participant_name: participantName,
                        participant_role: 'doctor'
                    };
                } else {
                    console.log('👤 Participant joining meeting...');
                    joinEndpoint = `/api/meetings/${meetingId}/join`;
                    joinData = {
                        participant_name: participantName
                    };
                }
                
                const response = await fetch(joinEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(joinData)
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

// ULTRA-ADVANCED: Connect to LiveKit room
async function connectToRoom(data) {
    console.log('🔗 Connecting to LiveKit room...', data.livekit_url);
    
    try {
        // Initialize room with ENHANCED AUDIO SETTINGS
        room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true,
            // CRITICAL: Enhanced audio settings to prevent echo
            audioCaptureDefaults: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 48000,
                channelCount: 1, // Mono to reduce processing
            },
            videoCaptureDefaults: {
                resolution: LiveKit.VideoPresets.h720.resolution,
            },
            // IMPORTANT: Prevent audio feedback
            publishDefaults: {
                stopMicTrackOnMute: false, // Keep track alive when muted
                audioPreset: LiveKit.AudioPresets.speech, // Optimized for speech
            },
        });
        
        // BULLETPROOF: Event handlers setup
        room.on(LiveKit.RoomEvent.Connected, () => {
            console.log('🎉 Room connected successfully!');
            
            // CRITICAL: Process local participant first - use CONSISTENT function
            console.log('👤 Processing LOCAL participant:', room.localParticipant.identity);
            const localContainer = createConsistentContainer(room.localParticipant, true);
            
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

// MEGA-IMPROVED: Handle new participant joining
function handleParticipantConnected(participant) {
    console.log('👤 NEW PARTICIPANT CONNECTED:', participant.identity);
    
    // BULLETPROOF: Create container for new participant - use CONSISTENT function
    const container = createConsistentContainer(participant, false);
    
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
    updateConsistentGrid();
    
    console.log('✅ Participant setup completed for:', participant.identity);
}

// BULLETPROOF: Handle participant leaving
function handleParticipantDisconnected(participant) {
    console.log('👋 PARTICIPANT DISCONNECTED:', participant.identity);
    
    // Remove their container - use CONSISTENT ID scheme
    const container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        container.remove();
        console.log('🗑️ Removed container for:', participant.identity);
    }
    
    // Update UI
    updateParticipantCount();
    updateConsistentGrid();
}

// ULTRA-ROBUST: Handle track subscription (when video/audio arrives)
function handleTrackSubscribed(track, publication, participant) {
    console.log(`🎵 TRACK SUBSCRIBED: ${track.kind} from ${participant.identity}`);
    
    // Get participant container - use CONSISTENT ID scheme
    const container = document.getElementById(`participant-${participant.sid}`);
    if (!container) {
        console.warn('⚠️ No container found for participant:', participant.identity);
        // Try to create it
        createConsistentContainer(participant, false);
        return;
    }
    
    if (track.kind === 'video') {
        console.log('📹 Attaching VIDEO track for:', participant.identity);
        
        // Get video element
        const video = container.querySelector('video');
        if (!video) {
            console.error('❌ No video element found in container for:', participant.identity);
            return;
        }
        
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
        
        console.log('✅ Video track attached successfully for:', participant.identity);
        
    } else if (track.kind === 'audio') {
        console.log('🔊 Attaching AUDIO track for:', participant.identity);
        
        // Create audio element for remote audio
        const audio = document.createElement('audio');
        audio.autoplay = true;
        audio.muted = false; // Remote audio should NOT be muted
        audio.volume = 1.0;
        
        track.attach(audio);
        container.appendChild(audio);
        
        console.log('✅ Audio track attached successfully for:', participant.identity);
    }
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
        
        // CRITICAL: Handle local tracks properly to prevent echo - use CONSISTENT ID scheme
        const localContainer = document.getElementById(`participant-${room.localParticipant.sid}`);
        if (!localContainer) {
            console.log('🔧 Creating missing local container...');
            createConsistentContainer(room.localParticipant, true);
            return; // Wait for container to be created
        }
        
        const localVideo = localContainer.querySelector('video');
        if (!localVideo) {
            console.error('❌ Local video element not found');
            return;
        }
        
        // ECHO PREVENTION: Ensure local video is ALWAYS muted
        localVideo.muted = true;
        localVideo.volume = 0;
        
        // Attach video tracks to local video element
        room.localParticipant.videoTrackPublications.forEach((publication) => {
            if (publication.track) {
                console.log('📹 Attaching LOCAL video track');
                publication.track.attach(localVideo);
                localVideo.style.display = videoEnabled ? 'block' : 'none';
            }
        });
        
        // CRITICAL: NEVER attach local audio tracks to prevent echo
        room.localParticipant.audioTrackPublications.forEach((publication) => {
            if (publication.track) {
                console.log('🔇 LOCAL audio track found - NOT attaching to prevent echo');
                // Do NOT attach local audio track - this prevents echo!
            }
        });
        
        console.log('✅ Local media enabled successfully (echo-free)');
        
        // Hide loading and show controls
        const loadingElement = document.getElementById('loadingState');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
        // Update participant count and layout
        updateParticipantCount();
        updateConsistentGrid();
        
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