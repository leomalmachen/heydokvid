// CRITICAL FIX: Meeting initialization patch
console.log('🔧 Applying meeting initialization fix...');

// LiveKit compatibility layer - fix for undefined constants
function createLiveKitCompatibilityLayer() {
    console.log('🔧 Creating LiveKit compatibility layer...');
    
    if (typeof window.LiveKit !== 'undefined') {
        // Ensure Track.Source constants exist
        if (!window.LiveKit.Track) {
            window.LiveKit.Track = {};
        }
        if (!window.LiveKit.Track.Source) {
            window.LiveKit.Track.Source = {
                Camera: 'camera',
                Microphone: 'microphone', 
                ScreenShare: 'screen_share'
            };
        }
        
        // Ensure TrackSource exists (legacy compatibility)
        if (!window.LiveKit.TrackSource) {
            window.LiveKit.TrackSource = {
                Camera: 'camera',
                Microphone: 'microphone',
                ScreenShare: 'screen_share'
            };
        }
        
        // Ensure Track.Kind exists
        if (!window.LiveKit.Track.Kind) {
            window.LiveKit.Track.Kind = {
                Video: 'video',
                Audio: 'audio'
            };
        }
        
        console.log('✅ LiveKit compatibility layer created');
        console.log('LiveKit.TrackSource:', window.LiveKit.TrackSource);
        console.log('LiveKit.Track.Source:', window.LiveKit.Track.Source);
    } else {
        console.error('❌ LiveKit not found in window object');
    }
}

// Apply compatibility layer immediately
createLiveKitCompatibilityLayer();

// Override the problematic initializeMeeting function
window.originalInitializeMeeting = window.initializeMeeting;

window.initializeMeeting = async function() {
    console.log('🚀 FIXED MEETING INITIALIZATION - AGGRESSIVE MODE');
    
    try {
        // Ensure LiveKit compatibility
        createLiveKitCompatibilityLayer();
        
        // Step 1: Load meeting data FIRST
        console.log('📋 STEP 1: Loading meeting data FIRST...');
        
        // Get meeting ID from URL
        const pathParts = window.location.pathname.split('/');
        const meetingId = pathParts[pathParts.length - 1];
        
        if (!meetingId || meetingId === 'meeting') {
            throw new Error('Meeting-ID nicht in URL gefunden');
        }
        
        // Check for existing meeting data
        let meetingData = sessionStorage.getItem('meetingData');
        if (!meetingData) {
            // Get participant name
            const participantName = await getParticipantName();
            console.log('👤 Participant name:', participantName);
            
            // Determine role from URL
            const urlParams = new URLSearchParams(window.location.search);
            const userRole = urlParams.get('role');
            console.log('🎭 User role:', userRole);
            
            // Choose appropriate endpoint
            let endpoint, requestData;
            if (userRole === 'doctor') {
                endpoint = `/api/meetings/${meetingId}/join-doctor`;
                requestData = {
                    participant_name: participantName,
                    participant_role: 'doctor'
                };
            } else {
                endpoint = `/api/meetings/${meetingId}/join`;
                requestData = {
                    participant_name: participantName
                };
            }
            
            console.log('📞 Calling API:', endpoint, requestData);
            
            // Make API call
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Meeting join fehlgeschlagen');
            }
            
            meetingData = await response.json();
            console.log('✅ Meeting data loaded from API:', meetingData);
            
            // Store for future use
            sessionStorage.setItem('meetingData', JSON.stringify(meetingData));
        } else {
            meetingData = JSON.parse(meetingData);
            console.log('✅ Found existing meeting data:', meetingData);
        }
        
        // Step 2: Get local media permissions EARLY
        console.log('🎥 STEP 2: Getting local media permissions EARLY...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: 30 }
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            console.log('✅ Local media stream obtained:', stream);
            
            // Keep track for later use but don't stop immediately
            window._preConnectStream = stream;
            
        } catch (mediaError) {
            console.error('❌ Failed to get local media:', mediaError);
            // Don't fail here - we'll try again during connection
            console.warn('⚠️ Will retry media access during room connection');
        }
        
        // Step 3: Connect to room with meeting data
        console.log('🔗 STEP 3: Connecting to LiveKit room...');
        await connectToRoom(meetingData);
        
        console.log('✅ Meeting initialization completed successfully!');
        
    } catch (error) {
        console.error('❌ Meeting initialization failed:', error);
        
        // Enhanced error message based on error type
        let userMessage = 'Meeting-Initialisierung fehlgeschlagen: ';
        if (error.message.includes('Camera')) {
            userMessage += 'Kamera-Zugriff Problem. Bitte Seite neu laden.';
        } else if (error.message.includes('getUserMedia')) {
            userMessage += 'Kamera/Mikrofon Zugriff verweigert. Bitte Berechtigungen überprüfen.';
        } else {
            userMessage += error.message;
        }
        
        alert(userMessage);
        throw error;
    }
};

// Add enhanced hideLoadingOverlay function
window.hideLoadingOverlay = function() {
    const loadingState = document.getElementById('loadingState');
    if (loadingState) {
        loadingState.style.display = 'none';
    }
    console.log('✅ Loading overlay hidden');
};

// Add utility function for safe LiveKit constant access
window.getLiveKitSource = function(sourceType) {
    try {
        if (window.LiveKit?.Track?.Source?.[sourceType]) {
            return window.LiveKit.Track.Source[sourceType];
        } else if (window.LiveKit?.TrackSource?.[sourceType]) {
            return window.LiveKit.TrackSource[sourceType];
        } else {
            // Return lowercase version as fallback
            return sourceType.toLowerCase();
        }
    } catch (error) {
        console.warn('⚠️ Could not access LiveKit source constant:', sourceType, error);
        return sourceType.toLowerCase();
    }
};

console.log('✅ Meeting initialization fix applied!'); 