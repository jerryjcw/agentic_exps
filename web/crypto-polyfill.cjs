const crypto = require('crypto');

// Polyfill for crypto.hash() for Node.js versions < 15.12.0
if (!crypto.hash) {
  crypto.hash = function(algorithm, data, outputEncoding = 'hex') {
    const hash = crypto.createHash(algorithm);
    hash.update(data);
    return hash.digest(outputEncoding);
  };
}

module.exports = crypto;