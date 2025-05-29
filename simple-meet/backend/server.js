const express = require('express');
const http = require('http');
const socketIO = require('socket.io');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');
const path = require('path');

const app = express();
const server = http.createServer(app);

// CORS-Konfiguration
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3001',
  credentials: true
}));

app.use(express.json());

// Serve static files from the React app build directory
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../frontend/dist')));
}

// Socket.io mit CORS
const io = socketIO(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3001',
    methods: ['GET', 'POST'],
    credentials: true
  }
});

// Speichere aktive Räume und Teilnehmer
const rooms = new Map();

// REST API Endpoints
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Erstelle einen neuen Meeting-Raum
app.post('/api/rooms', (req, res) => {
  const roomId = uuidv4();
  rooms.set(roomId, {
    id: roomId,
    participants: new Map(),
    createdAt: new Date()
  });
  res.json({ roomId });
});

// Überprüfe ob ein Raum existiert
app.get('/api/rooms/:roomId', (req, res) => {
  const { roomId } = req.params;
  const room = rooms.get(roomId);
  
  if (room) {
    res.json({ 
      exists: true, 
      participantCount: room.participants.size 
    });
  } else {
    res.json({ exists: false });
  }
});

// Socket.io Verbindungen
io.on('connection', (socket) => {
  console.log('Neue Socket-Verbindung:', socket.id);

  socket.on('join-room', ({ roomId, userName }) => {
    console.log(`${userName} tritt Raum ${roomId} bei`);
    
    // Erstelle Raum falls nicht vorhanden
    if (!rooms.has(roomId)) {
      rooms.set(roomId, {
        id: roomId,
        participants: new Map(),
        createdAt: new Date()
      });
    }

    const room = rooms.get(roomId);
    
    // Füge Teilnehmer hinzu
    room.participants.set(socket.id, {
      id: socket.id,
      userName,
      joinedAt: new Date()
    });

    // Trete Socket.io Raum bei
    socket.join(roomId);

    // Informiere andere Teilnehmer
    socket.to(roomId).emit('user-joined', {
      userId: socket.id,
      userName
    });

    // Sende Liste aller Teilnehmer an den neuen User
    const otherParticipants = Array.from(room.participants.entries())
      .filter(([id]) => id !== socket.id)
      .map(([id, data]) => ({ userId: id, userName: data.userName }));
    
    socket.emit('existing-participants', otherParticipants);

    // Speichere Raum-Info im Socket
    socket.roomId = roomId;
    socket.userName = userName;
  });

  // WebRTC Signaling
  socket.on('offer', ({ offer, to }) => {
    console.log('Weiterleitung Offer von', socket.id, 'an', to);
    socket.to(to).emit('offer', {
      offer,
      from: socket.id,
      userName: socket.userName
    });
  });

  socket.on('answer', ({ answer, to }) => {
    console.log('Weiterleitung Answer von', socket.id, 'an', to);
    socket.to(to).emit('answer', {
      answer,
      from: socket.id
    });
  });

  socket.on('ice-candidate', ({ candidate, to }) => {
    console.log('Weiterleitung ICE Candidate von', socket.id, 'an', to);
    socket.to(to).emit('ice-candidate', {
      candidate,
      from: socket.id
    });
  });

  // Trennung
  socket.on('disconnect', () => {
    console.log('Socket getrennt:', socket.id);
    
    if (socket.roomId) {
      const room = rooms.get(socket.roomId);
      if (room) {
        room.participants.delete(socket.id);
        
        // Informiere andere Teilnehmer
        socket.to(socket.roomId).emit('user-left', {
          userId: socket.id,
          userName: socket.userName
        });

        // Lösche leere Räume
        if (room.participants.size === 0) {
          rooms.delete(socket.roomId);
          console.log('Raum gelöscht:', socket.roomId);
        }
      }
    }
  });
});

// Catch-all handler: send back React's index.html file for production
if (process.env.NODE_ENV === 'production') {
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/dist/index.html'));
  });
}

const PORT = process.env.PORT || 5001;
server.listen(PORT, () => {
  console.log(`Server läuft auf Port ${PORT}`);
}); 