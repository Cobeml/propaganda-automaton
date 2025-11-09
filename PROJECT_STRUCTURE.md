# Project Structure - Clean & Organized

## 📁 Core Application Files

### **Radio Streaming**
- `radio.py` - Main radio server (runs at https://radio.cobe.dev)
- `audio_mixer.py` - Mixes music with voice tracks, handles sponsored queue
- `shared_broadcast.py` - Manages shared broadcast stream
- `audio_gen.py` - TTS generation using Kokoro
- `generate_test_voices.py` - Utility to generate test voice files

### **Admin Panel**
- `admin.py` - Admin interface for approving/rejecting bids

### **Frontend**
- `fasthtml_radio_player.ipynb` - Jupyter notebook with radio player UI

### **Configuration**
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (not in git)

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

- **Radio Stream:** https://radio.cobe.dev/radio/stream
- **Radio API:** https://radio.cobe.dev/radio/info
- **Admin Panel:** http://localhost:5001 (local only)
- **Frontend:** http://localhost:8002 (Jupyter notebook)

---

## 🚀 Quick Start Commands

### Start Everything
```bash
# 1. Start radio (background)
sudo systemctl start radio

# 2. Start Cloudflare tunnel (background)
sudo systemctl start cloudflared

# 3. Start admin panel (when needed)
python admin.py

# 4. Start Jupyter frontend (when needed)
jupyter notebook fasthtml_radio_player.ipynb
```

### Check Status
```bash
# Radio status
sudo systemctl status radio

# Tunnel status
sudo systemctl status cloudflared

# Test public URL
curl https://radio.cobe.dev/radio/info
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
├── Setup Scripts (3 .sh files)
│   ├── setup_cloudflare_tunnel.sh
│   ├── setup_radio_service.sh
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
  radio.py (HTTP server)
         ↓
  Cloudflare Tunnel
         ↓
  https://radio.cobe.dev
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

---

## 🔒 Security Notes

- `.env` contains secrets (gitignored)
- `admin.py` is localhost-only
- Cloudflare hides server IP
- Private keys in `.env` never exposed
- Self-signed certs removed (not needed)

---

This structure is now clean, organized, and production-ready! 🎉

