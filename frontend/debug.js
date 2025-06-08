// Enhanced debugging functions for HeyDok Video troubleshooting
window.debugMeeting = {
    // Check media permissions
    async checkPermissions() {
        console.log('🔍 CHECKING MEDIA PERMISSIONS...');
        try {
            const cameraPermission = await navigator.permissions.query({name: 'camera'});
            const microphonePermission = await navigator.permissions.query({name: 'microphone'});
            console.log('📷 Camera permission:', cameraPermission.state);
            console.log('🎤 Microphone permission:', microphonePermission.state);
            return {
                camera: cameraPermission.state,
                microphone: microphonePermission.state
            };
        } catch (e) {
            console.error('❌ Permission check failed:', e);
            return null;
        }
    },
    
    // List available devices
    async listDevices() {
        console.log('🔍 LISTING AVAILABLE DEVICES...');
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const cameras = devices.filter(d => d.kind === 'videoinput');
            const microphones = devices.filter(d => d.kind === 'audioinput');
            const speakers = devices.filter(d => d.kind === 'audiooutput');
            
            console.log('📷 Cameras:', cameras.length, cameras);
            console.log('🎤 Microphones:', microphones.length, microphones);
            console.log('🔊 Speakers:', speakers.length, speakers);
            
            return { cameras, microphones, speakers };
        } catch (e) {
            console.error('❌ Device enumeration failed:', e);
            return null;
        }
    },
    
    // Test basic getUserMedia
    async testGetUserMedia() {
        console.log('🔍 TESTING getUserMedia...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true
            });
            
            const videoTracks = stream.getVideoTracks();
            const audioTracks = stream.getAudioTracks();
            
            console.log('✅ getUserMedia successful!');
            console.log('📷 Video tracks:', videoTracks.length, videoTracks);
            console.log('🎤 Audio tracks:', audioTracks.length, audioTracks);
            
            // Clean up
            stream.getTracks().forEach(track => track.stop());
            
            return { success: true, videoTracks: videoTracks.length, audioTracks: audioTracks.length };
        } catch (e) {
            console.error('❌ getUserMedia failed:', e);
            return { success: false, error: e.message };
        }
    },
    
    // Check room state
    getRoomState() {
        console.log('🔍 CURRENT ROOM STATE...');
        if (!window.room) {
            console.log('❌ No room instance');
            return null;
        }
        
        const room = window.room;
        const state = {
            roomState: room.state,
            localParticipant: room.localParticipant ? {
                identity: room.localParticipant.identity,
                sid: room.localParticipant.sid,
                videoTracks: room.localParticipant.videoTrackPublications.size,
                audioTracks: room.localParticipant.audioTrackPublications.size
            } : null,
            remoteParticipants: Array.from(room.remoteParticipants.values()).map(p => ({
                identity: p.identity,
                sid: p.sid,
                videoTracks: p.videoTrackPublications.size,
                audioTracks: p.audioTrackPublications.size
            }))
        };
        
        console.log('🏠 Room State:', state);
        return state;
    },
    
    // Check track attachments
    checkTrackAttachments() {
        console.log('🔍 CHECKING TRACK ATTACHMENTS...');
        const containers = document.querySelectorAll('.participant-container');
        
        containers.forEach(container => {
            const participantId = container.id;
            const video = container.querySelector('video');
            const audios = container.querySelectorAll('audio');
            
            console.log(`👤 Container ${participantId}:`);
            console.log('  📷 Video element:', !!video, video ? `srcObject: ${!!video.srcObject}` : 'none');
            console.log('  🎤 Audio elements:', audios.length);
            
            audios.forEach((audio, i) => {
                console.log(`    Audio ${i}: srcObject: ${!!audio.srcObject}, participant: ${audio.getAttribute('data-participant')}`);
            });
        });
    },
    
    // Quick test sequence
    async runFullDiagnostic() {
        console.log('🚀 RUNNING FULL DIAGNOSTIC...');
        
        console.log('\n1. Checking permissions...');
        await this.checkPermissions();
        
        console.log('\n2. Listing devices...');
        await this.listDevices();
        
        console.log('\n3. Testing getUserMedia...');
        await this.testGetUserMedia();
        
        console.log('\n4. Checking room state...');
        this.getRoomState();
        
        console.log('\n5. Checking track attachments...');
        this.checkTrackAttachments();
        
        console.log('\n✅ DIAGNOSTIC COMPLETE');
    }
};

// Make debug functions globally available
console.log('🔧 DEBUG TOOLS LOADED!');
console.log('Use these commands in browser console:');
console.log('• debugMeeting.checkPermissions() - Check media permissions');
console.log('• debugMeeting.listDevices() - List cameras/mics');
console.log('• debugMeeting.testGetUserMedia() - Test media access');
console.log('• debugMeeting.getRoomState() - Check LiveKit room');
console.log('• debugMeeting.checkTrackAttachments() - Check elements');
console.log('• debugMeeting.runFullDiagnostic() - Run all tests');
console.log('💡 Quick fix: window.forceSubscribeToAllRemoteTracks()'); 