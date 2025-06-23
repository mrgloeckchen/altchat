// Crypto fix für Node.js Umgebung
global.crypto = require('crypto')

const express = require('express')
const baileys = require('@whiskeysockets/baileys')
const { default: makeWASocket, useMultiFileAuthState } = baileys

const app = express()
const port = 3000

app.use(express.json())

async function startSock() {
  // MultiFile Auth State laden
  const { state, saveCreds } = await useMultiFileAuthState('./auth_info')

  const sock = makeWASocket({
    auth: state,
    printQRInTerminal: true,
  })

  sock.ev.on('creds.update', saveCreds)

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect } = update
    if (connection === 'close') {
      const shouldReconnect = (lastDisconnect?.error?.output?.statusCode !== 401)
      console.log('Connection closed, reconnecting?', shouldReconnect)
      if (shouldReconnect) {
        startSock()
      }
    } else if (connection === 'open') {
      console.log('WhatsApp Webhook läuft auf Port', port)
    }
  })

  sock.ev.on('messages.upsert', ({ messages, type }) => {
    if (type === 'notify') {
      const msg = messages[0]
      if (!msg.key.fromMe && msg.message) {
        console.log('Neue Nachricht von', msg.key.remoteJid, ':', msg.message)
      }
    }
  })

  return sock
}

// Socket global speichern für den POST /send
startSock().then(sock => global.sock = sock)

app.post('/send', async (req, res) => {
  console.log("📥 Neue Anfrage an /send", req.body);
  const { number, message } = req.body;
  if (!number || !message) {
    return res.status(400).json({ status: 'error', message: 'Nummer oder Nachricht fehlt' });
  }
  try {
    await global.sock.sendMessage(number + '@s.whatsapp.net', { text: message });
    console.log(`✅ Nachricht an ${number} gesendet`);
    res.json({ status: 'success', message: 'Nachricht gesendet' });
  } catch (e) {
    console.error('❌ Fehler beim Senden:', e);
    res.status(500).json({ status: 'error', message: 'Senden fehlgeschlagen' });
  }
});


app.listen(port, () => {
  console.log(`Express Server läuft auf http://localhost:${port}`)
})