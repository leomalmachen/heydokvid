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
        
        // Create room instance with better error handling and background optimization
        room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true,
            // Optimize for background operation
            audioCaptureDefaults: {
                autoGainControl: true,
                echoCancellation: true,
                noiseSuppression: true,
            },
            videoCaptureDefaults: {
                resolution: LiveKit.VideoPresets.h720.resolution,
            },
            publishDefaults: {
                videoSimulcastLayers: [
                    LiveKit.VideoPresets.h90,
                    LiveKit.VideoPresets.h180,
                    LiveKit.VideoPresets.h360,
                ],
                // Keep publishing even when tab is hidden
                stopMicTrackOnMute: false,
                videoCodec: 'vp8', // More stable codec
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
            
            // Step 1: Get explicit permissions first (CRITICAL for stability)
            console.log('🔐 Step 1: Requesting explicit browser permissions...');
            const permissionStream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: 30, max: 30 }
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
                        console.log('📹 Creating robust video track...');
                        const videoTrack = await LiveKit.createLocalVideoTrack({
                            resolution: LiveKit.VideoPresets.h720.resolution,
                            frameRate: 30
                        });
                        
                        console.log('📤 Publishing robust video track...');
                        await room.localParticipant.publishTrack(videoTrack, {
                            name: 'camera',
                            source: LiveKit.Track.Source.Camera
                        });
                        
                        videoEnabled = true;
                        console.log('✅ Robust video track published successfully');
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
        // Critical: Ensure container exists BEFORE trying to attach
        let container = document.getElementById(`participant-${participant.sid}`);
        if (!container) {
            console.log('📦 Creating participant container for:', participant.identity);
            container = createParticipantContainer(participant, false);
            
            // Wait a moment for DOM to be ready
            setTimeout(() => {
                attachTrackToContainer(track, publication, participant, container);
            }, 100);
        } else {
            console.log('📦 Using existing container for:', participant.identity);
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
            
            // Critical: Detach any existing track first
            const existingTracks = videoElement.srcObject?.getTracks() || [];
            existingTracks.forEach(existingTrack => existingTrack.stop());
            
            // Attach the new track
            track.attach(videoElement);
            
            // Ensure video plays
            videoElement.onloadeddata = () => {
                console.log('📹 Video data loaded for:', participant.identity);
                videoElement.play().catch(playError => {
                    console.warn('Video autoplay prevented for:', participant.identity, playError);
                    // Try to play again after user interaction
                    document.addEventListener('click', () => {
                        videoElement.play().catch(e => console.warn('Manual play failed:', e));
                    }, { once: true });
                });
            };
            
            // Error handling
            videoElement.onerror = (error) => {
                console.error('❌ Video element error for:', participant.identity, error);
                // Try to reattach after error
                setTimeout(() => {
                    try {
                        track.attach(videoElement);
                        console.log('🔄 Video track reattached after error');
                    } catch (reattachError) {
                        console.error('❌ Video reattach failed:', reattachError);
                    }
                }, 2000);
            };
            
            console.log('✅ Video track attached successfully for:', participant.identity);
            
        } else if (track.kind === LiveKit.Track.Kind.Audio) {
            console.log('🎤 Attaching audio track...');
            
            // Remove any existing audio elements for this participant
            const existingAudio = container.querySelectorAll('audio');
            existingAudio.forEach(audio => audio.remove());
            
            // Create new audio element
            const audioElement = document.createElement('audio');
            audioElement.autoplay = true;
            audioElement.playsInline = true;
            audioElement.controls = false; // Hidden controls
            
            // Attach track
            track.attach(audioElement);
            container.appendChild(audioElement);
            
            // Ensure audio plays
            audioElement.onloadeddata = () => {
                console.log('🎤 Audio data loaded for:', participant.identity);
                audioElement.play().catch(playError => {
                    console.warn('Audio autoplay prevented for:', participant.identity, playError);
                });
            };
            
            console.log('✅ Audio track attached successfully for:', participant.identity);
        }
        
        // Update container visibility
        container.style.opacity = '1';
        container.style.visibility = 'visible';
        
    } catch (attachError) {
        console.error('❌ CRITICAL: Track attachment failed for:', participant.identity, attachError);
        
        // Retry attachment after delay
        setTimeout(() => {
            console.log('🔄 Retrying track attachment for:', participant.identity);
            try {
                attachTrackToContainer(track, publication, participant, container);
            } catch (retryError) {
                console.error('❌ Track attachment retry failed:', retryError);
            }
        }, 2000);
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
    
    participants.set(participant.sid, participant);
    
    // Create container immediately when participant connects
    let container = document.getElementById(`participant-${participant.sid}`);
    if (!container) {
        console.log('📦 Creating container for new participant:', participant.identity);
        container = createParticipantContainer(participant, false);
    }
    
    updateParticipantCount();
    
    // Subscribe to existing tracks immediately
    participant.tracks.forEach((trackPublication) => {
        if (trackPublication.track) {
            console.log('📹 Subscribing to existing track:', trackPublication.kind, 'from', participant.identity);
            handleTrackSubscribed(trackPublication.track, trackPublication, participant);
        }
    });
}

function handleParticipantDisconnected(participant) {
    console.log('👥 PARTICIPANT DISCONNECTED:', participant.identity);
    participants.delete(participant.sid);
    
    // Remove participant container with cleanup
    const container = document.getElementById(`participant-${participant.sid}`);
    if (container) {
        console.log('🗑️ Cleaning up container for:', participant.identity);
        
        // Stop all media elements
        const mediaElements = container.querySelectorAll('video, audio');
        mediaElements.forEach(element => {
            if (element.srcObject) {
                element.srcObject.getTracks().forEach(track => track.stop());
            }
            element.remove();
        });
        
        // Remove container
        container.remove();
        console.log('✅ Container cleaned up for:', participant.identity);
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
    console.log('📦 CREATING CONTAINER for:', participant.identity, '(local:', isLocal, ')');
    
    const container = document.createElement('div');
    container.className = 'participant-container';
    container.id = `participant-${participant.sid}`;
    
    // Initially hidden until tracks are attached
    container.style.opacity = '0';
    container.style.visibility = 'hidden';
    container.style.transition = 'opacity 0.3s ease';
    
    const video = document.createElement('video');
    video.autoplay = true;
    video.playsInline = true;
    video.muted = isLocal; // Mute local video to prevent echo
    video.style.width = '100%';
    video.style.height = '100%';
    video.style.objectFit = 'cover';
    
    // Add loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = '🔄 Verbinde...';
    loadingIndicator.style.position = 'absolute';
    loadingIndicator.style.top = '50%';
    loadingIndicator.style.left = '50%';
    loadingIndicator.style.transform = 'translate(-50%, -50%)';
    loadingIndicator.style.color = 'white';
    loadingIndicator.style.fontSize = '14px';
    
    const nameLabel = document.createElement('div');
    nameLabel.className = 'participant-name';
    nameLabel.textContent = participant.identity || participant.name || 'Teilnehmer';
    if (isLocal) nameLabel.textContent += ' (Du)';
    
    container.appendChild(video);
    container.appendChild(loadingIndicator);
    container.appendChild(nameLabel);
    
    const videoGrid = document.getElementById('videoGrid');
    if (videoGrid) {
        videoGrid.appendChild(container);
        console.log('✅ Container added to video grid for:', participant.identity);
    } else {
        console.error('❌ Video grid not found!');
    }
    
    // Remove loading indicator when video loads
    video.addEventListener('loadeddata', () => {
        loadingIndicator.style.display = 'none';
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
    
    room.participants.forEach((participant, sid) => {
        console.log(`- Remote: ${participant.identity} (${sid})`);
        
        // Ensure container exists
        let container = document.getElementById(`participant-${sid}`);
        if (!container) {
            console.log('📦 Creating missing container for:', participant.identity);
            container = createParticipantContainer(participant, false);
        }
        
        // Re-attach all tracks
        participant.tracks.forEach((trackPublication) => {
            if (trackPublication.track && trackPublication.isSubscribed) {
                console.log('🔄 Re-attaching track:', trackPublication.kind, 'for', participant.identity);
                attachTrackToContainer(trackPublication.track, trackPublication, participant, container);
            }
        });
    });
    
    // Ensure local participant container exists
    if (room.localParticipant) {
        let localContainer = document.getElementById(`participant-${room.localParticipant.sid}`);
        if (!localContainer) {
            console.log('📦 Creating missing local container');
            localContainer = createParticipantContainer(room.localParticipant, true);
        }
    }
    
    updateParticipantCount();
    console.log('✅ Participant display update completed');
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