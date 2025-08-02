const express = require('express');
const axios = require('axios');
require('dotenv').config();

const app = express();
app.use(express.json());

// Middleware API Key lokal
app.use((req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  if (apiKey !== process.env.API_KEY_LOCAL) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  next();
});

/**
 * MCP Endpoint: escalate
 * Mengirim pesan ke owner via API WA Gateway
 */
app.post('/escalate', async (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'Message is required' });

  try {
    const payload = {
      api_key: process.env.WA_API_KEY,
      sender: process.env.WA_SENDER,
      number: process.env.WA_OWNER_NUMBER,
      message: message
    };

    const result = await axios.post(process.env.WA_ENDPOINT, payload, {
      headers: { 'Content-Type': 'application/json' }
    });

    res.json({
      success: true,
      sent_to: process.env.WA_OWNER_NUMBER,
      gateway_response: result.data
    });
  } catch (err) {
    console.error('Error sending message:', err.message);
    res.status(500).json({ error: 'Failed to send message to owner' });
  }
});
const path = require('path');

// Serve ai-plugin.json
app.get('/.well-known/ai-plugin.json', (req, res) => {
  res.sendFile(path.join(__dirname, 'ai-plugin.json'));
});

// Serve openapi.yaml
app.get('/openapi.yaml', (req, res) => {
  res.sendFile(path.join(__dirname, 'openapi.yaml'));
});


app.listen(process.env.PORT, () => {
  console.log(`MCP server berjalan di http://localhost:${process.env.PORT}`);
});
