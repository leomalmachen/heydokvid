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
            const directJoin = urlParams.get('direct'); // New: Check if this is a direct join from meeting creation
            
            console.log('🔍 URL Role parameter:', userRole);
            console.log('🔍 Direct join parameter:', directJoin);
            console.log('🔍 Current URL:', window.location.href);
            
            // Check if doctor has stored meeting data from meeting creation
            if (userRole === 'doctor' && directJoin === 'true') {
                const storedDoctorData = sessionStorage.getItem('doctorMeetingData');
                if (storedDoctorData) {
                    try {
                        const doctorMeetingData = JSON.parse(storedDoctorData);
                        if (doctorMeetingData.meeting_id === meetingId) {
                            console.log('🩺 Using stored doctor meeting data from creation');
                            console.log('🩺 Stored data:', doctorMeetingData);
                            meetingData = doctorMeetingData;
                            sessionStorage.setItem('meetingData', JSON.stringify(meetingData));
                            
                            // Clear the stored doctor data so it's only used once
                            sessionStorage.removeItem('doctorMeetingData');
                            
                            // Connect directly to room using stored token
                            await connectToRoom(meetingData);
                            isInitialized = true;
                            console.log('🎉 Doctor initialization completed using stored token!');
                            return;
                        } else {
                            console.warn('⚠️ Stored doctor data is for different meeting, clearing...');
                            sessionStorage.removeItem('doctorMeetingData');
                        }
                    } catch (error) {
                        console.error('❌ Error parsing stored doctor data:', error);
                        sessionStorage.removeItem('doctorMeetingData');
                    }
                }
            }
            
            // FALLBACK: Check if doctor has stored data even without direct=true (for refreshes/direct URLs)
            if (userRole === 'doctor') {
                const storedDoctorData = sessionStorage.getItem('doctorMeetingData');
                if (storedDoctorData) {
                    try {
                        const doctorMeetingData = JSON.parse(storedDoctorData);
                        if (doctorMeetingData.meeting_id === meetingId) {
                            console.log('🩺 FALLBACK: Using stored doctor data for direct URL access');
                            meetingData = doctorMeetingData;
                            sessionStorage.setItem('meetingData', JSON.stringify(meetingData));
                            
                            // Connect directly to room using stored token
                            await connectToRoom(meetingData);
                            isInitialized = true;
                            console.log('🎉 Doctor fallback initialization completed!');
                            return;
                        }
                    } catch (error) {
                        console.warn('⚠️ Stored doctor data parsing failed for fallback:', error);
                    }
                }
            }
            
            // IMPROVED: Use nice modal for name input
            try {
                let participantName;
                
                // SPECIAL: For doctors, try to use stored meeting data first
                if (userRole === 'doctor') {
                    // Try to get doctor name from meeting data that might be lost due to Heroku restart
                    try {
                        const response = await fetch(`/api/meetings/${meetingId}/status`);
                        if (response.ok) {
                            const statusData = await response.json();
                            if (statusData.doctor_name) {
                                participantName = statusData.doctor_name;
                                console.log('🩺 Using doctor name from meeting status:', participantName);
                            }
                        }
                    } catch (error) {
                        console.warn('⚠️ Could not fetch meeting status for doctor name:', error);
                    }
                }
                
                // If no automatic name found, ask user
                if (!participantName) {
                    participantName = await getParticipantName();
                }
                
                // Use role-specific endpoints
                let joinEndpoint, joinData;
                
                if (userRole === 'doctor') {
                    console.log('🩺 Doctor joining meeting...');
                    console.log('🩺 Using doctor endpoint for:', participantName);
                    joinEndpoint = `/api/meetings/${meetingId}/join-doctor`;
                    joinData = {
                        participant_name: participantName,
                        participant_role: 'doctor'
                    };
                } else {
                    console.log('👤 Participant joining meeting...');
                    console.log('👤 Using patient endpoint for:', participantName);
                    joinEndpoint = `/api/meetings/${meetingId}/join`;
                    joinData = {
                        participant_name: participantName
                    };
                }
                
                console.log('📞 Making API call to:', joinEndpoint);
                console.log('📞 With data:', joinData);
                
                const response = await fetch(joinEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(joinData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('❌ API Error:', errorData);
                    throw new Error(errorData.detail || 'Could not join meeting');
                }

                meetingData = await response.json();
                console.log('✅ Meeting data received:', meetingData);
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

        // CRITICAL FIX: Ensure meetingData is always parsed as object before connecting
        if (typeof meetingData === 'string') {
            console.log('🔧 Parsing meetingData string to object...');
            try {
                meetingData = JSON.parse(meetingData);
                console.log('✅ meetingData successfully parsed:', meetingData);
            } catch (parseError) {
                console.error('❌ Failed to parse meetingData:', parseError);
                console.error('❌ Raw meetingData:', meetingData);
                throw new Error('Meeting data is corrupted and cannot be parsed');
            }
        }
        
        // VALIDATION: Ensure meetingData has required fields
        if (!meetingData || typeof meetingData !== 'object') {
            throw new Error('Meeting data is not a valid object');
        }
        
        if (!meetingData.livekit_url) {
            console.error('❌ Missing livekit_url in meetingData:', meetingData);
            throw new Error('LiveKit URL is missing from meeting data');
        }
        
        if (!meetingData.token) {
            console.error('❌ Missing token in meetingData:', meetingData);
            throw new Error('LiveKit token is missing from meeting data');
        }
        
        console.log('✅ meetingData validation passed:', {
            has_livekit_url: !!meetingData.livekit_url,
            has_token: !!meetingData.token,
            meeting_id: meetingData.meeting_id
        });

        // Connect to room - ULTRA-SIMPLE
        await connectToRoom(meetingData);
        
        isInitialized = true;
        console.log('🎉 ULTRA-SIMPLE initialization completed!');
        
        // DEBUG: Show success information if debug parameter is present
        const showDebug = new URLSearchParams(window.location.search).get('debug');
        if (showDebug === 'true') {
            const debugInfo = {
                success: true,
                meetingId: meetingId,
                currentURL: window.location.href,
                userRole: new URLSearchParams(window.location.search).get('role'),
                directJoin: new URLSearchParams(window.location.search).get('direct'),
                meetingData: meetingData,
                roomState: room ? room.state : 'null',
                participantCount: room ? (1 + room.remoteParticipants.size) : 0,
                timestamp: new Date().toISOString()
            };
            
            setTimeout(() => showDebugOverlay(debugInfo), 2000);
        }
        
    } catch (error) {
        console.error('❌ Initialization failed:', error);
        
        // EMERGENCY DEBUG: Show detailed error information
        const debugInfo = {
            error: error.message,
            stack: error.stack,
            meetingId: meetingId,
            currentURL: window.location.href,
            userRole: new URLSearchParams(window.location.search).get('role'),
            directJoin: new URLSearchParams(window.location.search).get('direct'),
            sessionStorageData: {
                meetingData: sessionStorage.getItem('meetingData'),
                doctorMeetingData: sessionStorage.getItem('doctorMeetingData'),
                participantName: sessionStorage.getItem('participantName')
            },
            roomState: room ? room.state : 'null',
            timestamp: new Date().toISOString()
        };
        
        showDebugOverlay(debugInfo);
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
        // Single participant - centered, large
        console.log('📋 1 participant - centered layout');
        videoGrid.style.gridTemplateColumns = '1fr';
        videoGrid.style.gridTemplateRows = '1fr';
        videoGrid.style.placeItems = 'center';
        
        // Make single container large but not full screen
        containers[0].style.width = 'min(80vw, 600px)';
        containers[0].style.height = 'min(60vh, 450px)';
        
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
        
        // BULLETPROOF: Event handlers setup
        room.on(LiveKit.RoomEvent.Connected, () => {
            console.log('🎉 Room connected successfully!');
            console.log('🎉 Local participant identity:', room.localParticipant.identity);
            console.log('🎉 Local participant SID:', room.localParticipant.sid);
            
            // CRITICAL: Process local participant first - use CONSISTENT function
            console.log('👤 Processing LOCAL participant:', room.localParticipant.identity);
            const localContainer = createConsistentContainer(room.localParticipant, true);
            console.log('👤 Local container created:', localContainer ? 'SUCCESS' : 'FAILED');
            
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
            console.log('🎥 About to enable local media...');
            enableLocalMedia();
        });
        
        room.on(LiveKit.RoomEvent.ParticipantConnected, handleParticipantConnected);
        room.on(LiveKit.RoomEvent.ParticipantDisconnected, handleParticipantDisconnected);
        room.on(LiveKit.RoomEvent.TrackSubscribed, handleTrackSubscribed);
        room.on(LiveKit.RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed);
        room.on(LiveKit.RoomEvent.TrackMuted, handleTrackMuted);
        room.on(LiveKit.RoomEvent.TrackUnmuted, handleTrackUnmuted);
        
        room.on(LiveKit.RoomEvent.Reconnecting, () => {
            console.log('🔄 Room reconnecting...');
            showStatus('Verbindung wird wiederhergestellt...', 'warning');
        });
        
        room.on(LiveKit.RoomEvent.Reconnected, () => {
            console.log('✅ Room reconnected!');
            showStatus('Verbindung wiederhergestellt!', 'success');
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
    console.log(`🎵 Track details:`, {
        kind: track.kind,
        sid: track.sid,
        participant: participant.identity,
        participantSid: participant.sid
    });
    
    // Get participant container - use CONSISTENT ID scheme
    const container = document.getElementById(`participant-${participant.sid}`);
    if (!container) {
        console.warn('⚠️ No container found for participant:', participant.identity);
        console.warn('⚠️ Creating missing container...');
        // Try to create it
        const newContainer = createConsistentContainer(participant, false);
        if (!newContainer) {
            console.error('❌ Failed to create container for participant:', participant.identity);
            return;
        }
        console.log('✅ Container created for participant:', participant.identity);
        // Give the container a moment to be added to DOM
        setTimeout(() => handleTrackSubscribed(track, publication, participant), 100);
        return;
    }
    
    if (track.kind === 'video') {
        console.log('📹 Attaching VIDEO track for:', participant.identity);
        
        // Get video element
        const video = container.querySelector('video');
        if (!video) {
            console.error('❌ No video element found in container for:', participant.identity);
            console.error('❌ Container HTML:', container.innerHTML);
            return;
        }
        
        console.log('📹 Video element found, attaching track...');
        
        // CRITICAL: Attach track properly
        try {
            track.attach(video);
            
            // IMPORTANT: Ensure video is visible and playing
            video.style.display = 'block';
            video.style.visibility = 'visible';
            video.style.opacity = '1';
            
            // Try to play the video
            video.play().then(() => {
                console.log('✅ Video playing successfully for:', participant.identity);
            }).catch(e => {
                console.warn('⚠️ Video autoplay prevented for:', participant.identity, e);
                // This is usually okay, user interaction will start playback
            });
            
            console.log('✅ Video track attached and made visible for:', participant.identity);
            
        } catch (error) {
            console.error('❌ Failed to attach video track for:', participant.identity, error);
            return;
        }
        
        // Handle video track events
        track.on(LiveKit.TrackEvent.Muted, () => {
            console.log('📹❌ Video muted for:', participant.identity);
            video.style.display = 'none';
        });
        
        track.on(LiveKit.TrackEvent.Unmuted, () => {
            console.log('📹✅ Video unmuted for:', participant.identity);
            video.style.display = 'block';
        });
        
        // CRITICAL: Update grid layout after video is attached
        updateConsistentGrid();
        
    } else if (track.kind === 'audio') {
        console.log('🔊 Attaching AUDIO track for:', participant.identity);
        
        // Create audio element for remote audio
        const audio = document.createElement('audio');
        audio.autoplay = true;
        audio.muted = false; // Remote audio should NOT be muted
        audio.volume = 1.0;
        audio.style.display = 'none'; // Audio elements don't need to be visible
        
        try {
            track.attach(audio);
            container.appendChild(audio);
            
            console.log('✅ Audio track attached successfully for:', participant.identity);
        } catch (error) {
            console.error('❌ Failed to attach audio track for:', participant.identity, error);
        }
    }
    
    console.log('🎵 Track subscription completed for:', participant.identity, track.kind);
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
        console.error('❌ Room:', room);
        console.error('❌ Local participant:', room ? room.localParticipant : 'Room is null');
        return;
    }
    
    try {
        console.log('🎥 Enabling local media with saved state...');
        console.log('🎥 Video enabled state:', videoEnabled);
        console.log('🎥 Audio enabled state:', audioEnabled);
        console.log('🎥 Local participant identity:', room.localParticipant.identity);
        console.log('🎥 Local participant SID:', room.localParticipant.sid);
        
        // Enable camera and microphone based on saved state
        console.log('🎥 Setting camera enabled to:', videoEnabled);
        await room.localParticipant.setCameraEnabled(videoEnabled);
        console.log('🎥 Setting microphone enabled to:', audioEnabled);
        await room.localParticipant.setMicrophoneEnabled(audioEnabled);
        
        console.log('🎥 Camera and microphone set successfully');
        
        // Update UI buttons
        updateMediaButtons();
        
        // CRITICAL: Handle local tracks properly to prevent echo - use CONSISTENT ID scheme
        const localContainerId = `participant-${room.localParticipant.sid}`;
        console.log('🎥 Looking for local container with ID:', localContainerId);
        const localContainer = document.getElementById(localContainerId);
        
        if (!localContainer) {
            console.log('🔧 Creating missing local container...');
            console.log('🔧 Local participant for container creation:', room.localParticipant);
            const newContainer = createConsistentContainer(room.localParticipant, true);
            console.log('🔧 New container created:', newContainer ? 'SUCCESS' : 'FAILED');
            if (newContainer) {
                console.log('🔧 New container ID:', newContainer.id);
            }
            return; // Wait for container to be created
        }
        
        console.log('✅ Local container found:', localContainer);
        
        const localVideo = localContainer.querySelector('video');
        if (!localVideo) {
            console.error('❌ Local video element not found in container');
            console.error('❌ Container contents:', localContainer.innerHTML);
            return;
        }
        
        console.log('✅ Local video element found:', localVideo);
        
        // ECHO PREVENTION: Ensure local video is ALWAYS muted
        localVideo.muted = true;
        localVideo.volume = 0;
        
        console.log('🎥 Processing video track publications...');
        console.log('🎥 Video track publications count:', room.localParticipant.videoTrackPublications.size);
        
        // Attach video tracks to local video element
        room.localParticipant.videoTrackPublications.forEach((publication, index) => {
            if (publication.track) {
                console.log(`📹 Attaching LOCAL video track ${index}:`, publication.track);
                publication.track.attach(localVideo);
                localVideo.style.display = videoEnabled ? 'block' : 'none';
                console.log(`📹 Video track ${index} attached successfully, display:`, localVideo.style.display);
            } else {
                console.log(`📹 Video track publication ${index} has no track`);
            }
        });
        
        console.log('🎥 Processing audio track publications...');
        console.log('🎥 Audio track publications count:', room.localParticipant.audioTrackPublications.size);
        
        // CRITICAL: NEVER attach local audio tracks to prevent echo
        room.localParticipant.audioTrackPublications.forEach((publication, index) => {
            if (publication.track) {
                console.log(`🔇 LOCAL audio track ${index} found - NOT attaching to prevent echo`);
                // Do NOT attach local audio track - this prevents echo!
            } else {
                console.log(`🔇 Audio track publication ${index} has no track`);
            }
        });
        
        console.log('✅ Local media enabled successfully (echo-free)');
        
        // Hide loading and show controls
        const loadingElement = document.getElementById('loadingState');
        if (loadingElement) {
            loadingElement.style.display = 'none';
            console.log('✅ Loading state hidden');
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
        console.error('❌ Error stack:', error.stack);
        showError('Fehler beim Aktivieren von Kamera/Mikrofon: ' + error.message);
    }
} 