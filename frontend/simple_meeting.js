/**
 * HeyDok - Saubere LiveKit Video Implementation 
 * Fokus: Einfach, stabil, langfristig wartbar
 */

class SimpleMeeting {
    constructor() {
        this.room = null;
        this.participants = new Map();
        this.isConnected = false;
        this.isInitialized = false;
        
        // Media State
        this.audioEnabled = true;
        this.videoEnabled = true;
        
        console.log('🚀 SimpleMeeting initialized');
    }
    
    /**
     * Hauptinitialisierung - sauber und einfach
     */
    async initialize() {
        if (this.isInitialized) {
            console.log('⚠️ Already initialized');
            return;
        }
        
        try {
            console.log('🔧 Starting initialization...');
            
            // 1. Lade Meeting Data
            const meetingData = await this.loadMeetingData();
            
            // 2. Verbinde zu LiveKit Room
            await this.connectToRoom(meetingData);
            
            // 3. Setup Media
            await this.setupLocalMedia();
            
            this.isInitialized = true;
            console.log('✅ Initialization completed');
            
        } catch (error) {
            console.error('❌ Initialization failed:', error);
            this.showError('Fehler beim Verbinden zum Meeting', error.message);
        }
    }
    
    /**
     * Meeting Data laden - vereinfacht
     */
    async loadMeetingData() {
        const pathParts = window.location.pathname.split('/');
        const meetingId = pathParts[pathParts.length - 1];
        
        // Prüfe SessionStorage
        let meetingData = sessionStorage.getItem('meetingData') || 
                         sessionStorage.getItem('doctorMeetingData');
        
        if (meetingData) {
            return JSON.parse(meetingData);
        }
        
        // Fallback: Join API
        const response = await fetch(`/api/meetings/${meetingId}/join`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: this.getParticipantName()})
        });
        
        if (!response.ok) {
            throw new Error(`Meeting join failed: ${response.status}`);
        }
        
        return await response.json();
    }
    
    /**
     * Room Connection - clean und robust
     */
    async connectToRoom(meetingData) {
        console.log('🔗 Connecting to room...');
        
        // Room erstellen
        this.room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true,
            audioCaptureDefaults: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        // Event Handlers - NUR EINMAL setzen
        this.setupRoomEvents();
        
        // Verbinden
        await this.room.connect(meetingData.livekit_url, meetingData.token);
        
        this.isConnected = true;
        console.log('✅ Connected to room');
    }
    
    /**
     * Room Events - klar strukturiert
     */
    setupRoomEvents() {
        // Connection Events
        this.room.on(LiveKit.RoomEvent.Connected, () => {
            console.log('🎉 Room connected');
            this.processExistingParticipants();
        });
        
        this.room.on(LiveKit.RoomEvent.Disconnected, () => {
            console.log('❌ Room disconnected');
            this.isConnected = false;
        });
        
        // Participant Events
        this.room.on(LiveKit.RoomEvent.ParticipantConnected, (participant) => {
            console.log('👤 Participant connected:', participant.identity);
            this.handleParticipantJoined(participant);
        });
        
        this.room.on(LiveKit.RoomEvent.ParticipantDisconnected, (participant) => {
            console.log('👤 Participant disconnected:', participant.identity);
            this.handleParticipantLeft(participant);
        });
        
        // Track Events - KRITISCH für Video
        this.room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log(`🎵 Track subscribed: ${track.kind} from ${participant.identity}`);
            this.handleTrackReceived(track, publication, participant);
        });
        
        this.room.on(LiveKit.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
            console.log(`🔇 Track unsubscribed: ${track.kind} from ${participant.identity}`);
            this.handleTrackRemoved(track, publication, participant);
        });
    }
    
    /**
     * Participant Management - simpel und klar
     */
    handleParticipantJoined(participant) {
        // Container erstellen
        const container = this.createParticipantContainer(participant);
        
        // Zu Map hinzufügen
        this.participants.set(participant.sid, {
            participant,
            container,
            videoTrack: null,
            audioTrack: null
        });
        
        // Grid aktualisieren
        this.updateGrid();
        
        console.log(`✅ Participant ${participant.identity} setup completed`);
    }
    
    handleParticipantLeft(participant) {
        const participantData = this.participants.get(participant.sid);
        if (participantData) {
            // Container entfernen
            participantData.container.remove();
            
            // Aus Map entfernen
            this.participants.delete(participant.sid);
            
            // Grid aktualisieren
            this.updateGrid();
        }
    }
    
    /**
     * Track Handling - DAS KERNPROBLEM
     */
    handleTrackReceived(track, publication, participant) {
        const participantData = this.participants.get(participant.sid);
        if (!participantData) {
            console.warn('⚠️ No participant data for track:', participant.identity);
            return;
        }
        
        if (track.kind === 'video') {
            this.attachVideoTrack(track, participantData);
        } else if (track.kind === 'audio') {
            this.attachAudioTrack(track, participantData);
        }
    }
    
    /**
     * Video Track Attachment - VEREINFACHT
     */
    attachVideoTrack(track, participantData) {
        const video = participantData.container.querySelector('video');
        if (!video) {
            console.error('❌ No video element found');
            return;
        }
        
        // Track anhängen
        track.attach(video);
        
        // Video Element konfigurieren
        video.autoplay = true;
        video.playsInline = true;
        video.muted = false; // Remote video NICHT muten
        
        // Play forcieren
        video.play().catch(e => console.log('Video play error:', e));
        
        // Track speichern
        participantData.videoTrack = track;
        
        console.log(`✅ Video track attached for ${participantData.participant.identity}`);
    }
    
    /**
     * Audio Track Attachment
     */
    attachAudioTrack(track, participantData) {
        const audio = participantData.container.querySelector('audio') || 
                     document.createElement('audio');
        
        if (!participantData.container.querySelector('audio')) {
            participantData.container.appendChild(audio);
        }
        
        track.attach(audio);
        audio.autoplay = true;
        audio.muted = false;
        
        participantData.audioTrack = track;
        
        console.log(`✅ Audio track attached for ${participantData.participant.identity}`);
    }
    
    /**
     * Container Creation - clean HTML
     */
    createParticipantContainer(participant) {
        const container = document.createElement('div');
        container.id = `participant-${participant.sid}`;
        container.className = 'participant-container';
        
        container.innerHTML = `
            <video autoplay playsinline></video>
            <div class="participant-name">${participant.identity}</div>
        `;
        
        // Zum Grid hinzufügen
        const grid = document.getElementById('participants-grid') || 
                    document.querySelector('.participants-grid');
        
        if (grid) {
            grid.appendChild(container);
        }
        
        return container;
    }
    
    /**
     * Local Media Setup
     */
    async setupLocalMedia() {
        if (!this.room.localParticipant) {
            throw new Error('No local participant');
        }
        
        // Kamera aktivieren
        if (this.videoEnabled) {
            await this.room.localParticipant.setCameraEnabled(true);
            console.log('✅ Camera enabled');
        }
        
        // Mikrofon aktivieren  
        if (this.audioEnabled) {
            await this.room.localParticipant.setMicrophoneEnabled(true);
            console.log('✅ Microphone enabled');
        }
        
        // Local Video anzeigen
        this.setupLocalVideo();
    }
    
    /**
     * Local Video Setup
     */
    setupLocalVideo() {
        const localContainer = this.createParticipantContainer(this.room.localParticipant);
        const localVideo = localContainer.querySelector('video');
        
        // Local Video Track finden und anhängen
        this.room.localParticipant.videoTrackPublications.forEach((publication) => {
            if (publication.track) {
                publication.track.attach(localVideo);
                localVideo.muted = true; // Local video MUTEN (Echo prevention)
                console.log('✅ Local video attached');
            }
        });
    }
    
    /**
     * Grid Layout Update
     */
    updateGrid() {
        const grid = document.getElementById('participants-grid') || 
                    document.querySelector('.participants-grid');
        
        if (!grid) return;
        
        const count = this.participants.size + 1; // +1 for local
        grid.className = `participants-grid grid-${Math.min(count, 4)}`;
    }
    
    /**
     * Existing Participants Processing
     */
    processExistingParticipants() {
        // Local Participant
        this.setupLocalVideo();
        
        // Remote Participants
        this.room.remoteParticipants.forEach((participant) => {
            this.handleParticipantJoined(participant);
            
            // Existing tracks
            participant.trackPublications.forEach((publication) => {
                if (publication.isSubscribed && publication.track) {
                    this.handleTrackReceived(publication.track, publication, participant);
                }
            });
        });
    }
    
    /**
     * Hilfsfunktionen
     */
    getParticipantName() {
        return sessionStorage.getItem('participantName') || 
               prompt('Ihr Name:') || 
               'Gast';
    }
    
    showError(title, message) {
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = `
            <h3>${title}</h3>
            <p>${message}</p>
            <button onclick="location.reload()">Neu laden</button>
        `;
        errorDiv.style.cssText = 'position:fixed;top:20%;left:50%;transform:translateX(-50%);background:white;padding:20px;border:2px solid red;z-index:9999;';
        document.body.appendChild(errorDiv);
    }
}

// Global Instance
window.simpleMeeting = new SimpleMeeting();

// Auto-Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.simpleMeeting.initialize();
    });
} else {
    window.simpleMeeting.initialize();
} 