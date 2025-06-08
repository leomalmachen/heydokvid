// CRITICAL FIX: Meeting initialization patch
console.log('🔧 Applying meeting initialization fix...');

// Override the problematic initializeMeeting function
window.originalInitializeMeeting = window.initializeMeeting;

window.initializeMeeting = async function() {
    console.log('🚀 FIXED MEETING INITIALIZATION - AGGRESSIVE MODE');
    
    try {
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
        
        // Step 2: Get local media permissions
        console.log('🎥 STEP 2: Getting local media permissions...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true
            });
            console.log('✅ Local media stream obtained:', stream);
            
            // Stop the test stream - we'll get it again in enableLocalMedia
            stream.getTracks().forEach(track => track.stop());
            
        } catch (mediaError) {
            console.error('❌ Failed to get local media:', mediaError);
            alert('Kamera/Mikrofon Zugriff verweigert! Bitte erlauben Sie den Zugriff und laden Sie die Seite neu.');
            return;
        }
        
        // Step 3: Connect to room with meeting data
        console.log('🔗 STEP 3: Connecting to LiveKit room...');
        await connectToRoom(meetingData);
        
        console.log('✅ Meeting initialization completed successfully!');
        
    } catch (error) {
        console.error('❌ Meeting initialization failed:', error);
        alert('Meeting-Initialisierung fehlgeschlagen: ' + error.message);
        throw error;
    }
};

// Add missing hideLoadingOverlay function
window.hideLoadingOverlay = function() {
    const loadingState = document.getElementById('loadingState');
    if (loadingState) {
        loadingState.style.display = 'none';
    }
    console.log('✅ Loading overlay hidden');
};

console.log('✅ Meeting initialization fix applied!'); 