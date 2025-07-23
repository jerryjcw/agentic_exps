const http = require('http');

console.log('Starting minimal server...');

const server = http.createServer((req, res) => {
  console.log(`Request: ${req.method} ${req.url}`);
  
  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
  });
  
  res.end(JSON.stringify({ message: 'Hello from minimal server', timestamp: Date.now() }));
});

server.on('error', (err) => {
  console.error('Server error:', err);
});

server.listen(3003, '127.0.0.1', () => {
  console.log('✅ Minimal server listening on http://127.0.0.1:3003');
});

console.log('Server setup complete, waiting for connections...');