# 🟢 ALTCHAT v1.0.5-beta

*(WhatsApp Notification Bot included)*

AltChat is a secure, private, terminal-style web chat system designed for closed communities. It runs on a Flask + Socket.IO server with custom encoding and real-time features.

This version includes a WhatsApp Notification Bot to alert offline users when they receive a new message.

![Notification Preview](/screenschots/notify.jpg)

---

## 📁 Project Structure

```
altchat-project/
├── altchat/             # Flask-Socket.IO server (AltChat)
│   ├── templates/       # HTML files (chat, login, etc.)
│   ├── static/          # CSS, JS, fonts
│   ├── database/        # SQLite DBs
│   └── app.py           # Main server logic
│
├── whatsapp-bot/        # WhatsApp Notification Bot
│   ├── bot.cjs          # Node.js bot code
│   ├── package.json     # Bot dependencies
│   ├── package-lock.json
│   └── auth_info/       # WhatsApp session (auto-created)
└── README.md
```

---

## ⚙️ Requirements

* Python 3.10+
* Node.js v18+
* pip (Python)
* npm (Node.js)
* WhatsApp account for pairing

---

## 🥪 Installation

### 1. Clone the project

```bash
git clone https://github.com/mrgloeckchen/altchat.git
cd altchat
```

---

### 2. Install AltChat (Python backend)

```bash
cd altchat
pip install -r requirements.txt
```

> Make sure `flask`, `flask_socketio`, `eventlet`, `sqlite3`, etc. are installed.

---

### 3. Install WhatsApp Bot

```bash
cd ../whatsapp-bot
npm install
```

> This installs:
>
> * `@whiskeysockets/baileys`
> * `express`
> * `pino`
> * `qrcode-terminal`
> * `@hapi/boom`

---

## 🚀 Run the System

### 1. Start WhatsApp Bot

```bash
cd whatsapp-bot
node bot.cjs
```

> 🟡 On first launch, a QR code will appear in the terminal.
> Scan it using WhatsApp → Settings → Linked Devices.

---

### 2. Start AltChat Server

```bash
cd ../altchat
python3 app.py
```

Now visit:
👉 [http://localhost:5000](http://localhost:5000)

---

## 🔔 How Notifications Work

* If a user receives a message while **offline**,
* AltChat sends a `POST` to `http://localhost:3000/send`
* The bot delivers the message via WhatsApp.

✅ Format:

```json
{
  "number": "491234567890",
  "message": "New message in AltChat!"
}
```

---

## 🛡️ Security

* Auth system with admin & mod roles
* Offline user tracking
* User-specific color assignments
* Altsprache™ transformation system

---

## 📷 Screenshot

![WhatsApp Notification Preview](/altchat/screenshots)

---

## ❗ Don't Track This

Make sure `.gitignore` includes:

```
node_modules/
auth_info/
__pycache__/
*.db
.env
```

---

## 💡 Tip

You can create a `start_all.sh` script to run both services:

```bash
#!/bin/bash
(cd whatsapp-bot && node bot.cjs) &
(cd altchat && python3 app.py)
```

---

## 🥃 Maintainer

> Made with 💚 by [@mrgloeckchen](https://github.com/mrgloeckchen)
> Follow on TikTok & Instagram: [@mrgloeckchen](https://instagram.com/mrgloeckchen)

---

## 🧠 License

MIT – free to use, mod, remix & enhance.
