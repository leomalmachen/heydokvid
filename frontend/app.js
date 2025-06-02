// Global variables
let room;
let localParticipant;
let audioEnabled = true;
let videoEnabled = true;
const participants = new Map();
let isTabVisible = true;
let visibilityCheckInterval;

// Get meeting ID from URL
const pathParts = window.location.pathname.split('/');
const meetingId = pathParts[pathParts.length - 1];

// Handle page visibility changes to keep connection alive
function handleVisibilityChange() {
    if (document.hidden) {
        console.log('📴 Tab hidden - implementing keep-alive strategies');
        isTabVisible = false;
        
        // Start keep-alive ping
        if (room && room.state === LiveKit.ConnectionState.Connected) {
            startKeepAlive();
        }
        
        // Prevent media stream pause
        preventMediaPause();
        
    } else {
        console.log('👁️ Tab visible - resuming normal operation');
        isTabVisible = true;
        
        // Stop keep-alive ping
        stopKeepAlive();
        
        // Ensure media streams are active
        resumeMediaStreams();
        
        // Check connection state and reconnect if needed
        if (room && room.state !== LiveKit.ConnectionState.Connected) {
            console.log('🔄 Tab refocused - checking connection status');
            setTimeout(checkAndReconnect, 1000);
        }
    }
}

function startKeepAlive() {
    if (visibilityCheckInterval) return;
    
    console.log('💓 Starting keep-alive ping');
    visibilityCheckInterval = setInterval(() => {
        if (room && room.state === LiveKit.ConnectionState.Connected) {
            // Send a small data message to keep connection active
            try {
                room.localParticipant.publishData(
                    new TextEncoder().encode('ping'), 
                    LiveKit.DataPacket_Kind.RELIABLE
                );
            } catch (error) {
                console.warn('Keep-alive ping failed:', error);
            }
        }
    }, 10000); // Every 10 seconds
}

function stopKeepAlive() {
    if (visibilityCheckInterval) {
        console.log('💓 Stopping keep-alive ping');
        clearInterval(visibilityCheckInterval);
        visibilityCheckInterval = null;
    }
}

function preventMediaPause() {
    console.log('🔒 Preventing media stream pause during tab hide');
    
    // Keep video tracks active by setting a small constraint
    if (room && room.localParticipant) {
        const videoTrack = room.localParticipant.getTrack(LiveKit.Track.Source.Camera);
        if (videoTrack && videoTrack.track) {
            try {
                // Ensure track remains active
                videoTrack.track.enabled = true;
                console.log('✅ Video track kept active');
            } catch (error) {
                console.warn('Could not maintain video track:', error);
            }
        }
        
        const audioTrack = room.localParticipant.getTrack(LiveKit.Track.Source.Microphone);
        if (audioTrack && audioTrack.track) {
            try {
                // Ensure track remains active
                audioTrack.track.enabled = audioEnabled;
                console.log('✅ Audio track kept active');
            } catch (error) {
                console.warn('Could not maintain audio track:', error);
            }
        }
    }
}

function resumeMediaStreams() {
    console.log('▶️ Resuming media streams after tab focus');
    
    if (room && room.localParticipant) {
        // Re-enable video if it was enabled
        if (videoEnabled) {
            setTimeout(async () => {
                try {
                    const videoTrack = room.localParticipant.getTrack(LiveKit.Track.Source.Camera);
                    if (!videoTrack || !videoTrack.track || !videoTrack.track.enabled) {
                        console.log('🔄 Re-enabling video after tab focus');
                        await room.localParticipant.setCameraEnabled(true);
                    }
                } catch (error) {
                    console.warn('Could not resume video:', error);
                }
            }, 500);
        }
        
        // Re-enable audio if it was enabled
        if (audioEnabled) {
            setTimeout(async () => {
                try {
                    const audioTrack = room.localParticipant.getTrack(LiveKit.Track.Source.Microphone);
                    if (!audioTrack || !audioTrack.track || !audioTrack.track.enabled) {
                        console.log('🔄 Re-enabling audio after tab focus');
                        await room.localParticipant.setMicrophoneEnabled(true);
                    }
                } catch (error) {
                    console.warn('Could not resume audio:', error);
                }
            }, 500);
        }
    }
}

async function checkAndReconnect() {
    if (!room || room.state === LiveKit.ConnectionState.Connected) {
        return;
    }
    
    console.log('🔄 Connection lost during tab switch, attempting reconnect...');
    
    try {
        // Get fresh meeting data
        const meetingData = sessionStorage.getItem('meetingData');
        if (meetingData) {
            const data = JSON.parse(meetingData);
            await room.connect(data.livekit_url, data.token);
            console.log('✅ Reconnected successfully after tab switch');
        }
    } catch (error) {
        console.error('❌ Reconnection failed:', error);
        // Try to reload the page as last resort
        setTimeout(() => {
            if (confirm('Verbindung verloren. Seite neu laden?')) {
                location.reload();
            }
        }, 2000);
    }
}

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
        
        // Create room instance with STABLE settings (reduced quality for better connection)
        room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true,
            // STABLE: Lower quality for better connection stability
            audioCaptureDefaults: {
                autoGainControl: true,
                echoCancellation: true,
                noiseSuppression: true,
            },
            videoCaptureDefaults: {
                resolution: LiveKit.VideoPresets.h720.resolution, // Back to 720p for stability
                frameRate: 30,
            },
            publishDefaults: {
                // STABLE: Reduced quality for better connection
                videoSimulcastLayers: [
                    LiveKit.VideoPresets.h180,
                    LiveKit.VideoPresets.h360, 
                    LiveKit.VideoPresets.h720, // Max 720p
                ],
                stopMicTrackOnMute: false,
                videoCodec: 'vp8', // VP8 is more stable than H264
                // STABLE: Lower bitrate for connection stability
                videoEncoding: {
                    maxBitrate: 1000000, // 1 Mbps (reduced from 2.5)
                    maxFramerate: 30,
                },
                audioEncoding: {
                    maxBitrate: 64000, // Reduced audio bitrate
                },
            },
            // Reconnection settings
            reconnectPolicy: {
                nextRetryDelayInMs: (context) => {
                    console.log(`Reconnect attempt ${context.retryCount}`);
                    return Math.min(1000 * Math.pow(2, context.retryCount), 30000);
                },
                maxRetryCount: 10,
            }
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

        // Request camera and microphone permissions and enable them with rock-solid stability
        try {
            console.log('🎥 Starting STABLE media setup process...');
            
            // Check if browser supports getUserMedia
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                console.warn('getUserMedia not supported in this browser');
                showError('Ihr Browser unterstützt keine Kamera/Mikrofon-Zugriffe. Bitte verwenden Sie einen modernen Browser.');
                return;
            }
            
            // Step 1: Get explicit permissions first (STABLE settings)
            console.log('🔐 Step 1: Requesting stable browser permissions...');
            const permissionStream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 1280, min: 640 }, // Reduced for stability
                    height: { ideal: 720, min: 480 },
                    frameRate: { ideal: 30, max: 30 },
                    facingMode: 'user'
                }, 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            console.log('✅ Browser permissions granted successfully');
            console.log('📹 Video tracks available:', permissionStream.getVideoTracks().length);
            console.log('🎤 Audio tracks available:', permissionStream.getAudioTracks().length);
            
            // Step 2: Stop permission stream immediately (let LiveKit handle actual streaming)
            permissionStream.getTracks().forEach(track => {
                track.stop();
                console.log('🛑 Permission track stopped:', track.kind);
            });
            
            // Step 3: Wait a moment for cleanup
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Step 4: Enable through LiveKit with bulletproof error handling
            console.log('🚀 Step 2: Enabling tracks through LiveKit...');
            
            // Enable audio first (usually more stable)
            console.log('🎤 Enabling microphone...');
            try {
                await room.localParticipant.setMicrophoneEnabled(true);
                audioEnabled = true;
                console.log('✅ Microphone enabled and published successfully');
                
                // Verify audio track was actually published
                await new Promise(resolve => setTimeout(resolve, 1000));
                const audioTrack = room.localParticipant.getTrack(LiveKit.Track.Source.Microphone);
                if (audioTrack && audioTrack.track) {
                    console.log('✅ Audio track verification passed');
                } else {
                    console.warn('⚠️ Audio track verification failed, retrying...');
                    throw new Error('Audio track not properly published');
                }
                
            } catch (audioError) {
                console.error('❌ Microphone enable failed:', audioError);
                audioEnabled = false;
            }
            
            // Enable video second
            console.log('📹 Enabling camera...');
            try {
                await room.localParticipant.setCameraEnabled(true);
                videoEnabled = true;
                console.log('✅ Camera enabled and published successfully');
                
                // Verify video track was actually published
                await new Promise(resolve => setTimeout(resolve, 1000));
                const videoTrack = room.localParticipant.getTrack(LiveKit.Track.Source.Camera);
                if (videoTrack && videoTrack.track) {
                    console.log('✅ Video track verification passed');
                    
                    // Ensure local video is immediately visible
                    setTimeout(() => {
                        const localContainer = document.getElementById(`participant-${room.localParticipant.sid}`);
                        if (localContainer) {
                            const videoElement = localContainer.querySelector('video');
                            if (videoElement && videoTrack.track) {
                                try {
                                    videoTrack.track.attach(videoElement);
                                    videoElement.play().catch(e => console.warn('Local video autoplay prevented:', e));
                                    console.log('✅ Local video immediately attached');
                                } catch (e) {
                                    console.warn('Local video immediate attachment failed:', e);
                                }
                            }
                        }
                    }, 500);
                    
                } else {
                    console.warn('⚠️ Video track verification failed, retrying...');
                    throw new Error('Video track not properly published');
                }
                
            } catch (videoError) {
                console.error('❌ Camera enable failed:', videoError);
                videoEnabled = false;
            }
            
            // Step 5: If standard method failed, try alternative robust publishing
            if (!audioEnabled || !videoEnabled) {
                console.log('🔄 Standard method partially failed, trying robust alternative...');
                
                try {
                    if (!audioEnabled) {
                        console.log('🎤 Creating robust audio track...');
                        const audioTrack = await LiveKit.createLocalAudioTrack({
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        });
                        
                        console.log('📤 Publishing robust audio track...');
                        await room.localParticipant.publishTrack(audioTrack, {
                            name: 'microphone',
                            source: LiveKit.Track.Source.Microphone
                        });
                        
                        audioEnabled = true;
                        console.log('✅ Robust audio track published successfully');
                    }
                    
                    if (!videoEnabled) {
                        console.log('📹 Creating stable video track...');
                        const videoTrack = await LiveKit.createLocalVideoTrack({
                            resolution: LiveKit.VideoPresets.h720.resolution, // Stable quality
                            frameRate: 30,
                            facingMode: 'user'
                        });
                        
                        console.log('📤 Publishing stable video track...');
                        await room.localParticipant.publishTrack(videoTrack, {
                            name: 'camera',
                            source: LiveKit.Track.Source.Camera
                        });
                        
                        videoEnabled = true;
                        console.log('✅ Stable video track published successfully');
                    }
                    
                } catch (robustError) {
                    console.error('❌ Robust publishing also failed:', robustError);
                }
            }
            
            // Step 6: Final verification and UI update
            console.log('🔍 Final track verification...');
            console.log('📊 Final state - Audio:', audioEnabled, 'Video:', videoEnabled);
            
            // Update button states
            updateControlButtons();
            
            // Force update participant display
            setTimeout(() => {
                updateParticipantDisplay();
            }, 1000);
            
            console.log('🎉 Media setup completed successfully!');
            
        } catch (error) {
            console.error('❌ CRITICAL: Media setup completely failed:', error);
            
            if (error.name === 'NotAllowedError') {
                showError('Kamera/Mikrofon-Zugriff wurde verweigert. Bitte erlauben Sie den Zugriff und laden Sie die Seite neu.');
            } else if (error.name === 'NotFoundError') {
                showError('Keine Kamera oder Mikrofon gefunden. Bitte überprüfen Sie Ihre Geräte.');
            } else {
                console.warn('Continuing without full media setup...', error);
                // Don't show error - allow participation without media
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
    console.log('📹 TRACK SUBSCRIBED:', track.kind, 'from', participant.identity);
    console.log('📹 Track details:', {
        trackSid: track.sid,
        enabled: track.enabled,
        muted: track.muted,
        source: track.source,
        participant: participant.identity
    });
    
    if (track.kind === LiveKit.Track.Kind.Video || track.kind === LiveKit.Track.Kind.Audio) {
        // FIXED: Conservative approach - no more aggressive retries
        let container = document.getElementById(`participant-${participant.sid}`);
        if (!container) {
            console.log('📦 Creating participant container for:', participant.identity);
            container = createParticipantContainer(participant, false);
            
            // Single retry with reasonable delay
            setTimeout(() => {
                const verifyContainer = document.getElementById(`participant-${participant.sid}`);
                if (verifyContainer) {
                    attachTrackToContainer(track, publication, participant, verifyContainer);
                } else {
                    console.error('❌ Container creation failed for:', participant.identity);
                }
            }, 300);
        } else {
            console.log('📦 Using existing container for:', participant.identity);
            // Ensure container is properly visible before attaching
            container.style.display = 'block';
            attachTrackToContainer(track, publication, participant, container);
        }
    }
}

function attachTrackToContainer(track, publication, participant, container) {
    console.log('🔗 ATTACHING TRACK:', track.kind, 'to container for', participant.identity);
    
    try {
        if (track.kind === LiveKit.Track.Kind.Video) {
            const videoElement = container.querySelector('video');
            if (!videoElement) {
                console.error('❌ No video element found in container for:', participant.identity);
                return;
            }
            
            console.log('📹 Attaching video track...');
            
            // Enhanced: Better cleanup of existing tracks
            if (videoElement.srcObject) {
                const existingTracks = videoElement.srcObject.getTracks();
                existingTracks.forEach(existingTrack => {
                    existingTrack.stop();
                    console.log('🛑 Stopped existing track:', existingTrack.kind);
                });
                videoElement.srcObject = null;
            }
            
            // Enhanced: More robust track attachment
            try {
                track.attach(videoElement);
                console.log('✅ Video track attached to element');
            } catch (attachError) {
                console.warn('❌ Direct attach failed, trying alternative method:', attachError);
                // Alternative attachment method
                const stream = new MediaStream([track]);
                videoElement.srcObject = stream;
            }
            
            // Enhanced: Better video loading handling
            const handleVideoLoad = () => {
                console.log('📹 Video data loaded for:', participant.identity);
                // Ensure container becomes visible
                container.style.opacity = '1';
                container.style.visibility = 'visible';
                
                // Hide loading indicator
                const loadingIndicator = container.querySelector('.loading-indicator');
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                // Attempt to play
                videoElement.play().catch(playError => {
                    console.warn('Video autoplay prevented for:', participant.identity, playError);
                    // Create a user-interaction based play button
                    if (!container.querySelector('.play-button')) {
                        const playButton = document.createElement('button');
                        playButton.className = 'play-button';
                        playButton.innerHTML = '▶️ Play';
                        playButton.style.position = 'absolute';
                        playButton.style.top = '50%';
                        playButton.style.left = '50%';
                        playButton.style.transform = 'translate(-50%, -50%)';
                        playButton.style.zIndex = '10';
                        playButton.onclick = () => {
                            videoElement.play().then(() => {
                                playButton.remove();
                            }).catch(e => console.warn('Manual play failed:', e));
                        };
                        container.appendChild(playButton);
                    }
                });
            };
            
            // Enhanced: Multiple event handlers for reliability
            videoElement.addEventListener('loadeddata', handleVideoLoad, { once: true });
            videoElement.addEventListener('canplay', handleVideoLoad, { once: true });
            
            // Enhanced: Better error handling
            videoElement.onerror = (error) => {
                console.error('❌ Video element error for:', participant.identity, error);
                
                // Show error state in container
                const errorDiv = document.createElement('div');
                errorDiv.innerHTML = '❌ Video Error';
                errorDiv.style.position = 'absolute';
                errorDiv.style.top = '50%';
                errorDiv.style.left = '50%';
                errorDiv.style.transform = 'translate(-50%, -50%)';
                errorDiv.style.color = '#ea4335';
                container.appendChild(errorDiv);
                
                // Retry attachment after error
                setTimeout(() => {
                    try {
                        console.log('🔄 Retrying video attachment after error');
                        errorDiv.remove();
                        track.attach(videoElement);
                    } catch (reattachError) {
                        console.error('❌ Video reattach failed:', reattachError);
                    }
                }, 3000);
            };
            
            console.log('✅ Video track setup completed for:', participant.identity);
            
        } else if (track.kind === LiveKit.Track.Kind.Audio) {
            console.log('🎤 Attaching audio track...');
            
            // Enhanced: Better audio element management
            const existingAudio = container.querySelectorAll('audio');
            existingAudio.forEach(audio => {
                if (audio.srcObject) {
                    audio.srcObject.getTracks().forEach(track => track.stop());
                }
                audio.remove();
            });
            
            // Create new audio element with better configuration
            const audioElement = document.createElement('audio');
            audioElement.autoplay = true;
            audioElement.playsInline = true;
            audioElement.controls = false;
            audioElement.volume = 1.0;
            
            // Enhanced: Robust audio attachment
            try {
                track.attach(audioElement);
                console.log('✅ Audio track attached to element');
            } catch (attachError) {
                console.warn('❌ Direct audio attach failed, trying alternative:', attachError);
                const stream = new MediaStream([track]);
                audioElement.srcObject = stream;
            }
            
            container.appendChild(audioElement);
            
            // Enhanced: Audio loading handling
            audioElement.addEventListener('loadeddata', () => {
                console.log('🎤 Audio data loaded for:', participant.identity);
                audioElement.play().catch(playError => {
                    console.warn('Audio autoplay prevented for:', participant.identity, playError);
                    // Most browsers allow audio after user interaction
                    document.addEventListener('click', () => {
                        audioElement.play().catch(e => console.warn('Manual audio play failed:', e));
                    }, { once: true });
                });
            }, { once: true });
            
            console.log('✅ Audio track setup completed for:', participant.identity);
        }
        
    } catch (attachError) {
        console.error('❌ CRITICAL: Track attachment failed for:', participant.identity, attachError);
        
        // Show error state in container
        const errorState = document.createElement('div');
        errorState.innerHTML = `
            <div style="text-align: center; color: #ea4335; padding: 1rem;">
                ❌ Connection Error<br>
                <small>Retrying...</small>
            </div>
        `;
        errorState.style.position = 'absolute';
        errorState.style.top = '50%';
        errorState.style.left = '50%';
        errorState.style.transform = 'translate(-50%, -50%)';
        container.appendChild(errorState);
        
        // Enhanced: Exponential backoff retry
        let retryCount = 0;
        const maxRetries = 3;
        
        const retryAttachment = () => {
            retryCount++;
            const delay = Math.min(1000 * Math.pow(2, retryCount), 10000); // Max 10s delay
            
            setTimeout(() => {
                console.log(`🔄 Retry ${retryCount}/${maxRetries} for track attachment:`, participant.identity);
                
                try {
                    errorState.remove();
                    attachTrackToContainer(track, publication, participant, container);
                } catch (retryError) {
                    console.error(`❌ Retry ${retryCount} failed:`, retryError);
                    if (retryCount < maxRetries) {
                        retryAttachment();
                    } else {
                        console.error('❌ All retries exhausted for:', participant.identity);
                        errorState.innerHTML = `
                            <div style="text-align: center; color: #ea4335; padding: 1rem;">
                                ❌ Connection Failed<br>
                                <small>Unable to display video</small>
                            </div>
                        `;
                    }
                }
            }, delay);
        };
        
        retryAttachment();
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
    console.log('👥 PARTICIPANT CONNECTED:', participant.identity);
    console.log('👥 Participant details:', {
        sid: participant.sid,
        identity: participant.identity,
        name: participant.name,
        metadata: participant.metadata
    });
    
    // CRITICAL: Prevent duplicate processing
    if (participants.has(participant.sid)) {
        console.warn('⚠️ Participant already exists, skipping duplicate:', participant.identity);
        return; // STOP processing duplicates immediately
    }
    
    participants.set(participant.sid, participant);
    
    // CRITICAL: Remove any existing container before creating new one
    let container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        console.log('🗑️ Removing existing container for participant:', participant.identity);
        container.remove();
    }
    
    console.log('📦 Creating fresh container for new participant:', participant.identity);
    container = createParticipantContainer(participant, false);
    
    // Wait for container to be properly inserted before processing tracks
    setTimeout(() => {
        // Verify container is in DOM
        const verifyContainer = document.getElementById(`participant-${participant.sid}`);
        if (!verifyContainer) {
            console.error('❌ Container creation failed for:', participant.identity);
            return;
        }
        
        updateParticipantCount();
        updateParticipantDisplay();
        
        // Process existing tracks with simple approach
        console.log('📹 Processing existing tracks for:', participant.identity);
        participant.tracks.forEach((trackPublication) => {
            if (trackPublication.track && trackPublication.isSubscribed) {
                console.log('📹 Subscribing to existing track:', trackPublication.kind, 'from', participant.identity);
                setTimeout(() => {
                    handleTrackSubscribed(trackPublication.track, trackPublication, participant);
                }, 200); // Small delay to prevent race conditions
            }
        });
        
    }, 300);
}

function handleParticipantDisconnected(participant) {
    console.log('👥 PARTICIPANT DISCONNECTED:', participant.identity);
    
    // Enhanced: Better cleanup and state management
    participants.delete(participant.sid);
    
    // Enhanced: Comprehensive container cleanup
    const container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        console.log('🗑️ Starting comprehensive cleanup for:', participant.identity);
        
        // Stop all media elements with proper error handling
        const mediaElements = container.querySelectorAll('video, audio');
        mediaElements.forEach(element => {
            try {
                if (element.srcObject) {
                    const tracks = element.srcObject.getTracks();
                    tracks.forEach(track => {
                        track.stop();
                        console.log('🛑 Stopped track:', track.kind, 'for', participant.identity);
                    });
                    element.srcObject = null;
                }
                
                // Clear all event listeners
                element.onloadeddata = null;
                element.onerror = null;
                element.oncanplay = null;
                
                element.remove();
            } catch (cleanupError) {
                console.warn('⚠️ Error cleaning up media element:', cleanupError);
            }
        });
        
        // Remove any loading indicators or error states
        const loadingElements = container.querySelectorAll('.loading-indicator, .play-button, .error-state');
        loadingElements.forEach(el => el.remove());
        
        // Remove container with fade out
        container.style.transition = 'opacity 0.3s ease';
        container.style.opacity = '0';
        
        setTimeout(() => {
            if (container.parentNode) {
                container.remove();
                console.log('✅ Container fully removed for:', participant.identity);
                
                // Update layout after removal
                updateParticipantCount();
                updateParticipantDisplay();
            }
        }, 300);
        
    } else {
        console.log('🔍 No container found for disconnected participant:', participant.identity);
    }
    
    // Enhanced: Force layout recalculation
    setTimeout(() => {
        const videoGrid = document.getElementById('videoGrid');
        if (videoGrid) {
            // Trigger CSS reflow to fix grid layout
            videoGrid.style.display = 'none';
            videoGrid.offsetHeight; // Force reflow
            videoGrid.style.display = 'grid';
        }
    }, 500);
}

function handleDisconnect(reason) {
    console.log('❌ Disconnect event triggered, reason:', reason);
    console.log('❌ Connection state:', room?.state);
    
    // CRITICAL: Be much more conservative about reconnection
    const isExpectedDisconnect = reason === 'user_left' || reason === 'manual' || 
                                reason === 'CLIENT_INITIATED' || reason === 'disconnect';
    
    if (isExpectedDisconnect) {
        console.log('👋 Expected disconnect - cleaning up gracefully');
        performGracefulCleanup();
        return;
    }
    
    // CONSERVATIVE: Only reconnect for very specific cases
    if (room && (room.state === LiveKit.ConnectionState.Connected || 
                 room.state === LiveKit.ConnectionState.Connecting)) {
        console.log('⚠️ Room still connected/connecting - ignoring disconnect event');
        return;
    }
    
    console.log('❌ Handling unexpected disconnect - but being conservative');
    
    // DON'T auto-reconnect - let user decide
    showFinalDisconnectUI();
}

// DISABLED: Remove aggressive reconnection
function attemptReconnection(attempt) {
    console.log('🚫 Auto-reconnection disabled to prevent loops');
    showFinalDisconnectUI();
}

// Enhanced: Show final disconnect UI when all reconnection attempts failed
function showFinalDisconnectUI() {
    const finalUI = document.createElement('div');
    finalUI.innerHTML = `
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        ">
            <div style="
                background: #303134;
                padding: 2rem;
                border-radius: 8px;
                text-align: center;
                max-width: 500px;
                width: 90%;
                border: 1px solid #ea4335;
            ">
                <div style="font-size: 48px; margin-bottom: 1rem;">❌</div>
                <h3 style="margin-bottom: 1rem; color: #e8eaed;">Verbindung verloren</h3>
                <p style="color: #9aa0a6; margin-bottom: 2rem;">
                    Die Verbindung zum Meeting konnte nicht wiederhergestellt werden. 
                    Dies kann an Netzwerkproblemen oder Serverfehlern liegen.
                </p>
                <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                    <button onclick="location.reload()" style="
                        background: #1a73e8;
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 1rem;
                    ">Erneut versuchen</button>
                    <button onclick="window.location.href='/'" style="
                        background: #5f6368;
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 1rem;
                    ">Zur Startseite</button>
                </div>
            </div>
        </div>
    `;
    
    // Replace reconnection UI with final UI
    const reconnectionUI = document.getElementById('reconnectionUI');
    if (reconnectionUI) {
        reconnectionUI.remove();
    }
    
    document.body.appendChild(finalUI);
}

// Enhanced: Graceful cleanup for expected disconnects
function performGracefulCleanup() {
    console.log('🧹 Performing graceful cleanup...');
    
    // Stop all media tracks
    if (room && room.localParticipant) {
        room.localParticipant.tracks.forEach((publication) => {
            if (publication.track) {
                publication.track.stop();
                console.log('🛑 Stopped local track:', publication.kind);
            }
        });
    }
    
    // Clean up all participant containers
    const containers = document.querySelectorAll('.participant-container');
    containers.forEach(container => {
        const mediaElements = container.querySelectorAll('video, audio');
        mediaElements.forEach(element => {
            if (element.srcObject) {
                element.srcObject.getTracks().forEach(track => track.stop());
                element.srcObject = null;
            }
        });
    });
    
    // Show disconnect message
    const videoGrid = document.getElementById('videoGrid');
    if (videoGrid) {
        videoGrid.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #9aa0a6;
                text-align: center;
            ">
                <div style="font-size: 48px; margin-bottom: 1rem;">👋</div>
                <h3 style="margin-bottom: 1rem;">Meeting beendet</h3>
                <p>Sie haben das Meeting verlassen.</p>
                <button onclick="window.location.href='/'" style="
                    background: #1a73e8;
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 1rem;
                ">Zur Startseite</button>
            </div>
        `;
    }
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
    console.log('📦 CREATING CONTAINER for:', participant.identity, '(local:', isLocal, ')');
    
    // CRITICAL: Absolutely prevent duplicates
    const existingContainer = document.getElementById(`participant-${participant.sid}`);
    if (existingContainer) {
        console.log('⚠️ DUPLICATE PREVENTION: Container already exists for:', participant.identity);
        return existingContainer; // Return existing instead of creating new
    }
    
    const container = document.createElement('div');
    container.className = 'participant-container';
    container.id = `participant-${participant.sid}`;
    
    // Better initial state management
    container.style.opacity = '0';
    container.style.visibility = 'hidden';
    container.style.transition = 'opacity 0.3s ease, visibility 0.3s ease';
    container.style.display = 'block';
    
    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    video.muted = isLocal; // Mute local video to prevent echo
    video.style.width = '100%';
    video.style.height = '100%';
    video.style.objectFit = 'cover';
    video.style.backgroundColor = '#202124';
    
    // Loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = `
        <div style="text-align: center;">
            <div style="
                width: 32px;
                height: 32px;
                border: 3px solid #5f6368;
                border-top-color: #8ab4f8;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 0.5rem;
            "></div>
            🔄 Verbinde...
        </div>
    `;
    
    // Name label with proper participant identification
    const nameLabel = document.createElement('div');
    nameLabel.className = 'participant-name';
    let displayName = participant.identity || participant.name || 'Teilnehmer';
    
    if (isLocal) {
        displayName += ' (Du)';
        nameLabel.style.background = 'rgba(26, 115, 232, 0.8)'; // Blue for local user
    } else {
        nameLabel.style.background = 'rgba(0, 0, 0, 0.7)'; // Dark for remote users
    }
    
    nameLabel.textContent = displayName;
    
    // Connection quality indicator
    const connectionQuality = document.createElement('div');
    connectionQuality.className = 'connection-quality excellent';
    connectionQuality.title = 'Connection Quality: Excellent';
    connectionQuality.style.borderRadius = '50%';
    
    // Assemble container
    container.appendChild(video);
    container.appendChild(loadingIndicator);
    container.appendChild(nameLabel);
    container.appendChild(connectionQuality);
    
    const videoGrid = document.getElementById('videoGrid');
    if (videoGrid) {
        videoGrid.appendChild(container);
        console.log('✅ Container added to video grid for:', participant.identity);
        
        // Force layout recalculation
        setTimeout(() => {
            optimizeVideoGrid();
        }, 100);
    } else {
        console.error('❌ Video grid not found!');
        return null;
    }
    
    // Video ready handler
    const handleVideoReady = () => {
        console.log('📹 Video ready for:', participant.identity);
        loadingIndicator.style.display = 'none';
        container.style.opacity = '1';
        container.style.visibility = 'visible';
        container.classList.add('loaded');
        
        if (video.videoWidth > 0 && video.videoHeight > 0) {
            connectionQuality.className = 'connection-quality excellent';
            connectionQuality.title = 'Connection Quality: Excellent';
        }
    };
    
    // Multiple event listeners for maximum compatibility
    video.addEventListener('loadeddata', handleVideoReady, { once: true });
    video.addEventListener('canplay', handleVideoReady, { once: true });
    video.addEventListener('playing', handleVideoReady, { once: true });
    
    // Fallback visibility timer - but more conservative
    setTimeout(() => {
        if (container.style.opacity === '0') {
            console.log('⏰ Fallback visibility timeout for:', participant.identity);
            
            const hasVideo = video.srcObject && video.srcObject.getVideoTracks().length > 0;
            const hasAudio = container.querySelector('audio')?.srcObject?.getAudioTracks().length > 0;
            
            if (hasVideo || hasAudio || isLocal) {
                handleVideoReady();
            } else {
                // Show placeholder for participants without tracks
                loadingIndicator.innerHTML = `
                    <div style="text-align: center; color: #9aa0a6;">
                        📷 Warten auf Video...
                    </div>
                `;
                container.style.opacity = '1';
                container.style.visibility = 'visible';
            }
        }
    }, 5000); // Increased to 5 seconds
    
    // Handle video errors gracefully
    video.addEventListener('error', (error) => {
        console.error('❌ Video error for:', participant.identity, error);
        loadingIndicator.innerHTML = `
            <div style="text-align: center; color: #ea4335;">
                ❌ Video Error<br>
                <small>Retrying...</small>
            </div>
        `;
        container.style.opacity = '1';
        container.style.visibility = 'visible';
    });
    
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

function updateParticipantDisplay() {
    console.log('🔄 UPDATING PARTICIPANT DISPLAY');
    
    if (!room) {
        console.warn('Room not available for participant display update');
        return;
    }
    
    console.log('👥 Current participants:');
    console.log('- Local:', room.localParticipant.identity);
    
    // Enhanced: Track which containers should exist
    const expectedContainers = new Set();
    expectedContainers.add(`participant-${room.localParticipant.sid}`);
    
    // Enhanced: Process remote participants with better error handling
    room.participants.forEach((participant, sid) => {
        console.log(`- Remote: ${participant.identity} (${sid})`);
        expectedContainers.add(`participant-${sid}`);
        
        // Ensure container exists with validation
        let container = document.getElementById(`participant-${sid}`);
        if (!container) {
            console.log('📦 Creating missing container for:', participant.identity);
            container = createParticipantContainer(participant, false);
        } else {
            // Validate container is properly configured
            const videoElement = container.querySelector('video');
            if (!videoElement) {
                console.warn('⚠️ Container missing video element, recreating:', participant.identity);
                container.remove();
                container = createParticipantContainer(participant, false);
            }
        }
        
        // Enhanced: Re-attach tracks with validation
        participant.tracks.forEach((trackPublication) => {
            if (trackPublication.track && trackPublication.isSubscribed) {
                console.log('🔄 Validating track attachment:', trackPublication.kind, 'for', participant.identity);
                
                // Check if track is actually attached
                const isAttached = checkTrackAttachment(trackPublication.track, container);
                if (!isAttached) {
                    console.log('🔄 Re-attaching track:', trackPublication.kind, 'for', participant.identity);
                    attachTrackToContainer(trackPublication.track, trackPublication, participant, container);
                }
            }
        });
    });
    
    // Enhanced: Clean up orphaned containers
    const allContainers = document.querySelectorAll('.participant-container');
    allContainers.forEach(container => {
        if (!expectedContainers.has(container.id)) {
            console.log('🗑️ Removing orphaned container:', container.id);
            container.remove();
        }
    });
    
    // Enhanced: Ensure local participant container exists and is configured
    if (room.localParticipant) {
        let localContainer = document.getElementById(`participant-${room.localParticipant.sid}`);
        if (!localContainer) {
            console.log('📦 Creating missing local container');
            localContainer = createParticipantContainer(room.localParticipant, true);
            
            // Attach local tracks if they exist
            room.localParticipant.tracks.forEach((trackPublication) => {
                if (trackPublication.track) {
                    console.log('🔄 Attaching local track:', trackPublication.kind);
                    attachTrackToContainer(trackPublication.track, trackPublication, room.localParticipant, localContainer);
                }
            });
        }
    }
    
    updateParticipantCount();
    
    // Enhanced: Trigger grid layout optimization
    setTimeout(() => {
        optimizeVideoGrid();
    }, 100);
    
    console.log('✅ Participant display update completed');
}

// Enhanced: Helper function to check if track is properly attached
function checkTrackAttachment(track, container) {
    if (track.kind === LiveKit.Track.Kind.Video) {
        const videoElement = container.querySelector('video');
        if (!videoElement || !videoElement.srcObject) {
            return false;
        }
        
        const tracks = videoElement.srcObject.getTracks();
        return tracks.some(t => t.id === track.id);
    } else if (track.kind === LiveKit.Track.Kind.Audio) {
        const audioElement = container.querySelector('audio');
        if (!audioElement || !audioElement.srcObject) {
            return false;
        }
        
        const tracks = audioElement.srcObject.getTracks();
        return tracks.some(t => t.id === track.id);
    }
    
    return false;
}

// SIMPLE: Optimize video grid layout with CLASS-BASED approach (works in ALL browsers)
function optimizeVideoGrid() {
    const videoGrid = document.getElementById('videoGrid');
    const containers = document.querySelectorAll('.participant-container');
    
    if (!videoGrid || containers.length === 0) return;
    
    const participantCount = containers.length;
    console.log('📐 Setting SIMPLE grid layout for', participantCount, 'participants');
    
    // REMOVE all existing classes
    videoGrid.className = '';
    
    // ADD appropriate class based on participant count
    if (participantCount === 1) {
        videoGrid.classList.add('single-participant');
        console.log('✅ Applied: single-participant layout');
    } else if (participantCount === 2) {
        videoGrid.classList.add('two-participants');
        console.log('✅ Applied: two-participants layout (side-by-side)');
    } else if (participantCount <= 4) {
        videoGrid.classList.add('multiple-participants');
        console.log('✅ Applied: multiple-participants layout');
    } else {
        videoGrid.classList.add('many-participants');
        console.log('✅ Applied: many-participants layout');
    }
    
    // ENSURE all containers are properly visible
    containers.forEach((container, index) => {
        container.style.opacity = '1';
        container.style.visibility = 'visible';
        
        // Ensure videos fill the container properly
        const video = container.querySelector('video');
        if (video) {
            video.style.width = '100%';
            video.style.height = '100%';
            video.style.objectFit = 'cover';
        }
    });
    
    console.log('✅ SIMPLE grid layout applied successfully');
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
                    // Cleanup before disconnect
                    stopKeepAlive();
                    
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
    
    // Setup page visibility handling to keep connection alive
    console.log('🔧 Setting up page visibility handling');
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Handle beforeunload to maintain connection
    window.addEventListener('beforeunload', (event) => {
        console.log('⚠️ Page unloading - maintaining connection');
        // Don't disconnect immediately, let the user come back
        event.preventDefault();
        return 'Meeting ist noch aktiv. Wirklich verlassen?';
    });
    
    // Handle page focus/blur for additional stability  
    window.addEventListener('focus', () => {
        console.log('👁️ Window focused');
        if (!isTabVisible) {
            handleVisibilityChange(); // Force check
        }
    });
    
    window.addEventListener('blur', () => {
        console.log('👁️ Window blurred');
        // Don't immediately react, let visibilitychange handle it
    });
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