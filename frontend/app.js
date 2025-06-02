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
async function initializeMeeting() {
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
    
    // Check if LiveKit is available - try both LiveKit and LivekitClient
    const LiveKit = typeof window.LiveKit !== 'undefined' ? window.LiveKit : 
                   typeof window.LivekitClient !== 'undefined' ? window.LivekitClient : undefined;
    
    if (typeof LiveKit === 'undefined') {
        showError('LiveKit Video SDK konnte nicht geladen werden. Bitte laden Sie die Seite neu.');
        return;
    }
    
    // Make LiveKit globally available under the expected name
    if (typeof window.LiveKit === 'undefined' && typeof window.LivekitClient !== 'undefined') {
        window.LiveKit = window.LivekitClient;
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
        console.log('Meeting data:', meetingData);
        console.log('LiveKit URL:', meetingData.livekit_url);
        console.log('Token length:', meetingData.token ? meetingData.token.length : 'No token');
        
        // Validate meeting data
        if (!meetingData.livekit_url || !meetingData.token) {
            throw new Error('Ungültige Meeting-Daten: URL oder Token fehlt');
        }
        
        // Create room instance with better error handling
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

        // Set up event handlers with better error logging
        room
            .on(LiveKit.RoomEvent.TrackSubscribed, handleTrackSubscribed)
            .on(LiveKit.RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
            .on(LiveKit.RoomEvent.ParticipantConnected, handleParticipantConnected)
            .on(LiveKit.RoomEvent.ParticipantDisconnected, handleParticipantDisconnected)
            .on(LiveKit.RoomEvent.Disconnected, handleDisconnect)
            .on(LiveKit.RoomEvent.LocalTrackPublished, handleLocalTrackPublished)
            .on(LiveKit.RoomEvent.ConnectionStateChanged, (state) => {
                console.log('🔄 Connection state changed:', state);
                if (state === LiveKit.ConnectionState.Failed) {
                    console.error('❌ Connection failed!');
                    showError('Verbindung fehlgeschlagen. Bitte überprüfen Sie Ihre Internetverbindung.');
                } else if (state === LiveKit.ConnectionState.Disconnected) {
                    console.log('🔌 Connection disconnected');
                } else if (state === LiveKit.ConnectionState.Connecting) {
                    console.log('🔄 Connecting...');
                } else if (state === LiveKit.ConnectionState.Connected) {
                    console.log('✅ Connected successfully!');
                } else if (state === LiveKit.ConnectionState.Reconnecting) {
                    console.log('🔄 Reconnecting...');
                }
            })
            .on(LiveKit.RoomEvent.Reconnecting, () => {
                console.log('🔄 Room reconnecting event');
            })
            .on(LiveKit.RoomEvent.Reconnected, () => {
                console.log('✅ Room reconnected event');
            })
            .on(LiveKit.RoomEvent.RoomMetadataChanged, (metadata) => {
                console.log('📝 Room metadata changed:', metadata);
            })
            .on(LiveKit.RoomEvent.ConnectionQualityChanged, (quality, participant) => {
                console.log('📶 Connection quality changed:', quality, participant?.identity);
            })
            .on(LiveKit.RoomEvent.MediaDevicesError, (error) => {
                console.error('🎥 Media devices error:', error);
                showError('Fehler beim Zugriff auf Kamera/Mikrofon: ' + error.message);
            })
            .on(LiveKit.RoomEvent.SignalConnected, () => {
                console.log('📡 Signal connection established');
            })
            .on(LiveKit.RoomEvent.SignalDisconnected, () => {
                console.log('📡 Signal connection lost - but may reconnect automatically');
            })
            .on(LiveKit.RoomEvent.TrackMuted, (publication, participant) => {
                console.log('🔇 Track muted:', publication.kind, participant?.identity);
                console.log('🔇 Muted track details:', {
                    trackSid: publication.trackSid,
                    source: publication.source,
                    isLocal: participant === room.localParticipant
                });
            })
            .on(LiveKit.RoomEvent.TrackUnmuted, (publication, participant) => {
                console.log('🔊 Track unmuted:', publication.kind, participant?.identity);
                console.log('🔊 Unmuted track details:', {
                    trackSid: publication.trackSid,
                    source: publication.source,
                    isLocal: participant === room.localParticipant
                });
            })
            .on(LiveKit.RoomEvent.LocalTrackUnpublished, (publication, participant) => {
                console.log('❌ Local track unpublished:', publication.kind);
                console.log('❌ Unpublished track details:', {
                    trackSid: publication.trackSid,
                    trackName: publication.trackName,
                    source: publication.source
                });
                
                // If video track is unpublished unexpectedly, try to republish
                if (publication.kind === LiveKit.Track.Kind.Video && videoEnabled) {
                    console.log('🔄 Attempting to republish video track...');
                    setTimeout(async () => {
                        try {
                            await room.localParticipant.setCameraEnabled(true);
                            console.log('✅ Video track republished successfully');
                        } catch (republishError) {
                            console.error('❌ Failed to republish video track:', republishError);
                        }
                    }, 1000);
                }
                
                // If audio track is unpublished unexpectedly, try to republish
                if (publication.kind === LiveKit.Track.Kind.Audio && audioEnabled) {
                    console.log('🔄 Attempting to republish audio track...');
                    setTimeout(async () => {
                        try {
                            await room.localParticipant.setMicrophoneEnabled(true);
                            console.log('✅ Audio track republished successfully');
                        } catch (republishError) {
                            console.error('❌ Failed to republish audio track:', republishError);
                        }
                    }, 1000);
                }
            });

        // Add connection timeout
        const connectionTimeout = setTimeout(() => {
            console.error('Connection timeout after 30 seconds');
            showError('Verbindung dauert zu lange. Bitte überprüfen Sie Ihre Internetverbindung.');
        }, 30000);

        try {
            // Connect to room
            console.log('🔗 Connecting to:', meetingData.livekit_url);
            console.log('🎫 Token preview:', meetingData.token ? meetingData.token.substring(0, 50) + '...' : 'No token');
            console.log('🏠 Room name:', meetingData.room_name || 'Not specified');
            
            await room.connect(meetingData.livekit_url, meetingData.token);
            clearTimeout(connectionTimeout);
            console.log('✅ Connected to room successfully');
            console.log('🏠 Room SID:', room.sid);
            console.log('👤 Local participant SID:', room.localParticipant.sid);
        } catch (connectError) {
            clearTimeout(connectionTimeout);
            console.error('Connection error details:', connectError);
            
            // Provide more specific error messages
            let errorMessage = 'Fehler beim Verbinden zum Meeting';
            if (connectError.message.includes('token')) {
                errorMessage = 'Ungültiger Meeting-Token. Bitte erstellen Sie ein neues Meeting.';
            } else if (connectError.message.includes('network') || connectError.message.includes('timeout')) {
                errorMessage = 'Netzwerkfehler. Bitte überprüfen Sie Ihre Internetverbindung.';
            } else if (connectError.message.includes('permission')) {
                errorMessage = 'Keine Berechtigung für das Meeting. Bitte überprüfen Sie den Meeting-Link.';
            } else {
                errorMessage += ': ' + connectError.message;
            }
            
            throw new Error(errorMessage);
        }

        // Hide loading state
        const loadingElement = document.getElementById('loadingState');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        // Set local participant
        localParticipant = room.localParticipant;
        console.log('Local participant:', localParticipant.identity);

        // Request camera and microphone permissions and enable them
        try {
            console.log('🎥 Requesting camera and microphone permissions...');
            
            // Check if browser supports getUserMedia
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                console.warn('getUserMedia not supported in this browser');
                showError('Ihr Browser unterstützt keine Kamera/Mikrofon-Zugriffe. Bitte verwenden Sie einen modernen Browser.');
                return;
            }
            
            // First, request permissions explicitly
            console.log('🔐 Requesting explicit media permissions...');
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: true, 
                audio: true 
            });
            
            console.log('✅ Media permissions granted');
            console.log('📹 Video tracks:', stream.getVideoTracks().length);
            console.log('🎤 Audio tracks:', stream.getAudioTracks().length);
            
            // Stop the test stream - we'll let LiveKit handle the actual streaming
            stream.getTracks().forEach(track => track.stop());
            
            // Now enable through LiveKit with better error handling
            console.log('🚀 Enabling camera and microphone through LiveKit...');
            
            try {
                // Enable microphone first
                console.log('🎤 Enabling microphone...');
                await room.localParticipant.setMicrophoneEnabled(true);
                audioEnabled = true;
                console.log('✅ Microphone enabled successfully');
                
                // Then enable camera
                console.log('📹 Enabling camera...');
                await room.localParticipant.setCameraEnabled(true);
                videoEnabled = true;
                console.log('✅ Camera enabled successfully');
                
            } catch (enableError) {
                console.error('❌ Error during LiveKit enable:', enableError);
                
                // Try alternative method - publish tracks manually
                console.log('🔄 Trying alternative track publishing method...');
                
                try {
                    const audioTrack = await LiveKit.createLocalAudioTrack();
                    const videoTrack = await LiveKit.createLocalVideoTrack();
                    
                    console.log('📹 Publishing video track...');
                    await room.localParticipant.publishTrack(videoTrack);
                    
                    console.log('🎤 Publishing audio track...');
                    await room.localParticipant.publishTrack(audioTrack);
                    
                    videoEnabled = true;
                    audioEnabled = true;
                    console.log('✅ Tracks published successfully via alternative method');
                    
                } catch (publishError) {
                    console.error('❌ Alternative track publishing failed:', publishError);
                    // Continue without throwing - user can still participate
                }
            }
            
            // Update button states
            updateControlButtons();
            
        } catch (error) {
            console.error('❌ Media permission error:', error);
            
            if (error.name === 'NotAllowedError') {
                showError('Kamera/Mikrofon-Zugriff wurde verweigert. Bitte erlauben Sie den Zugriff und laden Sie die Seite neu.');
            } else if (error.name === 'NotFoundError') {
                showError('Keine Kamera oder Mikrofon gefunden. Bitte überprüfen Sie Ihre Geräte.');
            } else {
                console.warn('Media setup partially failed, but continuing...', error);
                // Don't show error for partial failures - user can still join
            }
        }

        // Update participant count
        updateParticipantCount();

        // Set share link
        const shareUrl = window.location.href;
        const shareLinkInput = document.getElementById('shareLinkInput');
        if (shareLinkInput) {
            shareLinkInput.value = shareUrl;
        }

        console.log('Meeting initialization completed successfully');

    } catch (error) {
        console.error('Error connecting to room:', error);
        showError(error.message || 'Unbekannter Fehler beim Verbinden zum Meeting');
    }
}

function handleTrackSubscribed(track, publication, participant) {
    console.log('📹 Track subscribed:', track.kind, participant.identity);
    console.log('📹 Track details:', {
        trackSid: track.sid,
        enabled: track.enabled,
        muted: track.muted,
        source: track.source
    });
    
    if (track.kind === LiveKit.Track.Kind.Video || track.kind === LiveKit.Track.Kind.Audio) {
        // Get or create participant container
        let container = document.getElementById(`participant-${participant.sid}`);
        if (!container) {
            container = createParticipantContainer(participant);
        }

        // Attach track with better error handling
        if (track.kind === LiveKit.Track.Kind.Video) {
            const videoElement = container.querySelector('video');
            if (videoElement) {
                try {
                    track.attach(videoElement);
                    console.log('✅ Video track attached successfully');
                    
                    // Add event listeners to track video element state
                    videoElement.addEventListener('loadeddata', () => {
                        console.log('📹 Video data loaded');
                    });
                    
                    videoElement.addEventListener('error', (e) => {
                        console.error('❌ Video element error:', e);
                    });
                    
                } catch (attachError) {
                    console.error('❌ Error attaching video track:', attachError);
                }
            }
        } else if (track.kind === LiveKit.Track.Kind.Audio) {
            // Audio tracks are attached to a hidden element
            const audioElement = document.createElement('audio');
            audioElement.autoplay = true;
            try {
                track.attach(audioElement);
                container.appendChild(audioElement);
                console.log('✅ Audio track attached successfully');
            } catch (attachError) {
                console.error('❌ Error attaching audio track:', attachError);
            }
        }
    }
}

function handleTrackUnsubscribed(track, publication, participant) {
    console.log('📹 Track unsubscribed:', track.kind, participant.identity);
    console.log('📹 Unsubscribed track details:', {
        trackSid: track.sid,
        reason: publication?.unsubscribed ? 'unsubscribed' : 'unknown'
    });
    
    try {
        track.detach();
        console.log('✅ Track detached successfully');
    } catch (detachError) {
        console.error('❌ Error detaching track:', detachError);
    }
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

function handleDisconnect(reason) {
    console.log('❌ Disconnect event triggered, reason:', reason);
    console.log('❌ Connection state:', room?.state);
    console.log('❌ Room connected:', room?.state === LiveKit.ConnectionState.Connected);
    console.log('❌ Last error:', room?.lastError);
    
    // Check if we're actually disconnected or if this is a false positive
    if (room && room.state === LiveKit.ConnectionState.Connected) {
        console.log('⚠️ False disconnect detected - room is still connected, ignoring disconnect event');
        return; // Don't handle disconnect if we're still connected
    }
    
    // Check if this is just a reconnection attempt
    if (reason && (reason.includes('reconnect') || reason.includes('temporary'))) {
        console.log('🔄 Temporary disconnect for reconnection, waiting...');
        setTimeout(() => {
            if (room && room.state === LiveKit.ConnectionState.Connected) {
                console.log('✅ Reconnection successful, staying in meeting');
                return;
            }
        }, 3000);
        return;
    }
    
    console.log('❌ Confirmed disconnect - showing user options');
    
    // Don't immediately redirect, give user more information
    showError(`Verbindung zum Meeting wurde getrennt. Grund: ${reason || 'Unbekannt'}`);
    
    // Wait longer before redirect and give user option to retry
    setTimeout(() => {
        if (room && room.state === LiveKit.ConnectionState.Connected) {
            console.log('✅ Connection restored during timeout, canceling redirect');
            // Hide error message
            const loadingState = document.getElementById('loadingState');
            if (loadingState) {
                loadingState.style.display = 'none';
            }
            return;
        }
        
        if (confirm('Möchten Sie zur Startseite zurückkehren oder das Meeting erneut versuchen?')) {
            window.location.href = '/';
        } else {
            location.reload();
        }
    }, 5000);
}

function handleLocalTrackPublished(publication, participant) {
    console.log('📹 Local track published:', publication.kind);
    console.log('📹 Publication details:', {
        trackSid: publication.trackSid,
        trackName: publication.trackName,
        source: publication.source,
        enabled: publication.track?.enabled,
        muted: publication.track?.muted
    });
    
    // Create container for local participant if not exists
    let container = document.getElementById(`participant-${participant.sid}`);
    if (!container) {
        container = createParticipantContainer(participant, true);
        console.log('📹 Created local participant container');
    }

    // Attach local video with better error handling
    if (publication.kind === LiveKit.Track.Kind.Video && publication.track) {
        const videoElement = container.querySelector('video');
        if (videoElement) {
            try {
                publication.track.attach(videoElement);
                console.log('✅ Local video track attached successfully');
                
                // Ensure video is playing
                videoElement.play().catch(playError => {
                    console.warn('Auto-play prevented, but this is normal:', playError);
                });
                
            } catch (attachError) {
                console.error('❌ Error attaching local video track:', attachError);
            }
        } else {
            console.error('❌ Video element not found in local container');
        }
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

// Make initializeMeeting globally available
window.initializeMeeting = initializeMeeting;

// DOM ready check and initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, setting up event listeners and initializing meeting...');
        setupEventListeners();
        initializeMeeting();
    });
} else {
    // DOM already loaded
    console.log('DOM already loaded, setting up event listeners and initializing meeting...');
    setupEventListeners();
    initializeMeeting();
} 