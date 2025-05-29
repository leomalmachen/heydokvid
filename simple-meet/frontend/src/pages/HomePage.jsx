import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Box, Typography, Button, Paper } from '@mui/material';
import VideoCallIcon from '@mui/icons-material/VideoCall';
import axios from 'axios';

function HomePage() {
  const navigate = useNavigate();

  const createNewMeeting = async () => {
    try {
      const response = await axios.post('/api/rooms');
      const { roomId } = response.data;
      navigate(`/meet/${roomId}`);
    } catch (error) {
      console.error('Fehler beim Erstellen des Meetings:', error);
      alert('Fehler beim Erstellen des Meetings. Bitte versuchen Sie es erneut.');
    }
  };

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          py: 4,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 6,
            borderRadius: 2,
            textAlign: 'center',
            width: '100%',
            maxWidth: 500,
          }}
        >
          <VideoCallIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          
          <Typography variant="h3" component="h1" gutterBottom fontWeight="600">
            Simple Meet
          </Typography>
          
          <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
            Premium-Videokonferenzen. Jetzt für alle kostenlos.
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Erstellen Sie ein Meeting und teilen Sie den Link mit anderen Teilnehmern.
            Keine Anmeldung erforderlich.
          </Typography>
          
          <Button
            variant="contained"
            size="large"
            startIcon={<VideoCallIcon />}
            onClick={createNewMeeting}
            sx={{
              py: 1.5,
              px: 4,
              fontSize: '1.1rem',
              textTransform: 'none',
              borderRadius: 2,
            }}
          >
            Neues Meeting starten
          </Button>
          
          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-around' }}>
            <Box>
              <Typography variant="h6" fontWeight="500">
                Bis zu 100
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Teilnehmer
              </Typography>
            </Box>
            <Box>
              <Typography variant="h6" fontWeight="500">
                Keine
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Zeitbegrenzung
              </Typography>
            </Box>
            <Box>
              <Typography variant="h6" fontWeight="500">
                HD
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Videoqualität
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default HomePage; 