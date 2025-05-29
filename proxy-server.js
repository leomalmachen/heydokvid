const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = 3002;

// Serve static files from frontend directory
app.use(express.static(path.join(__dirname, 'frontend')));

// Proxy API requests to backend
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:8001',
  changeOrigin: true,
  logLevel: 'debug'
}));

// Proxy health endpoint
app.use('/health', createProxyMiddleware({
  target: 'http://localhost:8001',
  changeOrigin: true
}));

// Serve index.html for all other routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'index.html'));
});

app.get('/meeting.html', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'meeting.html'));
});

app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`);
  console.log('Proxying /api/* to http://localhost:8001');
  console.log('Serving frontend files from ./frontend');
}); 