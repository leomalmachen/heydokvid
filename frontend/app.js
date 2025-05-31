// Global variables
let room;
let localParticipant;
let audioEnabled = true;
let videoEnabled = true;
const participants = new Map();

// Get meeting ID from URL
const pathParts = window.location.pathname.split('/');
const meetingId = pathParts[pathParts.length - 1];

// Initialize the meeting
async function initMeeting() {
    console.log('Initializing meeting:', meetingId);
    
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
                throw new Error('Failed to join meeting');
            }

            meetingData = await response.json();
            sessionStorage.setItem('meetingData', JSON.stringify(meetingData));
        } catch (error) {
            alert('Fehler beim Beitreten: ' + error.message);
            window.location.href = '/';
            return;
        }
    } else {
        meetingData = JSON.parse(meetingData);
    }

    // Connect to LiveKit room
    await connectToRoom(meetingData);
}

async function connectToRoom(meetingData) {
    try {
        // Create room instance
        room = new LivekitClient.Room({
            adaptiveStream: true,
            dynacast: true,
        });

        // Set up event handlers
        room
            .on(LivekitClient.RoomEvent.TrackSubscribed, handleTrackSubscribed)
            .on(LivekitClient.RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
            .on(LivekitClient.RoomEvent.ParticipantConnected, handleParticipantConnected)
            .on(LivekitClient.RoomEvent.ParticipantDisconnected, handleParticipantDisconnected)
            .on(LivekitClient.RoomEvent.Disconnected, handleDisconnect)
            .on(LivekitClient.RoomEvent.LocalTrackPublished, handleLocalTrackPublished);

        // Connect to room
        await room.connect(meetingData.livekit_url, meetingData.token);
        console.log('Connected to room');

        // Hide loading state
        document.getElementById('loadingState').style.display = 'none';

        // Set local participant
        localParticipant = room.localParticipant;

        // Enable camera and microphone
        await room.localParticipant.enableCameraAndMicrophone();

        // Update participant count
        updateParticipantCount();

        // Set share link
        const shareUrl = window.location.href;
        document.getElementById('shareLinkInput').value = shareUrl;

    } catch (error) {
        console.error('Error connecting to room:', error);
        alert('Fehler beim Verbinden: ' + error.message);
    }
}

function handleTrackSubscribed(track, publication, participant) {
    console.log('Track subscribed:', track.kind, participant.identity);
    
    if (track.kind === 'video' || track.kind === 'audio') {
        // Get or create participant container
        let container = document.getElementById(`participant-${participant.sid}`);
        if (!container) {
            container = createParticipantContainer(participant);
        }

        // Attach track
        if (track.kind === 'video') {
            const videoElement = container.querySelector('video');
            track.attach(videoElement);
        } else if (track.kind === 'audio') {
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
    alert('Verbindung zum Meeting verloren');
    window.location.href = '/';
}

function handleLocalTrackPublished(publication, participant) {
    console.log('Local track published:', publication.kind);
    
    // Create container for local participant if not exists
    let container = document.getElementById(`participant-${participant.sid}`);
    if (!container) {
        container = createParticipantContainer(participant, true);
    }

    // Attach local video
    if (publication.kind === 'video') {
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
    
    document.getElementById('videoGrid').appendChild(container);
    
    return container;
}

function updateParticipantCount() {
    const count = room ? room.participants.size + 1 : 1; // +1 for local participant
    document.getElementById('participantCount').textContent = count;
}

// Control button handlers
document.getElementById('toggleMic').addEventListener('click', async () => {
    if (!room) return;
    
    audioEnabled = !audioEnabled;
    await room.localParticipant.setMicrophoneEnabled(audioEnabled);
    
    const btn = document.getElementById('toggleMic');
    btn.classList.toggle('active', audioEnabled);
    btn.querySelector('.mic-on').classList.toggle('hidden', !audioEnabled);
    btn.querySelector('.mic-off').classList.toggle('hidden', audioEnabled);
});

document.getElementById('toggleVideo').addEventListener('click', async () => {
    if (!room) return;
    
    videoEnabled = !videoEnabled;
    await room.localParticipant.setCameraEnabled(videoEnabled);
    
    const btn = document.getElementById('toggleVideo');
    btn.classList.toggle('active', videoEnabled);
    btn.querySelector('.video-on').classList.toggle('hidden', !videoEnabled);
    btn.querySelector('.video-off').classList.toggle('hidden', videoEnabled);
});

document.getElementById('shareLink').addEventListener('click', () => {
    document.getElementById('shareModal').classList.add('show');
});

document.getElementById('copyLink').addEventListener('click', () => {
    const input = document.getElementById('shareLinkInput');
    input.select();
    document.execCommand('copy');
    
    const btn = document.getElementById('copyLink');
    btn.textContent = '✓ Kopiert!';
    setTimeout(() => {
        btn.textContent = '📋 Kopieren';
    }, 2000);
});

document.getElementById('leaveMeeting').addEventListener('click', async () => {
    if (confirm('Meeting wirklich verlassen?')) {
        if (room) {
            await room.disconnect();
        }
        sessionStorage.removeItem('meetingData');
        window.location.href = '/';
    }
});

// Close modal on outside click
document.getElementById('shareModal').addEventListener('click', (e) => {
    if (e.target.id === 'shareModal') {
        e.target.classList.remove('show');
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initMeeting); 