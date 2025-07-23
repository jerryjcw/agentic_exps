#!/usr/bin/env node

const http = require('http');

const server = http.createServer((req, res) => {
  console.log(`${req.method} ${req.url}`);
  
  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  });
  
  res.end(JSON.stringify({ status: 'ok', method: req.method, url: req.url }));
});

server.listen(3002, () => {
  console.log('Test server running on http://localhost:3002');
});