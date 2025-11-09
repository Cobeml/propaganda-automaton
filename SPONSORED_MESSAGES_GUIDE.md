# Sponsored Messages System - Complete Guide

## Overview

The radio sponsorship system now integrates blockchain-based bids with automated audio generation and live radio broadcasting. When you approve a bid in the admin panel, it:

1. ✅ Accepts the bid on the blockchain (transfers tokens to owner)
2. 🎙️ Generates TTS audio from the sponsor's message using Kokoro
3. 📻 Adds the audio to the radio broadcast queue
4. 🔊 Plays it ONCE on the radio (not recurring)

## Architecture

```
User submits bid (Web3)
         ↓
    Blockchain
         ↓
Admin approves bid → Transaction → Audio Generation → Radio Queue
         ↓                ↓                ↓              ↓
   RadioSponsor      (admin.py)      (audio_gen.py)  (radio.py)
     Contract                              ↓              ↓
                                    sponsored/*.wav   Plays Next
```

## Components

### 1. **RadioSponsor.sol** (Smart Contract)
- Stores bids on-chain
- Handles USDC token transfers
- Tracks bid status (Pending/Accepted/Rejected)

### 2. **admin.py** (Admin Panel)
- Displays pending bids
- Accept/Reject buttons for each bid
- **NEW**: When accepting:
  - Sends blockchain transaction
  - Generates audio file using `bm_lewis` voice
  - Saves to `voices/sponsored/`
  - Calls radio API to queue the message

### 3. **audio_gen.py** (TTS Generation)
- Uses Kokoro-82M TTS model
- Converts sponsor message text to audio
- Voice: `bm_lewis` (male British voice)
- Output: 24kHz WAV files

### 4. **audio_mixer.py** (Audio Mixing)
- **NEW**: Maintains two track lists:
  - **Recurring tracks**: Loop forever (hardcoded)
  - **Sponsored queue**: Play once, FIFO order
- Prioritizes sponsored messages
- Mixes voice with background music

### 5. **radio.py** (Radio Server)
- **NEW**: Uses hardcoded recurring voice files
- **NEW**: API endpoint `/radio/add_sponsored` to accept new sponsored messages
- Streams mixed audio to all connected clients
- Sponsored messages play next in queue

### 6. **shared_broadcast.py** (Broadcast Manager)
- **NEW**: `add_sponsored_message()` method
- Manages live audio stream
- All clients hear same audio simultaneously

## File Structure

```
fasthtml/
├── admin.py                    # Admin panel (approve/reject bids)
├── radio.py                    # Radio server
├── audio_gen.py                # TTS generation
├── audio_mixer.py              # Audio mixing logic
├── shared_broadcast.py         # Broadcast management
├── voices/
│   ├── 01_welcome.wav         # Recurring track 1
│   ├── 02_weather.wav         # Recurring track 2
│   ├── 03_safety.wav          # Recurring track 3
│   └── sponsored/             # Sponsored messages (one-time)
│       └── sponsored_1_20251108_123456.wav
└── music/
    └── Martian_Elevator_Loop.wav
```

## Configuration

### Environment Variables (.env)

```env
# Blockchain
RPC_URL=https://rpc.testnet.arc.network
CHAIN_ID=5042002
CONTRACT_ADDRESS=0x...  # Your RadioSponsor contract
OWNER_PRIVATE_KEY=0x... # Owner's private key for signing
USDC_ADDRESS=0x3600000000000000000000000000000000000000

# Radio Server
RADIO_SERVER_URL=https://localhost:5002
```

### Recurring Voice Files (radio.py)

Hardcoded list that loops continuously:

```python
RECURRING_VOICE_FILES = [
    "voices/01_welcome.wav",
    "voices/02_weather.wav",
    "voices/03_safety.wav"
]
```

These files play in order, on repeat, forever.

## How It Works

### Step 1: User Submits Bid

User connects wallet on the radio player page and submits:
- Amount (in USDC)
- Sponsor message text

Transaction goes to blockchain.

### Step 2: Admin Reviews Bid

Admin opens `admin.py` at `http://localhost:5001`:
- Sees list of pending bids
- Reads the message and amount
- Clicks **Approve** or **Reject**

### Step 3: Approval Process (The Magic!)

When you click **Approve**:

```
1. Blockchain Transaction
   ├─ Call acceptBid(bidId) on contract
   ├─ USDC transferred to owner
   └─ Wait for confirmation (120s timeout)

2. Audio Generation
   ├─ Extract message text from bid
   ├─ Generate audio with Kokoro TTS
   ├─ Voice: bm_lewis (British male)
   ├─ Speed: 1.0x
   └─ Save: voices/sponsored/sponsored_{bidId}_{timestamp}.wav

3. Radio Integration
   ├─ HTTP GET to https://localhost:5002/radio/add_sponsored?audio_file=...
   ├─ Radio adds to sponsored queue
   └─ Success message shown in admin panel

4. Playback
   ├─ Radio checks sponsored queue before each recurring track
   ├─ Finds new sponsored message
   ├─ Plays it NEXT (interrupts recurring playlist)
   ├─ Removes from queue after playing
   └─ Returns to recurring tracks
```

### Step 4: Radio Playback

The radio continuously:

1. Checks sponsored queue
2. If sponsored message exists → play it (once)
3. If no sponsored message → play next recurring track
4. Repeat

**Result**: Sponsored messages get priority and play immediately, but only once!

## API Endpoints

### Radio Server (radio.py)

#### GET /radio/stream
Live audio stream (all clients hear same audio)

#### GET /radio/info
```json
{
  "status": "live",
  "background_music": "Martian_Elevator_Loop.wav",
  "recurring_tracks": ["01_welcome.wav", "02_weather.wav", "03_safety.wav"],
  "recurring_count": 3,
  "now_playing": "01_welcome.wav",
  "is_paused": false
}
```

#### GET /radio/add_sponsored?audio_file=path/to/file.wav
Add sponsored message to queue

```json
{
  "success": true,
  "message": "Sponsored message added: sponsored_1_20251108.wav",
  "file": "voices/sponsored/sponsored_1_20251108.wav"
}
```

### Admin Panel (admin.py)

#### GET /
Main admin interface

#### GET /bids
Refresh bids list (HTMX endpoint)

#### POST /approve/{bid_id}
Approve bid → blockchain + audio + radio

#### POST /reject/{bid_id}
Reject bid → refund tokens

## Running the System

### 1. Start Radio Server

```bash
python radio.py
```

Output:
```
🎵 Web Radio Station Starting...
Loaded 3 recurring voice tracks
✅ Radio broadcast is live!
📻 Recurring tracks: 3
   - 01_welcome.wav
   - 02_weather.wav
   - 03_safety.wav
Access the radio at:
  Local:    https://localhost:5002
```

### 2. Start Admin Panel

```bash
python admin.py
```

Output:
```
Radio Sponsor Admin Panel starting...
Web3 connected: True
Contract loaded: 0x...
Admin panel ready at: http://localhost:5001
```

### 3. Approve a Bid

1. Open `http://localhost:5001` in browser
2. See pending bids
3. Click **Approve** on a bid
4. Watch console output:

```
✅ Bid 1 accepted on blockchain
📝 Generating audio for message: This is a test sponsor message...
Using device: cuda
GPU: NVIDIA GeForce RTX 3080
Initializing Kokoro pipeline...
Generating audio...
Segment 0: This is a test sponsor message
  Saved to: voices/sponsored/sponsored_1_20251108_143022.wav
🎙️  Audio generated: voices/sponsored/sponsored_1_20251108_143022.wav
📻 Added to radio queue successfully
```

### 4. Listen on Radio

Connect to `https://localhost:5002` in browser or media player.

When current track finishes, you'll hear:
1. **Sponsored message** (plays once)
2. Back to recurring tracks

## Troubleshooting

### "Audio generation failed"

**Cause**: Kokoro TTS model not installed or GPU issue

**Fix**:
```bash
pip install kokoro-onnx
# Test audio generation
python audio_gen.py
```

### "Radio server unreachable"

**Cause**: Radio server not running or wrong URL

**Fix**:
1. Check radio.py is running: `ps aux | grep radio.py`
2. Verify `RADIO_SERVER_URL` in .env
3. Check SSL certificate: `curl -k https://localhost:5002/radio/info`

### "Sponsored message doesn't play"

**Cause**: File not found or queue logic issue

**Fix**:
1. Check file exists: `ls -la voices/sponsored/`
2. Check radio logs for errors
3. Restart radio server
4. Try adding manually: `curl -k "https://localhost:5002/radio/add_sponsored?audio_file=voices/sponsored/test.wav"`

### "Transaction fails"

**Cause**: Bid already processed, insufficient gas, or network issue

**Fix**:
1. Check bid status on block explorer
2. Ensure owner wallet has gas (ARC tokens)
3. Check RPC connection: `w3.is_connected()`

## Adding New Recurring Tracks

To add more recurring voice files:

1. Generate audio:
```bash
python -c "from audio_gen import generate_audio; generate_audio('Your message here', 'voices/04_new_track.wav', 'bm_lewis')"
```

2. Edit `radio.py`:
```python
RECURRING_VOICE_FILES = [
    "voices/01_welcome.wav",
    "voices/02_weather.wav",
    "voices/03_safety.wav",
    "voices/04_new_track.wav",  # NEW
]
```

3. Restart radio server

## Voice Options

Available voices in Kokoro:
- `bm_lewis` - British male (default for sponsored messages)
- `af_heart` - American female
- `am_adam` - American male
- `bf_emma` - British female
- `af_bella`, `af_sarah`, `af_nicole`, `am_michael`, etc.

To change voice for sponsored messages, edit `admin.py`:
```python
audio_files = generate_audio(
    text=bid_message,
    output_path=str(output_file),
    voice="bf_emma",  # Change voice here
    lang_code="a",
    speed=1.0
)
```

## Security Notes

1. **Admin Panel**: No authentication - designed for local use only
2. **Private Key**: Stored in .env, never exposed to clients
3. **Radio API**: No auth, but only adds to queue (can't control playlist)
4. **SSL**: Self-signed cert for HTTPS (browser warnings expected)

## Future Enhancements

Potential improvements:
- [ ] Priority levels for sponsored messages (paid more = plays sooner)
- [ ] Scheduled playback times
- [ ] Multiple voice options per sponsor
- [ ] Audio effects (echo, reverb, etc.)
- [ ] Real-time queue visualization on radio player
- [ ] Webhook notifications when sponsored message plays
- [ ] Analytics (how many listeners heard each message)

## Summary

The system now provides a complete pipeline:

**Blockchain → Admin → Audio → Radio → Listeners**

1. User pays USDC to sponsor
2. Admin approves with one click
3. Audio generated automatically
4. Plays on live radio (one time)
5. All listeners hear it
6. Back to regular programming

Simple, automated, and decentralized! 🎉

