// Global variables
let room;
let localParticipant;
let audioEnabled = true;
let videoEnabled = true;
const participants = new Map();

// Get meeting ID from URL
const pathParts = window.location.pathname.split('/');
const meetingId = pathParts[pathParts.length - 1];

// Initialize the meeting only when LiveKit is ready
async function initMeeting() {
    console.log('Initializing meeting:', meetingId);
    
    // Wait for LiveKit to be available if it's still loading
    if (window.livekitLoading) {
        console.log('Waiting for LiveKit SDK to load...');
        let attempts = 0;
        while (window.livekitLoading && attempts < 50) { // Wait max 5 seconds
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
    }
    
    // Check if LiveKit is available
    if (typeof LiveKit === 'undefined') {
        showError('LiveKit Video SDK konnte nicht geladen werden. Bitte laden Sie die Seite neu.');
        return;
    }
    
    console.log('LiveKit SDK is ready, proceeding with meeting initialization...');
    
    // Get meeting data from sessionStorage
    let meetingData = sessionStorage.getItem('meetingData');
    
    if (!meetingData) {
        // If no data in session, we need to join the meeting
        const participantName = localStorage.getItem('userName') || prompt('Dein Name:') || 'Teilnehmer';
        
        try {
            const response = await fetch(`/api/meetings/${meetingId}/join`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ participant_name: participantName })
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Meeting nicht gefunden oder abgelaufen');
                }
                throw new Error('Fehler beim Beitreten zum Meeting');
            }

            meetingData = await response.json();
            sessionStorage.setItem('meetingData', JSON.stringify(meetingData));
        } catch (error) {
            showError('Fehler beim Beitreten: ' + error.message);
            setTimeout(() => {
                window.location.href = '/';
            }, 3000);
            return;
        }
    } else {
        meetingData = JSON.parse(meetingData);
    }

    // Connect to LiveKit room
    await connectToRoom(meetingData);
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

async function connectToRoom(meetingData) {
    try {
        console.log('Connecting to LiveKit room...');
        
        // Create room instance
        room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true,
            publishDefaults: {
                videoSimulcastLayers: [
                    LiveKit.VideoPresets.h90,
                    LiveKit.VideoPresets.h180,
                    LiveKit.VideoPresets.h360,
                ],
            },
        });

        // Set up event handlers
        room
            .on(LiveKit.RoomEvent.TrackSubscribed, handleTrackSubscribed)
            .on(LiveKit.RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
            .on(LiveKit.RoomEvent.ParticipantConnected, handleParticipantConnected)
            .on(LiveKit.RoomEvent.ParticipantDisconnected, handleParticipantDisconnected)
            .on(LiveKit.RoomEvent.Disconnected, handleDisconnect)
            .on(LiveKit.RoomEvent.LocalTrackPublished, handleLocalTrackPublished)
            .on(LiveKit.RoomEvent.ConnectionStateChanged, (state) => {
                console.log('Connection state changed:', state);
            })
            .on(LiveKit.RoomEvent.RoomMetadataChanged, (metadata) => {
                console.log('Room metadata changed:', metadata);
            });

        // Connect to room
        console.log('Connecting to:', meetingData.livekit_url);
        await room.connect(meetingData.livekit_url, meetingData.token);
        console.log('Connected to room successfully');

        // Hide loading state
        const loadingElement = document.getElementById('loadingState');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        // Set local participant
        localParticipant = room.localParticipant;

        // Request camera and microphone permissions and enable them
        try {
            console.log('Requesting camera and microphone permissions...');
            
            // First, try to get permission for both camera and microphone
            await room.localParticipant.enableCameraAndMicrophone();
            console.log('Camera and microphone enabled successfully');
            
            // Update button states
            updateControlButtons();
            
        } catch (error) {
            console.warn('Error enabling camera/microphone together:', error);
            
            // Try to enable them separately with better error handling
            try {
                await room.localParticipant.setMicrophoneEnabled(true);
                console.log('Microphone enabled');
            } catch (micError) {
                console.error('Microphone access denied:', micError);
                audioEnabled = false;
            }
            
            try {
                await room.localParticipant.setCameraEnabled(true);
                console.log('Camera enabled');
            } catch (camError) {
                console.error('Camera access denied:', camError);
                videoEnabled = false;
            }
            
            updateControlButtons();
        }

        // Update participant count
        updateParticipantCount();

        // Set share link
        const shareUrl = window.location.href;
        const shareLinkInput = document.getElementById('shareLinkInput');
        if (shareLinkInput) {
            shareLinkInput.value = shareUrl;
        }

    } catch (error) {
        console.error('Error connecting to room:', error);
        showError('Fehler beim Verbinden zum Meeting: ' + error.message);
    }
}

function handleTrackSubscribed(track, publication, participant) {
    console.log('Track subscribed:', track.kind, participant.identity);
    
    if (track.kind === LiveKit.Track.Kind.Video || track.kind === LiveKit.Track.Kind.Audio) {
        // Get or create participant container
        let container = document.getElementById(`participant-${participant.sid}`);
        if (!container) {
            container = createParticipantContainer(participant);
        }

        // Attach track
        if (track.kind === LiveKit.Track.Kind.Video) {
            const videoElement = container.querySelector('video');
            track.attach(videoElement);
        } else if (track.kind === LiveKit.Track.Kind.Audio) {
            // Audio tracks are attached to a hidden element
            const audioElement = document.createElement('audio');
            audioElement.autoplay = true;
            track.attach(audioElement);
            container.appendChild(audioElement);
        }
    }
}

function handleTrackUnsubscribed(track, publication, participant) {
    console.log('Track unsubscribed:', track.kind, participant.identity);
    track.detach();
}

function handleParticipantConnected(participant) {
    console.log('Participant connected:', participant.identity);
    participants.set(participant.sid, participant);
    updateParticipantCount();
}

function handleParticipantDisconnected(participant) {
    console.log('Participant disconnected:', participant.identity);
    participants.delete(participant.sid);
    
    // Remove participant container
    const container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        container.remove();
    }
    
    updateParticipantCount();
}

function handleDisconnect() {
    console.log('Disconnected from room');
    showError('Verbindung zum Meeting wurde getrennt');
    setTimeout(() => {
        window.location.href = '/';
    }, 3000);
}

function handleLocalTrackPublished(publication, participant) {
    console.log('Local track published:', publication.kind);
    
    // Create container for local participant if not exists
    let container = document.getElementById(`participant-${participant.sid}`);
    if (!container) {
        container = createParticipantContainer(participant, true);
    }

    // Attach local video
    if (publication.kind === LiveKit.Track.Kind.Video) {
        const videoElement = container.querySelector('video');
        publication.track.attach(videoElement);
    }
}

function createParticipantContainer(participant, isLocal = false) {
    const container = document.createElement('div');
    container.className = 'participant-container';
    container.id = `participant-${participant.sid}`;
    
    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    video.muted = isLocal; // Mute local video to prevent echo
    
    const nameLabel = document.createElement('div');
    nameLabel.className = 'participant-name';
    nameLabel.textContent = participant.identity || participant.name || 'Teilnehmer';
    if (isLocal) nameLabel.textContent += ' (Du)';
    
    container.appendChild(video);
    container.appendChild(nameLabel);
    
    const videoGrid = document.getElementById('videoGrid');
    if (videoGrid) {
        videoGrid.appendChild(container);
    }
    
    return container;
}

function updateParticipantCount() {
    const count = room ? room.participants.size + 1 : 1; // +1 for local participant
    const participantCountElement = document.getElementById('participantCount');
    if (participantCountElement) {
        participantCountElement.textContent = count;
    }
}

function updateControlButtons() {
    // Update microphone button
    const micBtn = document.getElementById('toggleMic');
    if (micBtn) {
        micBtn.classList.toggle('active', audioEnabled);
        const micOn = micBtn.querySelector('.mic-on');
        const micOff = micBtn.querySelector('.mic-off');
        if (micOn) micOn.classList.toggle('hidden', !audioEnabled);
        if (micOff) micOff.classList.toggle('hidden', audioEnabled);
    }
    
    // Update video button
    const videoBtn = document.getElementById('toggleVideo');
    if (videoBtn) {
        videoBtn.classList.toggle('active', videoEnabled);
        const videoOn = videoBtn.querySelector('.video-on');
        const videoOff = videoBtn.querySelector('.video-off');
        if (videoOn) videoOn.classList.toggle('hidden', !videoEnabled);
        if (videoOff) videoOff.classList.toggle('hidden', videoEnabled);
    }
}

// Setup event listeners when DOM is ready
function setupEventListeners() {
    // Control button handlers
    const toggleMicBtn = document.getElementById('toggleMic');
    if (toggleMicBtn) {
        toggleMicBtn.addEventListener('click', async () => {
            if (!room) return;
            
            try {
                audioEnabled = !audioEnabled;
                await room.localParticipant.setMicrophoneEnabled(audioEnabled);
                updateControlButtons();
                console.log('Microphone', audioEnabled ? 'enabled' : 'disabled');
            } catch (error) {
                console.error('Error toggling microphone:', error);
                // Revert the state if it failed
                audioEnabled = !audioEnabled;
                updateControlButtons();
            }
        });
    }

    const toggleVideoBtn = document.getElementById('toggleVideo');
    if (toggleVideoBtn) {
        toggleVideoBtn.addEventListener('click', async () => {
            if (!room) return;
            
            try {
                videoEnabled = !videoEnabled;
                await room.localParticipant.setCameraEnabled(videoEnabled);
                updateControlButtons();
                console.log('Camera', videoEnabled ? 'enabled' : 'disabled');
            } catch (error) {
                console.error('Error toggling camera:', error);
                // Revert the state if it failed
                videoEnabled = !videoEnabled;
                updateControlButtons();
            }
        });
    }

    const shareLinkBtn = document.getElementById('shareLink');
    if (shareLinkBtn) {
        shareLinkBtn.addEventListener('click', () => {
            const shareModal = document.getElementById('shareModal');
            if (shareModal) {
                shareModal.classList.add('show');
            }
        });
    }

    const copyLinkBtn = document.getElementById('copyLink');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', async () => {
            const input = document.getElementById('shareLinkInput');
            if (!input) return;
            
            try {
                // Use modern clipboard API if available
                if (navigator.clipboard && window.isSecureContext) {
                    await navigator.clipboard.writeText(input.value);
                } else {
                    // Fallback for older browsers
                    input.select();
                    document.execCommand('copy');
                }
                
                copyLinkBtn.textContent = '✓ Kopiert!';
                setTimeout(() => {
                    copyLinkBtn.textContent = '📋 Kopieren';
                }, 2000);
            } catch (error) {
                console.error('Error copying to clipboard:', error);
            }
        });
    }

    const leaveMeetingBtn = document.getElementById('leaveMeeting');
    if (leaveMeetingBtn) {
        leaveMeetingBtn.addEventListener('click', async () => {
            if (confirm('Meeting wirklich verlassen?')) {
                try {
                    if (room) {
                        await room.disconnect();
                    }
                } catch (error) {
                    console.error('Error disconnecting from room:', error);
                }
                
                sessionStorage.removeItem('meetingData');
                window.location.href = '/';
            }
        });
    }

    // Close modal on outside click
    const shareModal = document.getElementById('shareModal');
    if (shareModal) {
        shareModal.addEventListener('click', (e) => {
            if (e.target.id === 'shareModal') {
                e.target.classList.remove('show');
            }
        });
    }
}

// Initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, setting up event listeners and initializing meeting...');
        setupEventListeners();
        initMeeting();
    });
} else {
    // DOM already loaded
    console.log('DOM already loaded, setting up event listeners and initializing meeting...');
    setupEventListeners();
    initMeeting();
} 