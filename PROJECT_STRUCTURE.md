# Project Structure - Clean & Organized

## 📁 Core Application Files

### **Radio Streaming**
- `radio.py` - Main radio server (runs at https://radio.cobe.dev)
- `audio_mixer.py` - Mixes music with voice tracks, handles sponsored queue
- `shared_broadcast.py` - Manages shared broadcast stream
- `icecast_client.py` - Icecast source client for standard streaming protocol
- `audio_gen.py` - TTS generation using Kokoro
- `generate_test_voices.py` - Utility to generate test voice files

### **Admin Panel**
- `admin.py` - Admin interface for approving/rejecting bids

### **Frontend**
- `fasthtml_radio_player.ipynb` - Jupyter notebook with radio player UI

### **Configuration**
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (not in git)
- `icecast.xml` - Icecast server configuration

---

## 📚 Documentation (All Current & Useful)

### **Setup Guides**
- `QUICK_START_CLOUDFLARE.md` ⭐ - 10-minute Cloudflare Tunnel setup
- `CLOUDFLARE_TUNNEL_SETUP.md` - Detailed Cloudflare guide
- `RADIO_SYSTEMD_SERVICE.md` - Running radio 24/7

### **Feature Documentation**
- `ADMIN_README.md` - Admin panel usage
- `SPONSORED_MESSAGES_GUIDE.md` - Complete sponsored messages system
- `CHANGES_SUMMARY.md` - Implementation details

### **Reference**
- `kokoro.md` - TTS voice options

---

## 🛠️ Setup Scripts

### **Cloudflare Tunnel**
- `setup_cloudflare_tunnel.sh` - Complete Cloudflare setup
  - Commands: install, auth, create, route, daemon, status, logs

### **System Services**
- `setup_radio_service.sh` - Radio as systemd service
  - Commands: install, uninstall, status, logs, restart

### **Icecast Streaming**
- `setup_icecast.sh` - Icecast server installation and setup
  - Installs Icecast2 and ffmpeg
  - Configures icecast.xml
  - Starts Icecast service

---

## 📂 Media & Assets

### **Audio**
- `voices/01_welcome.wav` - Recurring track 1
- `voices/02_weather.wav` - Recurring track 2
- `voices/03_safety.wav` - Recurring track 3
- `voices/sponsored/` - One-time sponsored messages (auto-generated)
- `music/Martian_Elevator_Loop_*.wav` - Background music

### **Static Assets**
- `static/AsciiEffect.js` - Three.js ASCII effect
- `static/fdr.stl` - 3D model for background

---

## 🏗️ Blockchain

### **Smart Contracts**
- `arc-contract/src/RadioSponsor.sol` - Bid management contract
- `arc-contract/test/RadioSponsor.t.sol` - Contract tests

---

## 🗑️ Cleaned Up (Deleted)

### **Outdated Documentation**
- ❌ CORRECTED_ANALYSIS.md - Temporary fix document
- ❌ NOTEBOOK_FIX_GUIDE.md - Troubleshooting (issues fixed)

### **Old Certificate System**
- ❌ cert.pem - Self-signed certificate
- ❌ key.pem - Private key
- ❌ cert_backup_*/ - Certificate backups
- ❌ generate_cert.sh - Cert generation script
- ❌ setup_hostname.sh - Hosts file setup

**Reason:** Now using Cloudflare for HTTPS (no self-signed certs needed)

### **Replaced Files**
- ❌ testing.py - Old test file (replaced by Jupyter notebook)

---

## 🌐 Live URLs

### **HTTP Streams (Custom)**
- **Radio Stream (WAV):** https://radio.cobe.dev/radio/stream
- **Radio API:** https://radio.cobe.dev/radio/info
- **Icecast API:** https://radio.cobe.dev/radio/icecast

### **Icecast Streams (Standard Protocol)**
- **Icecast Stream (MP3):** http://localhost:8000/radio.mp3
  - Compatible with VLC, iTunes, WinAmp, and other standard players
  - Requires Icecast server to be running

### **Local Services**
- **Admin Panel:** http://localhost:5001 (local only)
- **Frontend:** http://localhost:8002 (Jupyter notebook)

---

## 🚀 Quick Start Commands

### Start Everything
```bash
# 1. Install and start Icecast (one-time setup)
sudo ./setup_icecast.sh

# 2. Start radio (background)
sudo systemctl start radio

# 3. Start Cloudflare tunnel (background)
sudo systemctl start cloudflared

# 4. Start admin panel (when needed)
python admin.py

# 5. Start Jupyter frontend (when needed)
jupyter notebook fasthtml_radio_player.ipynb
```

### Check Status
```bash
# Radio status
sudo systemctl status radio

# Icecast status
sudo systemctl status icecast2

# Tunnel status
sudo systemctl status cloudflared

# Test public URL
curl https://radio.cobe.dev/radio/info

# Test Icecast stream
curl http://localhost:8000/radio.mp3
```

---

## 📊 File Organization Summary

```
fasthtml/
├── Core Python Files (5)
│   ├── radio.py, audio_mixer.py, shared_broadcast.py
│   ├── audio_gen.py, admin.py
│
├── Documentation (7 .md files)
│   ├── Setup: QUICK_START_CLOUDFLARE.md, CLOUDFLARE_TUNNEL_SETUP.md
│   ├── Features: ADMIN_README.md, SPONSORED_MESSAGES_GUIDE.md
│   └── Reference: CHANGES_SUMMARY.md, kokoro.md
│
├── Setup Scripts (4 .sh files)
│   ├── setup_cloudflare_tunnel.sh
│   ├── setup_radio_service.sh
│   ├── setup_icecast.sh
│   └── test_sponsored_system.py
│
├── Media & Assets
│   ├── voices/ (3 recurring + sponsored/)
│   ├── music/ (background loops)
│   └── static/ (JS, 3D models)
│
└── Blockchain
    └── arc-contract/ (Solidity contracts)
```

**Total Cleanup:** Removed 9 obsolete files/folders

---

## 🎯 What Each File Does

### Core Workflow

```
User submits bid (Web3)
         ↓
  RadioSponsor.sol (blockchain)
         ↓
  admin.py (approve/reject)
         ↓
  audio_gen.py (TTS generation)
         ↓
  audio_mixer.py (mix with music)
         ↓
  shared_broadcast.py (live stream)
         ↓
  ┌──────────────┬──────────────┐
  │              │              │
radio.py      icecast_client.py
(HTTP WAV)    (MP3 encoding)
  │              │
  │              ↓
  │         Icecast Server
  │         (port 8000)
  │              │
  ↓              ↓
Cloudflare    Standard
Tunnel        Players
  │         (VLC, iTunes)
  ↓              │
https://         │
radio.cobe.dev   │
  │              │
  └──────┬───────┘
         ↓
    Users listen!
```

---

## 💡 Tips

1. **All documentation is current** - No outdated guides
2. **Certificates managed by Cloudflare** - No local SSL files
3. **Everything runs as services** - Survives reboots
4. **Test scripts included** - Easy to verify changes
5. **Clean separation** - Frontend, backend, admin, blockchain
6. **Dual streaming** - Both custom WAV and standard Icecast MP3 streams
7. **Icecast for compatibility** - Use Icecast stream for VLC, iTunes, etc.

---

## 🔒 Security Notes

- `.env` contains secrets (gitignored)
- `admin.py` is localhost-only
- Cloudflare hides server IP
- Private keys in `.env` never exposed
- Self-signed certs removed (not needed)
- **Icecast passwords** - Change default passwords in `icecast.xml` for production
  - Default source password: `hackme` (change this!)
  - Default admin password: `hackme` (change this!)

## 📻 Icecast Streaming

### **Hybrid Approach**
The radio server supports two streaming methods:

1. **Custom HTTP Stream (WAV)** - `/radio/stream`
   - Direct integration with web browsers
   - Uncompressed WAV format
   - Lower latency

2. **Icecast Stream (MP3)** - `http://localhost:8000/radio.mp3`
   - Standard streaming protocol
   - Compressed MP3 format (128 kbps)
   - Compatible with VLC, iTunes, WinAmp, mobile apps
   - Better for external players

### **Setup Icecast**
```bash
# Install and configure
sudo ./setup_icecast.sh

# Check status
sudo systemctl status icecast2

# View logs
sudo journalctl -u icecast2 -f
```

### **Configuration**
- Edit `icecast.xml` to change passwords, port, mount point
- Edit `radio.py` to adjust Icecast settings (host, port, format, bitrate)
- Set `ICECAST_ENABLED = False` to disable Icecast streaming

### **Testing**
```bash
# Test Icecast stream with VLC
vlc http://localhost:8000/radio.mp3

# Test with curl
curl http://localhost:8000/radio.mp3

# Check API
curl http://localhost:5002/radio/icecast
```

---

This structure is now clean, organized, and production-ready! 🎉

