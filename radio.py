"""
Web Radio Streaming Server
Streams audio files continuously via HTTP endpoint with background music and voice overlays
"""

from fasthtml.common import *
from starlette.responses import StreamingResponse
import asyncio
from pathlib import Path
from audio_mixer import RadioMixer

app, rt = fast_app(debug=True)

# Configuration
MUSIC_DIR = Path("music")
VOICES_DIR = Path("voices")
CHUNK_SIZE = 8192  # 8KB chunks for streaming
MUSIC_VOLUME = 0.15  # Background music volume (0.0-1.0)
VOICE_VOLUME = 1.0   # Voice track volume (0.0-1.0)
PAUSE_DURATION = 10.0  # Seconds between voice tracks


async def mixed_audio_stream_generator():
    """
    Generate an infinite stream of mixed audio (background music + voices).

    Yields:
        Audio data chunks
    """
    # Get music file
    music_files = list(MUSIC_DIR.glob("*.wav"))
    if not music_files:
        raise FileNotFoundError("No music files found")

    music_file = music_files[0]

    # Check for voice files
    voice_files = list(VOICES_DIR.glob("*.wav"))
    if not voice_files:
        print("Warning: No voice files found, creating placeholder...")
        # We'll just stream music if no voices available
        # In production, you'd want to handle this differently

    # Create mixer
    mixer = RadioMixer(
        music_file=music_file,
        voices_dir=VOICES_DIR,
        music_volume=MUSIC_VOLUME,
        voice_volume=VOICE_VOLUME,
        pause_duration=PAUSE_DURATION
    )

    # Stream mixed audio
    for chunk in mixer.generate_stream(chunk_size=CHUNK_SIZE):
        yield chunk
        await asyncio.sleep(0.001)  # Small delay to prevent blocking


@rt("/radio/stream")
async def radio_stream():
    """
    Stream audio endpoint - plays music files on infinite loop.
    Access this endpoint to listen to the radio.
    """
    # Get the first WAV file in the music directory
    music_files = list(MUSIC_DIR.glob("*.wav"))

    if not music_files:
        return Response("No music files found in music directory", status_code=404)

    # Use the first music file found
    music_file = music_files[0]

    return StreamingResponse(
        audio_stream_generator(music_file),
        media_type="audio/wav",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Disposition": f'inline; filename="radio-stream.wav"',
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

    if not music_files:
        return {"error": "No music files found"}

    return {
        "status": "live",
        "current_track": music_files[0].name,
        "stream_url": "/radio/stream",
        "format": "WAV",
        "mode": "continuous_loop"
    }


if __name__ == "__main__":
    print("=" * 60)
    print("🎵 Web Radio Station Starting...")
    print("=" * 60)
    print(f"Music directory: {MUSIC_DIR.absolute()}")
    music_files = list(MUSIC_DIR.glob("*.wav"))
    if music_files:
        print(f"Now playing: {music_files[0].name}")
    else:
        print("⚠️  No music files found!")
    print("=" * 60)
    print("Access the radio at:")
    print("  Local:    http://localhost:5002")
    print("  Network:  http://<your-ip>:5002")
    print("  Stream:   http://<your-ip>:5002/radio/stream")
    print("=" * 60)
    serve(port=5002)
