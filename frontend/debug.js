// ===================================
// HeyDok Video - Advanced Debugging Tools
// ===================================

// Global debug object
window.debugMeeting = {
    
    // Check camera and microphone permissions
    async checkPermissions() {
        console.log('🔒 Checking media permissions...');
        try {
            const permissions = {
                camera: await navigator.permissions.query({name: 'camera'}),
                microphone: await navigator.permissions.query({name: 'microphone'})
            };
            
            console.log('📷 Camera permission:', permissions.camera.state);
            console.log('🎤 Microphone permission:', permissions.microphone.state);
            
            return {
                camera: permissions.camera.state,
                microphone: permissions.microphone.state,
                granted: permissions.camera.state === 'granted' && permissions.microphone.state === 'granted'
            };
        } catch (error) {
            console.error('❌ Permission check failed:', error);
            return { error: error.message };
        }
    },
    
    // List available devices
    async listDevices() {
        console.log('📱 Enumerating media devices...');
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const cameras = devices.filter(d => d.kind === 'videoinput');
            const microphones = devices.filter(d => d.kind === 'audioinput');
            
            console.log('📷 Cameras found:', cameras.length);
            cameras.forEach((cam, i) => console.log(`  ${i+1}. ${cam.label || 'Camera ' + (i+1)}`));
            
            console.log('🎤 Microphones found:', microphones.length);
            microphones.forEach((mic, i) => console.log(`  ${i+1}. ${mic.label || 'Microphone ' + (i+1)}`));
            
            return { cameras, microphones, total: devices.length };
        } catch (error) {
            console.error('❌ Device enumeration failed:', error);
            return { error: error.message };
        }
    },
    
    // Test basic getUserMedia
    async testGetUserMedia() {
        console.log('🎥 Testing getUserMedia...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true
            });
            
            console.log('✅ getUserMedia successful');
            console.log('📹 Video tracks:', stream.getVideoTracks().length);
            console.log('🔊 Audio tracks:', stream.getAudioTracks().length);
            
            // Stop tracks immediately
            stream.getTracks().forEach(track => track.stop());
            
            return {
                success: true,
                videoTracks: stream.getVideoTracks().length,
                audioTracks: stream.getAudioTracks().length
            };
        } catch (error) {
            console.error('❌ getUserMedia failed:', error);
            return { error: error.message, name: error.name };
        }
    },
    
    // Get current room state
    getRoomState() {
        console.log('🏠 Checking room state...');
        
        if (!window.room) {
            console.log('❌ No room object found');
            return { error: 'No room object' };
        }
        
        const state = {
            roomState: window.room.state,
            localParticipant: {
                identity: window.room.localParticipant?.identity,
                sid: window.room.localParticipant?.sid,
                trackCount: window.room.localParticipant?.trackPublications?.size || 0
            },
            remoteParticipants: [],
            totalParticipants: 1 + (window.room.remoteParticipants?.size || 0)
        };
        
        if (window.room.remoteParticipants) {
            window.room.remoteParticipants.forEach((participant, sid) => {
                state.remoteParticipants.push({
                    identity: participant.identity,
                    sid: participant.sid,
                    trackCount: participant.trackPublications.size,
                    tracks: Array.from(participant.trackPublications.values()).map(pub => ({
                        kind: pub.kind,
                        source: pub.source,
                        subscribed: pub.isSubscribed,
                        hasTrack: !!pub.track
                    }))
                });
            });
        }
        
        console.log('🏠 Room state:', state);
        return state;
    },
    
    // Check track attachments in DOM
    checkTrackAttachments() {
        console.log('🎵 Checking track attachments in DOM...');
        
        const containers = document.querySelectorAll('.participant-container');
        const attachments = [];
        
        containers.forEach((container, index) => {
            const nameLabel = container.querySelector('.participant-name');
            const video = container.querySelector('video');
            const audios = container.querySelectorAll('audio');
            
            const info = {
                containerIndex: index,
                containerId: container.id,
                participantName: nameLabel?.textContent || 'Unknown',
                video: {
                    exists: !!video,
                    hasSource: video && (!!video.srcObject || !!video.src),
                    playing: video && !video.paused,
                    muted: video?.muted,
                    display: video?.style.display,
                    visibility: video?.style.visibility
                },
                audio: {
                    count: audios.length,
                    elements: Array.from(audios).map(audio => ({
                        hasSource: !!audio.srcObject || !!audio.src,
                        playing: !audio.paused,
                        muted: audio.muted,
                        volume: audio.volume
                    }))
                }
            };
            
            attachments.push(info);
            
            console.log(`📦 Container ${index + 1} (${info.participantName}):`);
            console.log(`   Video: ${info.video.exists ? 'Yes' : 'No'}, Source: ${info.video.hasSource ? 'Yes' : 'No'}, Playing: ${info.video.playing ? 'Yes' : 'No'}`);
            console.log(`   Audio: ${info.audio.count} elements`);
        });
        
        return attachments;
    },
    
    // Force reprocess all tracks
    forceReprocessTracks() {
        console.log('🔄 Force reprocessing all tracks...');
        
        if (window.forceProcessAllTracks) {
            window.forceProcessAllTracks();
            return { success: true, message: 'Called forceProcessAllTracks' };
        } else {
            console.error('❌ forceProcessAllTracks function not available');
            return { error: 'forceProcessAllTracks function not found' };
        }
    },
    
    // Force subscribe to remote tracks
    forceSubscribe() {
        console.log('🎯 Force subscribing to remote tracks...');
        
        if (window.forceSubscribeToAllRemoteTracks) {
            window.forceSubscribeToAllRemoteTracks();
            return { success: true, message: 'Called forceSubscribeToAllRemoteTracks' };
        } else {
            console.error('❌ forceSubscribeToAllRemoteTracks function not available');
            return { error: 'forceSubscribeToAllRemoteTracks function not found' };
        }
    },
    
    // Run full diagnostic
    async runFullDiagnostic() {
        console.log('🔍 === RUNNING FULL DIAGNOSTIC ===');
        
        const results = {
            timestamp: new Date().toISOString(),
            permissions: await this.checkPermissions(),
            devices: await this.listDevices(),
            getUserMedia: await this.testGetUserMedia(),
            roomState: this.getRoomState(),
            trackAttachments: this.checkTrackAttachments()
        };
        
        console.log('📊 DIAGNOSTIC RESULTS:', results);
        
        // Show summary
        console.log('\n🎯 === DIAGNOSTIC SUMMARY ===');
        console.log('✅ Permissions granted:', results.permissions.granted ? 'Yes' : 'No');
        console.log('📱 Devices found:', results.devices.total || 0);
        console.log('🎥 getUserMedia works:', results.getUserMedia.success ? 'Yes' : 'No');
        console.log('🏠 Room connected:', results.roomState.roomState === 'connected' ? 'Yes' : 'No');
        console.log('👥 Total participants:', results.roomState.totalParticipants || 0);
        console.log('📦 DOM containers:', results.trackAttachments.length);
        
        return results;
    }
};

// Auto-register debug commands
console.log('🔧 HeyDok Video Debug Tools loaded!');
console.log('📋 Available commands:');
console.log('  - debugMeeting.runFullDiagnostic()');
console.log('  - debugMeeting.checkPermissions()');
console.log('  - debugMeeting.listDevices()');
console.log('  - debugMeeting.testGetUserMedia()');
console.log('  - debugMeeting.getRoomState()');
console.log('  - debugMeeting.checkTrackAttachments()');
console.log('  - debugMeeting.forceReprocessTracks()');
console.log('  - debugMeeting.forceSubscribe()');

// Add visual debug indicator
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addDebugIndicator);
} else {
    addDebugIndicator();
}

function addDebugIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'debug-indicator';
    indicator.innerHTML = '🔧 Debug Tools Active';
    indicator.style.cssText = `
        position: fixed;
        bottom: 10px;
        left: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: #4CAF50;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 9999;
        font-family: monospace;
        cursor: pointer;
    `;
    
    indicator.onclick = () => {
        console.log('🔧 Running quick diagnostic...');
        debugMeeting.runFullDiagnostic();
    };
    
    document.body.appendChild(indicator);
} 