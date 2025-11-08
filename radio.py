"""
Web Radio Streaming Server
Streams audio files continuously via HTTP endpoint with background music and voice overlays
All clients tap into the same live broadcast
"""

from fasthtml.common import *
from starlette.responses import StreamingResponse
import asyncio
from pathlib import Path
from shared_broadcast import get_broadcast

app, rt = fast_app(debug=True)

# Configuration
MUSIC_DIR = Path("music")
VOICES_DIR = Path("voices")
CHUNK_SIZE = 8192  # 8KB chunks for streaming
MUSIC_VOLUME = 0.15  # Background music volume (0.0-1.0)
VOICE_VOLUME = 1.0   # Voice track volume (0.0-1.0)
PAUSE_DURATION = 10.0  # Seconds between voice tracks

# Broadcast instance (initialized on startup)
broadcast = None


@app.on_event("startup")
async def startup_event():
    """Initialize and start the shared broadcast on server startup"""
    global broadcast

    music_files = list(MUSIC_DIR.glob("*.wav"))
    if not music_files:
        print("⚠️  No music files found!")
        return

    # Create broadcast
    broadcast = get_broadcast(
        music_file=music_files[0],
        voices_dir=VOICES_DIR,
        music_volume=MUSIC_VOLUME,
        voice_volume=VOICE_VOLUME,
        pause_duration=PAUSE_DURATION
    )

    # Start background broadcast
    await broadcast.start()
    print("✅ Radio broadcast is live!")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the broadcast on server shutdown"""
    if broadcast:
        await broadcast.stop()


@rt("/radio/stream")
async def radio_stream():
    """
    Stream audio endpoint - taps into the live broadcast.
    All clients hear the same audio at the same time.
    """
    if broadcast is None:
        return Response("Broadcast not initialized", status_code=503)

    # Subscribe to the live broadcast
    return StreamingResponse(
        broadcast.subscribe(),
        media_type="audio/wav",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Disposition": 'inline; filename="radio-stream.wav"',
        }
    )


@rt("/")
def get():
    """
    Radio player interface with styled audio player
    """
    return Html(
        Head(
            Title("Web Radio Station"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Style("""
                body {
                    margin: 0;
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }

                .radio-container {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    text-align: center;
                    max-width: 500px;
                    width: 90%;
                }

                h1 {
                    color: #333;
                    margin-bottom: 10px;
                    font-size: 2.5em;
                }

                .subtitle {
                    color: #666;
                    margin-bottom: 30px;
                    font-size: 1.1em;
                }

                .now-playing {
                    background: #f0f0f0;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }

                .now-playing-label {
                    color: #888;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }

                .track-name {
                    color: #333;
                    font-size: 1.2em;
                    font-weight: bold;
                    margin-top: 5px;
                }

                audio {
                    width: 100%;
                    margin: 20px 0;
                    border-radius: 10px;
                }

                .status {
                    display: inline-block;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    margin-top: 20px;
                }

                .status.live {
                    background: #ff4444;
                    color: white;
                    animation: pulse 2s infinite;
                }

                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }

                .info {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 0.9em;
                }

                .stream-url {
                    background: #f8f8f8;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    word-break: break-all;
                    margin-top: 10px;
                }
            """)
        ),
        Body(
            Div(
                H1("🎵 Web Radio"),
                Div("Broadcasting Live", cls="subtitle"),

                Div(
                    Div("NOW PLAYING", cls="now-playing-label"),
                    Div("Martian Elevator Loop", cls="track-name", id="track-name"),
                    cls="now-playing"
                ),

                Audio(
                    Source(src="/radio/stream", type="audio/wav"),
                    controls=True,
                    preload="none",
                    id="radio-player"
                ),

                Span("🔴 LIVE", cls="status live"),

                Div(
                    P("Stream URL (for external players):"),
                    Div(id="stream-url", cls="stream-url"),
                    P("Compatible with VLC, iTunes, WinAmp, and web browsers"),
                    cls="info"
                ),

                Script("""
                    // Display the stream URL
                    const streamUrl = window.location.origin + '/radio/stream';
                    document.getElementById('stream-url').textContent = streamUrl;

                    // Auto-detect track name from first music file
                    const trackName = document.getElementById('track-name');

                    // Optional: Add player event listeners
                    const player = document.getElementById('radio-player');
                    player.addEventListener('play', () => {
                        console.log('Radio started streaming');
                    });
                    player.addEventListener('error', (e) => {
                        console.error('Streaming error:', e);
                    });
                """),

                cls="radio-container"
            )
        )
    )


@rt("/radio/info")
def radio_info():
    """API endpoint to get information about current stream"""
    music_files = list(MUSIC_DIR.glob("*.wav"))
    voice_files = list(VOICES_DIR.glob("*.wav"))

    if not music_files:
        return {"error": "No music files found"}

    # Get current playback state from broadcast
    current_track = "Waiting for broadcast..."
    is_paused = False
    if broadcast is not None:
        current_track, is_paused = broadcast.get_current_track()

    info = {
        "status": "live",
        "background_music": music_files[0].name,
        "voice_tracks": [v.name for v in sorted(voice_files)],
        "voice_count": len(voice_files),
        "stream_url": "/radio/stream",
        "format": "WAV",
        "mode": "shared_broadcast",
        "music_volume": MUSIC_VOLUME,
        "voice_volume": VOICE_VOLUME,
        "pause_duration": PAUSE_DURATION,
        "now_playing": current_track,
        "is_paused": is_paused
    }

    return info


if __name__ == "__main__":
    print("=" * 60)
    print("🎵 Web Radio Station Starting...")
    print("=" * 60)
    print(f"Music directory: {MUSIC_DIR.absolute()}")
    print(f"Voices directory: {VOICES_DIR.absolute()}")
    print()

    music_files = list(MUSIC_DIR.glob("*.wav"))
    if music_files:
        print(f"🎼 Background music: {music_files[0].name}")
        print(f"   Volume: {MUSIC_VOLUME * 100:.0f}%")
    else:
        print("⚠️  No music files found!")

    print()
    voice_files = sorted(VOICES_DIR.glob("*.wav"))
    if voice_files:
        print(f"🎙️  Voice tracks: {len(voice_files)} files")
        for vf in voice_files:
            print(f"   - {vf.name}")
        print(f"   Volume: {VOICE_VOLUME * 100:.0f}%")
        print(f"   Pause between: {PAUSE_DURATION}s")
    else:
        print("⚠️  No voice files found!")
        print("   Generate some with: python audio_gen.py")

    print("=" * 60)
    print("Access the radio at:")
    print("  Local:    http://localhost:5002")
    print("  Network:  http://<your-ip>:5002")
    print("  Stream:   http://<your-ip>:5002/radio/stream")
    print("=" * 60)
    serve(port=5002)
